# design-system-skill Specification

## Purpose

Define the contract for a canonical, agent-agnostic skill that loads the Forge design system rules, tokens, and component catalog into any AI coding agent before it generates UI. The skill lives at `skills/design-system/` at the hub root, pins a snapshot of the upstream `FTI00575-design-system` via `.ds-version`, and is consumed by the future `fdh init` CLI (per the `fdh-init-interactive` / `fdh-skills-sync` capabilities).
## Requirements
### Requirement: Canonical skill location at repo root

The skill SHALL live at `skills/design-system/` at the root of `forge-development-hub`, OUTSIDE of any of the four ecosystem mirror directories (`.claude/`, `.codex/`, `.github/`, `.opencode/`). The directory MUST contain, at minimum, `SKILL.md`, `README.md`, `.ds-version`, `scripts/sync.mjs`, and a `references/` subdirectory.

#### Scenario: Skill directory is created at the canonical location
- **WHEN** the change is applied
- **THEN** the path `skills/design-system/` exists at the repo root and contains `SKILL.md`, `README.md`, `.ds-version`, `scripts/sync.mjs`, and `references/`

#### Scenario: Skill is not mirrored to ecosystem directories
- **WHEN** the change is applied
- **THEN** no copy of the skill SHALL exist under `.claude/skills/design-system/`, `.codex/skills/design-system/`, `.github/skills/design-system/`, or `.opencode/skills/design-system/`

### Requirement: SKILL.md auto-activates on UI generation intent

The `description` field of the `SKILL.md` frontmatter SHALL be written so that the coding agent loads the skill automatically when the user expresses intent to build, design, style, or modify UI. The description MUST include at least one verb-led trigger phrase for each of: (a) component creation, (b) styling/theming, (c) accessibility, (d) Forge visual identity. The description MUST instruct the agent to load the skill BEFORE writing UI code.

#### Scenario: Description includes UI-generation triggers
- **WHEN** a reviewer reads the `description` field in `SKILL.md` frontmatter
- **THEN** it MUST contain explicit triggers for component creation (e.g., "build component", "create form"), styling (e.g., "style", "Tailwind", "CSS"), accessibility (e.g., "accessibility", "WCAG"), and Forge visual identity (e.g., "Forge design", "design tokens")

#### Scenario: Agent loads skill before generating UI code
- **WHEN** a user asks an AI coding agent in a consumer project to "create a Button component"
- **THEN** the agent SHALL load `SKILL.md` (via auto-detection on description match) BEFORE emitting any component code

### Requirement: Non-negotiable design system rules are embedded in SKILL.md

The body of `SKILL.md` SHALL embed, in a dedicated "Rules" section, the non-negotiable rules from the upstream `AGENTS.md`, covering at minimum: (a) tokens (no raw values, no primitive tokens in components, token resolution order), (b) colors (WCAG 2.1 AA contrast, dark mode via semantic tokens, status color reservation), (c) typography (type scale tokens only, max reading width, minimum font size), (d) spacing (spacing scale only, consistency rule), (e) components (use existing first, all interactive states, focus ring), (f) accessibility (semantic HTML, prefers-reduced-motion, 44×44 touch target, aria-label on icon-only buttons), (g) responsive (mobile-first, defined breakpoints only). The total embedded rule section SHOULD be under 8 KB.

#### Scenario: Rule section is present and complete
- **WHEN** a reviewer reads `SKILL.md`
- **THEN** the file MUST contain a section explicitly listing rules from each of the seven categories: tokens, colors, typography, spacing, components, accessibility, responsive

#### Scenario: SKILL.md stays compact
- **WHEN** the file size of `SKILL.md` is measured
- **THEN** it SHOULD NOT exceed 8 KB

### Requirement: References snapshot mirrors canonical DS docs

