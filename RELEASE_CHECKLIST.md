# Release checklist

MIT copyright holder: Jeff Otano, 2026. The source is public at
https://github.com/JeffOtano/pairhatch as an experimental candidate. It is not
a completed release: no tag, build artifact or package-registry publication
exists. See docs/PUBLIC_RELEASE.md.

Done for the source publication (2026-11-11):
- The owner authorized publication and confirmed the destination.
- The published root commit uses a public-safe author/committer identity.
- Hosted CI ran on the published repository and passed on Linux/macOS for
  Python 3.10 to 3.14. It covers mocks and packaging only.

Still open before any tagged or packaged release:
- Complete independent source/security/provenance review. Automated checks do
  not certify absence of every secret or ownership concern.
- Review the experimental private Claude transport and vendor terms; consider
  omitting it or replacing it with a supported public interface.
- Validate live integrations separately with exact destination/content approval.
  This candidate's tests use synthetic data and mocks only.
- Confirm public package-registry name availability, support contact and vulnerability
  reporting channel. No contact or organization has been invented.
- Build artifacts from reviewed source and inspect contents before publication.
- Review Git author/committer metadata of every new commit for personal
  addresses, not only current files. Do not rewrite history without explicit approval.
- Establish and verify a private security-reporting channel. The source was
  published without one.

Do not include live peer configuration, receipts, transcripts, host logs,
credentials, vendor application binaries or private machine state in releases.
