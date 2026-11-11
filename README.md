# Pairhatch

**Experimental release candidate, not publicly released or production-ready.**
Python 3.10+ on POSIX (Linux/macOS); no runtime dependencies. Windows is not
supported because file ownership, permissions and Unix sockets are integral.
The package name has not been reserved or checked on any public registry.

Pairhatch brokers explicit, bounded consultations between two enrolled agents.
It persists grants, message lineage and outcomes in SQLite, limits each
consultation to at most six total messages, and never automatically retries a
committed dispatch attempt. Peer text is untrusted analysis, never approval.
This is a same-user utility, **not** an authentication or agent isolation system.

## Start here

```sh
git clone https://github.com/JeffOtano/pairhatch.git
cd pairhatch
python3 -m pairhatch.setup
```

One setup command, no dependency install. It verifies an offline roundtrip,
creates a private empty configuration and prints the next step. It does not
contact a model, create a lasting grant or edit host settings. Already have
~/pairhatch-demo? Add `--directory "$HOME/pairhatch-demo-2"`.

Prefer a familiar two-command Claude Code or Codex plugin install? See
[INSTALL.md](INSTALL.md). The optional plugin supplies setup instructions only,
with no hooks or automatic MCP registration. Marketplace installation is not yet
verified; the source-checkout route above is covered by automated tests.

## Install from this reviewed source

Before publication, repository access is required. Clone the reviewed source first:

```sh
git clone https://github.com/JeffOtano/pairhatch.git
cd pairhatch
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
pairhatch --help
```

Building uses setuptools from the standard Python package registry. Installation
does not register an MCP server, install a daemon, obtain credentials or send a
message. Licensed under MIT, copyright (c) 2026 Jeff Otano. This candidate is prepared for experimental release; publication is a separate
maintainer action. No stable native-host compatibility is claimed.

## Offline demo

Run from any directory after installation. Choose a fresh directory directly
under your home (the initializer refuses to overwrite an existing one):

```sh
pairhatch-init --directory "$HOME/pairhatch-demo"
CONFIG="$HOME/pairhatch-demo/peers.json"
pairhatch --config "$CONFIG" grant --id demo --participants peer-a peer-b --topic 'Synthetic coding discussion' --max-messages 2 --confirm 'ALLOW peer-a peer-b'
pairhatch --config "$CONFIG" --actor peer-a ask --grant demo --to peer-b --consultation demo-chat --message-id 11111111-1111-4111-8111-111111111111 --text 'What should median([]) do?'
pairhatch --config "$CONFIG" --actor peer-b reply --consultation demo-chat --in-reply-to 11111111-1111-4111-8111-111111111111 --message-id 22222222-2222-4222-8222-222222222222 --text 'Raise ValueError.' --final
pairhatch --config "$CONFIG" --actor peer-a status --consultation demo-chat
```

Expected: `ask` reports `state: accepted`; final status reports consultation
`state: completed` with exactly two messages.

This exercises local protocol state only. Mock admission does not contact a
model. Use fresh grant/consultation/message IDs for a new consultation. Identical
message ID replays return recorded outcomes without resending.

## CLI and optional MCP

Commands: grant, ask, reply, status, inbox, pause, resume, cancel, revoke, doctor,
serve. See `pairhatch --help` and subcommand help. Omit `--text` to read bounded
stdin. Prefer stdin for private text because command arguments may be visible in
process listings or shell history. `doctor` does not send, but may create a database and persist peer bindings.
It exits nonzero when any destination preflight fails.

Inbox reads default to at most 100 messages. Use `--limit` and `--offset`
(or MCP `limit`/`offset`) to page in consultation-ID/sequence order, not arrival
order. Concurrent arrivals can shift offsets and skip or duplicate records; this
is for quiet historical browsing, not reliable live polling. See OPERATIONS.md.

`pairhatch --config /absolute/path/peers.json --actor peer-a serve` starts an
optional stdio MCP process (baseline protocol 2024-11-05). Tools: ask_peer,
reply_to_peer, consultation_status, peer_inbox, stop_consultation. Administration
is deliberately excluded. Host registration is a separate, explicitly authorized
step, not performed by this package. See
[the host validation plan](docs/HOST_VALIDATION.md) for the remaining checks. Real host tool negotiation, permissions and
independent self-service reply cycles have not been validated for this release.

## Native integrations: opt-in experiments

The mock transport is the default. `examples/native.template.json` contains
nonfunctional placeholders and disables native transports. After reviewing exact
authorized destinations and runtime compatibility, an operator must explicitly
set `experimental_native_transports` to true. This enables loading a native
configuration; it is not authentication or user authorization.

Codex uses a pinned CLI's `queue` command. Claude uses an **observed private local
socket protocol**, macOS-specific kernel PID checks and hard-coded observed
socket layout. Neither is a stable, supported cross-version integration contract.
Upgrades or changed identities should fail closed. No vendor application code,
app bundles, original session configuration, transcripts or live receipts are
included. The source adapters implement broker-side protocol interactions only;
this is not a legal provenance or ownership certification.

Accepted means transport admission, not model receipt/completion. No live native
traffic was sent while validating this candidate. Historic prototype tests are
not certification of this sanitized release. Read SECURITY.md, OPERATIONS.md and
docs/RETENTION.md before considering live use.

## Development

```sh
python -m unittest discover -s tests -v
python -m pip wheel --no-deps --wheel-dir dist .
python scripts/clean_install_test.py
```

The clean-install smoke test uses a fresh virtual environment, a locally built
wheel, an unrelated working directory and only synthetic mock messages. CI is
provided for Linux/macOS and several Python versions; it has not run remotely.
See [CONTRIBUTING.md](CONTRIBUTING.md) for the contributor workflow and
[RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) for remaining publication gates.

## Native Codex command-line disclosure

Even when broker input comes from stdin, the experimental Codex queue adapter
passes the complete rendered peer message, approved topic and correlation IDs
in the child process's --message argument. These may be visible in process
listings and process-audit logs. Stdin avoids the broker's own --text argument
and shell history, but does not prevent this downstream exposure. Do not use
this adapter for sensitive content. A verified non-argv native input mechanism
is not implemented.


## Host skills and tooling

`python3 -m pairhatch.setup` now generates review-only Claude Code, Codex, Cursor,
and generic stdio MCP bundles: each has an operational skill and tooling, with
per-actor project paths and activation/removal instructions. Use `--host cursor`
(or repeat `--host`) to select bundles. Setup does not register a host, create
grants, or wake agents. See [installation](INSTALL.md) and the
[capability matrix](docs/COMPATIBILITY.md#host-onboarding-matrix-2026-11-11).

## Documentation for agents

Start repository work at [AGENTS.md](AGENTS.md). For tool usage, read the
[MCP reference and tested cookbook](docs/MCP_COOKBOOK.md); for failures, use the
[troubleshooting guide](docs/TROUBLESHOOTING.md). These complement the setup and
operational skills without granting permission to contact other agents.
