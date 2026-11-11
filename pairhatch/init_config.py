"""Create a fresh, portable mock configuration. Never registers a host."""
import argparse
import json
import os
import sys
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True, help='New private directory for demo configuration and state')
    args = parser.parse_args(argv)
    try:
        directory = Path(args.directory).expanduser().resolve()
        # Refuse existing destinations rather than overwrite a live configuration.
        directory.mkdir(mode=0o700, parents=False, exist_ok=False)
        config = {'version': 10, 'database': str(directory / 'broker.sqlite'),
                  'peers': [{'id': name, 'label': name, 'kind': 'mock'} for name in ('peer-a', 'peer-b')]}
        path = directory / 'peers.json'
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump(config, stream, indent=2)
            stream.write('\n')
    except FileExistsError:
        print('pairhatch-init: destination already exists; choose a new directory. Nothing was overwritten.', file=sys.stderr)
        return 1
    except FileNotFoundError:
        print('pairhatch-init: parent directory does not exist; create it first or choose an existing parent.', file=sys.stderr)
        return 1
    except (OSError, RuntimeError) as exc:
        print(f'pairhatch-init: cannot initialize directory: {exc}. Check the path and permissions; inspect any partially created directory before retrying.', file=sys.stderr)
        return 1
    print(path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

