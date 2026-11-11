# Candidate validation

Local Linux/Python 3.12 validation covers offline unit and regression tests,
Python syntax/release checks, wheel installation in a fresh environment, source
archive inspection, extracted-source tests, offline wheel rebuild and clean setup.
See CONTRIBUTING.md for reproducible commands; the preparation report records
exact counts and artifact checksums for this snapshot.

The default setup is mock-only, uses disposable synthetic checks, leaves zero
grants in persistent setup state, and writes review-only host artifacts. Tests
cover host formats, resource/skill packaging, JSON/TOML paths, MCP cookbook calls,
message budgets, explicit IDs, replay, and transport failure handling.

Separately observed: Codex 0.167.0 on macOS completed MCP initialization and
discovered all five tools. Tool calls were denied by the host's noninteractive
approval policy. Claude host validation was blocked by network policy. No broker
messages were created in that host check. This establishes discovery only, not
an independent two-host exchange. Raw host logs are not included.

Not established: the full hosted OS/Python matrix, actual plugin marketplace
installation, live native delivery, real host permission/reply cycles, automated
retention/deletion or adversarial same-user isolation (not provided). Hosted CI
was budget-blocked; no successful hosted validation is claimed.

The observed private Claude protocol, Codex command-line exposure, authentication
boundary and remaining release gates still apply. Pattern checks are not an
exhaustive secret, security or provenance audit.
