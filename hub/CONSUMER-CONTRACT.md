# hub/CONSUMER-CONTRACT.md

The schemas a consumer repo (and a consumer's machine) must implement to be served by `fdh`. Three artifacts, three purposes:

| Artifact | Lives in | Committed? | Edited by | Updated by |
|---|---|---|---|---|
| `.fdh/manifest.yaml` | consumer repo | ✓ yes | humans | humans |
| `.fdh/lock.yaml` | consumer repo | ✓ yes | `fdh install` | `fdh install`, `fdh update` |
| `~/.fdh/state.json` | user HOME | ✗ no, per-machine | `fdh` automatically | every `fdh` command |

Plus a per-component marker (`.fdh-managed.yaml`) and a sectioned block in `.gitignore`, both written by `fdh install`.

---

## 1. `.fdh/manifest.yaml` (intent)

### Purpose

Declare what the project wants. The single line `profile: minimal` is enough for most projects; teams that need finer control combine a profile with `extends:` or list components explicitly.

### Schema

```yaml
schema_version: 1

# OPTIONAL — reference a curated profile from hub/profiles.yaml.
# If omitted, the explicit lists below are the only source.
profile: <profile-name>

# OPTIONAL — extend or restrict the chosen profile.
extends:
  add_skills:    [<name>, ...]
  add_rules:     [<name>, ...]
  add_agents:    [<name>, ...]
  add_hooks:     [<name>, ...]
  remove_skills: [<name>, ...]
  remove_rules:  [<name>, ...]
  remove_agents: [<name>, ...]
  remove_hooks:  [<name>, ...]

# OPTIONAL — explicit lists. If used with `profile:`, they ADD to the profile's
# expansion (combine with `extends.add_*`). If used without `profile:`, they are
# the only components installed.
skills:
  - <name>
  - { name: <name> }   # mapping form also accepted
rules:    [...]
agents:   [...]
hooks:    [...]
```

### Resolution order at `fdh install`

1. If `profile:` is set, expand it from `hub/profiles.yaml` into the four component lists.
2. Apply `extends.add_*` lists on top.
3. Apply `extends.remove_*` lists last (idempotent — removing a name not in the set is a no-op + warning).
4. If explicit `skills:`/`rules:`/`agents:`/`hooks:` lists are present, **union** them with the profile result.
5. Result is written to `.fdh/lock.yaml` with versions + integrity hashes.

### Validation

```bash
python tools/validate-manifest.py path/to/.fdh/manifest.yaml
```

The validator confirms: schema_version is supported, profile (if referenced) exists in `hub/profiles.yaml`, every component name resolves to a real catalog entry of the matching kind. Removes of non-existent components are permissive (legacy cleanup is OK).

### Example: minimal

```yaml
schema_version: 1
profile: minimal
```

### Example: profile + extension

```yaml
schema_version: 1
profile: minimal
extends:
  add_skills:    [i18n-helper]
  remove_hooks:  [doctor-on-session-start]
```

### Example: no profile, explicit only

```yaml
schema_version: 1
skills: [design-system, code-review]
rules:  [no-console-log]
```

---

## 2. `.fdh/lock.yaml` (reproducible snapshot)

### Purpose

A byte-deterministic snapshot of what the last `fdh install` resolved, so two developers on the same commit of the consumer repo with the same `registry.url` get byte-identical installs.

### Schema

```yaml
schema_version: 1
hub_commit: <SHA of the hub at resolve time>
resolved_at: <ISO 8601 timestamp>
resolved_from_profile: <profile-name>   # informational; not used for resolution

skills:
  - name: <name>
    version: <version>
    path: <repo-relative path in the hub>
    integrity: sha256:<hex>
rules:    [...]
agents:   [...]
hooks:    [...]
```

### Regeneration rules

- `fdh install` (no flags) regenerates the lock if the manifest changed since the last resolve, or if the hub at `registry.url` moved.
- `fdh install --frozen` does NOT regenerate the lock; if the lock no longer satisfies the manifest, the command fails with a clear error and exits non-zero. Intended for CI.
- In CI environments (`CI=true`), `--frozen` is auto-applied unless the user passes `--no-frozen`.

### Diff-friendly format

The lock is YAML with `sort_keys: false` so the order is stable and PR diffs only show real changes. Hash-only changes to a single component produce a small diff.

---

## 3. `~/.fdh/state.json` (per-machine inventory)

### Purpose

A local ledger so `fdh list-installed`, `fdh repair`, and `fdh uninstall --dry-run` can answer questions without scanning every project on disk.

**Per-machine, not committed.** Two developers with the same lock have different `state.json` files; that's intentional.

### Schema (v1 minimal)

```json
{
  "schema_version": 1,
  "user_scope_installs": {
    "skills":  [{ "name": "...", "version": "...", "installed_at": "...", "path": "..." }],
    "rules":   [...],
    "agents":  [...],
    "hooks":   [...]
  },
  "hub_cache": {
    "url": "https://...",
    "last_pulled": "ISO 8601",
    "commit": "SHA"
  },
  "projects": {
    "/abs/path/to/consumer/repo": {
      "lock_hash": "sha256:<hex of .fdh/lock.yaml>",
      "managed_paths": [".claude/skills/design-system/", "..."],
      "last_install_at": "ISO 8601"
    }
  }
}
```

`projects:` is optional and grows lazily — each `fdh install` registers (or updates) the entry for the project it ran in.

### NFS / shared HOME edge case

If `$HOME` is shared across hosts (NFS, dev containers), set `FDH_HOSTNAME_NAMESPACED=true` so `fdh` writes to `~/.fdh/state.<hostname>.json` instead of `~/.fdh/state.json`. Default is the unnamespaced file (works for ~95% of devs with local disks).

### `fdh doctor` reads from here

Drift detection cross-references `state.json` with `.fdh-managed.yaml` markers on disk and the lock. Three failure modes detected:

- **Path missing**: state says installed, disk says no → suggest `fdh repair`.
- **Marker hash mismatch**: disk content differs from what was installed → suggest `fdh update --force` if intentional, or revert.
- **Orphan**: directory present without `.fdh-managed.yaml` → treated as developer-owned, never touched by `fdh`.

---

## 4. `.fdh-managed.yaml` (per-component marker)

### Purpose

A small YAML written inside (or beside) every materialized component so `fdh doctor` can identify what `fdh` owns vs what the developer wrote by hand.

### Schema

```yaml
name: <component name>
kind: skill | rule | agent | hook
version: <component version>
hub_commit: <SHA of hub at install time>
installed_at: <ISO 8601>
installed_by_fdh: <fdh CLI version>
source_path: <repo-relative path in the hub>
```

### Location

- For directory-based components (skills, rules in some agent layouts, agents, hooks with their own dirs): `.fdh-managed.yaml` lives **inside** the directory.
- For single-file components (Copilot prompts, OpenCode commands): the marker is a sibling file `<file>.fdh-managed.yaml`.

### Legacy migration

`fdh` recognizes the v1-era marker `.skill-version` (introduced by `add-fdh-cli-distribution-and-interactive-init`) and migrates it silently on the next `fdh install` or `fdh update`, replacing it with `.fdh-managed.yaml` (adding `kind:` and `source_path:`).

---

## 5. `.gitignore` sectioned block (write-managed paths only)

### Purpose

Exclude materialized components from git without preventing the developer from committing their own hand-written agents, skills, or hooks.

### Format

`fdh install` writes a sectioned block delimited by markers and only modifies content **between** the markers. Everything outside is preserved:

```
# >>> fdh:managed-paths >>>
# Auto-managed by `fdh install`. Do not edit by hand.
.claude/skills/design-system/
.claude/rules/no-console-log.md
.claude/agents/falabella-pr-writer.md
.codex/skills/design-system/
.github/prompts/design-system.prompt.md
.opencode/commands/design-system.md
# <<< fdh:managed-paths <<<
```

If the section becomes empty after `fdh uninstall`, the markers are removed too.

If `.gitignore` doesn't exist, it is created with only the section.

---

## 6. `.claude/settings.json` managed block (hooks)

### Purpose

Hooks for Claude Code live inside `.claude/settings.json` (a mixed-ownership file: the developer has their own keymaps, permissions, and hooks there). `fdh install` adds its hooks with a `_fdh_managed: <hook-name>` marker on each entry:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "*",
        "command": "fdh doctor --quiet",
        "timeout_seconds": 10,
        "_fdh_managed": "doctor-on-session-start"
      }
    ]
  }
}
```

`fdh uninstall <hook-name>` filters and removes only the entries with the matching `_fdh_managed` value, never touching the developer's own.

If `.claude/settings.json` doesn't exist, `fdh install` creates it with the minimal structure needed.

---

## See also

- `openspec/specs/consumer-manifest-and-lock/spec.md`
- `openspec/specs/installation-state-ledger/spec.md`
- `openspec/specs/consumer-managed-paths/spec.md`
- `hub/README.md` — hub-side layout and the four primitives.
