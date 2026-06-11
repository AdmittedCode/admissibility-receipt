import copy
import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from admissibility_receipt.canon import hash_obj
from admissibility_receipt.generate import generate
from admissibility_receipt.verify import verify

def _fixture(root):
    repo = root / "demo"
    repo.mkdir(parents=True, exist_ok=True)
    (repo / "repo-guard.json").write_text(json.dumps({"governance_role": "consumer"}), encoding="utf-8")
    (repo / "app.py").write_text("x=1\n", encoding="utf-8")
    return repo

def _gen(repo):
    return generate(
        repo,
        entity="AdmittedCode",
        repo_name="admittedcode/demo",
        release="v1.0.0",
        manifest_path="repo-guard.json",
        verdict="ALLOW",
        reason_code="OK",
        basis="b",
        portability_class="hybrid",
        platform_dependencies=["ci"],
        decision_engine="StegCore",
        decision_engine_version="0.1.0",
        enforcement_manager="StegCGE",
        enforcement_manager_version="0.1.0",
        scope_asserts=["a"],
        scope_disclaims=["not security"],
        previous_receipt_hash="sha256:GENESIS",
    )

def _reseal(r):
    b = copy.deepcopy(r)
    b.pop("receipt_id", None)
    r["receipt_id"] = hash_obj(b)

def test_valid_receipt_verifies():
    with tempfile.TemporaryDirectory() as d:
        repo = _fixture(pathlib.Path(d))
        r = _gen(repo)
        assert all(c.passed for c in verify(r, repo))

def test_receipt_file_inside_repo_is_excluded_from_state_hash():
    with tempfile.TemporaryDirectory() as d:
        repo = _fixture(pathlib.Path(d))
        r = _gen(repo)
        (repo / "admissibility-receipt.json").write_text(json.dumps(r), encoding="utf-8")
        assert all(c.passed for c in verify(r, repo))

def test_tamper_verdict_fails_id_and_reproducibility():
    with tempfile.TemporaryDirectory() as d:
        repo = _fixture(pathlib.Path(d))
        r = _gen(repo)
        r["decision"]["decision"] = "DENY"
        failed = {c.name for c in verify(r, repo) if not c.passed}
        assert "receipt_id" in failed and "decision_reproducible" in failed, failed

def test_tamper_enforcement_binding_fails_anti_splice():
    with tempfile.TemporaryDirectory() as d:
        repo = _fixture(pathlib.Path(d))
        r = _gen(repo)
        r["enforcement"]["enacted_decision_fingerprint"] = "sha256:" + "0" * 64
        _reseal(r)
        failed = {c.name for c in verify(r, repo) if not c.passed}
        assert failed == {"anti_splice"}, failed

def test_tamper_state_fails_state_hash():
    with tempfile.TemporaryDirectory() as d:
        repo = _fixture(pathlib.Path(d))
        r = _gen(repo)
        (repo / "app.py").write_text("x=999\n", encoding="utf-8")
        failed = {c.name for c in verify(r, repo) if not c.passed}
        assert "state_hash" in failed, failed

def test_missing_scope_disclaimer_fails():
    with tempfile.TemporaryDirectory() as d:
        repo = _fixture(pathlib.Path(d))
        r = _gen(repo)
        r["scope"]["does_not_assert"] = []
        _reseal(r)
        failed = {c.name for c in verify(r, repo) if not c.passed}
        assert failed == {"scope_present"}, failed

def test_missing_transition_field_fails():
    with tempfile.TemporaryDirectory() as d:
        repo = _fixture(pathlib.Path(d))
        r = _gen(repo)
        del r["transition"]["authority_class"]
        _reseal(r)
        failed = {c.name for c in verify(r, repo) if not c.passed}
        assert "transition_fields" in failed and "decision_reproducible" in failed, failed

if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        try:
            fn()
            print("PASS", fn.__name__)
            passed += 1
        except AssertionError:
            print("FAIL", fn.__name__)
            traceback.print_exc()
    print(f"\n{passed}/{len(fns)} passed")
    sys.exit(0 if passed == len(fns) else 1)
