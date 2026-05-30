"""Tests for tools/validate-manifest.py.

Run: python -m pytest tests/test_validate_manifest.py -q
(or: python tests/test_validate_manifest.py for a quick smoke).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_VALIDATOR = REPO_ROOT / "tools" / "validate-manifest.py"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "manifests"


def _run(path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(MANIFEST_VALIDATOR), str(path)],
        capture_output=True,
        text=True,
    )


def test_minimal_valid():
    r = _run(FIXTURES / "minimal-valid.yaml")
    assert r.returncode == 0, r.stderr


def test_explicit_components_valid():
    r = _run(FIXTURES / "explicit-components-valid.yaml")
    assert r.returncode == 0, r.stderr


def test_extends_valid():
    r = _run(FIXTURES / "extends-valid.yaml")
    assert r.returncode == 0, r.stderr


def test_deprecated_profile_alias_valid_with_warning():
    # A legacy `profile:` manifest still validates (exit 0) but warns.
    r = _run(FIXTURES / "deprecated-profile-valid.yaml")
    assert r.returncode == 0, r.stderr
    assert "deprecated" in r.stderr.lower(), r.stderr


def test_unknown_harness_invalid():
    r = _run(FIXTURES / "unknown-harness-invalid.yaml")
    assert r.returncode == 1, "expected validation failure"


def test_empty_invalid():
    r = _run(FIXTURES / "empty-invalid.yaml")
    assert r.returncode == 1, "expected validation failure"


def test_unsupported_schema_invalid():
    r = _run(FIXTURES / "unsupported-schema-invalid.yaml")
    assert r.returncode == 1, "expected validation failure"


if __name__ == "__main__":
    # Lightweight smoke runner when pytest isn't available.
    failures = 0
    checks = [
        ("minimal-valid", "minimal-valid.yaml", 0),
        ("explicit-components-valid", "explicit-components-valid.yaml", 0),
        ("extends-valid", "extends-valid.yaml", 0),
        ("deprecated-profile-valid", "deprecated-profile-valid.yaml", 0),
        ("unknown-harness-invalid", "unknown-harness-invalid.yaml", 1),
        ("empty-invalid", "empty-invalid.yaml", 1),
        ("unsupported-schema-invalid", "unsupported-schema-invalid.yaml", 1),
    ]
    for label, fname, want in checks:
        proc = _run(FIXTURES / fname)
        ok = proc.returncode == want
        print(f"[{'PASS' if ok else 'FAIL'}] {label}: rc={proc.returncode} (want {want})")
        if not ok:
            failures += 1
    sys.exit(1 if failures else 0)
