import contextlib
import io
import json
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import test_engine
from pairhatch.__main__ import main as cli
from pairhatch.init_config import main as initialize
from pairhatch.mcp import handle
from pairhatch.store import Refused
from pairhatch.transports import ClaudeSocket, PreflightRejected


class InboxTests(unittest.TestCase):
    setUp = test_engine.EngineTests.setUp
    tearDown = test_engine.EngineTests.tearDown

    def test_sql_filters_and_paginates_without_loading_other_actors(self):
        self.a.ask('g', 'claude', 'First question', 'a', 'm1')
        self.b.reply('a', 'm1', 'First answer', True, 'm2')
        self.a.ask('g', 'claude', 'Second question', 'b', 'm3')
        with patch.object(self.s, 'list_messages', side_effect=AssertionError('Unbounded read')):
            self.assertEqual([m['message_id'] for m in self.b.inbox(1, 0)], ['m1'])
            self.assertEqual([m['message_id'] for m in self.b.inbox(1, 1)], ['m3'])
            self.assertEqual(self.b.inbox(1, 2), [])
            self.assertEqual([m['message_id'] for m in self.a.inbox()], ['m2'])

    def test_rejects_invalid_page_bounds(self):
        for limit, offset in ((0, 0), (101, 0), (True, 0), (1.5, 0), (1, -1), (1, True), (1, 2**63)):
            with self.subTest(limit=limit, offset=offset), self.assertRaises(Refused):
                self.b.inbox(limit, offset)

    def test_mcp_pagination(self):
        self.a.ask('g', 'claude', 'Question', 'a', 'm1')
        request = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                   'params': {'name': 'peer_inbox', 'arguments': {'limit': 1, 'offset': 1}}}
        result = handle(self.b, request)
        self.assertEqual(json.loads(result['content'][0]['text']), [])
        request['params']['arguments']['limit'] = True
        with self.assertRaises(Refused):
            handle(self.b, request)


class OperatorTests(unittest.TestCase):
    def doctor(self, failures):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp).resolve() / 'demo'
            with contextlib.redirect_stdout(io.StringIO()):
                initialize(['--directory', str(directory)])
            output = io.StringIO()
            with patch('pairhatch.transports.MockTransport.preflight', side_effect=failures), contextlib.redirect_stdout(output):
                code = cli(['--config', str(directory / 'peers.json'), '--actor', 'peer-a', 'doctor'])
            return code, json.loads(output.getvalue())

    def test_doctor_success(self):
        code, result = self.doctor([None, None])
        self.assertEqual(code, 0)
        self.assertEqual([p['preflight'] for p in result['peers']], ['passed', 'passed'])

    def test_doctor_mixed_result(self):
        code, result = self.doctor([None, PreflightRejected('synthetic failure')])
        self.assertEqual(code, 1)
        self.assertEqual([p['preflight'] for p in result['peers']], ['passed', 'failed'])

    def test_initializer_missing_parent(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stderr(io.StringIO()) as error:
            code = initialize(['--directory', str(Path(tmp) / 'missing' / 'demo')])
        self.assertEqual(code, 1)
        self.assertIn('parent directory does not exist', error.getvalue())
        self.assertNotIn('Traceback', error.getvalue())


class NativeSnapshotTests(unittest.TestCase):
    def test_default_mode_valid_snapshot_with_synthetic_os_fixtures(self):
        sid = '11111111-1111-4111-8111-111111111111'
        peer = dict(kind='claude_socket', session_id=sid, desktop_session_id='synthetic',
                    version='synthetic-version', registry='registry', metadata='metadata')
        registry = dict(sessionId=sid, hostSessionId='synthetic', version='synthetic-version',
                        peerProtocol=1, status='idle', pid=12345,
                        messagingSocketPath='/tmp/cc-socks/12345.sock', procStart='synthetic-start')
        metadata = dict(cliSessionId=sid, sessionId='synthetic', permissionMode='default')
        socket_info = SimpleNamespace(st_mode=stat.S_IFSOCK | 0o600, st_uid=os.getuid())
        directory_info = SimpleNamespace(st_mode=stat.S_IFDIR | 0o700, st_uid=os.getuid())
        with patch('pairhatch.transports.secure_read_json', side_effect=[registry, metadata]), \
             patch('pairhatch.transports.os.lstat', side_effect=[socket_info, directory_info]), \
             patch('pairhatch.transports.bounded_capture', return_value='synthetic-start'):
            result, info = ClaudeSocket().snapshot(peer)
        self.assertEqual(result, registry)
        self.assertIs(info, socket_info)
