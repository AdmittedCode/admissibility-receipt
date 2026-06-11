"""
Admissibility Receipt Generator.

Emits `stegverse.admissibility_receipt.v1`. The ALLOW/DENY/FAIL_CLOSED verdict
is supplied by StegCore/StegCGE inputs; this generator seals the envelope and
hashes without inventing authority.
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
from typing import List

from .canon import CANON_METHOD, DEFAULT_REPO_EXCLUDES, hash_file, hash_obj, hash_repo_state

SCHEMA = "stegverse.admissibility_receipt.v1"

DEFAULT_DISCLAIMS = [
    "Security, vulnerability-freedom, or penetration resistance.",
    "Regulatory or legal compliance (e.g. PCI, HIPAA, GDPR).",
    "Fitness for any particular purpose.",
    "Runtime correctness beyond declared policy.",
]

def now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def _engine_hash(name: str, version: str) -> str:
    # Placeholder until engines publish signed release artifacts.
    return hash_obj({"engine": name, "version": version})

def generate(
    repo: pathlib.Path,
    *,
    entity: str,
    repo_name: str,
    release: str,
    manifest_path: str,
    verdict: str,
    reason_code: str,
    basis: str,
    portability_class: str,
    platform_dependencies: List[str],
    decision_engine: str,
    decision_engine_version: str,
    enforcement_manager: str,
    enforcement_manager_version: str,
    scope_asserts: List[str],
    scope_disclaims: List[str],
    previous_receipt_hash: str,
    stage: str = "publish",
    actor: str = "ci/release",
    declared_action: str = "publish_product_release",
    transition_class: str = "release",
    transition_cell: str = "release.publish",
    authority_class: str = "policy_decision_bound",
    state_effect: str = "publishable_artifact",
    binding_level: str = "receipt_bound",
    tvc_policy_hash: str = "sha256:UNSPECIFIED",
    tv_receipt_refs: List[str] | None = None,
    formalism_refs: List[str] | None = None,
) -> dict:
    repo = pathlib.Path(repo)
    state_hash = hash_repo_state(repo)
    mpath = repo / manifest_path
    manifest_hash = hash_file(mpath) if mpath.is_file() else "sha256:MISSING"

    decision_inputs = {
        "manifest_hash": manifest_hash,
        "state_hash": state_hash,
        "verdict": verdict,
        "reason": reason_code,
        "transition_cell": transition_cell,
        "authority_class": authority_class,
    }
    decision_fp = hash_obj(decision_inputs)
    replay_hash = hash_obj({
        "state_hash": state_hash,
        "manifest_hash": manifest_hash,
        "decision_fingerprint": decision_fp,
        "previous_receipt_hash": previous_receipt_hash,
    })

    receipt = {
        "schema": SCHEMA,
        "timestamp_utc": now_utc(),
        "entity": entity,
        "repo": repo_name,
        "release": release,
        "stage": stage,
        "actor": actor,
        "declared_action": declared_action,
        "input": {
            "path": ".",
            "sha256": state_hash,
            "excluded_paths": list(DEFAULT_REPO_EXCLUDES),
        },
        "manifest": {"path": manifest_path, "sha256": manifest_hash},
        "transition": {
            "transition_class": transition_class,
            "transition_cell": transition_cell,
            "authority_class": authority_class,
            "state_effect": state_effect,
            "binding_level": binding_level,
        },
        "authority_evidence": {
            "tvc_policy_hash": tvc_policy_hash,
            "tv_receipt_refs": tv_receipt_refs or [],
            "formalism_refs": formalism_refs or [],
        },
        "decision": {
            "engine": decision_engine,
            "engine_version": decision_engine_version,
            "engine_hash": _engine_hash(decision_engine, decision_engine_version),
            "decision": verdict,
            "reason_code": reason_code,
            "basis": basis,
            "fingerprint": decision_fp,
        },
        "enforcement": {
            "manager": enforcement_manager,
            "manager_version": enforcement_manager_version,
            "manager_hash": _engine_hash(enforcement_manager, enforcement_manager_version),
            "route": verdict,
            "enacted_decision_fingerprint": decision_fp,
            "portability_class": portability_class,
            "platform_dependencies": platform_dependencies,
            "fail_closed_reason": "" if verdict != "FAIL_CLOSED" else reason_code,
        },
        "verification": {
            "state_hash": state_hash,
            "replay_hash": replay_hash,
            "reverification_possible": True,
            "reverify_command": "admissibility-verify <receipt> --repo <path>",
        },
        "canonicalization": {
            "method": CANON_METHOD,
            "hash": "sha256",
            "notes": "UTF-8; keys sorted; separators ',', ':'; no floats in hashed payloads; LF recommended for files.",
        },
        "scope": {"asserts": scope_asserts, "does_not_assert": scope_disclaims},
        "outputs": [],
        "previous_receipt_hash": previous_receipt_hash,
    }
    receipt["receipt_id"] = hash_obj(receipt)
    return receipt

def main() -> int:
    ap = argparse.ArgumentParser(description="Generate a StegVerse admissibility receipt")
    ap.add_argument("repo", help="Repo path to certify")
    ap.add_argument("--entity", default="AdmittedCode")
    ap.add_argument("--repo-name", required=True)
    ap.add_argument("--release", required=True)
    ap.add_argument("--manifest", default="repo-guard.json")
    ap.add_argument("--verdict", default="ALLOW", choices=["ALLOW", "DENY", "FAIL_CLOSED"])
    ap.add_argument("--reason-code", default="OK")
    ap.add_argument("--basis", default="conforms to declared manifest under GCAT/BCAT evaluation")
    ap.add_argument("--portability-class", default="hybrid", choices=["portable", "hybrid", "platform_bound"])
    ap.add_argument("--platform-deps", nargs="*", default=["ci_runner_identity"])
    ap.add_argument("--decision-engine", default="StegCore")
    ap.add_argument("--decision-engine-version", default="0.1.0")
    ap.add_argument("--enforcement-manager", default="StegCGE")
    ap.add_argument("--enforcement-manager-version", default="0.1.0")
    ap.add_argument("--previous-receipt-hash", default="sha256:GENESIS")
    ap.add_argument("--tvc-policy-hash", default="sha256:UNSPECIFIED")
    ap.add_argument("--out", default="admissibility-receipt.json")
    args = ap.parse_args()

    receipt = generate(
        pathlib.Path(args.repo).resolve(),
        entity=args.entity,
        repo_name=args.repo_name,
        release=args.release,
        manifest_path=args.manifest,
        verdict=args.verdict,
        reason_code=args.reason_code,
        basis=args.basis,
        portability_class=args.portability_class,
        platform_dependencies=args.platform_deps,
        decision_engine=args.decision_engine,
        decision_engine_version=args.decision_engine_version,
        enforcement_manager=args.enforcement_manager,
        enforcement_manager_version=args.enforcement_manager_version,
        scope_asserts=[
            "Conforms to declared manifest under GCAT/BCAT at this release.",
            "Reproducible from committed policy + this receipt.",
        ],
        scope_disclaims=DEFAULT_DISCLAIMS,
        previous_receipt_hash=args.previous_receipt_hash,
        tvc_policy_hash=args.tvc_policy_hash,
    )
    pathlib.Path(args.out).write_text(json.dumps(receipt, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(f"wrote {args.out} receipt_id={receipt['receipt_id']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
