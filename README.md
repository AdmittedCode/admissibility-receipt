# Admissibility Receipt

The **proof layer** for AdmittedCode. Three tools, one shared canonical core:

- **generate** — emit a `stegverse.admissibility_receipt.v1` for a repo/release.
- **verify** — independently re-derive every claim from the receipt alone. No
  dependency on the generator. A skeptic runs this and gets PASS/FAIL per check.
- **fleet** — verify receipts org-wide; gate CI on any invalid.

## Why it matters

A receipt is only worth something if a *third party* can check it without
trusting you. The verifier re-computes every hash from the receipt (and,
optionally, the repo it describes). Tampering with any sealed field is caught
and localized — you see exactly which check failed.

## Install

```bash
pip install admissibility-receipt
```

## Use

```bash
# generate a receipt for a release
admissibility-generate ./my-repo --repo-name org/my-repo --release v1.0.0 \
  --manifest repo-guard.json --out receipt.json

# independently verify it (a buyer/auditor runs this)
admissibility-verify receipt.json --repo ./my-repo

# audit a whole fleet of receipts
admissibility-fleet ./receipts/ --fail-on-invalid
```

## Usage Snippet

Admissibility Receipts generates, verifies, and audits portable governance proof envelopes.

```bash
python -m pip install -e .
python -m pytest
admissibility-receipt generate --input examples/decision-event.json --out receipts/sample-receipt.json
admissibility-receipt verify --receipt receipts/sample-receipt.json
```

See:

```text
docs/USAGE.md
```

## What a receipt proves — and does not

A receipt asserts the product conformed to its declared manifest under GCAT/BCAT
evaluation at that release, and that the result is reproducible. Every receipt
carries an explicit `scope.does_not_assert` block; verification fails if it is
empty. It does **not** assert security, regulatory compliance, or fitness for
purpose — and the verifier enforces that the disclaimer is present.

## Canonicalization

All hashes use `stegverse.jcs.v1`: UTF-8, sorted keys, no insignificant
whitespace, integers only (floats rejected), SHA-256. The rules live in
`canon.py` and are simple enough to re-implement in any language — which is what
makes a receipt device/OS/language-agnostic to verify.

## Checks the verifier performs

| Check | What it proves |
|-------|----------------|
| `receipt_id` | the receipt body is unaltered |
| `anti_splice` | enforcement is bound to the decision it enacted |
| `decision_reproducible` | the verdict follows from its declared inputs |
| `state_hash` | the repo matches what was certified (with `--repo`) |
| `scope_present` | the receipt honestly states what it does NOT assert |
| `canon_method` | the receipt declares the canonicalization it was sealed under |
| `replay_hash` | the receipt carries a recompute anchor |
| `transition_fields` | the receipt binds the action to transition posture |
| `authority_evidence_fields` | the receipt carries TV/TVC evidence posture |
| `decision_engine_pinned` | the policy decision engine is named, versioned, and hashed |
| `enforcement_manager_pinned` | the enforcement manager is named, versioned, and hashed |

## License

MIT.
