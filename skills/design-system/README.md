# design-system skill

Canonical, agent-agnostic skill that loads the Forge design system rules into any AI coding agent before it generates UI. The upstream source of truth is the `@forge-enablers-genai/ui` package (repo `FTI00575-design-system`); this directory holds a pinned snapshot in `references/` and the rules in `SKILL.md`.

Until `fdh init` exists, install this skill manually following the steps below.

## Manual install (Claude Code)

1. Clone this hub:
   ```bash
   git clone <hub-url> forge-development-hub
   ```
2. Copy the skill into your project (project scope):
   ```bash
   # macOS / Linux
   cp -r forge-development-hub/skills/design-system <your-project>/.claude/skills/design-system
   # Windows PowerShell
   Copy-Item -Recurse forge-development-hub\skills\design-system <your-project>\.claude\skills\design-system
   ```
   For user scope, copy to `~/.claude/skills/design-system/` instead.
3. (Optional) Add `.claude/skills/` to your project's `.gitignore` so installed skills are not committed — re-install by re-running step 2.
4. Open the project and verify the skill loads: in Claude Code run `/skills`; `design-system` should appear in the list. Send a UI-generation prompt ("create a primary Button") and confirm the skill is loaded before any code is emitted.

## Other ecosystems

The same skill is intended to land in the convention of each ecosystem, but adaptation is not automated yet:

- `.codex/skills/design-system/` — Codex (directory layout matches Claude). TODO: handled by `fdh init`.
- `.github/prompts/design-system.prompt.md` — Copilot (single file, frontmatter adapted from `SKILL.md`). TODO: handled by `fdh init`.
- `.opencode/commands/design-system.md` — OpenCode (single file under `commands/`). TODO: handled by `fdh init`.

For now, in those ecosystems you may copy `SKILL.md` manually and adjust the frontmatter to the ecosystem's convention. The body is agent-agnostic and works as-is.

## Sync references

`references/` is a snapshot pinned to the version recorded in `.ds-version`. To refresh it against a newer upstream:

1. Have a local clone of the DS repo (default expected path: `../FTI00575-design-system` relative to this skill).
2. From this skill's directory:
   ```bash
   node scripts/sync.mjs --source ../FTI00575-design-system
   ```
3. The script copies the required files into `references/`, recomputes the `.ds-version` (commit SHA + package version + today's ISO date), and prints a warning if upstream `AGENTS.md` changed (because the 20 rules embedded in `SKILL.md` may need a manual review).

The script is offline — it does not clone or fetch. It is idempotent: re-running against an unchanged source produces no diff.

## Format note

`SKILL.md` follows Claude Code frontmatter conventions (YAML with `name`, `description`, `version`, `ds-version`). The body is plain Markdown and agent-agnostic — it contains no references to specific coding agents. Adaptation to Copilot/OpenCode/Codex formats will be handled by the future `fdh init` CLI when it copies the skill into each ecosystem's convention.

## Layout

```
design-system/
├── SKILL.md                     # frontmatter + 20 rules + how-to-access + setup + drift
├── README.md                    # this file (manual install + sync)
├── .ds-version                  # commit SHA + package version + sync date
├── references/                  # pinned upstream snapshot
│   ├── AGENTS.md
│   ├── COMPONENTS.md
│   ├── DESIGN.md
│   ├── components.meta.json
│   └── semantic-design/
│       ├── ds-react.md
│       ├── tokens.md
│       ├── actions.md
│       ├── forms.md
│       ├── surfaces.md
│       ├── feedback.md
│       ├── navigation.md
│       └── layout.md
└── scripts/
    └── sync.mjs                 # refresh references/ + .ds-version
```
