# Publication checklist

MIT copyright holder: Jeff Otano, 2026. This is an experimental candidate,
not a completed public release. See docs/PUBLIC_RELEASE.md.

Before public release:
- Obtain explicit publication authorization and confirm the destination.
- Complete independent source/security/provenance review. Automated checks do
  not certify absence of every secret or ownership concern.
- Review the experimental private Claude transport and vendor terms; consider
  omitting it or replacing it with a supported public interface.
- Validate live integrations separately with exact destination/content approval.
  This candidate's tests use synthetic data and mocks only.
- Confirm public package-registry name availability, support contact and vulnerability
  reporting channel. No contact or organization has been invented.
- Run CI on the intended repository and inspect results. CI configuration here
  is not evidence of a successful hosted run.
- Build artifacts from reviewed source and inspect contents before publication.
- Review all Git commit author/committer metadata for personal addresses, not
  only current files. Do not rewrite history without explicit approval.
- Establish and verify a private security-reporting channel before public release.

Do not include live peer configuration, receipts, transcripts, host logs,
credentials, vendor application binaries or private machine state in releases.
