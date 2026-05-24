## Why

The product is being rebranded from **forge Development Hub** to **Forge Development Hub**, dropping every occurrence of the word "forge" from this repository and from the contracts it publishes. The `FDH` acronym is preserved — only the expansion changes — but the brand sweep needs to be complete and consistent so consumers, the CLI, the registry, sibling repos, and the design system all speak with one voice.

## What Changes

- **BREAKING** Repo identity and docs: "forge Development Hub" → "Forge Development Hub" across `README.md`, `CLAUDE.md`, `hub/README.md`, `hub/CONSUMER-CONTRACT.md`, and every other narrative file. License footer "Internal forge use only" → "Internal Forge use only".
- **BREAKING** Component rename: `agents/forge-pr-writer/` → `agents/forge-pr-writer/` (directory + `AGENT.md` body + registry entry + every `agents_supported` and example reference).
- **BREAKING** Registry catalog: in `hub/registry.yaml` (and the generated mirror `skills/registry.yaml`), every `description` / `tags` / `path` that contains "forge" is rewritten — including `forge-identity` → `forge-identity` and `forge-style` → `forge-style`. Wording like "forge house style" / "forge design system" → "Forge house style" / "Forge design system".
- **BREAKING** CLI naming contract: the canonical npm package becomes `@forge/fdh` (was `@forge/fdh`); the canonical Go module path becomes `github.com/forge/fdh` (was `github.com/forge/fdh`); the legacy `forge-installer` stub binary and its 90-day backward-compat config-read window are **removed** from the spec (window assumed expired).
- **BREAKING** Sibling repo references: `github.com/forge/fdh` → `github.com/forge/fdh`; `forge/FTI00575-design-system` → `forge/FTI00575-design-system`; absolute path hints `C:/forge/...` → `C:/forge/...` in docs.
- Design system: terminology in `skills/design-system/SKILL.md`, `skills/design-system/README.md`, and references is updated to "Forge design system" / "Forge DS"; upstream pointer updated; `.ds-version` is annotated that the upstream repo was renamed.
- Tests and fixtures: `tests/test_validate_registry.py`, `tests/test_validate_manifest.py`, `tests/test_migrate_registry.py`, validator strings in `tools/validate-registry.py`, fixture manifests, and `.gitignore` block markers — all updated where they reference "forge".
- Hooks: `hooks/doctor-on-session-start/HOOK.md` body and example output strings.
- **BREAKING** OpenSpec history rewrite: every file under `openspec/changes/archive/` and `openspec/changes/_drafts/` that mentions "forge" is rewritten to use the new naming (per the user decision to make the rebrand historical-record-deep). The archive directories themselves are NOT renamed; only content is updated.
- Repo physical path: the hub itself currently lives at `C:\forge\forge-development-hub`. The change ships an `docs/operations/rename-checkout.md` runbook for developers to move their working copy to `C:\forge\forge-development-hub` (and the Unix equivalents). The change does not perform the local filesystem move.

## Capabilities

### New Capabilities

(none — this is a rebrand of existing capabilities, not new behavior)

### Modified Capabilities

- `fdh-cli-naming`: canonical CLI/module/config-dir identifiers move from `forge` to `forge`; legacy `forge-installer` migration requirements are dropped (90-day window assumed expired).
- `fdh-npm-wrapper`: the wrapper package and its postinstall integrity rules switch from `@forge/fdh` to `@forge/fdh`.
- `fdh-cli-distribution`: release channels, artifact naming, repo URLs, and channel docs switch to the `forge` namespace.
- `design-system-skill`: skill purpose, auto-activation triggers, and identity rules switch from "forge design system" to "Forge design system"; upstream pointer updated.
- `hub-agents-primitive`: the canonical example agent (used by validator, fixtures, and docs) is renamed `forge-pr-writer` → `forge-pr-writer`, and identity tags in the primitive contract are updated.
- `skill-installer-cli`: identifiers, default registry URL, and example invocations switch to the `forge` namespace.
- `skill-bundle-and-registry`: registry/bundle URL examples and identifiers switch to the `forge` namespace.

(Additional active specs — `fdh-scan-security`, `skill-portability`, `hub-profiles`, `portal-web`, `portal-api`, `instincts-format-and-storage`, `hub-skills-registry`, `agent-adapter-map` — contain only narrative/Purpose-level mentions of "forge". Those are handled as plain text edits in tasks.md without delta specs, because no requirements change.)

## Impact

- **Files touched**: ~83 (15 active spec.md files, 17 archived change directories, top-level docs, registry + mirror, agent dir rename, design-system skill, hooks, tests, validators).
- **APIs / contracts that break for consumers**:
  - Component name `forge-pr-writer` no longer resolves in the registry; consumer `.fdh/manifest.yaml` entries must move to `forge-pr-writer`.
  - npm package `@forge/fdh` and Go module `github.com/forge/fdh` no longer exist post-cutover.
  - `forge-installer` stub binary and `~/.config/forge-installer/` legacy directory support is removed.
- **Dependencies**: coordinated with the `fdh` sibling repo (binary/CLI) and the `FTI00575-design-system` upstream (rename in their org). The rebrand in this hub assumes those moves are in flight or already complete; the runbook documents the cutover order.
- **No-op for runtime behavior**: nothing changes about what skills/rules/agents/hooks DO; only their names, descriptions, and the brand wrapping around them change.
