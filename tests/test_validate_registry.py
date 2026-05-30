"""Tests for tools/validate-registry.py (schema v2 + profiles).

Run with stdlib unittest:
    python -m unittest tests.test_validate_registry
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "tools" / "validate-registry.py"

spec = importlib.util.spec_from_file_location("validate_registry", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
vr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vr)


class TestRegistryTopLevel(unittest.TestCase):
    def test_valid_v2(self) -> None:
        data = {"schema_version": 2, "hub_version": "x", "components": []}
        self.assertEqual(vr.validate_registry_top_level(data), [])

    def test_missing_schema_version(self) -> None:
        errs = vr.validate_registry_top_level({"hub_version": "x", "components": []})
        self.assertTrue(any("schema_version" in e for e in errs))

    def test_wrong_schema_version_v1(self) -> None:
        errs = vr.validate_registry_top_level(
            {"schema_version": 1, "hub_version": "x", "components": []}
        )
        self.assertTrue(any("unsupported `schema_version`" in e for e in errs))
        # Should also suggest the migration script
        self.assertTrue(any("migrate-registry-v1-v2.py" in e for e in errs))

    def test_v1_style_skills_key_flagged(self) -> None:
        errs = vr.validate_registry_top_level(
            {"schema_version": 2, "hub_version": "x", "skills": []}
        )
        self.assertTrue(any("v1 schema" in e for e in errs))

    def test_missing_hub_version(self) -> None:
        errs = vr.validate_registry_top_level({"schema_version": 2, "components": []})
        self.assertTrue(any("hub_version" in e for e in errs))

    def test_missing_components(self) -> None:
        errs = vr.validate_registry_top_level({"schema_version": 2, "hub_version": "x"})
        self.assertTrue(any("components" in e for e in errs))

    def test_non_mapping(self) -> None:
        errs = vr.validate_registry_top_level("not a mapping")
        self.assertEqual(len(errs), 1)
        self.assertIn("must be a mapping", errs[0])


def _valid_entry(kind: str = "skill", name: str = "design-system") -> dict:
    return {
        "name": name,
        "kind": kind,
        "description": "Test component.",
        "owner_team": "x",
        "tags": ["a"],
        "default": True,
        "min_fdh_version": "0.4.0",
        "agents_supported": ["claude-code"],
        "path": f"{kind}s/{name}",
    }


class TestComponentEntry(unittest.TestCase):
    def test_valid_skill_entry(self) -> None:
        self.assertEqual(vr.validate_component_entry(0, _valid_entry()), [])

    def test_valid_rule_entry(self) -> None:
        self.assertEqual(
            vr.validate_component_entry(0, _valid_entry(kind="rule", name="no-console-log")),
            [],
        )

    def test_missing_kind(self) -> None:
        entry = _valid_entry()
        del entry["kind"]
        errs = vr.validate_component_entry(0, entry)
        self.assertTrue(any("missing field `kind`" in e for e in errs))

    def test_unknown_kind(self) -> None:
        entry = _valid_entry()
        entry["kind"] = "weirdo"
        errs = vr.validate_component_entry(0, entry)
        self.assertTrue(any("unknown `kind` 'weirdo'" in e for e in errs))

    def test_name_not_kebab(self) -> None:
        entry = _valid_entry()
        entry["name"] = "Not_Kebab"
        errs = vr.validate_component_entry(0, entry)
        self.assertTrue(any("kebab-case" in e for e in errs))

    def test_min_fdh_version_invalid_semver(self) -> None:
        entry = _valid_entry()
        entry["min_fdh_version"] = "0.4"
        errs = vr.validate_component_entry(0, entry)
        self.assertTrue(any("semver" in e for e in errs))

    def test_agents_supported_empty(self) -> None:
        entry = _valid_entry()
        entry["agents_supported"] = []
        errs = vr.validate_component_entry(0, entry)
        self.assertTrue(any("must be non-empty" in e for e in errs))

    def test_agents_supported_unknown_value(self) -> None:
        entry = _valid_entry()
        entry["agents_supported"] = ["claude-code", "cursor"]
        errs = vr.validate_component_entry(0, entry)
        self.assertTrue(any("unknown values" in e for e in errs))

    def test_path_inconsistent_with_kind(self) -> None:
        entry = _valid_entry(kind="rule", name="foo")
        entry["path"] = "skills/foo"  # inconsistent: kind=rule should live in rules/
        errs = vr.validate_component_entry(0, entry)
        self.assertTrue(any("inconsistent with kind" in e for e in errs))

    def test_non_dict_entry(self) -> None:
        errs = vr.validate_component_entry(0, "not-a-dict")
        self.assertEqual(len(errs), 1)
        self.assertIn("must be a mapping", errs[0])


class TestUniqueness(unittest.TestCase):
    def test_duplicates_within_kind(self) -> None:
        a = _valid_entry(kind="skill", name="design-system")
        b = _valid_entry(kind="skill", name="design-system")
        errs = vr.validate_uniqueness_per_kind([a, b])
        self.assertTrue(any("duplicate component skill:design-system" in e for e in errs))

    def test_same_name_different_kinds_allowed(self) -> None:
        a = _valid_entry(kind="skill", name="overlap")
        b = _valid_entry(kind="rule", name="overlap")
        # path coherence test handled elsewhere; uniqueness allows same name in different kinds
        errs = vr.validate_uniqueness_per_kind([a, b])
        self.assertEqual(errs, [])


class TestProfileEntry(unittest.TestCase):
    def setUp(self) -> None:
        self.components_idx = {
            "skill": {"design-system", "code-review"},
            "rule": {"no-console-log"},
            "agent": {"forge-pr-writer"},
            "hook": {"doctor-on-session-start"},
        }

    def test_valid_minimal_profile(self) -> None:
        profile = {
            "description": "Starter pack.",
            "owner_team": "dx-platform",
            "skills": ["design-system"],
            "rules": ["no-console-log"],
        }
        errs = vr.validate_profile_entry("minimal", profile, self.components_idx)
        self.assertEqual(errs, [])

    def test_profile_missing_description(self) -> None:
        profile = {"owner_team": "x", "skills": ["design-system"]}
        errs = vr.validate_profile_entry("p", profile, self.components_idx)
        self.assertTrue(any("description" in e for e in errs))

    def test_profile_references_unknown_component(self) -> None:
        profile = {
            "description": "x",
            "owner_team": "x",
            "rules": ["does-not-exist"],
        }
        errs = vr.validate_profile_entry("p", profile, self.components_idx)
        self.assertTrue(any("unknown rule 'does-not-exist'" in e for e in errs))

    def test_profile_references_component_with_wrong_kind(self) -> None:
        profile = {
            "description": "x",
            "owner_team": "x",
            # design-system is a skill, not a rule
            "rules": ["design-system"],
        }
        errs = vr.validate_profile_entry("p", profile, self.components_idx)
        self.assertTrue(any("unknown rule 'design-system'" in e for e in errs))

    def test_profile_empty_must_reference_at_least_one(self) -> None:
        profile = {"description": "x", "owner_team": "x"}
        errs = vr.validate_profile_entry("p", profile, self.components_idx)
        self.assertTrue(any("at least one component" in e for e in errs))

    def test_profile_lists_must_be_lists(self) -> None:
        profile = {
            "description": "x",
            "owner_team": "x",
            "skills": "not-a-list",
        }
        errs = vr.validate_profile_entry("p", profile, self.components_idx)
        self.assertTrue(any("must be a list" in e for e in errs))


class TestProfilesTopLevel(unittest.TestCase):
    def test_valid(self) -> None:
        self.assertEqual(
            vr.validate_profiles_top_level({"schema_version": 1, "profiles": {}}),
            [],
        )

    def test_missing_schema_version(self) -> None:
        errs = vr.validate_profiles_top_level({"profiles": {}})
        self.assertTrue(any("schema_version" in e for e in errs))

    def test_unsupported_version(self) -> None:
        errs = vr.validate_profiles_top_level({"schema_version": 2, "profiles": {}})
        self.assertTrue(any("unsupported" in e for e in errs))

    def test_profiles_must_be_mapping(self) -> None:
        errs = vr.validate_profiles_top_level({"schema_version": 1, "profiles": []})
        self.assertTrue(any("must be a mapping" in e for e in errs))


class TestIndexHelper(unittest.TestCase):
    def test_indexes_by_kind(self) -> None:
        entries = [
            _valid_entry(kind="skill", name="a"),
            _valid_entry(kind="rule", name="b"),
            _valid_entry(kind="rule", name="c"),
        ]
        idx = vr._index_components_by_kind(entries)
        self.assertEqual(idx["skill"], {"a"})
        self.assertEqual(idx["rule"], {"b", "c"})
        self.assertEqual(idx["agent"], set())
        self.assertEqual(idx["hook"], set())


if __name__ == "__main__":
    unittest.main()
