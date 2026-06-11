"""
Fleet audit for StegVerse admissibility receipts.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any, Dict, List, Tuple

from .verify import verify

def audit_fleet(pairs: List[Tuple[pathlib.Path, pathlib.Path | None]]) -> Dict[str, Any]:
    results = []
    valid = invalid = unreadable = 0
    for rpath, repo in pairs:
        entry: Dict[str, Any] = {"receipt": str(rpath), "repo": str(repo) if repo else None}
        try:
            receipt = json.loads(pathlib.Path(rpath).read_text(encoding="utf-8"))
            checks = verify(receipt, pathlib.Path(repo) if repo else None)
        except Exception as e:
            entry.update(valid=False, error=f"unreadable_or_unverifiable: {e}")
            unreadable += 1
            results.append(entry)
            continue
        ok = all(c.passed for c in checks)
        entry.update(
            valid=ok,
            product=receipt.get("repo"),
            release=receipt.get("release"),
            portability_class=receipt.get("enforcement", {}).get("portability_class"),
            failed_checks=[c.name for c in checks if not c.passed],
        )
        valid += int(ok)
        invalid += int(not ok)
        results.append(entry)
    return {
        "schema": "stegverse.fleet_audit.v1",
        "summary": {"total": len(pairs), "valid": valid, "invalid": invalid, "unreadable": unreadable},
        "results": results,
    }

def main() -> int:
    ap = argparse.ArgumentParser(description="Verify admissibility receipts org-wide")
    ap.add_argument("receipts", nargs="+", help="Receipt JSON paths or directories to search for *receipt*.json")
    ap.add_argument("--repos-root", default="", help="Optional root; each receipt maps to repos-root/<product-basename>")
    ap.add_argument("--format", choices=["pretty", "json"], default="pretty")
    ap.add_argument("--fail-on-invalid", action="store_true")
    args = ap.parse_args()

    paths: list[pathlib.Path] = []
    for item in args.receipts:
        p = pathlib.Path(item)
        paths.extend(sorted(p.rglob("*receipt*.json")) if p.is_dir() else [p])

    root = pathlib.Path(args.repos_root) if args.repos_root else None
    pairs = []
    for p in paths:
        repo = None
        if root:
            try:
                product = json.loads(p.read_text(encoding="utf-8")).get("repo", "").split("/")[-1]
                cand = root / product
                repo = cand if cand.is_dir() else None
            except Exception:
                repo = None
        pairs.append((p, repo))

    report = audit_fleet(pairs)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        s = report["summary"]
        print(f"\nFleet Audit — {s['valid']}/{s['total']} valid ({s['invalid']} invalid, {s['unreadable']} unreadable)\n")
        for r in report["results"]:
            mark = "✅" if r["valid"] else "❌"
            extra = f" failed: {r['failed_checks']}" if r.get("failed_checks") else (f" ({r['error']})" if r.get("error") else "")
            print(f"  {mark} {r.get('product') or r['receipt']} {r.get('release') or ''}{extra}")
    return 1 if args.fail_on_invalid and report["summary"]["invalid"] + report["summary"]["unreadable"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
