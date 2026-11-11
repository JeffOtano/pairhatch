import json
import os
from pathlib import Path
import tempfile
import unittest
from pairhatch.engine import load_config
from pairhatch.init_config import main
from pairhatch.store import Refused


class ReleaseTests(unittest.TestCase):
    def test_portable_private_mock_initializer(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp).resolve() / 'demo'
            self.assertEqual(main(['--directory', str(directory)]), 0)
            path = directory / 'peers.json'
            config, peers = load_config(path)
            self.assertEqual(Path(config['database']).parent, directory)
            self.assertEqual(set(peers), {'peer-a', 'peer-b'})
            self.assertEqual(directory.stat().st_mode & 0o777, 0o700)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            import contextlib, io
            error = io.StringIO()
            before = path.read_bytes()
            with contextlib.redirect_stderr(error):
                self.assertEqual(main(['--directory', str(directory)]), 1)
            self.assertIn('destination already exists', error.getvalue())
            self.assertNotIn('Traceback', error.getvalue())
            self.assertEqual(path.read_bytes(), before)

    def test_native_gate_requires_boolean_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'config.json'
            config = {'version': 10, 'peers': [
                {'id': 'a', 'label': 'A', 'kind': 'codex_queue'},
                {'id': 'b', 'label': 'B', 'kind': 'mock'}]}
            for value in (None, False, 'true', 1):
                config['experimental_native_transports'] = value
                path.write_text(json.dumps(config))
                with self.assertRaises(Refused):
                    load_config(path)
            config['experimental_native_transports'] = True
            path.write_text(json.dumps(config))
            self.assertEqual(len(load_config(path)[1]), 2)


class BoundedPreflightTests(unittest.TestCase):
    def capture(self, code, **kwargs):
        import sys
        from pairhatch.transports import bounded_capture
        return bounded_capture([sys.executable, '-c', code], **kwargs)

    def test_output(self):
        self.assertEqual(self.capture("print('synthetic-version')"), 'synthetic-version')

    def test_stdout_limit(self):
        from pairhatch.transports import PreflightRejected
        with self.assertRaisesRegex(PreflightRejected, 'output exceeded'):
            self.capture("print('x' * 100000)", limit=100)

    def test_stderr_limit(self):
        from pairhatch.transports import PreflightRejected
        with self.assertRaisesRegex(PreflightRejected, 'output exceeded'):
            self.capture("import sys; sys.stderr.write('x' * 100000)", limit=100)

    def test_timeout(self):
        from pairhatch.transports import PreflightRejected
        with self.assertRaisesRegex(PreflightRejected, 'timed out'):
            self.capture("import time; time.sleep(10)", timeout=0.1)

    def test_nonzero(self):
        from pairhatch.transports import PreflightRejected
        with self.assertRaisesRegex(PreflightRejected, 'exited 2'):
            self.capture("raise SystemExit(2)")

    def test_already_exited_child_output_still_bounded(self):
        import subprocess
        from unittest.mock import patch
        from pairhatch.transports import PreflightRejected
        real_popen = subprocess.Popen
        def exited_popen(*args, **kwargs):
            process = real_popen(*args, **kwargs)
            process.wait(timeout=5)
            return process
        with patch('pairhatch.transports.subprocess.Popen', exited_popen):
            with self.assertRaisesRegex(PreflightRejected, 'output exceeded'):
                self.capture("print('x' * 256)", limit=100)


class ClaudeMetadataTests(unittest.TestCase):
    def test_missing_or_invalid_pin_is_rejected_before_read(self):
        from pairhatch.transports import ClaudeSocket, PreflightRejected
        from unittest.mock import patch
        peer = {'kind': 'claude_socket', 'session_id': '11111111-1111-4111-8111-111111111111'}
        for value in (None, '', ' ', 1, False):
            with self.subTest(value=value), patch('pairhatch.transports.secure_read_json') as read:
                with self.assertRaisesRegex(PreflightRejected, 'Pinned Claude'):
                    ClaudeSocket().snapshot(dict(peer, version=value))
                read.assert_not_called()

    def test_unknown_or_elevated_mode_rejected_before_socket(self):
        from pairhatch.transports import ClaudeSocket, PreflightRejected
        from unittest.mock import patch
        sid = '11111111-1111-4111-8111-111111111111'
        peer = dict(kind='claude_socket', session_id=sid, desktop_session_id='synthetic',
                    version='synthetic-version', registry='registry', metadata='metadata')
        registry = dict(sessionId=sid, hostSessionId='synthetic', version='synthetic-version',
                        peerProtocol=1, status='idle')
        for mode in (None, '', 'bypassPermissions', 'unrecognized', 1, False, 'acceptEdits'):
            metadata = dict(cliSessionId=sid, sessionId='synthetic', permissionMode=mode)
            with self.subTest(mode=mode), patch('pairhatch.transports.secure_read_json', side_effect=[registry, metadata]):
                with self.assertRaisesRegex(PreflightRejected, 'permission mode'):
                    ClaudeSocket().snapshot(peer)


class DoctorTests(unittest.TestCase):
    def test_failed_preflight_returns_nonzero_with_json(self):
        import contextlib
        import io
        from unittest.mock import patch
        from pairhatch.__main__ import main as cli
        from pairhatch.transports import PreflightRejected
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp).resolve() / 'demo'
            with contextlib.redirect_stdout(io.StringIO()):
                main(['--directory', str(directory)])
            output = io.StringIO()
            with patch('pairhatch.transports.MockTransport.preflight', side_effect=PreflightRejected('synthetic failure')), contextlib.redirect_stdout(output):
                code = cli(['--config', str(directory / 'peers.json'), '--actor', 'peer-a', 'doctor'])
            self.assertEqual(code, 1)
            self.assertTrue(all(p['preflight'] == 'failed' for p in json.loads(output.getvalue())['peers']))
