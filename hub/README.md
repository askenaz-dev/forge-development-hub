# hub/

Authoritative source of the Falabella Development Hub catalog and profiles. This directory replaces the v1 layout where everything lived under `skills/`.

## Layout

```
hub/
├── registry.yaml          # v2 catalog of all components (skills, rules, agents, hooks)
├── profiles.yaml          # curated bundles a consumer manifest can reference
├── README.md              # this file
└── CONSUMER-CONTRACT.md   # schemas for .fdh/manifest.yaml, .fdh/lock.yaml, ~/.fdh/state.json
```

Component source directories remain at the repo root, paired by `kind`:

```
skills/<name>/         # SKILL.md + optional references/, scripts/
rules/<name>/          # RULE.md
agents/<name>/         # AGENT.md
hooks/<name>/          # HOOK.md + hook.json
```

## The four primitives

| Primitive | Where it lives | What it is | Materialized to |
|---|---|---|---|
| `skill`  | `skills/<name>/SKILL.md` | On-demand workflow guidance (procedures, references) | `.claude/skills/<name>/` (and equivalents per agent) |
| `rule`   | `rules/<name>/RULE.md`   | Always-on guideline scoped by glob (one rule, one concern) | `.claude/rules/<name>.md` (and equivalents) |
| `agent`  | `agents/<name>/AGENT.md` | Specialized subagent (system prompt + tools + template) | `.claude/agents/<name>.md` |
| `hook`   | `hooks/<name>/{HOOK.md, hook.json}` | Event-triggered command (SessionStart, PreToolUse, etc.) | Block managed inside `.claude/settings.json` |

All four are listed in a unified `registry.yaml` discriminated by the `kind` field.

## Profiles

A **profile** is a named bundle of components a consumer can reference with a single line:

```yaml
# Consumer's .fdh/manifest.yaml
profile: minimal
```

instead of enumerating every component. Profiles live in `profiles.yaml`, are curated by `dx-platform` (or another designated owner), and may be **extended** or **restricted** by the consumer:

```yaml
# Consumer's .fdh/manifest.yaml
profile: falabella-frontend
extends:
  add_skills: [i18n-helper]
  remove_rules: [no-console-log]
```

The expanded list is what gets resolved into `.fdh/lock.yaml`; the profile reference is informational.

## Relationship with the consumer

Consumer repos own three artifacts:

- **`.fdh/manifest.yaml`** — committed; declares intent ("I want profile X plus these extras").
- **`.fdh/lock.yaml`** — committed; the exact resolution from the last `fdh install` (versions, integrity hashes, hub commit).
- **`~/.fdh/state.json`** — NOT committed; per-machine ledger so `fdh list-installed`, `fdh repair`, `fdh uninstall --dry-run` work without scanning every project.

Schemas for the three are documented in [`CONSUMER-CONTRACT.md`](./CONSUMER-CONTRACT.md).

The hub itself only owns `registry.yaml` and `profiles.yaml`; the rest is consumer state.

## Backward compatibility: `skills/registry.yaml` mirror

During a 60-day migration window after this change applies, `skills/registry.yaml` is kept as a generated mirror of `hub/registry.yaml` so external tools that pinned the old path keep working.

- On Linux/macOS: `skills/registry.yaml` is a POSIX symlink to `hub/registry.yaml`.
- On Windows: `skills/registry.yaml` is a regenerated copy with a `DO NOT EDIT` header. CI runs `tools/regenerate-skills-registry-mirror.py` on every PR to keep it in sync; pre-commit hook strongly recommended for local dev.

**Do not edit `skills/registry.yaml` directly.** Edit `hub/registry.yaml` and let CI (or the regen script) update the mirror.

The mirror is removed 60 days post-apply by a follow-up cleanup change.

## Running validators locally

Before opening a PR that touches `hub/`, `skills/`, `rules/`, `agents/`, or `hooks/`:

```bash
# Validate the catalog and the four directory trees
python tools/validate-registry.py

# Validate a sample consumer manifest against the catalog
python tools/validate-manifest.py tests/fixtures/manifests/minimal-valid.yaml

# Regenerate the skills/registry.yaml mirror (Windows or after editing hub/registry.yaml)
python tools/regenerate-skills-registry-mirror.py
```

Both validators exit 0 on success, non-zero with actionable messages on failure.

CI: `.github/workflows/validate-registry.yml` runs all three on every PR touching the relevant paths.

## Adding a new component

1. Create the source directory under the matching kind: `rules/no-secrets/`, `agents/code-reviewer/`, etc.
2. Add the entrypoint file (`RULE.md`, `AGENT.md`, `HOOK.md`, or `SKILL.md`) with required frontmatter.
3. Add an entry to `hub/registry.yaml` with the correct `kind` and a matching `path`.
4. If the component should be part of a profile, reference it from `hub/profiles.yaml`.
5. Run `python tools/validate-registry.py` locally; fix errors.
6. Run `python tools/regenerate-skills-registry-mirror.py` to update the mirror.
7. Open PR. CI runs the same checks; merge only when green.

## Schema migration v1 → v2

Run `python tools/migrate-registry-v1-v2.py` on a v1 `skills/registry.yaml` to produce a v2 `hub/registry.yaml` automatically (adds `kind: skill` to every entry, renames the list, bumps `schema_version`). The script is idempotent — running it on an already-v2 file is a no-op.

## See also

- `openspec/specs/hub-registry-v2/spec.md` — the v2 schema spec.
- `openspec/specs/hub-profiles/spec.md` — the profiles spec.
- `openspec/specs/consumer-manifest-and-lock/spec.md` — the manifest + lock contract.
- `openspec/specs/installation-state-ledger/spec.md` — the state.json contract.
- `openspec/specs/hub-rules-primitive/spec.md`, `hub-agents-primitive/spec.md`, `hub-hooks-primitive/spec.md` — the new primitives.
