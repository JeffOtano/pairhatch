"""Offline contract tests, not live-host compatibility certification."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from pairhatch.hosts import HOSTS
from pairhatch.setup import main, setup

try:
    import tomllib
except ImportError:
    tomllib = None


class HostBundleTests(unittest.TestCase):
    def generate(self, path, *args):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--directory", str(path), *args]), 0)

    def test_all_host_actor_contracts_launch_with_private_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve() / 'demo " café'
            self.generate(root)
            manifest = json.loads((root / 'host-bundles.json').read_text())
            self.assertEqual(manifest['status'], 'generated-not-installed')
            self.assertEqual(len(manifest['bundles']), 8)
            for item in manifest['bundles']:
                with self.subTest(host=item['host'], actor=item['actor']):
                    bundle = root / item['bundle']
                    skill = (bundle / item['skill_path']).read_text()
                    self.assertIn('name: pairhatch', skill)
                    self.assertIn('no automatic listener', ' '.join(skill.split()))
                    self.assertFalse(item['installed'])
                    self.assertFalse(item['host_validated'])
                    self.assertFalse(item['automatic_wakeup'])
                    raw = (bundle / item['config_path']).read_text()
                    if item['host'] == 'codex':
                        if tomllib is None:
                            continue  # Python 3.10 still checks JSON adapters and artifact paths.
                        server = tomllib.loads(raw)['mcp_servers']['pairhatch']
                    elif item['host'] == 'generic':
                        server = json.loads(raw)
                        self.assertEqual(server['transport'], 'stdio')
                    else:
                        server = json.loads(raw)['mcpServers']['pairhatch']
                        self.assertEqual(server['type'], 'stdio')
                    self.assertEqual(server['args'][-2:], [item['actor'], 'serve'])
                    self.assertTrue(Path(server['command']).is_absolute())
                    requests = [
                        {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize'},
                        {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
                        {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
                        {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call',
                         'params': {'name': 'peer_inbox', 'arguments': {}}},
                        {'jsonrpc': '2.0', 'id': 4, 'method': 'tools/call',
                         'params': {'name': 'ask_peer', 'arguments': {
                             'grant_id': 'absent', 'recipient': 'peer-b' if item['actor'] == 'peer-a' else 'peer-a',
                             'text': 'Synthetic test', 'consultation_id': 'check', 'message_id': 'question'}}},
                    ]
                    run = subprocess.run([server['command'], *server['args']], cwd=tmp,
                                         input=''.join(json.dumps(r)+'\n' for r in requests),
                                         capture_output=True, text=True, timeout=10)
                    self.assertEqual(run.returncode, 0, run.stderr)
                    results = [json.loads(line) for line in run.stdout.splitlines()]
                    self.assertEqual([r['id'] for r in results], [1, 2, 3, 4])
                    self.assertEqual(results[0]['result']['protocolVersion'], '2024-11-05')
                    self.assertEqual({t['name'] for t in results[1]['result']['tools']},
                                     {'ask_peer', 'reply_to_peer', 'consultation_status', 'peer_inbox', 'stop_consultation'})
                    self.assertFalse(results[2]['result']['isError'])
                    self.assertTrue(results[3]['result']['isError'])
            for path in (root / 'hosts').rglob('*'):
                self.assertEqual(path.stat().st_mode & 0o777, 0o700 if path.is_dir() else 0o600)

    def test_cursor_claude_bundles_share_mock_inbox_and_correlated_reply(self):
        from pairhatch.store import Store
        import time
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve() / 'demo'
            self.generate(root, '--host', 'cursor', '--host', 'claude')
            store = Store(str(root / 'broker.sqlite'))
            try:
                store.create_grant('synthetic', ['peer-a', 'peer-b'],
                                   'Synthetic offline contract', time.time()+60, 2, 1)
            finally:
                store.close()
            def call(host, actor, name, arguments):
                config_path = HOSTS[host][0]
                server = json.loads((root / 'hosts' / host / actor / config_path).read_text())['mcpServers']['pairhatch']
                request = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                           'params': {'name': name, 'arguments': arguments}}
                result = subprocess.run([server['command'], *server['args']], cwd=tmp,
                                        input=json.dumps(request)+'\n', capture_output=True,
                                        text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                response = json.loads(result.stdout)['result']
                self.assertFalse(response['isError'], response)
                return json.loads(response['content'][0]['text'])
            sent = call('cursor', 'peer-a', 'ask_peer', {
                'grant_id': 'synthetic', 'recipient': 'peer-b', 'text': 'Synthetic question',
                'consultation_id': 'chat', 'message_id': 'question'})
            self.assertEqual(sent['state'], 'accepted')
            inbox = call('claude', 'peer-b', 'peer_inbox', {})
            self.assertIn('Synthetic question', json.dumps(inbox))
            call('claude', 'peer-b', 'reply_to_peer', {
                'consultation_id': 'chat', 'in_reply_to': 'question', 'text': 'Synthetic answer',
                'message_id': 'answer', 'final': True})
            status = call('cursor', 'peer-a', 'consultation_status', {'consultation_id': 'chat'})
            self.assertEqual(status['consultation']['state'], 'completed')
            self.assertEqual(len(status['messages']), 2)

    @unittest.skipIf(tomllib is None, 'stdlib TOML parser requires Python 3.11+')
    def test_toml_control_character_paths_round_trip(self):
        import shlex
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve() / 'demo \x7f \t \n café 😀'
            self.generate(root)
            original = json.loads((root / 'peer-a.claude.json').read_text())['mcpServers']['pairhatch']
            for path in ('peer-a.codex.toml', 'hosts/codex/peer-a/.codex/config.toml'):
                parsed = tomllib.loads((root / path).read_text())['mcp_servers']['pairhatch']
                self.assertEqual(parsed, original)
            readme = (root / 'README.txt').read_text()
            command = next(line for line in readme.splitlines() if line.startswith('codex -c '))
            args = shlex.split(command)
            self.assertEqual(tomllib.loads(args[2])['mcp_servers']['pairhatch']['command'], original['command'])
            self.assertEqual(tomllib.loads(args[4])['mcp_servers']['pairhatch']['args'], original['args'])

    def test_select_and_deduplicate_hosts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve() / 'demo'
            self.generate(root, '--host', 'cursor', '--host', 'generic', '--host', 'cursor')
            self.assertEqual({p.name for p in (root / 'hosts').iterdir()}, {'cursor', 'generic'})
            self.assertEqual(len(json.loads((root / 'host-bundles.json').read_text())['bundles']), 4)

    def test_invalid_host_fails_before_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'absent'
            with self.assertRaises(ValueError):
                setup(root, ['unknown'])
            self.assertFalse(root.exists())
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main(['--directory', str(root), '--host', '../escape'])
            self.assertFalse(root.exists())

    def test_host_interpolation_paths_fail_before_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / '${workspaceFolder}'
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(['--directory', str(root)]), 1)
            self.assertFalse(root.exists())

    def test_selected_bundle_does_not_mutate_existing_home_configs(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp).resolve()
            for name in ('.claude', '.codex', '.cursor', '.agents'):
                (home / name).mkdir()
                (home / name / 'sentinel').write_bytes(b'existing host data\x00')
            before = {str(p): p.read_bytes() for p in home.rglob('*') if p.is_file()}
            self.generate(home / 'demo')
            for name, content in before.items():
                self.assertEqual(Path(name).read_bytes(), content)
            for name in ('.claude', '.codex', '.cursor', '.agents'):
                self.assertEqual([p.name for p in (home / name).iterdir()], ['sentinel'])
