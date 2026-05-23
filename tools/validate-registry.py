#!/usr/bin/env python3
"""Validate skills/registry.yaml against the rules in the hub-skills-registry spec.

Exit codes:
    0  registry valid
    1  registry has one or more errors (printed to stderr)
    2  usage error (file not found, YAML parse error)

Run from the hub root:
    python tools/validate-registry.py

TODO: migrate to `fdh validate-registry` once the Go implementation lands.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print(
        "error: PyYAML is required (pip install pyyaml). "
        "In CI: actions/setup-python + 'pip install pyyaml'.",
        file=sys.stderr,
    )
    sys.exit(2)

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "skills" / "registry.yaml"
SKILLS_DIR = REPO_ROOT / "skills"

SUPPORTED_AGENTS = {"claude-code", "codex", "copilot", "opencode"}
SUPPORTED_SCHEMA_VERSIONS = {1}
KEBAB = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[\w.]+)?$")

REQUIRED_SKILL_FIELDS = {
    "name": str,
    "description": str,
    "owner_team": str,
    "tags": list,
    "default": bool,
    "min_fdh_version": str,
    "agents_supported": list,
    "path": str,
}


def fail(errors: list[str]) -> None:
    for err in errors:
        print(f"  ✗ {err}", file=sys.stderr)
    print(f"\nregistry invalid: {len(errors)} error(s)", file=sys.stderr)
    sys.exit(1)


def validate_top_level(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["top-level must be a mapping"]
    if "schema_version" not in data:
        errors.append("missing top-level field: schema_version")
    elif not isinstance(data["schema_version"], int):
        errors.append(f"schema_version must be int, got {type(data['schema_version']).__name__}")
    elif data["schema_version"] not in SUPPORTED_SCHEMA_VERSIONS:
        errors.append(
            f"unsupported schema_version: {data['schema_version']} "
            f"(supported: {sorted(SUPPORTED_SCHEMA_VERSIONS)})"
        )
    if "hub_version" not in data:
        errors.append("missing top-level field: hub_version")
    elif not isinstance(data["hub_version"], str) or not data["hub_version"].strip():
        errors.append("hub_version must be a non-empty string")
    if "skills" not in data:
        errors.append("missing top-level field: skills")
    elif not isinstance(data["skills"], list):
        errors.append("skills must be a list")
    return errors


def validate_skill_entry(idx: int, entry: object) -> list[str]:
    if not isinstance(entry, dict):
        return [f"skills[{idx}]: must be a mapping, got {type(entry).__name__}"]
    errors: list[str] = []
    ident = entry.get("name", f"<index {idx}>")
    for field, expected_type in REQUIRED_SKILL_FIELDS.items():
        if field not in entry:
            errors.append(f"skills[{ident}]: missing field '{field}'")
            continue
        value = entry[field]
        if not isinstance(value, expected_type):
            errors.append(
                f"skills[{ident}]: field '{field}' must be {expected_type.__name__}, "
                f"got {type(value).__name__}"
            )

    if isinstance(entry.get("name"), str) and not KEBAB.match(entry["name"]):
        errors.append(f"skills[{ident}]: 'name' must be kebab-case (e.g. design-system)")
    if isinstance(entry.get("description"), str) and not entry["description"].strip():
        errors.append(f"skills[{ident}]: 'description' must be non-empty")
    if isinstance(entry.get("owner_team"), str) and not entry["owner_team"].strip():
        errors.append(f"skills[{ident}]: 'owner_team' must be non-empty")
    if isinstance(entry.get("min_fdh_version"), str) and not SEMVER.match(entry["min_fdh_version"]):
        errors.append(
            f"skills[{ident}]: 'min_fdh_version' must be semver "
            f"(got '{entry['min_fdh_version']}')"
        )

    agents = entry.get("agents_supported")
    if isinstance(agents, list):
        if len(agents) == 0:
            errors.append(f"skills[{ident}]: 'agents_supported' must be non-empty")
        unknown = [a for a in agents if a not in SUPPORTED_AGENTS]
        if unknown:
            errors.append(
                f"skills[{ident}]: 'agents_supported' has unknown values {unknown} "
                f"(allowed: {sorted(SUPPORTED_AGENTS)})"
            )

    return errors


def validate_paths_and_orphans(entries: list[dict]) -> list[str]:
    errors: list[str] = []
    declared_paths: dict[str, str] = {}
    declared_dirs: set[Path] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name", "<unnamed>")
        path = entry.get("path")
        if not isinstance(path, str):
            continue
        abs_path = (REPO_ROOT / path).resolve()
        if not abs_path.exists():
            errors.append(f"skills[{name}]: declared path '{path}' does not exist")
            continue
        if not abs_path.is_dir():
            errors.append(f"skills[{name}]: declared path '{path}' is not a directory")
            continue
        try:
            abs_path.relative_to(SKILLS_DIR.resolve())
        except ValueError:
            errors.append(
                f"skills[{name}]: declared path '{path}' must be under skills/"
            )
            continue
        if path in declared_paths:
            errors.append(
                f"skills[{name}]: path '{path}' already declared by "
                f"skills[{declared_paths[path]}]"
            )
        declared_paths[path] = name
        declared_dirs.add(abs_path)

    if SKILLS_DIR.exists():
        for child in SKILLS_DIR.iterdir():
            if not child.is_dir():
                continue
            if child.resolve() not in declared_dirs:
                rel = child.relative_to(REPO_ROOT)
                errors.append(
                    f"orphan: directory '{rel}' has no entry in registry.yaml "
                    f"(add an entry or remove the directory)"
                )

    return errors


def validate_unique_names(entries: list[dict]) -> list[str]:
    errors: list[str] = []
    seen: dict[str, int] = {}
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if not isinstance(name, str):
            continue
        if name in seen:
            errors.append(
                f"duplicate skill name '{name}' at indices {seen[name]} and {idx}"
            )
        else:
            seen[name] = idx
    return errors


def main() -> int:
    if not REGISTRY_PATH.exists():
        print(f"error: {REGISTRY_PATH} does not exist", file=sys.stderr)
        return 2
    try:
        data = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        print(f"error: failed to parse {REGISTRY_PATH}: {exc}", file=sys.stderr)
        return 2

    errors: list[str] = []
    errors.extend(validate_top_level(data))

    if isinstance(data, dict) and isinstance(data.get("skills"), list):
        entries = data["skills"]
        for idx, entry in enumerate(entries):
            errors.extend(validate_skill_entry(idx, entry))
        errors.extend(validate_unique_names(entries))
        errors.extend(validate_paths_and_orphans(entries))

    if errors:
        fail(errors)

    skill_count = len(data.get("skills", [])) if isinstance(data, dict) else 0
    print(f"registry valid: schema_version={data.get('schema_version')}, "
          f"hub_version={data.get('hub_version')}, skills={skill_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
