*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

## 1. Skill scaffolding

- [x] 1.1 Create directory `skills/design-system/` at repo root
- [x] 1.2 Create subdirectories `skills/design-system/references/`, `skills/design-system/references/semantic-design/`, `skills/design-system/scripts/`
- [x] 1.3 Add `skills/design-system/` to top-level `README.md` (or `CLAUDE.md`) so the hub documents the new canonical skills location
- [x] 1.4 Confirm no copies of the skill are created under `.claude/skills/`, `.codex/skills/`, `.github/skills/`, or `.opencode/skills/`

## 2. DS reference snapshot

- [x] 2.1 Identify the exact upstream version to pin: read `tmp/FTI00575-design-system/packages/ui/package.json` for the `@forge-enablers-genai/ui` semver, and capture the HEAD commit SHA of the clone
- [x] 2.2 Copy `tmp/FTI00575-design-system/AGENTS.md` → `skills/design-system/references/AGENTS.md` (verbatim)
- [x] 2.3 Copy `tmp/FTI00575-design-system/COMPONENTS.md` → `skills/design-system/references/COMPONENTS.md` (verbatim)
- [x] 2.4 Copy `tmp/FTI00575-design-system/DESIGN.md` → `skills/design-system/references/DESIGN.md` (verbatim)
- [x] 2.5 Copy `tmp/FTI00575-design-system/components.meta.json` → `skills/design-system/references/components.meta.json` (verbatim)
- [x] 2.6 Copy every `tmp/FTI00575-design-system/semantic-design/*.md` (at minimum `ds-react.md`, `tokens.md`, `actions.md`, `forms.md`, `surfaces.md`, `feedback.md`, `navigation.md`, `layout.md`) → `skills/design-system/references/semantic-design/`
- [x] 2.7 Diff each copied file against the upstream source to confirm verbatim copy (no line-ending or encoding drift)

## 3. Version pinning

- [x] 3.1 Create `skills/design-system/.ds-version` containing three structured entries: `commit: <sha>`, `package-version: <semver>`, `sync-date: <ISO 8601 date>`
- [x] 3.2 Add a short comment block at the top of `.ds-version` documenting the file format (one-liner)

## 4. SKILL.md authoring

- [x] 4.1 Write `skills/design-system/SKILL.md` frontmatter with `name: design-system`, `description` containing UI-generation triggers across component creation, styling, accessibility, and Forge visual identity, plus `version: 0.1.0` and `ds-version: <semver from .ds-version>`
- [x] 4.2 Write "Purpose" section in body that names the upstream DS and instructs the agent to treat `references/` as canonical
- [x] 4.3 Write "Rules" section embedding the 20 non-negotiable rules from `references/AGENTS.md`, grouped into Tokens, Colors, Typography, Spacing, Components, Accessibility, Responsive — keep verbatim wording where possible
- [x] 4.4 Write "How to access the DS" section that lists `references/AGENTS.md`, `references/COMPONENTS.md`, `references/DESIGN.md`, `references/semantic-design/*.md`, and explains when to read each
- [x] 4.5 Write "Setup in consumer project" section with: (a) `.npmrc` block, (b) PAT instructions (link to GitHub settings), (c) recommended CLI flow (`npx @forge-enablers-genai/cli init`, then `cli add <component>`), (d) alternative npm package flow with `@import "@forge-enablers-genai/ui/tokens.css"`. Mark CLI as "recommended"
- [x] 4.6 Write "Drift detection" section instructing the agent to: (a) re-read `references/COMPONENTS.md` if a requested component is absent, (b) warn when `.ds-version` `sync-date` is > 60 days old, (c) refuse to invent tokens or components and instead surface the gap
- [x] 4.7 Audit `SKILL.md` body: search for "Claude Code", "Codex", "Copilot", "OpenCode" — they MUST NOT appear in the body (frontmatter is allowed)
- [x] 4.8 Verify `SKILL.md` size is under 8 KB; if larger, move detail into `references/` and reduce

## 5. README.md authoring

- [x] 5.1 Write `skills/design-system/README.md` "Manual install (Claude Code)" section with numbered steps: clone hub, copy directory to `.claude/skills/design-system/`, optionally add to `.gitignore`, verify via `/skills`
- [x] 5.2 Write "Other ecosystems" subsection naming `.codex/skills/`, `.github/skills/`, `.opencode/skills/` as future targets with an explicit `TODO: handled by fdh init` marker
- [x] 5.3 Write "Sync references" subsection documenting how to run `scripts/sync.mjs --source <path>` to refresh `references/` and `.ds-version`
- [x] 5.4 Write "Format note" subsection acknowledging `SKILL.md` follows Claude Code frontmatter conventions and that `fdh init` will adapt for other ecosystems

## 6. Sync script

- [x] 6.1 Implement `skills/design-system/scripts/sync.mjs` (Node ESM, no external deps) accepting `--source <path>` with default `../FTI00575-design-system`
- [x] 6.2 Add validation: if `<source>/AGENTS.md` or `<source>/tokens/tokens.json` are missing, exit non-zero with a clear error pointing at the missing files
- [x] 6.3 Copy the required reference files (same list as section 2) preserving structure
- [x] 6.4 Read upstream `git rev-parse HEAD` (shell out) and `<source>/packages/ui/package.json` to fetch SHA + semver; write to `.ds-version` with today's ISO date
- [x] 6.5 Add a hash-check guard: compute SHA256 of upstream `AGENTS.md`; if it differs from the previous sync, print a warning instructing the maintainer to re-review the embedded "Rules" section of `SKILL.md` (do NOT auto-rewrite)
- [x] 6.6 Verify idempotency: run the script twice in a row against an unchanged source and confirm no diff in the working tree on the second run

## 7. Validation

- [ ] 7.1 Manual auto-detection check: open Claude Code in a fresh empty directory with the skill copied into `.claude/skills/design-system/`, send the prompt "create a primary Button React component"; verify Claude loads the skill before generating
- [ ] 7.2 Negative trigger check: send unrelated prompts ("write a python sorting algorithm", "explain merge sort") and verify the skill does NOT auto-load
- [ ] 7.3 Drift check: temporarily set `.ds-version` `sync-date` to 90 days in the past, prompt the agent to generate UI, and verify it surfaces the stale-snapshot warning
- [ ] 7.4 Unknown-component check: prompt the agent to use a fictitious component (e.g., `<SuperWidget>`); verify it refuses and proposes either composition or an upstream RFC
- [x] 7.5 Update top-level `CLAUDE.md` of the hub with a one-paragraph pointer to `skills/design-system/` so future agents working on this hub know the canonical location

## 8. Final hygiene

- [x] 8.1 Run `openspec validate add-design-system-skill --strict` (or equivalent) to confirm the change is internally consistent
- [ ] 8.2 Update `CHANGELOG.md` of the hub with a one-line entry for the new skill (if a changelog exists; create one if absent only when explicitly approved)
- [x] 8.3 Confirm `tmp/FTI00575-design-system/` is gitignored or note it for the user (clone is local-only, should not be committed)
