# Packaged host validation plan

This is a runbook, not permission to register a server or send messages. The
repository's offline tests do not prove real host negotiation or a live reply.

## 1. Establish the exact test scope

Before live work, record the two named agents/hosts, their exact destination
identities, the pinned runtime versions, the synthetic message content, and a
maximum of two messages. Obtain explicit authorization to contact those named
agents. Separately obtain action-time approval for any persistent MCP registration,
credential entry, OAuth grant or access expansion. A broker grant alone does not
supply those permissions. Do not put real identities or registration files here.

## 2. Install the reviewed package

Build the reviewed commit's wheel, run the unit and clean-install checks, then
install that wheel in a dedicated virtual environment. Use absolute paths for the
installed executable and a fresh private configuration/state directory. Generate
mock configuration with `pairhatch-init`; do not overwrite an existing setup.

First validate only the stdio surface in an approved host with mock peers. The
server command is the installed absolute `pairhatch` executable with arguments:

```text
--config /absolute/private/peers.json --actor peer-a serve
```

A second host would use the same approved configuration and `--actor peer-b`.
Actor labels remain same-user claims, not authentication. Exact registration UI,
file locations and host schema must be taken from the installed host's supported
instructions; no universal registration command is verified here. Do not register
the server until the exact persistent access change is approved.

## 3. Check real host negotiation without native traffic

Verify initialization, the advertised 2024-11-05 baseline, five tool definitions,
list/call response rendering, error handling, cancellation, clean EOF/shutdown and
restart. Check the host's actual permission prompts and whether it can invoke the
tools without altering scope. Test a synthetic two-message mock consultation,
including exact replay, final completion and bounded inbox paging. This proves
host-to-broker behavior only; mock transport never delivers to another model.

## 4. Preflight approved native destinations

Only after separate native scope approval, populate a private copy of the native
template and enable experimental transports. Pin the exact Codex binary/version,
home and thread identity; pin Claude runtime/session/desktop identities and metadata
paths. Claude requires permission mode `default` and macOS kernel peer-PID support.
The private socket contract may have changed; stop on any mismatch rather than
weakening checks. Do not include sensitive content: Codex exposes message text in
child-process arguments.

Run the installed CLI with the private configuration, explicit actor and `doctor`.
This does not send but can initialize the database, persist peer bindings and run
version/process preflight commands. Require exit 0 and every peer preflight passed.
A pass is not delivery certification. If a destination is already bound differently,
stop and review; never silently repoint it.

## 5. One bounded, authorized live consultation

Create one expiring grant for the exact pair and synthetic topic with a two-message
budget and one consultation. Use fresh explicit UUID message IDs. Send one question
through the approved initiating agent and inspect the exact target host for receipt.
Have that target agent invoke `reply_to_peer` with the received consultation ID,
question ID, a fresh reply UUID and `final: true`. Confirm the final reply in the
original host and verify broker state is completed with exactly two admitted
messages. Accepted transport receipts alone are insufficient.

Replay the same IDs only to verify recorded outcomes, never to force redispatch.
On rejection or uncertainty, inspect recorded state; do not automatically retry or
switch targets. Record sanitized pass/fail results and precise runtime versions,
never raw transcripts, live IDs, credentials or host registration files in Git.

## Current blockers

- Partial evidence: temporary Codex 0.167.0 on macOS initialized and discovered
  five tools from an earlier candidate, but noninteractive policy denied tool
  execution. No messages were sent. This is not installed-bundle or two-host
  certification. Claude validation was network-policy blocked; Cursor live
  validation and marketplace installation remain unverified. See VALIDATION.md.
- Persistent registration/access and exact named live contacts/content require
  separate authorization before execution.
- Native Claude uses an observed private protocol; vendor compatibility/terms and
  macOS behavior remain unverified here.
- Hosted CI is independently budget-blocked; local Linux checks do not establish
  the configured multi-platform matrix.
