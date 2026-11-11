# Data and retention

The SQLite database stores message plaintext, grant topics, exact configured
peer routes, logical identities, timestamps, lineage and delivery diagnostics.
Console/MCP output can contain the same information. Native destinations retain
messages independently according to their own policies. There is no telemetry
in this package, automatic export, encryption at rest or automatic expiration
cleanup. Grant expiry is an authority limit, not data deletion.

Use a private 0700 directory and 0600 database/configuration files on trusted
local storage. Avoid synchronized folders and shared machines. Review backups,
shell history, process listings and host logs separately. Submit only content
explicitly permitted for the destination. Prefer stdin rather than --text.

Choose a retention period before deployment. To retire state: pause the broker,
revoke grants, stop all CLI/MCP clients and any separately registered host, then
archive or remove the database and its SQLite sidecars under your own approved
policy. Do not delete live SQLite files. Deleting local state cannot retract
messages or copies in recipient hosts, backups or SSD snapshots, and does not
guarantee secure erasure. A newly created database has no previous deduplication
history: never use fresh state to blindly retry an uncertain prior send.

No purge command is included. Operators must separately authorize destructive
cleanup and coordinate access. Retention automation remains future work.

## Native Codex command-line disclosure

Even when broker input comes from stdin, the experimental Codex queue adapter
passes the complete rendered peer message, approved topic and correlation IDs
in the child process's --message argument. These may be visible in process
listings and process-audit logs. Stdin avoids the broker's own --text argument
and shell history, but does not prevent this downstream exposure. Do not use
this adapter for sensitive content. A verified non-argv native input mechanism
is not implemented.
