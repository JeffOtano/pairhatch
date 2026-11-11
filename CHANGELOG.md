# Changelog

## Unreleased

- Published the source repository; corrected documentation and generated
  bundle text that described it as private or not yet run in hosted CI.

- Add one-command offline setup with disposable checks, zero persistent grants,
  and review-only host snippets; add optional instruction-only plugin manifests.

- Bound inbox reads to 100 records with SQL filtering and CLI/MCP pagination.
  Pages use consultation-ID/sequence order; concurrent arrivals can shift offsets.
- Return nonzero from doctor when any preflight fails; document database effects.
- Fail closed on missing Claude version pins and unknown/elevated permission modes.
- Report expected initializer path errors without a traceback or overwriting files.
- Add positive/mixed preflight tests and a scoped packaged-host validation runbook.

- Reject explicit empty consultation/message IDs instead of silently generating
  new IDs, preserving replay safety and preventing unintended repeated dispatch.

- Added contributor workflow, review template and synthetic-data bug template.
- Added release-content checks and reproducible offline validation guidance.
- Expanded CI matrix and bounded job duration; no automated publication.

## 10.0.0 - Private experimental candidate

- Packaged the local peer-consultation broker with CLI and optional stdio MCP.
- Added SQLite grants, bounded consultations, replay outcomes and mock transport.
- Kept native Codex and private Claude transports behind an experimental opt-in.
- Added offline tests, portable mock initializer and clean wheel-install smoke test.

No public release or stable native-protocol compatibility is claimed.

## Unreleased: portable host onboarding

- Generate private, review-only skill + MCP bundles for Claude Code, Codex, Cursor
  and generic stdio clients, with explicit per-actor paths and repeatable --host.
- Package the operational skill inside wheels; keep the plugin setup skill separate.
- Document manual activation/removal, host capability matrix, and no automatic
  wake-up claim. No host settings or permission policies are changed by setup.
- Contract-test all generated host/actor launchers, tool discovery and grant denial.
