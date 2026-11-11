# Compatibility and validation boundaries

## Tested offline

Linux / Python 3.12: unit tests, CLI mock consultation, stdio protocol subprocess,
wheel installation and source-distribution rebuild. See VALIDATION.md for exact
checks and dates. Python 3.10-3.14 on Linux/macOS is the configured CI target, not a
claim of a successful full hosted matrix. Windows is unsupported.

## Experimental and not end-to-end validated

- Optional stdio MCP advertises baseline 2024-11-05. Real host negotiation,
  registration, independent agent replies and host permission UX are not certified.
- Codex adapter depends on an exact pinned CLI and queue receipt. The full message
  is exposed in child-process arguments, even when broker input uses stdin.
- Claude adapter depends on an observed private protocol and macOS socket/PID
  checks. Metadata must have an exact nonempty version pin and `default` permission
  mode. Other modes are rejected. No stable vendor API or upgrade support is claimed.
- Accepted means transport admission, not model receipt, completion or approval.

The 10.0.0 number preserves the prototype's V10 lineage and configuration format;
it does not imply ten public releases, stable APIs or production readiness. Future
versioning and any first public-release number must be decided at release review.

## Deliberately not provided

Cryptographic agent identity, adversarial same-user isolation, automatic retries,
automatic retention cleanup, a background daemon, live host registration, and
public package publication. Read SECURITY.md and RELEASE_CHECKLIST.md.

## Host onboarding matrix (2026-11-11)

Setup now supplies both an operational skill and a tool configuration for each
listed host. All artifacts are generated under a fresh setup directory, NOT
installed into a host. The existing instruction-only marketplace plugin is a
separate, optional way to discover setup. Neither route authorizes communication.

| Host | Project skill destination | Project MCP destination | Validation |
| --- | --- | --- | --- |
| Claude Code | `.claude/skills/pairhatch/SKILL.md` | `.mcp.json`, `mcpServers` JSON | Generated config + subprocess contract tested; live install unverified |
| Codex CLI / local IDE | `.agents/skills/pairhatch/SKILL.md` | `.codex/config.toml`, `mcp_servers` TOML | Generated contract tested; earlier temporary 0.167.0 tool discovery only |
| Cursor local Agent | `.cursor/skills/pairhatch/SKILL.md` | `.cursor/mcp.json`, `mcpServers` JSON with `type: stdio` | Generated contract tested; live install unverified |
| Other local stdio MCP clients | Portable `skills/pairhatch/SKILL.md`, discovery varies | `stdio-server.json` descriptor to translate, NOT universal config | Descriptor subprocess tested; host-specific install unverified |
| Agent without local tools or stdio MCP | Instructions can be read manually | No integration supplied | Unsupported execution path |

Codex project MCP settings require a trusted project. Cursor also discovers
`.agents/skills`; install the skill in only one discovery path, not both. Each
host bundle contains peer-a and peer-b alternatives; use one actor per session.
JSON is not interchangeable with Codex TOML. These local absolute paths do not
configure remote/cloud agents, ChatGPT web, or arbitrary desktop chat clients.
Managed host policy may prohibit a server even if the format is valid.

### Three independent capabilities

1. **Skill discovery:** the host can read Pairhatch's workflow instructions.
2. **Tool access:** a host loads the stdio MCP process and exposes five tools.
3. **Peer wake-up:** a destination transport schedules another running agent.

The first two have generated adapters. Neither implies the third. Default mock
routes record broker messages locally; an operator can manually prompt a second
host on that same broker to check its inbox and reply. That is not automatic
agent delivery. There is no Cursor wake-up adapter. Native Claude/Codex wake-up
remains opt-in and experimental, with the restrictions above. No generic hook,
listener, auto-grant, background polling, or universal transport is claimed.

### Sources and design comparison

Checked 2026-11-11 against official host docs. Documentation compatibility is not
live-host certification; follow HOST_VALIDATION.md before claiming a working pair.

- [Claude skills](https://code.claude.com/docs/en/skills) and
  [MCP](https://code.claude.com/docs/en/mcp).
- [Codex skills](https://learn.chatgpt.com/docs/build-skills) and
  [MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).
- [Cursor skills](https://cursor.com/docs/skills) and
  [MCP](https://cursor.com/docs/mcp).
- [Ponytail installation](https://github.com/DietrichGebert/ponytail/blob/main/INSTALL.md)
  and [portability](https://github.com/DietrichGebert/ponytail/blob/main/docs/agent-portability.md).

Ponytail distributes common instructions through host-specific plugins, hooks,
and rules. Its host capabilities differ. Pairhatch follows the shared-skill plus
thin-adapter pattern, not Ponytail's lifecycle hooks: a consultation broker needs
explicit grants and known destinations, not automatic context injection. No
Ponytail implementation is bundled and no affiliation is implied.
