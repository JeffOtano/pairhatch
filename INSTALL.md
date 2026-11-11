# Install Pairhatch

**Experimental. Offline setup works; independent two-host delivery is not certified.**
Linux/macOS, Python 3.10+. No runtime dependencies. The source repository is
public. No package-registry name or release is available yet.

## Fastest working route: one command after checkout

```sh
git clone https://github.com/JeffOtano/pairhatch.git
cd pairhatch
python3 -m pairhatch.setup
```

That last command creates **~/pairhatch-demo** and checks a synthetic two-message
roundtrip locally. Existing directories are never overwritten; choose another with
`--directory "$HOME/pairhatch-demo-2"`.

Expected result:

```text
Offline broker check passed. No model contacted; host connection not yet verified.
```

You get a private config, an empty broker database, an absolute-path launcher and
Claude/Codex legacy snippets plus Claude, Codex, Cursor, and generic host bundles
for peer-a and peer-b. Each bundle supplies BOTH an operational skill and MCP tooling. The synthetic check runs in disposable
state, removed afterward. Your real setup has **zero grants**. No package download,
app settings change, shell-profile change, daemon, credentials or native messages.
Keep this checkout and its Python interpreter where they are: the launcher points
to those paths. To move them, generate a fresh setup from the new location.

## Skill + tooling bundles for your agent

The same setup command generates `hosts/<host>/<actor>/` for `claude`, `codex`,
`cursor`, and `generic`. To generate only selected bundles:

```sh
python3 -m pairhatch.setup --directory "$HOME/pairhatch-cursor" --host cursor
```

`--host` is repeatable. Existing setup directories are never overwritten. The
legacy top-level Claude/Codex snippets are retained for compatibility regardless
of selection. `host-bundles.json` records every selected bundle and its proposed
project installation paths. All generated files are private, review-only artifacts.

1. Pick the host and ONE actor. The two actors share one broker; each host must
   use a different actor. This does not create another model or daemon.
2. Read that bundle's README.txt, skill, and exact MCP command/args. Authorize the
   named project and continuing tool access before activation. Do not open a
   bundle itself as a trusted host project just to inspect it.
3. Merge only the `pairhatch` MCP entry into the approved project's existing config.
   Never replace the whole file. Stop for an existing Pairhatch entry or skill;
   compare before changing it. Copy the skill folder to the listed project path.
   These are manual activation steps, not actions setup performs silently.
4. Restart/reload the host as needed. Codex project settings require a trusted
   project. Keep host approval prompts enabled. Verify the skill and five tools
   appear, then check `peer_inbox`. Zero grants means sending must be refused.
5. A separately approved synthetic exchange can test two hosts. On default mock
   routes, manually ask the recipient host to check its inbox; nothing wakes it
   automatically. Native Claude/Codex transports are experimental; there is no
   native Cursor wake-up transport.

The generic bundle includes a portable skill and `stdio-server.json` describing
command/args. It is NOT a universal installable config; translate it using the
client's documented schema. Hosts without local stdio MCP or shell tools cannot
run this integration. Local paths do not configure cloud/remote agents.

See [the capability matrix](docs/COMPATIBILITY.md#host-onboarding-matrix-2026-11-11).
Skill distribution, MCP access, and automatic agent delivery are different checks.
To uninstall, stop the host and remove only its Pairhatch server entry and copied
skill. Preserve unrelated settings; broker data remains for separate review.

## Familiar plugin route: instructions, not automatic connection

Like Ponytail, Pairhatch includes Claude Code and Codex plugin manifests and a
setup skill. This route has **not been installation-tested in either marketplace**.
These are preparatory commands for supported host versions, not proof of host
compatibility. The plugin contains no hooks and registers no MCP server.

Claude Code, as two separate prompts:

```text
/plugin marketplace add JeffOtano/pairhatch
```
```text
/plugin install pairhatch@pairhatch
```

Then ask: "Use Pairhatch to walk me through the offline setup."

Codex:

```sh
codex plugin marketplace add JeffOtano/pairhatch
codex plugin add pairhatch@pairhatch
```

Then ask: "Use the pairhatch skill to set up a local offline demo."

Plugin installation persists instructions in your host; it does not grant broker
access or connect peers. Installing a plugin is optional. The source-checkout
command above works without it. Host installation may require host approval. Never put a token in a command or config example.

## Prefer an installed CLI?

From the reviewed source:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
pairhatch-setup
```

Building may download setuptools from the standard Python registry. Runtime has
no third-party dependencies. To install offline, use a separately reviewed wheel:
`python -m pip install --no-index --no-deps /path/to/pairhatch.whl` (use its real
wheel filename), then `pairhatch-setup`.

## Connect a host only when you are ready

Read the generated README.txt and review one actor's snippet per host.
They are **proposals**, not installed settings. Mock peers never contact another
model, even when a real host can call the tools.

A temporary Claude Code session can load the generated peer-b.claude.json with
`claude --strict-mcp-config --mcp-config /absolute/path/peer-b.claude.json`.
Codex's generated TOML is a reviewable example for its MCP configuration. Prefer
project scope when supported; do not overwrite a whole existing settings file.

Launching hosts may send prompts/tool results to their model providers and retain
logs. Persistent registration grants continuing tool access and requires separate
informed authorization. Keep normal host permission prompts enabled.
See [the validation runbook](docs/HOST_VALIDATION.md).

After connection, each real consultation needs an explicitly approved pair,
topic/content scope, expiry and total-message budget. Installation is not permission
to send. Native transports remain disabled; do not switch them on just to complete
setup. Codex command-line exposure and Claude's private protocol remain limitations.

## What has actually been checked?

- Automated offline broker tests, installed wheel and source-distribution rebuild.
- Codex 0.167.0 temporary MCP handshake and all five tools discovered.
- Codex tool calls were denied by its noninteractive approval policy; no broker
  message was sent. Claude host validation was blocked by network policy.
- Plugin marketplace installation and a complete independent two-host exchange
  remain unverified. Do not advertise "connected" until those checks pass.

## Uninstall and retained data

Remove the instruction plugin through your host's plugin manager (Codex:
`codex plugin remove pairhatch`; Claude Code: `/plugin uninstall pairhatch@pairhatch`).
For an installed Python package, activate its environment and run
`python -m pip uninstall pairhatch`. A source-only demo installed no package.

Neither step deletes ~/pairhatch-demo, transcripts or separately registered MCP
entries. Stop hosts first, remove only Pairhatch's own registration if you added
one, then review retained data using [RETENTION.md](docs/RETENTION.md). Never run
blanket cleanup against a shared config or database.

## Installation references

- [Ponytail installation UX](https://github.com/DietrichGebert/ponytail/blob/main/INSTALL.md):
  inspiration for a host-specific short path, not bundled code or an affiliation.
- [Claude Code plugins](https://code.claude.com/docs/en/plugins)
- [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)
