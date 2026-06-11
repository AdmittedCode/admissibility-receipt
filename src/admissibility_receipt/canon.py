"""
Canonical hashing for StegVerse admissibility receipts.

This module is the single source of truth for `stegverse.jcs.v1` bytes.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import pathlib
from typing import Any, Iterable

CANON_METHOD = "stegverse.jcs.v1"
DEFAULT_REPO_EXCLUDES = (
    ".git/**",
    "**/__pycache__/**",
    "**/*.pyc",
    "**/*.pyo",
    "**/*.egg-info/**",
    "node-compile-cache/**",
    "receipts/**",
    "reports/**",
    "dist/**",
    "build/**",
    "admissibility-receipt.json",
    "admissibility_receipt.json",
    "*receipt*.json",
)

class CanonError(ValueError):
    """Raised when a value cannot be canonicalized deterministically."""

def _reject_floats(obj: Any, path: str = "$") -> None:
    if isinstance(obj, float):
        raise CanonError(
            f"float at {path}: floats are not allowed in hashed payloads "
            "(use integers or canonical decimal strings)."
        )
    if isinstance(obj, dict):
        for k, v in obj.items():
            if not isinstance(k, str):
                raise CanonError(f"non-string JSON object key at {path}: {k!r}")
            _reject_floats(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            _reject_floats(v, f"{path}[{i}]")

def canon_bytes(obj: Any) -> bytes:
    _reject_floats(obj)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def sha256_hex(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()

def hash_obj(obj: Any) -> str:
    return sha256_hex(canon_bytes(obj))

def hash_file(path: pathlib.Path | str) -> str:
    return sha256_hex(pathlib.Path(path).read_bytes())

def _excluded(rel: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(rel, pat) for pat in patterns)

def hash_repo_state(repo: pathlib.Path | str, *, excludes: Iterable[str] = DEFAULT_REPO_EXCLUDES) -> str:
    """
    Deterministic hash of a repo file tree as {posix_relpath: filehash}.

    Receipt/report/build outputs are excluded by default so a generated receipt
    can live beside the product without changing the product state it certifies.
    """
    repo = pathlib.Path(repo)
    state: dict[str, str] = {}
    for p in sorted(repo.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(repo).as_posix()
        if _excluded(rel, excludes):
            continue
        state[rel] = hash_file(p)
    return hash_obj(state)
