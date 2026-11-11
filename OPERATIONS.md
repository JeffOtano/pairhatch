# Operations and deployment checklist

1. Review the package and run its offline tests. Select two exact authorized sessions and non-sensitive scope. Do not equate a title with identity.
2. Place a reviewed config and private database in a deliberate location. Run `doctor`. Do not silently repoint an old logical peer or reuse an old grant for a new session.
3. Obtain approval before registering an MCP server or otherwise creating persistent access in either host. Specify exact executable, configuration, database and actor for each. Existing shell approval policies remain applicable. Do not work around a denied tool/command.
4. Create one finite operator grant for the exact pair/topic and bounded messages. Start with one two-message synthetic consultation. Confirm receipt in each actual host, not merely stdout or queue admission. If structured reply is unavailable, stop and report that setup remains incomplete.
5. In the intended UX, either agent explicitly invokes ask_peer only when a second opinion helps. The recipient may answer, ask one follow-up, or finish. It does not recursively spawn agents. Final messages require no reply. There are no nested consultations for a pair and no automatic replay of ordinary chat messages.
6. Inspect status/inbox for recorded evidence. Inbox is a historical view, not an acknowledgement queue or unread indicator. Use consultation IDs and parent message IDs to correlate answers.
7. `pause` stops new claims globally; `revoke --grant ID` disables a grant; `cancel --consultation ID` stops future participation. These do not retract already queued messages. `resume` cannot restore revoked authority.
8. For attempted/unknown outcomes, inspect the exact recipient manually using its supported UI/API, preserving IDs. Never blindly resubmit. There is deliberately no forced replay/reconcile command. Cancel the consultation if uncertain. If a new test is authorized, use a fresh consultation and message IDs.
9. On runtime upgrades, rerun tests and review protocol/schema changes before repinning. Do not bypass failed checks. SQLite schema version changes are refused, not automatically migrated.
10. Stop stdio hosts normally to stop tool availability. No service, launch agent, network listener, schedule or credential was installed by this build. After deployment, remove host registration explicitly if desired; retain or delete local evidence according to your own policy.

## Remaining production work

Host-specific registration and end-to-end validation of the rewritten MCP interface; authenticated origin separation if same-user shell access is not trusted; supported public Claude transport or explicitly maintained pinned compatibility; host receipt/completion events; real spend accounting; UI for grants, activity and cancellation; signing/update policy; automated retention controls. These are named limits, not implemented features.


## Bounded inbox pages

`inbox` returns an array of at most 100 accepted messages addressed to the selected
actor. Use `--limit 1..100 --offset N`; MCP `peer_inbox` accepts integer `limit` and
`offset` arguments with the same defaults (100 and 0). Increase offset by the page
size until fewer than that many records are returned. Results are ordered by
consultation ID then sequence, not arrival time. Offset pages are not a snapshot:
concurrent incoming records can shift pages, so deduplicate by message ID and
restart from offset zero when needed. This is not acknowledgement, deletion or a
background listener. Filtering happens in SQL before the bounded result is loaded.

See docs/HOST_VALIDATION.md for the separately authorized packaged-host test plan.
