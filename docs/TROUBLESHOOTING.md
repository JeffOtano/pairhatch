# Troubleshooting decision guide

Start with the stage that failed. Keep config paths, IDs, message text and host logs
private. Share sanitized diagnostics only with approved recipients. Do not disable
permissions or broaden grants to make a check pass.

| Symptom | Check | Next safe step |
| --- | --- | --- |
| Setup destination exists | Existing/partial setup and README | Choose a new directory; never overwrite or delete state automatically |
| Missing parent or Python error | Existing parent; Python 3.10+; Linux/macOS | Correct the invocation; do not install software silently |
| Interpolation unsupported | `${...}` in setup/runtime path | Use a fresh literal path; do not feed host expansion into generated config |
| Skill absent | Correct host/project path from host-bundles.json | Confirm skill activation was approved, then reload/restart per host docs; avoid duplicate discovery paths |
| Skill present, no tools | Skill install and MCP registration are separate | Review the selected actor's MCP config; confirm registration approval and host support |
| Codex ignores project config | Project trust and `.codex/config.toml` | Ask operator to review trust; do not silently trust a project |
| Server process fails | Absolute Python/source/launcher paths; stderr | Paths may have moved; regenerate a fresh setup from current paths, not an unknown package download |
| Local bundle fails in cloud | Executor filesystem/runtime differs | Local paths are not remote provisioning; use an explicitly supported setup on the target executor |
| Permission prompt/denial | Host policy and exact requested tool | Stop the denied action and report it; keep approval checks enabled |
| Unknown/expired/revoked grant | Exact grant ID, pair, scope, expiry | Ask operator to inspect approved scope. No MCP grant capability; do not create/renew without approval |
| Pair active/budget exhausted | consultation_status and recorded messages | Finish/stop existing work when authorized; no replacement IDs or grants to evade limits |
| Empty inbox | Actor, same config/database, actual accepted recipient | Use correct approved actor; mock does not wake a model. Inbox is historical, not a delivery notification |
| Reply rejected | Exact latest accepted message, recipient, correlation | Correct only a known unsent invalid request; inspect uncertain outcomes before any action |
| accepted but no reply | Native admission vs model completion; manual inbox | Ask recipient host to inspect only within existing scope; do not send duplicates |
| attempted or unknown | consultation_status; process/transport evidence | Treat as potentially delivered; no automatic retry or target switching |
| Peer routes changed | Existing database pins initial routes | Stop and review. Do not edit database metadata or silently repoint destination |
| Private file/path checks fail | Ownership, 0700 directory, 0600 database, symlink components | Explain exact path problem; do not chmod shared trees or weaken checks silently |
| Package build fails offline | Already installed setuptools 77+ and wheel | Report missing build prerequisites; runtime has no third-party dependencies |
| CI red with no steps | Exact commit's job execution and account restrictions | Distinguish unrun tests from code failure. Do not change billing or claim local tests prove hosted matrix |

## Escalation report

Include stage, command/tool name (redact private paths/content), host and runtime
versions, observed error/state, whether any send could have occurred, completed
checks and smallest needed decision. Never send raw transcripts, credentials,
native session IDs or database files to a public issue. No public security contact
is configured; use an owner-approved private route.

## Known limits, not bugs to bypass

- Generated bundles are not installed registrations. Skills are not access grants.
- Codex temporary discovery of five tools was observed, but tool execution was
  denied. That does not certify a full exchange; Claude/Cursor live validation
  and marketplace installation remain unverified.
- No automatic Cursor wake-up, universal background listener or remote transport.
- Native Claude depends on an observed private protocol; Codex native message text
  appears in child-process arguments. See SECURITY.md before native work.
- Uninstalling the plugin/package does not remove retained broker data. Follow
  [retention](RETENTION.md) rather than blanket cleanup.
