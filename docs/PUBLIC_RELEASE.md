# Preparing an experimental release

This source snapshot has an independent Git history. Preparation does not publish
it, create a repository, change visibility or install host integrations.

Before publishing:
1. Confirm the public repository name and destination. Update repository URLs,
   plugin marketplace commands and metadata if the destination changes.
2. Review every tracked file and archive; do not include broker databases,
   credentials, live configuration, transcripts, host logs or old Git objects.
3. Verify author and committer attribution uses a public-safe identity. A .mailmap
   does not remove underlying author information.
4. Run the complete checks in CONTRIBUTING.md against the exact candidate.
   Local checks do not establish success across the hosted CI matrix.
5. Establish a private vulnerability-reporting route and preserve the experimental
   limitations in README.md, SECURITY.md and docs/COMPATIBILITY.md.
6. Publish only the reviewed snapshot to the approved destination. Verify remote
   refs and visibility, then tag/build artifacts from that source.

A Git bundle preserves the candidate's single clean root commit; a source ZIP
contains no Git history. Neither is a package-registry publication. Keep unrelated
private history and working copies separate, and never add them as parents.

The instruction-only plugin does not automatically connect agents. Marketplace
installation and a complete independent two-host exchange remain unverified.
