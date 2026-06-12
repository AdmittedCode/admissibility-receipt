# Admissibility Receipts Usage Guide

**Project:** AdmittedCode / admissibility-receipts  
**Role:** portable proof envelope  
**Purpose:** generate, verify, and audit receipt-bound decisions across AdmittedCode repos.

---

## 1. What This Repo Does

Admissibility Receipts records what was evaluated, what decision was made, what evidence was bound, and what the receipt does not assert.

It is the proof layer.

It does not make provider calls.

It does not decide policy alone.

It does not store secrets.

It emits portable receipts that can be independently verified.

---

## 2. Pipeline Position

```text
Code Admit Gate
↓
Coherency Scanner
↓
Admissibility Receipts
↓
Provider Harness
↓
Replayability
↓
governed execution
```

Canonical distinction:

```text
Code Admit Gate lets an action enter the pipeline.
Coherency Scanner checks governance posture.
Admissibility Receipts prove the decision.
Provider Harness demonstrates governed provider use.
```

---

## 3. Quick Start

Install from repo root:

```bash
python -m pip install -e .
```

Run tests:

```bash
python -m pytest
```

Generate a sample receipt:

```bash
admissibility-receipt generate \
  --input examples/decision-event.json \
  --out receipts/sample-receipt.json
```

Verify a receipt:

```bash
admissibility-receipt verify \
  --receipt receipts/sample-receipt.json
```

Audit a folder of receipts:

```bash
admissibility-receipt audit \
  --receipts receipts \
  --out reports/receipt-audit.json
```

---

## 4. Example Decision Event

```json
{
  "schema": "admittedcode.decision_event.v1",
  "event_id": "demo-provider-harness-mock-allow",
  "repo": "provider-harness",
  "declared_action": "provider_harness_mock_allow",
  "decision": "ALLOW",
  "mode": "mock",
  "key_requested": false,
  "evidence": {
    "request_hash": "sha256:example",
    "consent_hash": "sha256:example",
    "budget_hash": "sha256:example",
    "coherency_report_hash": "sha256:example"
  },
  "scope": {
    "asserts": [
      "the declared request was evaluated under the declared path"
    ],
    "does_not_assert": [
      "provider security",
      "output correctness",
      "guaranteed lower cost"
    ]
  }
}
```

---

## 5. Receipt Requirements

A receipt should include:

```text
schema
timestamp
repo
declared_action
decision
mode
key_requested
evidence hashes
gates or checks
scope.asserts
scope.does_not_assert
canonicalization
receipt_id
```

A receipt must not include:

```text
API keys
payment method values
raw provider responses
private prompt content
unredacted secrets
```

---

## 6. Verification

Verification means:

```text
canonicalize receipt body
remove receipt_id
hash canonical body
compare computed hash to receipt_id
validate required fields
validate scope disclaimers
```

A valid receipt proves only what it asserts.

It does not prove what it explicitly disclaims.

---

## 7. CI Usage

Suggested workflow path:

```text
.github/workflows/admissibility-receipts-ci.yml
```

Displayed without the leading dot:

```text
github/workflows/admissibility-receipts-ci.yml
```

CI should:

```text
install package
run tests
generate sample receipt
verify sample receipt
audit receipts folder
upload audit report
```

---

## 8. What Success Looks Like

A useful public demo should show:

```text
1. Receipt generation from a decision event.
2. Receipt verification succeeds.
3. Tampered receipt verification fails.
4. Folder audit summarizes valid/invalid receipts.
5. Scope disclaimer is present.
6. Receipt contains no secret-like fields.
```

---

## 9. Canonical Usage Claim

```text
Admissibility Receipts make governance decisions portable, independently verifiable, and replayable without requiring trust in the original service.
```
