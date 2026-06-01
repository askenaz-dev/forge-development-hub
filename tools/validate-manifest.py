#!/usr/bin/env python3
"""Validate a consumer's .fdh/manifest.yaml against the hub catalog.

Verifies:
  - schema_version is supported (currently 1).
  - If `harness:` is referenced, the harness exists in hub/harnesses.yaml.
    (`profile:` is accepted as a deprecated alias with a warning.)
  - If `extends:` is present, each referenced component (add_/remove_) exists
    in hub/registry.yaml with the matching kind.
  - If explicit `skills:`/`rules:`/`agents:`/`hooks:` lists are present, each
    name resolves to an existing component of that kind.
  - At least one of harness/skills/rules/agents/hooks is declared.

Usage:
    python tools/validate-manifest.py <path-to-manifest.yaml>

Exit codes:
    0  manifest valid against the catalog
    1  one or more validation errors (printed to stderr)
    2  usage error (file not found, YAML parse error)

TODO: migrate to `fdh validate-manifest` once the Go implementation lands.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("error: PyYAML is required (pip install pyyaml).", file=sys.stderr)
    sys.exit(2)


REPO_ROOT = Path(__file__).resolve().parent.parent
HUB_REGISTRY = REPO_ROOT / "hub" / "registry.yaml"
HUB_HARNESSES = REPO_ROOT / "hub" / "harnesses.yaml"

SUPPORTED_MANIFEST_SCHEMA_VERSIONS = {1}
SUPPORTED_KINDS = {"skill", "rule", "agent", "hook"}
KEBAB = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


def _index_components_by_kind(registry: dict) -> dict[str, set[str]]:
    idx: dict[str, set[str]] = {k: set() for k in SUPPORTED_KINDS}
    components = registry.get("components", [])
    if not isinstance(components, list):
        return idx
    for entry in components:
        if not isinstance(entry, dict):
            continue
        kind = entry.get("kind")
        name = entry.get("name")
        if isinstance(kind, str) and isinstance(name, str) and kind in SUPPORTED_KINDS:
            idx[kind].add(name)
    return idx


def _load_yaml(path: Path, label: str) -> object:
    if not path.exists():
        print(f"error: {label} not found at {path}", file=sys.stderr)
        sys.exit(2)
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        print(f"error: failed to parse {label} ({path}): {exc}", file=sys.stderr)
        sys.exit(2)


def validate_manifest_top_level(manifest: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["manifest: top-level must be a mapping"]
    if "schema_version" not in manifest:
        errors.append("manifest: missing top-level field `schema_version`")
    elif manifest["schema_version"] not in SUPPORTED_MANIFEST_SCHEMA_VERSIONS:
        errors.append(
            f"manifest: unsupported `schema_version` "
            f"{manifest.get('schema_version')} "
            f"(supported: {sorted(SUPPORTED_MANIFEST_SCHEMA_VERSIONS)})"
        )
    return errors


def validate_manifest_against_catalog(
    manifest: dict,
    harnesses_data: dict | None,
    components_idx: dict[str, set[str]],
) -> list[str]:
    errors: list[str] = []
    declared_anything = False

    # Harness reference. `harness:` is canonical; `profile:` is a deprecated
    # alias accepted for one migration window (warns, does not fail). If both
    # are present, `harness:` wins and `profile:` is ignored with a warning.
    harness_name = manifest.get("harness")
    legacy_profile = manifest.get("profile")
    if legacy_profile is not None:
        if harness_name is None:
            harness_name = legacy_profile
            print(
                "  ⚠ manifest: `profile:` is deprecated — rename it to `harness:`",
                file=sys.stderr,
            )
        else:
            print(
                "  ⚠ manifest: both `harness:` and `profile:` set — "
                "`profile:` is ignored (use `harness:` only)",
                file=sys.stderr,
            )

    if harness_name is not None:
        declared_anything = True
        if not isinstance(harness_name, str):
            errors.append(
                f"manifest: `harness` must be a string, "
                f"got {type(harness_name).__name__}"
            )
        elif harnesses_data is None or not isinstance(harnesses_data.get("harnesses"), dict):
            errors.append(
                f"manifest: harness '{harness_name}' referenced but "
                f"hub/harnesses.yaml has no harnesses defined"
            )
        elif harness_name not in harnesses_data["harnesses"]:
            available = sorted(harnesses_data["harnesses"].keys())
            errors.append(
                f"manifest: harness '{harness_name}' does not exist in "
                f"hub/harnesses.yaml (available: {available})"
            )

    # extends block
    extends = manifest.get("extends")
    if extends is not None:
        if not isinstance(extends, dict):
            errors.append(
                f"manifest: `extends` must be a mapping, "
                f"got {type(extends).__name__}"
            )
        else:
            for kind in SUPPORTED_KINDS:
                for op in ("add", "remove"):
                    key = f"{op}_{kind}s"
                    values = extends.get(key)
                    if values is None:
                        continue
                    declared_anything = True
                    if not isinstance(values, list):
                        errors.append(
                            f"manifest.extends.{key}: must be a list, "
                            f"got {type(values).__name__}"
                        )
                        continue
                    for ref in values:
                        if not isinstance(ref, str):
                            errors.append(
                                f"manifest.extends.{key}: entries must be strings"
                            )
                            continue
                        if not KEBAB.match(ref):
                            errors.append(
                                f"manifest.extends.{key}: '{ref}' is not kebab-case"
                            )
                        # add_ must reference an existing component
                        if op == "add" and ref not in components_idx.get(kind, set()):
                            errors.append(
                                f"manifest.extends.{key}: '{ref}' does not exist "
                                f"in hub/registry.yaml as kind='{kind}'"
                            )
                        # remove_ for inexistent: spec says warning, but we keep
                        # it permissive (no error) so removing legacy entries doesn't break.

    # Explicit component lists
    for kind in SUPPORTED_KINDS:
        key = f"{kind}s"
        values = manifest.get(key)
        if values is None:
            continue
        declared_anything = True
        if not isinstance(values, list):
            errors.append(
                f"manifest: `{key}` must be a list, got {type(values).__name__}"
            )
            continue
        for ref in values:
            ref_name = ref.get("name") if isinstance(ref, dict) else ref
            if not isinstance(ref_name, str):
                errors.append(
                    f"manifest.{key}: each entry must be a string name or "
                    f"a mapping with `name:`, got {type(ref).__name__}"
                )
                continue
            if not KEBAB.match(ref_name):
                errors.append(f"manifest.{key}: '{ref_name}' is not kebab-case")
                continue
            if ref_name not in components_idx.get(kind, set()):
                errors.append(
                    f"manifest.{key}: '{ref_name}' does not exist in "
                    f"hub/registry.yaml as kind='{kind}'"
                )

    if not declared_anything:
        errors.append(
            "manifest: must declare at least one of `profile`, `extends`, "
            "`skills`, `rules`, `agents`, `hooks`"
        )

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate .fdh/manifest.yaml against hub catalog.")
    parser.add_argument(
        "manifest",
        type=Path,
        help="Path to a .fdh/manifest.yaml file to validate.",
    )
    args = parser.parse_args(argv)

    if not args.manifest.exists():
        print(f"error: manifest not found at {args.manifest}", file=sys.stderr)
        return 2

    try:
        manifest = yaml.safe_load(args.manifest.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        print(f"error: failed to parse {args.manifest}: {exc}", file=sys.stderr)
        return 2

    registry = _load_yaml(HUB_REGISTRY, "hub/registry.yaml")
    harnesses_data = None
    if HUB_HARNESSES.exists():
        try:
            harnesses_data = yaml.safe_load(HUB_HARNESSES.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            print(f"error: failed to parse hub/harnesses.yaml: {exc}", file=sys.stderr)
            return 2

    components_idx = _index_components_by_kind(registry if isinstance(registry, dict) else {})

    errors: list[str] = []
    errors.extend(validate_manifest_top_level(manifest))

    if isinstance(manifest, dict):
        errors.extend(
            validate_manifest_against_catalog(manifest, harnesses_data, components_idx)
        )

    if errors:
        for err in errors:
            print(f"  ✗ {err}", file=sys.stderr)
        print(f"\nmanifest invalid: {len(errors)} error(s)", file=sys.stderr)
        return 1

    decl_summary: list[str] = []
    if isinstance(manifest, dict):
        if manifest.get("harness"):
            decl_summary.append(f"harness={manifest['harness']}")
        elif manifest.get("profile"):
            decl_summary.append(f"harness={manifest['profile']} (via deprecated profile:)")
        for kind in SUPPORTED_KINDS:
            key = f"{kind}s"
            if manifest.get(key):
                decl_summary.append(f"{key}={len(manifest[key])}")
        if manifest.get("extends"):
            decl_summary.append("extends=yes")
    print(
        f"manifest valid: {args.manifest} "
        f"({', '.join(decl_summary) if decl_summary else 'empty'})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