The `references/` subdirectory SHALL contain offline-readable copies of the following files from the `FTI00575-design-system` repository (now under the `forge` org): `AGENTS.md`, `COMPONENTS.md`, `DESIGN.md`, `components.meta.json`, and every `*.md` under `semantic-design/` (at least: `ds-react.md`, `tokens.md`, `actions.md`, `forms.md`, `surfaces.md`, `feedback.md`, `navigation.md`, `layout.md`). The copies MUST be unmodified from upstream (preserving formatting, headings, and content verbatim).

#### Scenario: All required reference files exist
- **WHEN** the change is applied and `skills/design-system/references/` is listed
- **THEN** the directory MUST contain `AGENTS.md`, `COMPONENTS.md`, `DESIGN.md`, `components.meta.json`, and `semantic-design/{ds-react,tokens,actions,forms,surfaces,feedback,navigation,layout}.md`

#### Scenario: References match upstream verbatim
- **WHEN** a reviewer diffs `references/AGENTS.md` against the source at `forge/FTI00575-design-system/AGENTS.md` at the pinned `.ds-version`
- **THEN** the diff MUST be empty (modulo line endings)

### Requirement: DS version pinning via .ds-version

The file `.ds-version` SHALL record the exact version of the `FTI00575-design-system` source the references were synced from. It MUST contain at least: (a) the upstream `git` commit SHA, (b) the `@forge-enablers-genai/ui` package version, (c) the ISO 8601 sync date, (d) an optional `note:` field for transitional context (e.g., upstream rename in progress). `SKILL.md` MUST reference `.ds-version` so the agent knows the snapshot age.

#### Scenario: .ds-version contains the required fields
- **WHEN** a reviewer reads `.ds-version`
- **THEN** it MUST contain three required keys identifying: upstream commit SHA, UI package semver (`@forge-enablers-genai/ui`), and sync date in ISO 8601; the optional `note:` key MAY be present

#### Scenario: SKILL.md surfaces the version to the agent
- **WHEN** an agent loads `SKILL.md`
- **THEN** the file MUST instruct the agent to read `.ds-version` and warn the user if the sync date is older than 60 days

### Requirement: Sync script is offline-capable and idempotent

`scripts/sync.mjs` SHALL accept a path to a local clone of `FTI00575-design-system` (via `--source <path>` flag with sensible default such as `../FTI00575-design-system`), copy the required files into `references/`, and rewrite `.ds-version` with the SHA, package version (`@forge-enablers-genai/ui`), and current ISO date. It MUST NOT clone, fetch, or perform any network operation. Running it twice in a row against the same source MUST produce identical output (idempotent). The script SHALL accept a source whose `package.json` declares either the old `@forge-enablers-genai/ui` or the new `@forge-enablers-genai/ui` name during the transitional period, normalizing both into `@forge-enablers-genai/ui` in `.ds-version`.

#### Scenario: Sync from local clone succeeds offline
- **WHEN** `scripts/sync.mjs --source ../FTI00575-design-system` is run without any network access
- **THEN** it MUST complete successfully, refresh `references/` with the upstream content, and update `.ds-version`

#### Scenario: Sync is idempotent
- **WHEN** `scripts/sync.mjs` is run twice against an unchanged source clone
- **THEN** the second run MUST leave the working tree unchanged (no diff)

#### Scenario: Sync refuses invalid source
- **WHEN** `scripts/sync.mjs --source <path>` is invoked with a path that does not contain `AGENTS.md` and `tokens/tokens.json`
- **THEN** the script MUST exit non-zero and print an error pointing at the missing files

#### Scenario: Sync normalizes legacy package name
- **WHEN** the source clone's `package.json` still declares `@forge-enablers-genai/ui` (upstream rename pending)
- **THEN** the sync writes `@forge-enablers-genai/ui` into `.ds-version` and adds a `note: legacy package name '@forge-enablers-genai/ui' detected in source; awaiting upstream rename` line

### Requirement: Setup guidance covers registry auth and both consumption paths

