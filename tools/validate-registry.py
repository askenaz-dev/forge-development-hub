#!/usr/bin/env python3
"""Validate the hub catalog (hub/registry.yaml) and curated profiles
(hub/profiles.yaml) against the schemas in the hub-registry-v2 +
hub-profiles + hub-skills-registry specs.

Exit codes:
    0  registry + profiles valid
    1  one or more validation errors (printed to stderr)
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
HUB_REGISTRY = REPO_ROOT / "hub" / "registry.yaml"
HUB_PROFILES = REPO_ROOT / "hub" / "profiles.yaml"

# kind -> directory under repo root that hosts that kind's components
KIND_DIRS: dict[str, Path] = {
    "skill": REPO_ROOT / "skills",
    "rule": REPO_ROOT / "rules",
    "agent": REPO_ROOT / "agents",
    "hook": REPO_ROOT / "hooks",
}
SUPPORTED_KINDS = set(KIND_DIRS.keys())
SUPPORTED_AGENTS = {"claude-code", "codex", "copilot", "opencode"}
SUPPORTED_REGISTRY_SCHEMA_VERSIONS = {2}
SUPPORTED_PROFILES_SCHEMA_VERSIONS = {1}
KEBAB = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[\w.]+)?$")

# Banner prefix emitted by `fdh evolve` for uncurated drafts. Hub PRs that
# try to merge a SKILL.md still containing this banner are blocked here so
# admins finish curation before publishing. Source of the constant: Go
# package github.com/forge/fdh/pkg/instincts (DraftBannerPrefix).
EVOLVE_DRAFT_BANNER = "> ⚠️ DRAFT"

REQUIRED_COMPONENT_FIELDS = {
    "name": str,
    "kind": str,
    "description": str,
    "owner_team": str,
    "tags": list,
    "default": bool,
    "min_fdh_version": str,
    "agents_supported": list,
    "path": str,
}


# ---------------------------------------------------------------------------
# Registry validation
# ---------------------------------------------------------------------------


def validate_registry_top_level(data: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["hub/registry.yaml: top-level must be a mapping"]
    if "schema_version" not in data:
        errors.append("hub/registry.yaml: missing top-level field `schema_version`")
    elif not isinstance(data["schema_version"], int):
        errors.append(
            f"hub/registry.yaml: `schema_version` must be int, "
            f"got {type(data['schema_version']).__name__}"
        )
    elif data["schema_version"] not in SUPPORTED_REGISTRY_SCHEMA_VERSIONS:
        errors.append(
            f"hub/registry.yaml: unsupported `schema_version` "
            f"{data['schema_version']} (supported: "
            f"{sorted(SUPPORTED_REGISTRY_SCHEMA_VERSIONS)}). "
            f"Run: python tools/migrate-registry-v1-v2.py"
        )
    if "hub_version" not in data:
        errors.append("hub/registry.yaml: missing top-level field `hub_version`")
    elif not isinstance(data["hub_version"], str) or not data["hub_version"].strip():
        errors.append("hub/registry.yaml: `hub_version` must be a non-empty string")
    if "components" not in data:
        errors.append("hub/registry.yaml: missing top-level field `components` (a list)")
    elif not isinstance(data["components"], list):
        errors.append("hub/registry.yaml: `components` must be a list")
    if "skills" in data and isinstance(data.get("skills"), list):
        errors.append(
            "hub/registry.yaml: top-level `skills:` is the v1 schema. v2 uses "
            "`components:` (with `kind:` per entry). "
            "Run: python tools/migrate-registry-v1-v2.py"
        )
    return errors


def validate_component_entry(idx: int, entry: object) -> list[str]:
    if not isinstance(entry, dict):
        return [f"components[{idx}]: must be a mapping, got {type(entry).__name__}"]
    errors: list[str] = []
    ident_name = entry.get("name", f"<index {idx}>")
    ident_kind = entry.get("kind", "<no-kind>")
    ident = f"{ident_kind}:{ident_name}"

    for field, expected_type in REQUIRED_COMPONENT_FIELDS.items():
        if field not in entry:
            errors.append(f"components[{ident}]: missing field `{field}`")
            continue
        value = entry[field]
        if not isinstance(value, expected_type):
            errors.append(
                f"components[{ident}]: field `{field}` must be "
                f"{expected_type.__name__}, got {type(value).__name__}"
            )

    name = entry.get("name")
    if isinstance(name, str) and not KEBAB.match(name):
        errors.append(f"components[{ident}]: `name` must be kebab-case (e.g. design-system)")

    kind = entry.get("kind")
    if isinstance(kind, str) and kind not in SUPPORTED_KINDS:
        errors.append(
            f"components[{ident}]: unknown `kind` '{kind}' "
            f"(supported: {sorted(SUPPORTED_KINDS)})"
        )

    desc = entry.get("description")
    if isinstance(desc, str) and not desc.strip():
        errors.append(f"components[{ident}]: `description` must be non-empty")
    owner = entry.get("owner_team")
    if isinstance(owner, str) and not owner.strip():
        errors.append(f"components[{ident}]: `owner_team` must be non-empty")
    min_ver = entry.get("min_fdh_version")
    if isinstance(min_ver, str) and not SEMVER.match(min_ver):
        errors.append(
            f"components[{ident}]: `min_fdh_version` must be semver "
            f"(got '{min_ver}')"
        )

    agents = entry.get("agents_supported")
    if isinstance(agents, list):
        if len(agents) == 0:
            errors.append(f"components[{ident}]: `agents_supported` must be non-empty")
        unknown = [a for a in agents if a not in SUPPORTED_AGENTS]
        if unknown:
            errors.append(
                f"components[{ident}]: `agents_supported` has unknown values "
                f"{unknown} (allowed: {sorted(SUPPORTED_AGENTS)})"
            )

    # path ↔ kind coherence
    path_str = entry.get("path")
    if isinstance(path_str, str) and isinstance(kind, str) and kind in SUPPORTED_KINDS:
        expected_prefix = KIND_DIRS[kind].name + "/"  # e.g. "rules/"
        if not path_str.startswith(expected_prefix):
            errors.append(
                f"components[{ident}]: path '{path_str}' inconsistent with "
                f"kind '{kind}' (expected prefix '{expected_prefix}')"
            )

    return errors


def validate_uniqueness_per_kind(entries: list) -> list[str]:
    """Enforce (kind, name) uniqueness. Same name in different kinds is allowed
    by spec but flagged here as a separate duplicate-by-kind check."""
    errors: list[str] = []
    seen: dict[tuple, int] = {}
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        kind = entry.get("kind")
        if not (isinstance(name, str) and isinstance(kind, str)):
            continue
        key = (kind, name)
        if key in seen:
            errors.append(
                f"duplicate component {kind}:{name} at indices "
                f"{seen[key]} and {idx}"
            )
        else:
            seen[key] = idx
    return errors


def validate_no_evolve_drafts(entries: list) -> list[str]:
    """Scan every component's entrypoint file for the `fdh evolve` draft banner.
    Drafts must be curated (banner removed) before they are merged into the hub.
    Blocks accidental publication of un-reviewed skill drafts."""
    errors: list[str] = []
    entrypoint_by_kind = {
        "skill": "SKILL.md",
        "rule": "RULE.md",
        "agent": "AGENT.md",
        "hook": "HOOK.md",
    }
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name", "<unnamed>")
        kind = entry.get("kind")
        path_str = entry.get("path")
        if not (isinstance(name, str) and isinstance(kind, str) and isinstance(path_str, str)):
            continue
        if kind not in entrypoint_by_kind:
            continue
        entrypoint = REPO_ROOT / path_str / entrypoint_by_kind[kind]
        if not entrypoint.exists():
            continue
        try:
            text = entrypoint.read_text(encoding="utf-8")
        except OSError:
            continue
        if EVOLVE_DRAFT_BANNER in text:
            errors.append(
                f"components[{kind}:{name}]: {entrypoint.relative_to(REPO_ROOT)} still contains "
                f"the `fdh evolve` draft banner ({EVOLVE_DRAFT_BANNER!r}). "
                f"Review TODOs and remove the banner before merging."
            )
    return errors


ENTRYPOINT_BY_KIND = {
    "skill": "SKILL.md",
    "rule": "RULE.md",
    "agent": "AGENT.md",
    "hook": "HOOK.md",
}


def _extract_frontmatter(text: str) -> dict | None:
    """Parse the leading YAML frontmatter block delimited by `---` lines.
    Returns the parsed mapping, or None if absent / no closing delimiter /
    unparseable."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    fm_lines: list[str] = []
    closed = False
    for line in lines[1:]:
        if line.strip() == "---":
            closed = True
            break
        fm_lines.append(line)
    if not closed:
        return None
    try:
        data = yaml.safe_load("\n".join(fm_lines))
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def validate_component_versions(entries: list) -> list[str]:
    """Every component's entrypoint frontmatter MUST declare a SemVer `version`.
    New components start at 0.1.0 (capability component-versioning-and-release).
    The frontmatter `version` is the source of truth for the component's
    published version; the release pipeline writes bumps back into it."""
    errors: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name", "<unnamed>")
        kind = entry.get("kind")
        path_str = entry.get("path")
        if not (
            isinstance(name, str)
            and isinstance(kind, str)
            and isinstance(path_str, str)
        ):
            continue
        if kind not in ENTRYPOINT_BY_KIND:
            continue
        entrypoint = REPO_ROOT / path_str / ENTRYPOINT_BY_KIND[kind]
        if not entrypoint.exists():
            continue  # missing-file is reported by the path/orphan checks
        ident = f"{kind}:{name}"
        try:
            text = entrypoint.read_text(encoding="utf-8")
        except OSError:
            continue
        fm = _extract_frontmatter(text)
        if fm is None:
            errors.append(
                f"components[{ident}]: {entrypoint.relative_to(REPO_ROOT)} is missing "
                f"parseable YAML frontmatter (required for `version`)"
            )
            continue
        version = fm.get("version")
        if version is None:
            errors.append(
                f"components[{ident}]: {entrypoint.relative_to(REPO_ROOT)} frontmatter "
                f"missing required `version` (new components start at 0.1.0)"
            )
        elif not isinstance(version, str) or not SEMVER.match(version):
            errors.append(
                f"components[{ident}]: frontmatter `version` must be SemVer "
                f"(got {version!r})"
            )
    return errors


