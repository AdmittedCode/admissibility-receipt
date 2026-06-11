# Changelog
## v1.0.0
- Generator: emit stegverse.admissibility_receipt.v1 for a repo/release.
- Verifier: independent re-derivation of every claim (auditable; no dependency on generator).
- Fleet audit: org-wide receipt verification with --fail-on-invalid gate.
- Shared canonical hashing core (stegverse.jcs.v1): floats rejected, sorted keys, UTF-8, SHA-256.
- Tamper detection verified for verdict, state, and scope.
