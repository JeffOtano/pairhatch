"""Build and validate an sdist roundtrip using already-installed build tools.

No index access, native traffic, host registration or publication occurs.
"""
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix='pairhatch-sdist-') as tmp:
        base = Path(tmp).resolve()
        env = dict(os.environ)
        env.pop('PYTHONPATH', None)
        env['PYTHONNOUSERSITE'] = '1'
        subprocess.run([sys.executable, '-c',
                        'from setuptools.build_meta import build_sdist; '
                        f'build_sdist({str(base)!r})'], cwd=ROOT, env=env, check=True)
        archives = list(base.glob('pairhatch-*.tar.gz'))
        if len(archives) != 1:
            raise SystemExit('Expected one source distribution')
        with tarfile.open(archives[0]) as archive:
            members = archive.getmembers()
            for member in members:
                path = Path(member.name)
                if path.is_absolute() or '..' in path.parts or not (member.isfile() or member.isdir()):
                    raise SystemExit('Unsafe source archive member: ' + member.name)
                if any(part in ('__pycache__', '.git', '.venv', 'dist', 'build') for part in path.parts):
                    raise SystemExit('Unexpected source archive member: ' + member.name)
                if path.suffix in ('.sqlite', '.db', '.pyc'):
                    raise SystemExit('Unexpected state in source archive: ' + member.name)
            archive.extractall(base)
        source = base / archives[0].name.removesuffix('.tar.gz')
        for args in (
            ['scripts/check_release.py'],
            ['-m', 'unittest', 'discover', '-s', 'tests', '-q'],
            ['-m', 'pip', 'wheel', '--no-index', '--no-build-isolation', '--no-deps', '--wheel-dir', 'dist', '.'],
            ['scripts/clean_install_test.py'],
        ):
            subprocess.run([sys.executable, *args], cwd=source, env=env, check=True)
        print('PASS: inspected sdist, extracted-source tests, offline wheel rebuild and fresh install')


if __name__ == '__main__':
    main()