def validate_paths_and_orphans(entries: list) -> list[str]:
    """Verify each entry's path exists + detect orphan directories under any
    of the four kind dirs. An orphan is a directory under skills/, rules/,
    agents/, hooks/ that has no entry in registry pointing at it."""
    errors: list[str] = []
    declared_paths: dict[str, str] = {}
    declared_dirs_per_kind: dict[str, set[Path]] = {k: set() for k in SUPPORTED_KINDS}

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name", "<unnamed>")
        kind = entry.get("kind")
        path_str = entry.get("path")
        if not isinstance(path_str, str) or not isinstance(kind, str):
            continue
        if kind not in SUPPORTED_KINDS:
            continue
        ident = f"{kind}:{name}"
        abs_path = (REPO_ROOT / path_str).resolve()
        if not abs_path.exists():
            errors.append(
                f"components[{ident}]: declared path '{path_str}' does not exist"
            )
            continue
        if not abs_path.is_dir():
            errors.append(
                f"components[{ident}]: declared path '{path_str}' is not a directory"
            )
            continue
        try:
            abs_path.relative_to(KIND_DIRS[kind].resolve())
        except ValueError:
            errors.append(
                f"components[{ident}]: declared path '{path_str}' must be "
                f"under '{KIND_DIRS[kind].name}/'"
            )
            continue
        if path_str in declared_paths:
            errors.append(
                f"components[{ident}]: path '{path_str}' already declared "
                f"by components[{declared_paths[path_str]}]"
            )
        declared_paths[path_str] = ident
        declared_dirs_per_kind[kind].add(abs_path)

    # Orphan detection per kind directory
    for kind, kind_dir in KIND_DIRS.items():
        if not kind_dir.exists():
            continue
        for child in kind_dir.iterdir():
            if not child.is_dir():
                continue
            if child.resolve() not in declared_dirs_per_kind[kind]:
                rel = child.relative_to(REPO_ROOT)
                errors.append(
                    f"orphan: directory '{rel}' has no entry in "
                    f"hub/registry.yaml with kind='{kind}' "
                    f"(add an entry or remove the directory)"
                )

    return errors


