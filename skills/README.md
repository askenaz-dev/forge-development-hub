# skills/

Skill component source directories. **The authoritative catalog moved to [`hub/registry.yaml`](../hub/) as part of `hub-v2-manifest-state-profiles`.**

`skills/registry.yaml` in this directory is now a **generated mirror** of `hub/registry.yaml`, kept for a 60-day backward-compat window so external tools that pinned the old path keep working. Do not edit it directly.

## Where things are now

| Concern | Location |
|---|---|
| Catalog (all primitives, not just skills) | [`hub/registry.yaml`](../hub/registry.yaml) |
| Profiles (curated bundles) | [`hub/profiles.yaml`](../hub/profiles.yaml) |
| Layout + four-primitive overview | [`hub/README.md`](../hub/README.md) |
| Consumer manifest/lock/state schemas | [`hub/CONSUMER-CONTRACT.md`](../hub/CONSUMER-CONTRACT.md) |
| Skill source directories | this directory (`skills/<name>/`) |
| Rule source directories | `rules/<name>/` |
| Agent source directories | `agents/<name>/` |
| Hook source directories | `hooks/<name>/` |

## What lives here

Each `skills/<name>/` directory contains the source of one **skill** (on-demand workflow guidance) published by the hub. At minimum:

- `SKILL.md` — required entrypoint with frontmatter + body.
- Optional: `README.md`, `references/`, `scripts/`, snapshot markers (e.g., `.ds-version`).

The corresponding entry in `hub/registry.yaml` declares `kind: skill` and `path: skills/<name>`.

## Adding a new skill

1. **Create the skill directory** at `skills/<name>/`. At minimum it must have a `SKILL.md`. If the skill ships a snapshot of upstream docs, follow the layout pioneered by `skills/design-system/` (`SKILL.md` + `README.md` + `.ds-version` + `references/` + `scripts/sync.mjs`).
2. **Add an entry to `hub/registry.yaml`** with `kind: skill` and all required fields:
   ```yaml
   - name: <kebab-case>
     kind: skill
     description: <one-line summary>
     owner_team: <team-slug>
     tags: [<list>]
     default: <true|false>     # pre-selected in fdh init wizard
     min_fdh_version: "0.4.0"  # minimum CLI version
     agents_supported: [claude-code, codex, copilot, opencode]
     path: skills/<name>
   ```
3. **Regenerate the mirror** so `skills/registry.yaml` stays in sync:
   ```bash
   python tools/regenerate-skills-registry-mirror.py
   ```
4. **Open a PR.** CI runs `tools/validate-registry.py` to confirm consistency across the catalog, the four primitive directories, and the mirror.

## Adding rules / agents / hooks instead

Skills are only one of four primitives. To add a rule, agent, or hook, use the corresponding directory (`rules/`, `agents/`, `hooks/`) and the appropriate `kind` in `hub/registry.yaml`. See [`hub/README.md`](../hub/README.md) for layout and entrypoint conventions.

## Mirror lifecycle

The mirror in `skills/registry.yaml` is removed by a follow-up cleanup change ~2026-07-22 (60 days post-apply of `hub-v2-manifest-state-profiles`). Update any internal tooling or docs that reference `skills/registry.yaml` to point at `hub/registry.yaml` before then.

## Validation

```bash
# Catalog + four directory trees
python tools/validate-registry.py

# Consumer manifest fixtures
python tools/validate-manifest.py tests/fixtures/manifests/<file>.yaml

# Mirror in sync with hub/registry.yaml
python tools/regenerate-skills-registry-mirror.py --check
```

CI: `.github/workflows/validate-registry.yml` runs all three on every PR touching `hub/**`, `skills/**`, `rules/**`, `agents/**`, `hooks/**`, or the validators themselves.

> **TODO:** Both local and CI validation will migrate to `fdh validate-registry` once the Go implementation lands in the `fdh` repo. Tracked as part of `add-fdh-cli-distribution-and-interactive-init` change handoff.
