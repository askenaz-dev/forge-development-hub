"""Tests for tools/validate-manifest.py.

Run with stdlib unittest:
    python -m unittest tests.test_validate_manifest
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "tools" / "validate-manifest.py"

spec = importlib.util.spec_from_file_location("validate_manifest", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
vm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vm)


# Sample components index simulating a hub with all four primitives present.
SAMPLE_COMPONENTS_IDX = {
    "skill": {"design-system", "i18n-helper"},
    "rule": {"no-console-log"},
    "agent": {"forge-pr-writer"},
    "hook": {"doctor-on-session-start"},
}

SAMPLE_PROFILES = {
    "profiles": {
        "minimal": {"description": "x", "owner_team": "x", "skills": ["design-system"]},
        "forge-frontend": {
            "description": "x", "owner_team": "x",
            "skills": ["design-system"], "rules": ["no-console-log"],
        },
    }
}


class TestManifestTopLevel(unittest.TestCase):
    def test_valid(self) -> None:
        self.assertEqual(
            vm.validate_manifest_top_level({"schema_version": 1, "profile": "minimal"}),
            [],
        )

    def test_missing_schema_version(self) -> None:
        errs = vm.validate_manifest_top_level({"profile": "minimal"})
        self.assertTrue(any("schema_version" in e for e in errs))

    def test_unsupported_schema_version(self) -> None:
        errs = vm.validate_manifest_top_level({"schema_version": 2})
        self.assertTrue(any("unsupported" in e for e in errs))

    def test_not_a_mapping(self) -> None:
        errs = vm.validate_manifest_top_level("nope")
        self.assertEqual(len(errs), 1)


class TestManifestAgainstCatalog(unittest.TestCase):
    def test_profile_only_valid(self) -> None:
        manifest = {"schema_version": 1, "profile": "minimal"}
        errs = vm.validate_manifest_against_catalog(
            manifest, SAMPLE_PROFILES, SAMPLE_COMPONENTS_IDX
        )
        self.assertEqual(errs, [])

    def test_profile_inexistent(self) -> None:
        manifest = {"schema_version": 1, "profile": "no-such-profile"}
        errs = vm.validate_manifest_against_catalog(
            manifest, SAMPLE_PROFILES, SAMPLE_COMPONENTS_IDX
        )
        self.assertTrue(any("no-such-profile" in e for e in errs))
        # Available profiles listed for accionability
        self.assertTrue(any("available:" in e for e in errs))

    def test_profile_referenced_but_no_profiles_file(self) -> None:
        manifest = {"schema_version": 1, "profile": "minimal"}
        errs = vm.validate_manifest_against_catalog(
            manifest, None, SAMPLE_COMPONENTS_IDX
        )
        self.assertTrue(any("no profiles defined" in e for e in errs))

    def test_extends_add_valid(self) -> None:
        manifest = {
            "schema_version": 1,
            "profile": "minimal",
            "extends": {"add_skills": ["i18n-helper"]},
        }
        errs = vm.validate_manifest_against_catalog(
            manifest, SAMPLE_PROFILES, SAMPLE_COMPONENTS_IDX
        )
        self.assertEqual(errs, [])

    def test_extends_add_inexistent(self) -> None:
        manifest = {
            "schema_version": 1,
            "profile": "minimal",
            "extends": {"add_skills": ["does-not-exist"]},
        }
        errs = vm.validate_manifest_against_catalog(
            manifest, SAMPLE_PROFILES, SAMPLE_COMPONENTS_IDX
        )
        self.assertTrue(any("does-not-exist" in e for e in errs))

    def test_extends_remove_inexistent_is_permissive(self) -> None:
        """remove_* of an inexistent component is allowed (legacy cleanup)."""
        manifest = {
            "schema_version": 1,
            "profile": "minimal",
            "extends": {"remove_skills": ["legacy-skill"]},
        }
        errs = vm.validate_manifest_against_catalog(
            manifest, SAMPLE_PROFILES, SAMPLE_COMPONENTS_IDX
        )
        self.assertEqual(errs, [])

    def test_extends_kebab_case_violation(self) -> None:
        manifest = {
            "schema_version": 1,
            "profile": "minimal",
            "extends": {"add_rules": ["Not_Kebab"]},
        }
        errs = vm.validate_manifest_against_catalog(
            manifest, SAMPLE_PROFILES, SAMPLE_COMPONENTS_IDX
        )
        self.assertTrue(any("not kebab-case" in e for e in errs))

    def test_explicit_components_valid(self) -> None:
        manifest = {
            "schema_version": 1,
            "skills": ["design-system"],
            "rules": ["no-console-log"],
        }
        errs = vm.validate_manifest_against_catalog(
            manifest, SAMPLE_PROFILES, SAMPLE_COMPONENTS_IDX
        )
        self.assertEqual(errs, [])

    def test_explicit_components_inexistent(self) -> None:
        manifest = {
            "schema_version": 1,
            "rules": ["phantom-rule"],
        }
        errs = vm.validate_manifest_against_catalog(
            manifest, SAMPLE_PROFILES, SAMPLE_COMPONENTS_IDX
        )
        self.assertTrue(any("phantom-rule" in e for e in errs))

    def test_explicit_with_mapping_form(self) -> None:
        """Entries can be either bare strings or `{name: <s>}` mappings."""
        manifest = {
            "schema_version": 1,
            "skills": [{"name": "design-system"}],
        }
        errs = vm.validate_manifest_against_catalog(
            manifest, SAMPLE_PROFILES, SAMPLE_COMPONENTS_IDX
        )
        self.assertEqual(errs, [])

    def test_empty_manifest_must_declare_something(self) -> None:
        manifest = {"schema_version": 1}
        errs = vm.validate_manifest_against_catalog(
            manifest, SAMPLE_PROFILES, SAMPLE_COMPONENTS_IDX
        )
        self.assertTrue(any("must declare at least one" in e for e in errs))

    def test_extends_must_be_mapping(self) -> None:
        manifest = {
            "schema_version": 1,
            "profile": "minimal",
            "extends": "not-a-mapping",
        }
        errs = vm.validate_manifest_against_catalog(
            manifest, SAMPLE_PROFILES, SAMPLE_COMPONENTS_IDX
        )
        self.assertTrue(any("`extends` must be a mapping" in e for e in errs))

    def test_explicit_lists_must_be_lists(self) -> None:
        manifest = {
            "schema_version": 1,
            "skills": "not-a-list",
        }
        errs = vm.validate_manifest_against_catalog(
            manifest, SAMPLE_PROFILES, SAMPLE_COMPONENTS_IDX
        )
        self.assertTrue(any("must be a list" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
