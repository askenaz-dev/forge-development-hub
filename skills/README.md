# skills/

Canonical, agent-agnostic skills published by this hub. The future `fdh` CLI reads from here via the `registry.url` config and copies skills into a developer's chosen AI coding agent (`.claude/skills/`, `.codex/skills/`, `.github/prompts/`, `.opencode/commands/`).

## Contract with `fdh`

- This hub is the **source**. `fdh init` and `fdh update` clone/pull it via `registry.url` and read `skills/registry.yaml` as the authoritative catalog.
- `skills/<name>/` directories are the **payload**. Each must contain a `SKILL.md`; supplementary `references/`, `scripts/`, and `README.md` are copied as-is for agents that support directory layouts (Claude Code, Codex), and dropped with a warning for agents that only accept single-file skills (Copilot, OpenCode).
- `skills/registry.yaml` is the **contract**. Hub admins edit it; `fdh` consumes it. The schema is documented inline in `registry.yaml`'s header comments.

## Adding a new skill

1. **Create the skill directory** at `skills/<name>/`. At minimum it must have a `SKILL.md`. If the skill ships a snapshot of upstream docs, follow the layout pioneered by `skills/design-system/` (`SKILL.md` + `README.md` + `.ds-version` + `references/` + `scripts/sync.mjs`).
2. **Add an entry to `skills/registry.yaml`** with all required fields:
   ```yaml
   - name: <kebab-case>
     description: <one-line summary>
     owner_team: <team-slug>
     tags: [<list>]
     default: <true|false>     # pre-selected in fdh init wizard
     min_fdh_version: "0.4.0"  # minimum CLI version
     agents_supported: [claude-code, codex, copilot, opencode]
     path: skills/<name>
   ```
3. **Open a PR.** CI runs `tools/validate-registry.py` to confirm:
   - `name` is unique and kebab-case.
   - `path` exists and is a directory under `skills/`.
   - `agents_supported` is non-empty and uses only known agent IDs.
   - No orphan directories (every `skills/<dir>/` must have a registry entry).
   - `schema_version` is supported.

If any check fails, the PR is blocked until the registry is consistent.

## Layout

```
skills/
├── registry.yaml         # authoritative catalog, edited by admins
├── README.md             # this file
└── <name>/
    └── SKILL.md          # required entrypoint
    └── ...               # optional: README.md, .ds-version, references/, scripts/
```

## Validation

Local:
```bash
python tools/validate-registry.py
```

CI: `.github/workflows/validate-registry.yml` (runs on PR + push to main when `skills/**`, `tools/validate-registry.py`, or the workflow itself changes).

> **TODO:** Both local and CI validation will migrate to `fdh validate-registry` once the Go implementation lands in the `fdh` repo. Tracked as part of the `add-fdh-cli-distribution-and-interactive-init` change handoff.
