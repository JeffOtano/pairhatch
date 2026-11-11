"""Install the local wheel offline in a fresh environment and exercise mock CLI."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import venv

ROOT = Path(__file__).resolve().parents[1]
wheels = list((ROOT / 'dist').glob('pairhatch-*.whl'))
if len(wheels) != 1:
    raise SystemExit('Build exactly one candidate wheel in dist first')
with tempfile.TemporaryDirectory(prefix='pairhatch-install-') as tmp:
    base = Path(tmp).resolve()
    venv.EnvBuilder(with_pip=True).create(base / 'venv')
    binary = base / 'venv' / 'bin'
    env = dict(os.environ)
    env.pop('PYTHONPATH', None)
    env['PYTHONNOUSERSITE'] = '1'
    def run(*args):
        return subprocess.run(args, cwd=base, env=env, check=True, capture_output=True, text=True).stdout
    run(str(binary / 'python'), '-m', 'pip', 'install', '--no-index', '--no-deps', str(wheels[0]))
    imported = run(str(binary / 'python'), '-c', 'import pairhatch; print(pairhatch.__file__)').strip()
    assert str(base / 'venv') in imported, imported
    run(str(binary / 'pairhatch'), '--help')
    setup_output = run(str(binary / 'pairhatch-setup'), '--directory', str(base / 'guided'))
    assert 'No model contacted' in setup_output, setup_output
    bundles = json.loads((base / 'guided' / 'host-bundles.json').read_text())
    assert len(bundles['bundles']) == 8
    for bundle in bundles['bundles']:
        skill = base / 'guided' / bundle['bundle'] / bundle['skill_path']
        assert 'name: pairhatch' in skill.read_text(), skill
    import sqlite3
    connection = sqlite3.connect(base / 'guided' / 'broker.sqlite')
    assert connection.execute('SELECT count(*) FROM grants').fetchone()[0] == 0
    connection.close()
    run(str(binary / 'pairhatch-init'), '--directory', str(base / 'demo'))
    config = base / 'demo' / 'peers.json'
    def call(actor, *args):
        return json.loads(run(str(binary / 'pairhatch'), '--config', str(config), '--actor', actor, *args))
    call('peer-a', 'grant', '--id', 'demo', '--participants', 'peer-a', 'peer-b', '--topic', 'Synthetic review', '--max-messages', '2', '--confirm', 'ALLOW peer-a peer-b')
    mid = '11111111-1111-4111-8111-111111111111'
    rid = '22222222-2222-4222-8222-222222222222'
    assert call('peer-a', 'ask', '--grant', 'demo', '--to', 'peer-b', '--consultation', 'demo-chat', '--message-id', mid, '--text', 'Synthetic question')['state'] == 'accepted'
    call('peer-b', 'reply', '--consultation', 'demo-chat', '--in-reply-to', mid, '--message-id', rid, '--text', 'Synthetic answer', '--final')
    status = call('peer-a', 'status', '--consultation', 'demo-chat')
    assert status['consultation']['state'] == 'completed'
    assert len(status['messages']) == 2
    print('PASS: fresh offline wheel install; installed import/entrypoints; mock roundtrip outside source tree')

