"""
Admissibility Receipt Verifier.

Re-derives receipt integrity, decision fingerprint, enforcement binding, replay
hash, scope, canonicalization, and optional repo state.
"""
from __future__ import annotations

import argparse
import copy
import json
import pathlib
from dataclasses import dataclass
from typing import List, Optional

from .canon import CANON_METHOD, hash_obj, hash_repo_state

SCHEMA = "stegverse.admissibility_receipt.v1"

@dataclass
class Check:
    name: str
    passed: bool
    detail: str

def verify(receipt: dict, repo: Optional[pathlib.Path] = None) -> List[Check]:
    checks: List[Check] = []

    checks.append(Check("schema", receipt.get("schema") == SCHEMA, f"declared {receipt.get('schema')}"))

    claimed_id = receipt.get("receipt_id")
    body = copy.deepcopy(receipt)
    body.pop("receipt_id", None)
    recomputed = hash_obj(body)
    checks.append(Check("receipt_id", claimed_id == recomputed, f"claimed {claimed_id}; recomputed {recomputed}"))

    dec = receipt.get("decision", {})
    enf = receipt.get("enforcement", {})
    trn = receipt.get("transition", {})

    enacted = enf.get("enacted_decision_fingerprint")
    decision_fp = dec.get("fingerprint")
    checks.append(Check("anti_splice", bool(enacted) and enacted == decision_fp, f"enacted={enacted}; decision={decision_fp}"))

    redecision = {
        "manifest_hash": receipt.get("manifest", {}).get("sha256"),
        "state_hash": receipt.get("input", {}).get("sha256"),
        "verdict": dec.get("decision"),
        "reason": dec.get("reason_code"),
        "transition_cell": trn.get("transition_cell"),
        "authority_class": trn.get("authority_class"),
    }
    rederived = hash_obj(redecision)
    checks.append(Check("decision_reproducible", rederived == decision_fp, f"re-derived {rederived}; claimed {decision_fp}"))

    replay = hash_obj({
        "state_hash": receipt.get("input", {}).get("sha256"),
        "manifest_hash": receipt.get("manifest", {}).get("sha256"),
        "decision_fingerprint": decision_fp,
        "previous_receipt_hash": receipt.get("previous_receipt_hash"),
    })
    claimed_replay = receipt.get("verification", {}).get("replay_hash")
    checks.append(Check("replay_hash", replay == claimed_replay, f"re-derived {replay}; claimed {claimed_replay}"))

    if repo is not None:
        actual = hash_repo_state(repo)
        claimed = receipt.get("input", {}).get("sha256")
        checks.append(Check("state_hash", actual == claimed, f"recomputed {actual}; claimed {claimed}"))
    else:
        checks.append(Check("state_hash", True, "skipped (no --repo provided)"))

    scope = receipt.get("scope", {})
    disclaims = scope.get("does_not_assert") or []
    asserts = scope.get("asserts") or []
    checks.append(Check("scope_present", bool(asserts) and bool(disclaims), f"{len(asserts)} assert(s), {len(disclaims)} disclaimer(s)"))

    declared = receipt.get("canonicalization", {}).get("method")
    checks.append(Check("canon_method", declared == CANON_METHOD, f"declared {declared}; verifier uses {CANON_METHOD}"))

    notes = receipt.get("canonicalization", {}).get("notes")
    checks.append(Check("canon_notes", bool(notes), "present" if notes else "missing"))

    for name, container, fields in [
        ("transition_fields", receipt.get("transition", {}), ["transition_class", "transition_cell", "authority_class", "state_effect", "binding_level"]),
        ("authority_evidence_fields", receipt.get("authority_evidence", {}), ["tvc_policy_hash", "tv_receipt_refs", "formalism_refs"]),
        ("decision_engine_pinned", dec, ["engine", "engine_version", "engine_hash"]),
        ("enforcement_manager_pinned", enf, ["manager", "manager_version", "manager_hash"]),
    ]:
        missing = [f for f in fields if f not in container]
        checks.append(Check(name, not missing, f"missing={missing}"))

    return checks

def main() -> int:
    ap = argparse.ArgumentParser(description="Verify a StegVerse admissibility receipt")
    ap.add_argument("receipt", help="Path to receipt JSON")
    ap.add_argument("--repo", default="", help="Repo path to re-hash for state verification")
    ap.add_argument("--format", choices=["pretty", "json"], default="pretty")
    args = ap.parse_args()

    receipt = json.loads(pathlib.Path(args.receipt).read_text(encoding="utf-8"))
    repo = pathlib.Path(args.repo).resolve() if args.repo else None
    checks = verify(receipt, repo)
    ok = all(c.passed for c in checks)

    result = {
        "schema": "stegverse.receipt_verification.v1",
        "receipt": args.receipt,
        "valid": ok,
        "checks": [vars(c) for c in checks],
    }
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"\nVerifying: {args.receipt}")
        for c in checks:
            print(f"  {'✅' if c.passed else '❌'} {c.name}: {c.detail}")
        print(f"\n{'VALID — all checks passed' if ok else 'INVALID — one or more checks failed'}")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
