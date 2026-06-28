#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTAKE = ROOT / "integration" / "gcat-bcat-intake.json"
OUT = ROOT / "dist" / "gcat-bcat-intake-result.json"
REQUIRED = [
    "decision reproducible",
    "scope non-claims present",
    "transition fields present",
    "authority evidence fields present",
    "decision engine pinned"
]


def main():
    data = json.loads(INTAKE.read_text(encoding="utf-8"))
    props = data.get("required_receipt_properties", [])
    missing = [item for item in REQUIRED if item not in props]
    ok = not missing and data.get("source_repository") == "Admissible-Existence/GCAT-BCAT"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"intake_id": data.get("intake_id"), "result": "PASS" if ok else "FAIL", "missing": missing}, indent=2) + "\n", encoding="utf-8")
    if ok:
        print("PASS GCAT BCAT intake")
        return 0
    print("FAIL GCAT BCAT intake", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
