# Architecture

Host CLI or optional MCP tool -> Broker -> transactional Store -> pinned destination adapter -> peer host.

The peer explicitly replies through the same broker using the consultation ID and prior message ID. The broker, not the model, enforces finite grants, alternation, lineage and dispatch states. It never turns arbitrary assistant output into another request.

## State

- Grant: immutable participant pair/topic/expiry/budgets, revocation flag, consultation count. Entire peer route mapping is pinned in database metadata.
- Consultation: initiator, immutable pair, message count, active/completed/rejected/cancelled/expired state. Pair exclusivity prevents nested cycles between those same participants.
- Message: stable ID, exact consultation, sequence, sender/recipient claims, parent ID, kind, bounded text, queued/attempted/accepted/rejected/unknown outcome and detail.

Creation of a consultation plus its first question is one transaction. Each claim is a separate committed transaction before external I/O. SQLite serializes competing callers. Duplicate IDs with identical payloads return existing records; mutated payloads are refused. Unknown/attempted records block further replies in that consultation. No external transport operation runs while a SQLite transaction is held.

## Adapter boundary

Preflight checks destination facts, then send performs literal bounded I/O. An explicit pre-send rejection can close the attempt as rejected. Any uncertain execution failure is conservatively unknown. A native receipt establishes queue/write admission only. The database is not a cross-process identity authority. The same-user threat model and exact meaning of completed are documented in SECURITY.md.

## Optional MCP

The stdio server supplies tool schemas and handles initialized, ping, list/call, parse errors and finite input lines. It does not expose administrative grant/resume commands. It requires request IDs for mutating tool calls. Native host installation, permission flow and tool-result rendering require separate validation. MCP client identity is not asserted merely because the process receives JSON-RPC.

## Compatibility

Codex adapter uses the installed CLI's `queue --thread UUID --message TEXT` without `--resume`, without an app-server control socket. It requires exact CLI version and home. Claude adapter uses observed peer protocol 1 with a pinned runtime. Neither adapter installs or configures providers, changes approvals, or starts hidden agents.
