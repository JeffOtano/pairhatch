# Contributing

Pairhatch is an experimental release candidate. Maintainers approve releases;
never publish private configuration, broker state, credentials or live logs.

## Local workflow

Use Python 3.10+ on Linux or macOS. Runtime has no third-party dependencies.
Create a virtual environment, install the package, and run:

```sh
python -m pip install "setuptools>=77" wheel
python -m unittest discover -s tests -v
python -m compileall -q pairhatch tests scripts
python scripts/check_release.py
python -m pip wheel --no-deps --wheel-dir dist .
python scripts/clean_install_test.py
python scripts/sdist_test.py
```

The sdist check needs setuptools 77+ and wheel installed in the current
environment; install them from the standard registry when available.
Build tools may need access to the standard Python package registry. If approved
build tools are already installed, add `--no-build-isolation` to the wheel command.
The smoke test installs offline, not the default wheel-building step. Keep exactly
one candidate wheel in `dist`. Never include real peer IDs, live messages, socket
paths, credentials or database files in tests, examples, issues or commits.

## Review expectations

Use small changes and add regression tests for bugs. Describe behavior, tests run
and checks not run. Preserve transactional message budgets, replay idempotency,
fail-closed identity checks, and the no-automatic-retry dispatch rule. Native
transports must stay opt-in. Do not claim transport admission is model completion
or that actor labels provide authentication. Read ARCHITECTURE.md and SECURITY.md.

Do not send live native traffic or register an MCP server as part of routine tests.
Those operations require separately scoped authorization. Security reports belong
in a private channel agreed with the owner, never a public issue or a live trace.
No verified public reporting address is configured yet.

## Release process

Follow RELEASE_CHECKLIST.md. A passing local suite does not establish platform
coverage, public-protocol compatibility or permission to publish. Do not add an
automatic publishing workflow until its destination and credentials are approved.
Keep author attribution public-safe in new commits; review existing history before
any public release without rewriting it as part of routine maintenance.
