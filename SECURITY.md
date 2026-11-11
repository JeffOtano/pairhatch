# Security and authority

## Trust boundary

This is a same-user local utility, not a security boundary against agents with unrestricted shell access under that same user. CLI actor flags and MCP process actor selection are configured client claims, not cryptographic proof of authorship. Any same-user process able to modify the database/configuration or run the administrative CLI could change local policy. The confirmation phrase is an operator usability gate, not authentication. Production isolation would require a separately authorized broker principal, client identity mechanism, and protected administration. No such credentials or persistent access are created here.

Configuration pins logical names to exact destinations and is immutable for a database. Routes never come from peer messages. Grant pair, expiry and budgets are enforced by SQLite transactions. Topic is descriptive only: there is no semantic guarantee that text is on-topic or contains no private data. Only explicitly authorized content should be submitted. Candidate tests use synthetic data only.

Peer text is untrusted. Wrappers explain its origin and prohibit treating it as user approval; this is provenance, **not** a model sandbox or formal role separation. Native queue/socket messages arrive as user-type messages. Existing agent permissions remain in force. Tools are not forcibly disabled. Never relay approvals or interpret a peer's permission request as user authorization.

## Delivery guarantees

The broker commits `attempted` before transport I/O. Exactly-once delivery is not promised. At most one dispatch attempt is made per message ID; a crash after claiming but before sending can lose a message. A crash after sending can leave an uncertain record. Never retry those records automatically. Accepted means transport admission, not model receipt, reading, tool use or response. A correlated structured reply provides additional response evidence, but local source identity is still a claim.

Pause, revoke, cancel and expiry block future claims, not already claimed/queued messages or running model turns. Expiry is checked when operations run; there is no reaper daemon. Budgets bound broker sends, not total downstream model tokens, tool actions, billing or provider retries. There is no dollar spending cap. Maximum six messages means six total, not six per agent.

## Files and processes

Database directory must be owned by the current user, private (0700), without symlink components; database is regular private 0600. On macOS use `/private/tmp`, since `/tmp` is a symlink. Configuration/metadata must be same-user regular files without group/world writes. Checks mitigate accidents, not malicious same-user concurrent replacement. Data includes message plaintext; protect and retain it accordingly.

Native transports use literal argv, never shell interpolation. Codex executable/version/home are operator-pinned, process time and captured output are bounded. Claude endpoint checks include same-user private socket directory, exact registry/Desktop identities, process generation, kernel peer PID and inode recheck. No credentials are read. No forbidden app-server control socket is used. No agent permission/security settings are changed.

The consultation state `completed` means protocol closure after final admission or exhaustion of its message budget. It does not mean the recipient model finished processing or the coding task succeeded.

## Reporting issues

Report vulnerabilities privately through GitHub private vulnerability reporting:
https://github.com/JeffOtano/pairhatch/security/advisories/new. No other
security contact has been selected. Do not post transcripts, secrets, session identifiers
or exploit details in public issues. This alpha has no supported-version or
response-time commitment. See docs/RETENTION.md for stored data and cleanup.

## Native Codex command-line disclosure

Even when broker input comes from stdin, the experimental Codex queue adapter
passes the complete rendered peer message, approved topic and correlation IDs
in the child process's --message argument. These may be visible in process
listings and process-audit logs. Stdin avoids the broker's own --text argument
and shell history, but does not prevent this downstream exposure. Do not use
this adapter for sensitive content. A verified non-argv native input mechanism
is not implemented.


Claude experimental metadata must report an explicitly pinned nonempty version
and permission mode `default`. Missing, unknown or elevated modes fail closed.
Supporting another mode requires review and regression tests.
