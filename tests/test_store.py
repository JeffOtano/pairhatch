import concurrent.futures
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from pairhatch.store import Refused, Store


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmp.name).resolve() / 'state.sqlite')
        self.now = 1000
        self.store = Store(self.path, clock=lambda: self.now)
        self.store.create_grant('g', ['alice', 'bob'], 'Review locally', 2000, 6, 20)
        self.store.open_consultation('g', 'c', 'alice')

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def queue(self, message='m'):
        return self.store.enqueue('c', message, 'alice', 'bob', 'Question')

    def accept(self):
        self.queue()
        self.store.claim('m')
        self.store.settle('m', 'accepted')

    def test_alternation_and_explicit_link(self):
        self.accept()
        for sender, recipient, link in [('alice', 'bob', 'm'), ('bob', 'alice', None), ('bob', 'alice', 'other')]:
            with self.assertRaises(Refused):
                self.store.enqueue('c', 'm2', sender, recipient, 'Answer', 'answer', link)
        result = self.store.enqueue('c', 'm2', 'bob', 'alice', 'Answer', 'answer', 'm')
        self.assertEqual(result['sequence'], 2)

    def test_final_closes_only_on_acceptance(self):
        self.accept()
        self.store.enqueue('c', 'm2', 'bob', 'alice', 'Done', 'final', 'm')
        self.assertEqual(self.store.get_consultation('c')['state'], 'active')
        self.store.claim('m2')
        self.store.settle('m2', 'accepted')
        self.assertEqual(self.store.get_consultation('c')['state'], 'completed')
        self.assertEqual(self.store.get_grant('g')['consultations_used'], 1)

    def test_concurrent_open_has_one_winner(self):
        self.store.cancel('c')
        def attempt(i):
            store = Store(self.path, clock=lambda: self.now)
            try:
                store.open_consultation('g', 'next' + str(i), 'alice')
                return True
            except Refused:
                return False
            finally:
                store.close()
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(sum(pool.map(attempt, range(16))), 1)
        self.assertEqual(self.store.get_grant('g')['consultations_used'], 2)

    def test_pending_exclusion_and_scope(self):
        with self.assertRaises(Refused):
            self.store.enqueue('c', 'm', 'mallory', 'bob', 'Question')
        with self.assertRaises(Refused):
            self.store.enqueue('c', 'm', 'bob', 'alice', 'Question')
        self.queue()
        with self.assertRaises(Refused):
            self.store.enqueue('c', 'm2', 'bob', 'alice', 'Answer', 'answer', 'm')

    def test_idempotency_and_mutation(self):
        one = self.queue()
        self.assertEqual(one, self.queue())
        with self.assertRaises(Refused):
            self.store.enqueue('c', 'm', 'alice', 'bob', 'Changed')
        self.store.create_grant('g', ['bob', 'alice'], 'Review locally', 2000, 6, 20)
        with self.assertRaises(Refused):
            self.store.create_grant('g', ['alice', 'bob'], 'Changed', 2000, 6, 20)
        self.store.open_consultation('g', 'c', 'alice')
        with self.assertRaises(Refused):
            self.store.open_consultation('g', 'c', 'bob')
        self.assertEqual(self.store.get_consultation('c')['messages_used'], 1)
        self.assertEqual(self.store.status()['consultations'], 1)

    def test_expiry_at_enqueue_and_claim(self):
        self.queue()
        self.now = 2000
        with self.assertRaises(Refused):
            self.store.claim('m')
        with self.assertRaises(Refused):
            self.store.enqueue('c', 'm2', 'alice', 'bob', 'New')
        self.assertEqual(self.store.get_message('m')['state'], 'queued')

    def test_pause_revoke_and_cancel(self):
        self.queue()
        self.store.pause()
        with self.assertRaises(Refused):
            self.store.claim('m')
        self.store.resume()
        self.store.revoke_grant('g')
        with self.assertRaises(Refused):
            self.store.claim('m')
        self.assertEqual(self.store.get_consultation('c')['state'], 'revoked')

    def test_cancel_after_claim_does_not_erase_evidence(self):
        self.queue()
        self.store.claim('m')
        self.store.cancel('c')
        self.store.settle('m', 'accepted', 'Transport admitted')
        self.assertEqual(self.store.get_consultation('c')['state'], 'cancelled')
        with self.assertRaises(Refused):
            self.store.enqueue('c', 'm2', 'bob', 'alice', 'Reply', 'answer', 'm')

    def test_attempted_survives_restart_and_cannot_retry(self):
        self.queue()
        self.store.claim('m')
        self.store.close()
        self.store = Store(self.path, clock=lambda: self.now)
        self.assertEqual(self.store.get_message('m')['state'], 'attempted')
        with self.assertRaises(Refused):
            self.store.claim('m')
        with self.assertRaises(Refused):
            self.store.enqueue('c', 'm2', 'bob', 'alice', 'Reply', 'answer', 'm')

    def test_unknown_is_terminal_message_state(self):
        self.queue()
        self.store.claim('m')
        self.store.settle('m', 'unknown', 'Timeout')
        self.store.settle('m', 'unknown', 'Timeout')
        for outcome in ('accepted', 'rejected'):
            with self.assertRaises(Refused):
                self.store.settle('m', outcome)
        with self.assertRaises(Refused):
            self.store.claim('m')
        with self.assertRaises(Refused):
            self.store.enqueue('c', 'm2', 'bob', 'alice', 'Reply', 'answer', 'm')

    def test_rejected_closes_without_retry(self):
        self.queue()
        self.store.claim('m')
        self.store.settle('m', 'rejected', 'Pre-transmission rejection')
        self.assertEqual(self.store.get_consultation('c')['state'], 'rejected')
        with self.assertRaises(Refused):
            self.store.claim('m')

    def test_budget_and_pair_release(self):
        self.store.cancel('c')
        self.store.create_grant('tiny', ['alice', 'bob'], 'One exchange', 2000, 1, 1)
        self.store.open_consultation('tiny', 'c2', 'bob')
        self.store.enqueue('c2', 'm', 'bob', 'alice', 'Hello')
        self.store.claim('m')
        self.store.settle('m', 'accepted')
        self.assertEqual(self.store.get_consultation('c2')['state'], 'completed')
        with self.assertRaises(Refused):
            self.store.open_consultation('tiny', 'c3', 'bob')
        self.store.open_consultation('g', 'c3', 'alice')

    def test_pair_exclusion_across_grants(self):
        self.store.create_grant('g2', ['bob', 'alice'], 'Other topic', 2000)
        with self.assertRaises(Refused):
            self.store.open_consultation('g2', 'c2', 'bob')
        self.store.cancel('c')
        self.store.open_consultation('g2', 'c2', 'bob')

    def test_expired_pair_lock_released(self):
        self.now = 2000
        self.store.create_grant('new', ['alice', 'bob'], 'New', 3000)
        self.store.open_consultation('new', 'newc', 'alice')
        self.assertEqual(self.store.get_consultation('c')['state'], 'expired')

    def test_cross_instance_claim_is_at_most_once(self):
        self.queue()
        def attempt(_):
            store = Store(self.path, clock=lambda: self.now)
            try:
                store.claim('m')
                return True
            except Refused:
                return False
            finally:
                store.close()
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(attempt, range(16)))
        self.assertEqual(sum(results), 1)

    def test_concurrent_replay_uses_one_budget_unit(self):
        def attempt(_):
            store = Store(self.path, clock=lambda: self.now)
            try:
                return store.enqueue('c', 'same', 'alice', 'bob', 'Same')['sequence']
            finally:
                store.close()
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(list(pool.map(attempt, range(16))), [1] * 16)
        self.assertEqual(self.store.get_consultation('c')['messages_used'], 1)

    def test_open_question_rolls_back_invalid_payload(self):
        self.store.cancel('c')
        before = self.store.get_grant('g')['consultations_used']
        for mid, recipient, text in [('m', 'bob', ''), ('bad id', 'bob', 'Hello'), ('m', 'mallory', 'Hello')]:
            with self.assertRaises(Refused):
                self.store.open_question('g', 'fresh', mid, 'alice', recipient, text)
            with self.assertRaises(Refused):
                self.store.get_consultation('fresh')
            self.assertEqual(self.store.get_grant('g')['consultations_used'], before)
        first = self.store.open_question('g', 'fresh', 'first', 'alice', 'bob', 'Hello')
        self.assertEqual(first, self.store.open_question('g', 'fresh', 'first', 'alice', 'bob', 'Hello'))
        self.assertEqual(self.store.get_grant('g')['consultations_used'], before + 1)
        with self.assertRaises(Refused):
            self.store.open_question('g', 'fresh', 'first', 'alice', 'bob', 'Changed')
        self.assertEqual(self.store.get_message('first')['text'], 'Hello')

    def test_bind_peers_is_immutable_and_persistent(self):
        routes = {'alice': {'thread_id': 'one', 'transport': 'local'}, 'bob': {'thread_id': 'two'}}
        result = self.store.bind_peers(routes)
        reordered = {'bob': {'thread_id': 'two'}, 'alice': {'transport': 'local', 'thread_id': 'one'}}
        self.assertEqual(self.store.bind_peers(reordered), result)
        second = Store(self.path, clock=lambda: self.now)
        try:
            self.assertEqual(second.bind_peers(routes), result)
            with self.assertRaises(Refused):
                second.bind_peers({'alice': {'thread_id': 'changed'}, 'bob': {'thread_id': 'two'}})
        finally:
            second.close()
        self.assertEqual(self.store.bind_peers(routes), result)
        for invalid in (None, {}, {'a': float('nan')}, {1: 'route'}):
            with self.assertRaises(Refused):
                self.store.bind_peers(invalid)

    def test_content_bounds(self):
        for value in ('', 'x\x00y', 'x\x7fy', 'é' * 4097, '\ud800'):
            with self.assertRaises(Refused):
                self.store.enqueue('c', 'm', 'alice', 'bob', value)
        self.store.enqueue('c', 'm', 'alice', 'bob', 'Line\n\tTab')

    def test_permissions_and_symlinks(self):
        self.assertEqual(os.stat(self.path).st_mode & 0o777, 0o600)
        link = str(Path(self.path).with_name('link.sqlite'))
        os.symlink(self.path, link)
        with self.assertRaises((Refused, OSError)):
            Store(link)
        os.chmod(self.path, 0o644)
        try:
            with self.assertRaises(Refused):
                Store(self.path)
        finally:
            os.chmod(self.path, 0o600)

    def test_unknown_schema_refused_without_migration(self):
        other = str(Path(self.path).with_name('unknown.sqlite'))
        db = sqlite3.connect(other)
        db.execute('CREATE TABLE unrelated(x)')
        db.close()
        os.chmod(other, 0o600)
        with self.assertRaises(Refused):
            Store(other)
        db = sqlite3.connect(other)
        self.assertEqual(db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall(), [('unrelated',)])
        db.close()

    def test_unsupported_protocol_refused(self):
        self.store.db.execute("UPDATE metadata SET value='999' WHERE key='protocol_version'")
        with self.assertRaises(Refused):
            Store(self.path)


if __name__ == '__main__':
    unittest.main()
