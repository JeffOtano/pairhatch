"""Durable local protocol state. Transport admission is not proof of peer receipt.

No content filter or model isolation is claimed here. Caller must perform an
explicitly authorized transport action only after claim succeeds. A crash after
claim remains attempted forever; inspect/cancel it, never automatically retry.
"""
import hashlib
import json
import math
import os
import re
import sqlite3
import stat
import threading
import time
from contextlib import contextmanager

PROTOCOL_VERSION = 10


class Refused(ValueError):
    pass


def _identifier(value, name='identifier'):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:@/-]{0,127}', value):
        raise Refused('Invalid ' + name)
    return value


def _text(value, name, limit=8192):
    if not isinstance(value, str) or not value.strip():
        raise Refused(name + ' must be nonempty text')
    try:
        encoded = value.encode('utf-8')
    except UnicodeError as exc:
        raise Refused('Invalid Unicode') from exc
    if len(encoded) > limit or any((ord(c) < 32 and c not in '\t\n') or 127 <= ord(c) <= 159 for c in value):
        raise Refused(name + ' exceeds size or contains controls')
    return value


class Store:
    def __init__(self, path, clock=time.time):
        self.clock = clock
        self._lock = threading.RLock()
        self._savepoint_counter = 0
        path = os.path.abspath(os.fspath(path))
        # Require a private directory: this also protects SQLite's journal files.
        parent = os.path.dirname(path)
        os.makedirs(parent, mode=0o700, exist_ok=True)
        components = parent.split(os.sep)
        current = os.sep
        for component in components[1:]:
            current = os.path.join(current, component)
            if stat.S_ISLNK(os.lstat(current).st_mode):
                raise Refused('Symlink path component refused')
        pstat = os.stat(parent)
        if pstat.st_uid != os.getuid() or pstat.st_mode & 0o077:
            raise Refused('Database directory must be owned by you and mode 0700')
        flags = os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0)
        fd = os.open(path, flags, 0o600)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
                raise Refused('Unsafe database file')
            if info.st_mode & 0o077:
                raise Refused('Database must have private permissions (0600)')
        finally:
            os.close(fd)
        self.db = sqlite3.connect(path, timeout=10, isolation_level=None, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.execute('PRAGMA synchronous=FULL')
        try:
            with self._tx():
                tables = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if tables and 'metadata' not in tables:
                    raise Refused('Unrecognized database; migration refused')
                if 'metadata' in tables:
                    version = self.db.execute("SELECT value FROM metadata WHERE key='protocol_version'").fetchone()
                    if version is None or version[0] != str(PROTOCOL_VERSION):
                        raise Refused('Unsupported protocol version; migration refused')
                for sql in [
                    'CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)',
                    '''CREATE TABLE IF NOT EXISTS grants (grant_id TEXT PRIMARY KEY, participants TEXT NOT NULL,
                    topic TEXT NOT NULL, expires REAL NOT NULL, max_messages INTEGER NOT NULL,
                    max_consultations INTEGER NOT NULL, consultations_used INTEGER NOT NULL DEFAULT 0,
                    revoked INTEGER NOT NULL DEFAULT 0)''',
                    '''CREATE TABLE IF NOT EXISTS consultations (consultation_id TEXT PRIMARY KEY,
                    grant_id TEXT NOT NULL REFERENCES grants(grant_id), initiator TEXT NOT NULL,
                    pair TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'active', messages_used INTEGER NOT NULL DEFAULT 0)''',
                    "CREATE UNIQUE INDEX IF NOT EXISTS active_pair ON consultations(pair) WHERE state='active'",
                    '''CREATE TABLE IF NOT EXISTS messages (message_id TEXT PRIMARY KEY,
                    consultation_id TEXT NOT NULL REFERENCES consultations(consultation_id), sequence INTEGER NOT NULL,
                    sender TEXT NOT NULL, recipient TEXT NOT NULL, text TEXT NOT NULL, kind TEXT NOT NULL,
                    in_reply_to TEXT REFERENCES messages(message_id), state TEXT NOT NULL DEFAULT 'queued',
                    detail TEXT NOT NULL DEFAULT '', created REAL NOT NULL,
                    UNIQUE(consultation_id, sequence))''',
                    'CREATE INDEX IF NOT EXISTS recipient_inbox ON messages(recipient,state,consultation_id,sequence)',
                ]:
                    self.db.execute(sql)
                self.db.execute("INSERT OR IGNORE INTO metadata VALUES ('protocol_version', ?)", (str(PROTOCOL_VERSION),))
                self.db.execute("INSERT OR IGNORE INTO metadata VALUES ('paused','0')")
        except Exception:
            self.db.close()
            raise

    @contextmanager
    def _tx(self):
        with self._lock:
            nested = self.db.in_transaction
            self._savepoint_counter += 1
            savepoint = 'nested_' + str(self._savepoint_counter)
            self.db.execute('SAVEPOINT ' + savepoint if nested else 'BEGIN IMMEDIATE')
            try:
                yield
                self.db.execute('RELEASE SAVEPOINT ' + savepoint if nested else 'COMMIT')
            except BaseException:
                if nested:
                    self.db.execute('ROLLBACK TO SAVEPOINT ' + savepoint)
                    self.db.execute('RELEASE SAVEPOINT ' + savepoint)
                else:
                    self.db.execute('ROLLBACK')
                raise

    def bind_peers(self, peers):
        """Bind this state database to immutable, JSON-serializable peer routes.

        This is configuration consistency, not authentication. The trusted host
        must call this before using grants and must never put secrets in peers.
        """
        if not isinstance(peers, dict) or not peers or any(not isinstance(k, str) for k in peers):
            raise Refused('Peers must be a nonempty mapping with string keys')
        try:
            canonical = json.dumps(peers, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise Refused('Peers must contain canonical JSON data') from exc
        digest = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
        with self._tx():
            previous = self.db.execute("SELECT value FROM metadata WHERE key='peer_routes'").fetchone()
            if previous is not None and previous[0] != canonical:
                raise Refused('Peer routes changed for existing database')
            self.db.execute("INSERT OR IGNORE INTO metadata VALUES ('peer_routes', ?)", (canonical,))
            self.db.execute("INSERT OR IGNORE INTO metadata VALUES ('peer_routes_sha256', ?)", (digest,))
            return {'peer_routes_sha256': digest}

    def open_question(self, grant_id, consultation_id, message_id, sender, recipient, text):
        """Atomically open a consultation and queue its first question.

        Invalid payloads cannot consume consultation budgets or hold pair locks.
        Existing IDs retain the same immutable replay checks as the basic API.
        """
        with self._tx():
            self.open_consultation(grant_id, consultation_id, sender)
            return self.enqueue(consultation_id, message_id, sender, recipient, text)

    def close(self):
        with self._lock:
            self.db.close()

    def _get(self, table, key, value):
        row = self.db.execute(f'SELECT * FROM {table} WHERE {key}=?', (value,)).fetchone()
        if row is None:
            raise Refused('Unknown ' + key)
        result = dict(row)
        if table == 'grants':
            result['participants'] = json.loads(result['participants'])
        return result

    def _enabled(self, grant):
        if self.db.execute("SELECT value FROM metadata WHERE key='paused'").fetchone()[0] == '1':
            raise Refused('Globally paused')
        if grant['revoked']:
            raise Refused('Grant revoked')
        if self.clock() >= grant['expires']:
            raise Refused('Grant expired')

    def create_grant(self, grant_id, participants, topic, expires, max_messages=6, max_consultations=20):
        _identifier(grant_id)
        if not isinstance(participants, list) or len(participants) != 2:
            raise Refused('Exactly two participants required')
        participants = sorted(_identifier(p, 'participant') for p in participants)
        if participants[0] == participants[1]:
            raise Refused('Participants must differ')
        _text(topic, 'topic')
        if isinstance(expires, bool) or not isinstance(expires, (int, float)) or not math.isfinite(expires):
            raise Refused('Invalid expiration')
        if type(max_messages) is not int or not 1 <= max_messages <= 6 or type(max_consultations) is not int or not 1 <= max_consultations <= 20:
            raise Refused('Invalid budgets')
        payload = dict(grant_id=grant_id, participants=participants, topic=topic, expires=expires,
                       max_messages=max_messages, max_consultations=max_consultations)
        with self._tx():
            if self.db.execute('SELECT 1 FROM grants WHERE grant_id=?', (grant_id,)).fetchone():
                old = self._get('grants', 'grant_id', grant_id)
                if any(old[k] != v for k, v in payload.items()):
                    raise Refused('Grant ID payload mismatch')
                return old
            if expires <= self.clock():
                raise Refused('Expiration must be in the future')
            self.db.execute('INSERT INTO grants(grant_id,participants,topic,expires,max_messages,max_consultations) VALUES (?,?,?,?,?,?)',
                            (grant_id, json.dumps(participants), topic, expires, max_messages, max_consultations))
            return self._get('grants', 'grant_id', grant_id)

    def open_consultation(self, grant_id, consultation_id, initiator):
        for v in (grant_id, consultation_id, initiator):
            _identifier(v)
        with self._tx():
            if self.db.execute('SELECT 1 FROM consultations WHERE consultation_id=?', (consultation_id,)).fetchone():
                old = self._get('consultations', 'consultation_id', consultation_id)
                if old['grant_id'] != grant_id or old['initiator'] != initiator:
                    raise Refused('Consultation ID payload mismatch')
                return old
            g = self._get('grants', 'grant_id', grant_id)
            self._enabled(g)
            if initiator not in g['participants']:
                raise Refused('Initiator outside grant')
            if g['consultations_used'] >= g['max_consultations']:
                raise Refused('Consultation budget exhausted')
            pair = json.dumps(g['participants'])
            # Expired grants cannot retain the pair lock indefinitely.
            self.db.execute("UPDATE consultations SET state='expired' WHERE state='active' AND grant_id IN (SELECT grant_id FROM grants WHERE expires<=?)", (self.clock(),))
            if self.db.execute("SELECT 1 FROM consultations WHERE pair=? AND state='active'", (pair,)).fetchone():
                raise Refused('Pair already has an active consultation')
            self.db.execute('INSERT INTO consultations(consultation_id,grant_id,initiator,pair) VALUES (?,?,?,?)', (consultation_id, grant_id, initiator, pair))
            self.db.execute('UPDATE grants SET consultations_used=consultations_used+1 WHERE grant_id=?', (grant_id,))
            return self._get('consultations', 'consultation_id', consultation_id)

    def enqueue(self, consultation_id, message_id, sender, recipient, text, kind='question', in_reply_to=None):
        for v in (consultation_id, message_id, sender, recipient):
            _identifier(v)
        _text(text, 'text')
        if kind not in ('question', 'answer', 'final'):
            raise Refused('Kind must be question, answer, or final')
        if in_reply_to is not None:
            _identifier(in_reply_to)
        payload = dict(consultation_id=consultation_id, message_id=message_id, sender=sender,
                       recipient=recipient, text=text, kind=kind, in_reply_to=in_reply_to)
        with self._tx():
            if self.db.execute('SELECT 1 FROM messages WHERE message_id=?', (message_id,)).fetchone():
                old = self._get('messages', 'message_id', message_id)
                if any(old[k] != v for k, v in payload.items()):
                    raise Refused('Message ID payload mismatch')
                return old
            c = self._get('consultations', 'consultation_id', consultation_id)
            g = self._get('grants', 'grant_id', c['grant_id'])
            self._enabled(g)
            if c['state'] != 'active':
                raise Refused('Consultation is not active')
            if sorted([sender, recipient]) != g['participants']:
                raise Refused('Message outside immutable pair')
            if c['messages_used'] >= g['max_messages']:
                raise Refused('Message budget exhausted')
            previous = self.db.execute('SELECT * FROM messages WHERE consultation_id=? ORDER BY sequence DESC LIMIT 1', (consultation_id,)).fetchone()
            if previous:
                if previous['state'] != 'accepted':
                    raise Refused('Previous message not safely admitted')
                if sender != previous['recipient'] or recipient != previous['sender'] or in_reply_to != previous['message_id']:
                    raise Refused('Reply must alternate and link last admitted message')
            elif sender != c['initiator'] or in_reply_to is not None or kind != 'question':
                raise Refused('First message must be initiator question without reply link')
            self.db.execute('''INSERT INTO messages(message_id,consultation_id,sequence,sender,recipient,text,kind,in_reply_to,created)
                            VALUES (?,?,?,?,?,?,?,?,?)''', (message_id, consultation_id, c['messages_used']+1, sender, recipient, text, kind, in_reply_to, self.clock()))
            self.db.execute('UPDATE consultations SET messages_used=messages_used+1 WHERE consultation_id=?', (consultation_id,))
            return self._get('messages', 'message_id', message_id)

    def claim(self, message_id):
        with self._tx():
            m = self._get('messages', 'message_id', message_id)
            c = self._get('consultations', 'consultation_id', m['consultation_id'])
            self._enabled(self._get('grants', 'grant_id', c['grant_id']))
            if c['state'] != 'active' or m['state'] != 'queued':
                raise Refused('Message cannot be claimed; never retry attempted sends')
            self.db.execute("UPDATE messages SET state='attempted' WHERE message_id=?", (message_id,))
            return self._get('messages', 'message_id', message_id)

    def settle(self, message_id, outcome, detail=''):
        if outcome not in ('accepted', 'unknown', 'rejected'):
            raise Refused('Invalid outcome')
        if detail:
            _text(detail, 'detail')
        elif not isinstance(detail, str):
            raise Refused('Detail must be text')
        with self._tx():
            m = self._get('messages', 'message_id', message_id)
            if m['state'] == outcome and m['detail'] == detail:
                return m
            if m['state'] != 'attempted':
                raise Refused('Only attempted messages can settle')
            self.db.execute('UPDATE messages SET state=?,detail=? WHERE message_id=?', (outcome, detail, message_id))
            c = self._get('consultations', 'consultation_id', m['consultation_id'])
            g = self._get('grants', 'grant_id', c['grant_id'])
            if outcome == 'rejected' or (outcome == 'accepted' and (m['kind'] == 'final' or c['messages_used'] >= g['max_messages'])):
                self.db.execute("UPDATE consultations SET state=? WHERE consultation_id=? AND state='active'", ('rejected' if outcome == 'rejected' else 'completed', c['consultation_id']))
            return self._get('messages', 'message_id', message_id)

    def get_grant(self, grant_id):
        with self._lock:
            return self._get('grants', 'grant_id', grant_id)

    def get_message(self, message_id):
        with self._lock:
            return self._get('messages', 'message_id', message_id)

    def get_consultation(self, consultation_id):
        with self._lock:
            return self._get('consultations', 'consultation_id', consultation_id)

    def list_messages(self, consultation_id=None):
        with self._lock:
            if consultation_id is None:
                rows = self.db.execute('SELECT * FROM messages ORDER BY consultation_id,sequence').fetchall()
            else:
                rows = self.db.execute('SELECT * FROM messages WHERE consultation_id=? ORDER BY sequence', (consultation_id,)).fetchall()
            return [dict(r) for r in rows]

    def inbox(self, recipient, limit=100, offset=0):
        """Bounded SQL-side filtering; offset pagination assumes a quiet inbox."""
        _identifier(recipient, 'recipient')
        if type(limit) is not int or not 1 <= limit <= 100:
            raise Refused('Inbox limit must be an integer from 1 to 100')
        if type(offset) is not int or not 0 <= offset <= 9223372036854775807:
            raise Refused('Inbox offset must be a nonnegative SQLite integer')
        with self._lock:
            rows = self.db.execute(
                "SELECT * FROM messages WHERE recipient=? AND state='accepted' "
                "ORDER BY consultation_id,sequence LIMIT ? OFFSET ?",
                (recipient, limit, offset)).fetchall()
            return [dict(row) for row in rows]

    def pause(self):
        with self._tx():
            self.db.execute("UPDATE metadata SET value='1' WHERE key='paused'")
        return self.status()

    def resume(self):
        with self._tx():
            self.db.execute("UPDATE metadata SET value='0' WHERE key='paused'")
        return self.status()

    def cancel(self, consultation_id):
        with self._tx():
            self._get('consultations', 'consultation_id', consultation_id)
            self.db.execute("UPDATE consultations SET state='cancelled' WHERE consultation_id=? AND state='active'", (consultation_id,))
            return self._get('consultations', 'consultation_id', consultation_id)

    def revoke_grant(self, grant_id):
        with self._tx():
            self._get('grants', 'grant_id', grant_id)
            self.db.execute('UPDATE grants SET revoked=1 WHERE grant_id=?', (grant_id,))
            self.db.execute("UPDATE consultations SET state='revoked' WHERE grant_id=? AND state='active'", (grant_id,))
            return self._get('grants', 'grant_id', grant_id)

    def status(self):
        with self._tx():
            return dict(protocol_version=PROTOCOL_VERSION,
                        paused=self.db.execute("SELECT value FROM metadata WHERE key='paused'").fetchone()[0] == '1',
                        grants=self.db.execute('SELECT COUNT(*) FROM grants').fetchone()[0],
                        consultations=self.db.execute('SELECT COUNT(*) FROM consultations').fetchone()[0],
                        messages=self.db.execute('SELECT COUNT(*) FROM messages').fetchone()[0],
                        message_states={r[0]:r[1] for r in self.db.execute('SELECT state,COUNT(*) FROM messages GROUP BY state')})

