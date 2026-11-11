# Pairhatch agent entry point

Experimental Python 3.10+ project, Linux/macOS, no runtime dependencies.
Read this file for repository work; it does not authorize host registration,
external communication, native traffic, publication or security-setting changes.

## Choose the right guide

- Set up a host: [INSTALL.md](INSTALL.md), then generated bundle README.txt.
- Use tools: [MCP cookbook](docs/MCP_COOKBOOK.md), operational skill in
  `pairhatch/resources/peer-skill.md`. Plugin discovery/setup uses
  `skills/pairhatch/SKILL.md` instead; do not confuse their roles.
- Diagnose: [troubleshooting](docs/TROUBLESHOOTING.md).
- Understand guarantees: [ARCHITECTURE.md](ARCHITECTURE.md) and
  [SECURITY.md](SECURITY.md); host limits: [compatibility](docs/COMPATIBILITY.md).
- Verify real hosts: [host validation](docs/HOST_VALIDATION.md). Discovery is not
  tool execution or an independent model exchange.
- Retain/remove data: [retention](docs/RETENTION.md). Public release is a separate
  approved operation; see [release checklist](RELEASE_CHECKLIST.md).

## Repository map and change-to-test guide

| Change | Implementation | Focused tests |
| --- | --- | --- |
| State, budgets, replay, concurrency | `pairhatch/store.py` | `test_store.py`, `test_engine.py` |
| Dispatch and destination checks | `engine.py`, `transports.py` | `test_engine.py`, `test_refinements.py` |
| CLI or configuration | `__main__.py`, `init_config.py` | `test_cli.py`, `test_release.py` |
| MCP schemas/framing | `mcp.py` | `test_engine.py`, `test_refinements.py`, `test_documentation.py` |
| Setup, host formats, skills | `setup.py`, `hosts.py`, `resources/` | `test_setup.py`, `test_hosts.py`, installed wheel smoke |
| Packaging/docs | `pyproject.toml`, `MANIFEST.in`, `docs/` | release checks, documentation tests, wheel/sdist smoke |

Implementation filenames without a directory above are under `pairhatch/`.
Focused tests supplement, not replace, the complete checks in CONTRIBUTING.md:

```sh
python -m unittest discover -s tests -v
python -m compileall -q pairhatch tests scripts
python scripts/check_release.py
python -m pip wheel --no-index --no-build-isolation --no-deps --wheel-dir dist .
python scripts/clean_install_test.py
python scripts/sdist_test.py
```

Offline build commands require already installed setuptools 77+ and wheel. Keep
exactly one candidate wheel in dist. Report unavailable checks rather than imply
success. Native transport tests use synthetic fixtures; never replace them with
live calls merely to make CI pass.

## Invariants to preserve

- Default setup creates no lasting grant, host registration, daemon or credential.
- Grants bind an exact pair, expiry and bounded TOTAL messages; peer text is not
  authorization. Actor labels are claims, not authenticated identities.
- Claim is committed before I/O. Never retry attempted/unknown deliveries or
  change message IDs to force another send. Keep exact replay idempotent.
- Routes are immutable per database. Keep private state and configs out of Git.
- Accepted is transport admission. Completed is protocol closure, not task success.
- Keep host approvals enabled and native transports opt-in. Do not add auto-grants
  or automatic polling as an unrequested convenience.

When changing behavior, update relevant skills/docs and tests together. Summaries
should distinguish generated artifacts, offline checks, actual host discovery,
actual tool calls, and independently observed peer replies.