# ---------------------------------------------------------------------------
# Profiles validation
# ---------------------------------------------------------------------------


def _index_components_by_kind(entries: list) -> dict[str, set[str]]:
    idx: dict[str, set[str]] = {k: set() for k in SUPPORTED_KINDS}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        kind = entry.get("kind")
        if isinstance(name, str) and isinstance(kind, str) and kind in SUPPORTED_KINDS:
            idx[kind].add(name)
    return idx


def validate_profiles_top_level(data: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["hub/profiles.yaml: top-level must be a mapping"]
    if "schema_version" not in data:
        errors.append("hub/profiles.yaml: missing top-level field `schema_version`")
    elif data["schema_version"] not in SUPPORTED_PROFILES_SCHEMA_VERSIONS:
        errors.append(
            f"hub/profiles.yaml: unsupported `schema_version` "
            f"{data.get('schema_version')} "
            f"(supported: {sorted(SUPPORTED_PROFILES_SCHEMA_VERSIONS)})"
        )
    if "profiles" not in data:
        errors.append("hub/profiles.yaml: missing top-level field `profiles`")
    elif not isinstance(data["profiles"], dict):
        errors.append("hub/profiles.yaml: `profiles` must be a mapping")
    return errors


def validate_profile_entry(
    name: str,
    profile: object,
    components_idx: dict[str, set[str]],
) -> list[str]:
    if not isinstance(profile, dict):
        return [f"profiles[{name}]: must be a mapping, got {type(profile).__name__}"]
    errors: list[str] = []
    if "description" not in profile:
        errors.append(f"profiles[{name}]: missing `description`")
    elif not isinstance(profile["description"], str) or not profile["description"].strip():
        errors.append(f"profiles[{name}]: `description` must be a non-empty string")
    if "owner_team" not in profile:
        errors.append(f"profiles[{name}]: missing `owner_team`")
    elif not isinstance(profile["owner_team"], str) or not profile["owner_team"].strip():
        errors.append(f"profiles[{name}]: `owner_team` must be a non-empty string")

    component_lists = {
        "skill": profile.get("skills", []),
        "rule": profile.get("rules", []),
        "agent": profile.get("agents", []),
        "hook": profile.get("hooks", []),
    }
    total_refs = 0
    for kind, refs in component_lists.items():
        if not isinstance(refs, list):
            errors.append(
                f"profiles[{name}]: `{kind}s` must be a list, "
                f"got {type(refs).__name__}"
            )
            continue
        for ref in refs:
            if not isinstance(ref, str):
                errors.append(
                    f"profiles[{name}].{kind}s: entries must be strings, "
                    f"got {type(ref).__name__}"
                )
                continue
            total_refs += 1
            if ref not in components_idx.get(kind, set()):
                errors.append(
                    f"profiles[{name}].{kind}s: references unknown {kind} "
                    f"'{ref}' (not present in hub/registry.yaml with kind='{kind}')"
                )

    if total_refs == 0:
        errors.append(
            f"profiles[{name}]: must reference at least one component "
            f"(any of skills/rules/agents/hooks)"
        )

    return errors


# ---------------------------------------------------------------------------
# Mirror sync check
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _fail(errors: list[str]) -> None:
    for err in errors:
        print(f"  ✗ {err}", file=sys.stderr)
    print(f"\nvalidation failed: {len(errors)} error(s)", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    if not HUB_REGISTRY.exists():
        print(f"error: {HUB_REGISTRY} does not exist", file=sys.stderr)
        return 2
    try:
        registry = yaml.safe_load(HUB_REGISTRY.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        print(f"error: failed to parse {HUB_REGISTRY}: {exc}", file=sys.stderr)
        return 2

    errors: list[str] = []
    errors.extend(validate_registry_top_level(registry))

    components: list = []
    if isinstance(registry, dict) and isinstance(registry.get("components"), list):
        components = registry["components"]
        for idx, entry in enumerate(components):
            errors.extend(validate_component_entry(idx, entry))
        errors.extend(validate_uniqueness_per_kind(components))
        errors.extend(validate_paths_and_orphans(components))
        errors.extend(validate_no_evolve_drafts(components))
        errors.extend(validate_component_versions(components))

    # Profiles validation (optional file)
    if HUB_PROFILES.exists():
        try:
            profiles_data = yaml.safe_load(HUB_PROFILES.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            errors.append(f"hub/profiles.yaml: failed to parse: {exc}")
            profiles_data = None
        if profiles_data is not None:
            errors.extend(validate_profiles_top_level(profiles_data))
            if isinstance(profiles_data, dict) and isinstance(
                profiles_data.get("profiles"), dict
            ):
                components_idx = _index_components_by_kind(components)
                for profile_name, profile in profiles_data["profiles"].items():
                    errors.extend(
                        validate_profile_entry(profile_name, profile, components_idx)
                    )

    if errors:
        _fail(errors)

    component_count = len(components)
    by_kind: dict[str, int] = {}
    for entry in components:
        if isinstance(entry, dict):
            k = entry.get("kind")
            if isinstance(k, str):
                by_kind[k] = by_kind.get(k, 0) + 1
    by_kind_str = ", ".join(f"{k}={v}" for k, v in sorted(by_kind.items())) or "none"
    profiles_count = (
        len(yaml.safe_load(HUB_PROFILES.read_text(encoding="utf-8")).get("profiles", {}))
        if HUB_PROFILES.exists()
        else 0
    )
    print(
        f"registry valid: schema_version={registry.get('schema_version')}, "
        f"hub_version={registry.get('hub_version')}, "
        f"components={component_count} ({by_kind_str}), profiles={profiles_count}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
