"""Tests for tools/migrate-registry-v1-v2.py.

Run with stdlib unittest (no pytest dependency):
    python -m unittest tests.test_migrate_registry
or:
    python tests/test_migrate_registry.py
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "tools" / "migrate-registry-v1-v2.py"

# Import the script as a module (it has a hyphen in the filename).
spec = importlib.util.spec_from_file_location("migrate_registry", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
migrate_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migrate_mod)

import yaml  # noqa: E402  (after sys.path manipulation above)


V1_SAMPLE = {
    "schema_version": 1,
    "hub_version": "2026.05",
    "skills": [
        {
            "name": "design-system",
            "description": "Forge design system.",
            "owner_team": "design-platform",
            "tags": ["ui", "react"],
            "default": True,
            "min_fdh_version": "0.4.0",
            "agents_supported": ["claude-code", "codex"],
            "path": "skills/design-system",
        },
        {
            "name": "code-review",
            "description": "Standard checklist.",
            "owner_team": "dx-platform",
            "tags": ["review"],
            "default": True,
            "min_fdh_version": "0.4.0",
            "agents_supported": ["claude-code"],
            "path": "skills/code-review",
        },
    ],
}


V2_SAMPLE = {
    "schema_version": 2,
    "hub_version": "2026.05",
    "components": [
        {
            "name": "design-system",
            "kind": "skill",
            "description": "Forge design system.",
            "owner_team": "design-platform",
            "tags": ["ui", "react"],
            "default": True,
            "min_fdh_version": "0.4.0",
            "agents_supported": ["claude-code", "codex"],
            "path": "skills/design-system",
        },
    ],
}


class TestMigrate(unittest.TestCase):
    """Pure function-level tests against migrate_mod.migrate()."""

    def test_v1_to_v2_basic(self) -> None:
        migrated, changed = migrate_mod.migrate(V1_SAMPLE)
        self.assertTrue(changed)
        self.assertEqual(migrated["schema_version"], 2)
        self.assertEqual(migrated["hub_version"], "2026.05")
        self.assertNotIn("skills", migrated)
        self.assertIn("components", migrated)
        self.assertEqual(len(migrated["components"]), 2)
        for entry in migrated["components"]:
            self.assertEqual(entry["kind"], "skill")

    def test_v1_to_v2_preserves_entry_field_order_with_kind_after_name(self) -> None:
        migrated, _ = migrate_mod.migrate(V1_SAMPLE)
        first = migrated["components"][0]
        keys = list(first.keys())
        self.assertEqual(keys[0], "name")
        self.assertEqual(keys[1], "kind")

    def test_v1_to_v2_preserves_unknown_top_level_fields(self) -> None:
        v1_with_extra = dict(V1_SAMPLE)
        v1_with_extra["custom_field"] = "preserved"
        migrated, _ = migrate_mod.migrate(v1_with_extra)
        self.assertEqual(migrated.get("custom_field"), "preserved")

    def test_v2_is_idempotent_noop(self) -> None:
        migrated, changed = migrate_mod.migrate(V2_SAMPLE)
        self.assertFalse(changed)
        self.assertEqual(migrated, V2_SAMPLE)

    def test_v1_missing_skills_list_raises(self) -> None:
        bad = {"schema_version": 1, "hub_version": "x"}
        with self.assertRaises(ValueError) as ctx:
            migrate_mod.migrate(bad)
        self.assertIn("skills", str(ctx.exception))

    def test_v1_skills_not_list_raises(self) -> None:
        bad = {"schema_version": 1, "hub_version": "x", "skills": "not-a-list"}
        with self.assertRaises(ValueError):
            migrate_mod.migrate(bad)

    def test_v2_missing_components_raises(self) -> None:
        bad = {"schema_version": 2, "hub_version": "x"}
        with self.assertRaises(ValueError) as ctx:
            migrate_mod.migrate(bad)
        self.assertIn("components", str(ctx.exception))

    def test_unsupported_future_version_raises(self) -> None:
        bad = {"schema_version": 3}
        with self.assertRaises(ValueError) as ctx:
            migrate_mod.migrate(bad)
        self.assertIn("unsupported", str(ctx.exception).lower())

    def test_unsupported_zero_version_raises(self) -> None:
        bad = {"schema_version": 0}
        with self.assertRaises(ValueError):
            migrate_mod.migrate(bad)

    def test_top_level_not_mapping_raises(self) -> None:
        with self.assertRaises(ValueError):
            migrate_mod.migrate(["not", "a", "mapping"])

    def test_entry_not_mapping_raises(self) -> None:
        bad = {
            "schema_version": 1,
            "hub_version": "x",
            "skills": ["this-is-not-a-mapping"],
        }
        with self.assertRaises(ValueError) as ctx:
            migrate_mod.migrate(bad)
        self.assertIn("must be a mapping", str(ctx.exception))


class TestCLI(unittest.TestCase):
    """End-to-end tests via the script's main() entrypoint."""

    def _write_yaml(self, tmpdir: Path, name: str, data: dict) -> Path:
        path = tmpdir / name
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        return path

    def test_cli_v1_to_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)
            in_path = self._write_yaml(tmpdir, "in.yaml", V1_SAMPLE)
            # Run main directly; capture stdout.
            from io import StringIO
            captured = StringIO()
            real_stdout = sys.stdout
            sys.stdout = captured
            try:
                rc = migrate_mod.main([str(in_path)])
            finally:
                sys.stdout = real_stdout
            self.assertEqual(rc, 0)
            output_data = yaml.safe_load(captured.getvalue())
            self.assertEqual(output_data["schema_version"], 2)
            self.assertIn("components", output_data)

    def test_cli_v1_in_place(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)
            in_path = self._write_yaml(tmpdir, "in.yaml", V1_SAMPLE)
            rc = migrate_mod.main([str(in_path), "--in-place"])
            self.assertEqual(rc, 0)
            after = yaml.safe_load(in_path.read_text(encoding="utf-8"))
            self.assertEqual(after["schema_version"], 2)
            self.assertIn("components", after)

    def test_cli_v1_to_output(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)
            in_path = self._write_yaml(tmpdir, "in.yaml", V1_SAMPLE)
            out_path = tmpdir / "subdir" / "out.yaml"
            rc = migrate_mod.main([str(in_path), "--output", str(out_path)])
            self.assertEqual(rc, 0)
            self.assertTrue(out_path.exists())
            after = yaml.safe_load(out_path.read_text(encoding="utf-8"))
            self.assertEqual(after["schema_version"], 2)

    def test_cli_v2_is_noop_exit_zero(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)
            in_path = self._write_yaml(tmpdir, "in.yaml", V2_SAMPLE)
            before_text = in_path.read_text(encoding="utf-8")
            rc = migrate_mod.main([str(in_path), "--in-place"])
            self.assertEqual(rc, 0)
            # In-place on already-v2 should not modify (no-op branch returns
            # before writing in --in-place mode).
            after_text = in_path.read_text(encoding="utf-8")
            self.assertEqual(before_text, after_text)

    def test_cli_unsupported_version_exit_one(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)
            in_path = self._write_yaml(tmpdir, "in.yaml", {"schema_version": 3})
            rc = migrate_mod.main([str(in_path)])
            self.assertEqual(rc, 1)

    def test_cli_missing_input_exit_two(self) -> None:
        rc = migrate_mod.main([str(Path("/nonexistent/path/file.yaml"))])
        self.assertEqual(rc, 2)

    def test_cli_malformed_input_exit_two(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)
            in_path = tmpdir / "in.yaml"
            in_path.write_text("not: valid: yaml: :\n", encoding="utf-8")
            rc = migrate_mod.main([str(in_path)])
            self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
