#!/usr/bin/env python3
"""Migrate a v1 registry.yaml to v2 by adding `kind: skill` to every entry,
renaming the `skills:` list to `components:`, and bumping `schema_version`.

The migration is **idempotent**: running this script on a file that is already
v2 produces no changes and exits 0 with an informational message.

Usage:
    python tools/migrate-registry-v1-v2.py <input.yaml> [--in-place]
    python tools/migrate-registry-v1-v2.py <input.yaml> --output <output.yaml>

    Without --in-place or --output: writes to stdout.
    --in-place                    : modifies <input.yaml> directly.
    --output <path>               : writes to <path>, creating dirs as needed.

Exit codes:
    0  migrated successfully OR file was already v2 (no-op)
    1  file is a recognized but unsupported schema version (e.g. v3 from the future)
    2  usage error (file not found, YAML parse error, missing required fields)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print(
        "error: PyYAML is required (pip install pyyaml).",
        file=sys.stderr,
    )
    sys.exit(2)


SUPPORTED_INPUT_VERSIONS = {1, 2}
TARGET_VERSION = 2


def migrate(data: dict) -> tuple[dict, bool]:
    """Return (migrated_data, changed) tuple. Idempotent.

    Raises ValueError for unsupported versions or malformed structure.
    """
    if not isinstance(data, dict):
        raise ValueError("top-level must be a mapping")

    version = data.get("schema_version")
    if not isinstance(version, int):
        raise ValueError(
            f"schema_version must be int, got {type(version).__name__}"
        )
    if version not in SUPPORTED_INPUT_VERSIONS:
        raise ValueError(
            f"unsupported input schema_version: {version} "
            f"(this script supports {sorted(SUPPORTED_INPUT_VERSIONS)})"
        )

    if version == TARGET_VERSION:
        # Already v2; verify shape and exit no-op.
        if "components" not in data:
            raise ValueError(
                f"file claims schema_version: {TARGET_VERSION} but has no "
                f"`components:` list — file looks malformed, not migrating"
            )
        return data, False

    # version == 1: migrate.
    if "skills" not in data:
        raise ValueError("v1 file is missing required `skills:` list")
    if not isinstance(data["skills"], list):
        raise ValueError(
            f"v1 `skills:` must be a list, got {type(data['skills']).__name__}"
        )

    migrated: dict = {}
    # Preserve insertion order; keep schema_version + hub_version on top.
    migrated["schema_version"] = TARGET_VERSION
    if "hub_version" in data:
        migrated["hub_version"] = data["hub_version"]

    components: list = []
    for idx, entry in enumerate(data["skills"]):
        if not isinstance(entry, dict):
            raise ValueError(
                f"skills[{idx}] must be a mapping, got {type(entry).__name__}"
            )
        new_entry: dict = {}
        # name first, then kind (newly added), then everything else preserving order.
        if "name" in entry:
            new_entry["name"] = entry["name"]
        new_entry["kind"] = "skill"
        for key, value in entry.items():
            if key in ("name", "kind"):
                continue
            new_entry[key] = value
        components.append(new_entry)

    migrated["components"] = components

    # Preserve any other top-level fields the user might have added.
    for key, value in data.items():
        if key in ("schema_version", "hub_version", "skills"):
            continue
        migrated[key] = value

    return migrated, True


def dump_yaml(data: dict) -> str:
    """Dump with stable, readable formatting."""
    return yaml.safe_dump(
        data,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        indent=2,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Migrate registry.yaml v1 -> v2.")
    parser.add_argument("input", type=Path, help="Path to v1 (or v2) registry.yaml")
    target = parser.add_mutually_exclusive_group()
    target.add_argument(
        "--in-place",
        action="store_true",
        help="Modify input file in place.",
    )
    target.add_argument(
        "--output",
        type=Path,
        help="Write migrated content to this path.",
    )
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"error: input not found: {args.input}", file=sys.stderr)
        return 2

    try:
        data = yaml.safe_load(args.input.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        print(f"error: failed to parse {args.input}: {exc}", file=sys.stderr)
        return 2

    try:
        migrated, changed = migrate(data)
    except ValueError as exc:
        msg = str(exc)
        # Distinguish "unsupported version" (exit 1) from malformed input (exit 2).
        if "unsupported input schema_version" in msg:
            print(f"error: {msg}", file=sys.stderr)
            return 1
        print(f"error: {msg}", file=sys.stderr)
        return 2

    rendered = dump_yaml(migrated)

    if not changed:
        print(
            f"no-op: {args.input} is already schema_version {TARGET_VERSION}",
            file=sys.stderr,
        )
        # Still write if --output requested (useful for build pipelines).
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(f"wrote (idempotent): {args.output}", file=sys.stderr)
        return 0

    if args.in_place:
        args.input.write_text(rendered, encoding="utf-8")
        print(f"migrated in place: {args.input}", file=sys.stderr)
    elif args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"migrated: {args.input} -> {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(rendered)

    return 0


if __name__ == "__main__":
    sys.exit(main())