`SKILL.md` SHALL include a "Setup in consumer project" section that documents: (a) creating an `.npmrc` with `@forge-enablers-genai:registry=https://npm.pkg.github.com` and `_authToken=${GITHUB_PKG_TOKEN}`, (b) generating a GitHub PAT with `read:packages` scope, (c) the recommended CLI path (`npx @forge-enablers-genai/cli init` then `cli add <component>`), and (d) the alternative package import path (`npm install @forge-enablers-genai/ui` with `@import "@forge-enablers-genai/ui/tokens.css"`). The recommended path MUST be visibly marked as such.

#### Scenario: Setup section is present and complete
- **WHEN** a reviewer reads `SKILL.md`
- **THEN** the file MUST contain a "Setup" section with all four sub-items: `.npmrc` config (using `@forge-enablers-genai` scope), PAT instructions, CLI usage, npm package alternative

#### Scenario: Recommended path is clearly marked
- **WHEN** a reviewer reads the Setup section
- **THEN** the CLI-based flow MUST be labeled as "recommended" (or equivalent unambiguous marker)

### Requirement: Manual installation documented in README.md

`README.md` of the skill SHALL describe step-by-step manual installation into a consumer project until `fdh init` exists. It MUST cover at least: (a) copying `skills/design-system/` into `.claude/skills/design-system/` of the consumer project, (b) optionally adding `.claude/skills/` to the consumer's `.gitignore`, (c) verifying the skill loads (e.g., via Claude Code's skill list), and (d) a short note for Codex/Copilot/OpenCode users pointing at the equivalent target path with a TODO marker for `fdh init`.

#### Scenario: README documents manual install steps for Claude Code
- **WHEN** a reviewer reads `README.md`
- **THEN** it MUST contain numbered or bulleted steps for copying the skill into a Claude Code project and verifying load

#### Scenario: README acknowledges other ecosystems
- **WHEN** a reviewer reads `README.md`
- **THEN** it MUST mention `.codex/`, `.github/`, and `.opencode/` as future targets with an explicit reference to the upcoming `fdh init` CLI

### Requirement: Skill instructs the agent to detect and report drift

`SKILL.md` SHALL contain a "Drift detection" section instructing the agent to: (a) re-read `references/COMPONENTS.md` if the user requests a component not listed there, (b) warn the user when `.ds-version` is older than 60 days, (c) refuse to invent tokens, colors, or components and instead surface the gap and propose an RFC per `references/CONTRIBUTING.md` (or upstream) when a needed token does not exist.

#### Scenario: Agent surfaces unknown component
- **WHEN** a user requests a component name that does not appear in `references/COMPONENTS.md`
- **THEN** the agent SHALL stop, report the gap, and propose either composing existing components or proposing an RFC upstream — not invent the component

#### Scenario: Agent warns on stale snapshot
- **WHEN** the date in `.ds-version` is more than 60 days before today
- **THEN** the agent SHALL warn the user that the DS snapshot may be stale and suggest running `scripts/sync.mjs` or (when available) `fdh update`

### Requirement: Skill body is agent-agnostic except for install section

The body of `SKILL.md` (rules, references, drift detection, setup) SHALL avoid hardcoded references to a specific coding agent (Claude Code, Codex, Copilot, OpenCode). Only the install/usage sections inside `README.md` MAY refer to specific agents. The frontmatter format MAY follow Claude Code conventions for this change, with an explicit note in `README.md` that adaptation to other ecosystems will be handled by `fdh init`.

#### Scenario: SKILL.md body avoids agent-specific references
- **WHEN** a reviewer searches the body of `SKILL.md` (excluding frontmatter) for "Claude Code", "Codex", "Copilot", "OpenCode"
- **THEN** no matches SHALL appear outside the frontmatter

#### Scenario: README acknowledges the ecosystem-coupling decision
- **WHEN** a reviewer reads `README.md`
- **THEN** it MUST contain a note that the current `SKILL.md` frontmatter follows Claude Code conventions and that `fdh init` will adapt it for other ecosystems

