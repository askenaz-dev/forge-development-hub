## 1. Setup and pre-flight

- [ ] 1.1 Create branch `rebrand/forge-dh` off `main`.
- [ ] 1.2 Run `grep -ri "forge" .` baseline; save count and per-file breakdown into a scratch file (excluded from the commit) to compare against after each layer.
- [ ] 1.3 Run the full validator suite green from baseline (`python tools/validate-registry.py`, `python -m unittest discover -s tests`, `python tools/regenerate-skills-registry-mirror.py --check`); record green status so any later red is attributable to the rebrand work.
- [ ] 1.4 Confirm with the design-platform team whether the upstream `FTI00575-design-system` rename is already in flight or still pending (affects whether `.ds-version` keeps a `note:` line).

## 2. Layer 1 — top-level docs and narrative text

- [x] 2.1 Update `README.md`: title `forge Development Hub` → `Forge Development Hub`; first paragraph `forge developers` → `Forge developers`; install snippet `@forge/fdh` → `@forge/fdh`; URL `https://github.com/forge/fdh/blob/main/docs/quickstart.md` → `https://github.com/forge/fdh/blob/main/docs/quickstart.md`; primitives table `forge DS` → `Forge DS`, `forge-pr-writer` → `forge-pr-writer`, `forge house style` → `Forge house style`; Sibling repos section `forge/fdh` → `forge/fdh`, `C:/forge/fdh/` → `C:/forge/fdh/`, `forge/FTI00575-design-system` → `forge/FTI00575-design-system`; License footer `Internal forge use only.` → `Internal Forge use only.`
- [x] 2.2 Update `CLAUDE.md`: any inline reference to `forge` (path examples, package names) using the substitution table from `design.md`. _(No matches found — the project CLAUDE.md tracked in this repo does not currently reference "forge" textually; the repo-path string in the prompt context comes from the OS path, not from CLAUDE.md content.)_
- [x] 2.3 Update `hub/README.md`: brand strings and example references.
- [x] 2.4 Update `hub/CONSUMER-CONTRACT.md`: examples, paths, comments.
- [x] 2.5 Update `hooks/doctor-on-session-start/HOOK.md`: any example output strings mentioning `forge`.
- [x] 2.6 Update `.gitignore`: replace `forge` references in the narrative comments. _(Note: the `# >>> fdh:managed-paths >>>` block referenced in the task does not yet exist in `.gitignore` — it is written by `fdh install` in consumer projects; the references found here are in the prose comments above `node_modules/`.)_
- [ ] 2.7 Run `python tools/validate-registry.py` and `python -m unittest discover -s tests`; commit layer 1 (`docs: rebrand top-level docs to Forge Development Hub`). _(Validators are run; commit is deferred to user per safety convention.)_

## 3. Layer 2 — registry catalog + mirror

- [x] 3.1 Update `hub/registry.yaml`: descriptions, tags (`forge-identity` → `forge-identity`, `forge-style` → `forge-style`), `forge-pr-writer` entry → `forge-pr-writer` + `agents/forge-pr-writer`.
- [x] 3.2 Update commented example block: `Standard forge code review checklist.` → `Standard Forge code review checklist.`
- [x] 3.3 Update `hub/profiles.yaml`: `agents: [forge-pr-writer]` → `agents: [forge-pr-writer]`. _(No narrative forge comments present.)_
- [x] 3.4 Update `tests/test_validate_registry.py`, `tests/test_validate_manifest.py`, `tests/test_migrate_registry.py`: fixture data updated; 65/65 tests pass.
- [x] 3.5 Update `tests/fixtures/manifests/*.yaml`: _(no forge references found in fixture manifests.)_
- [x] 3.6 Update `tools/validate-registry.py`: `github.com/forge/fdh/pkg/instincts` → `github.com/forge/fdh/pkg/instincts`.
- [x] 3.7 Run `python tools/regenerate-skills-registry-mirror.py` — mirror up to date.
- [ ] 3.8 Run the full validator + test suite; commit layer 2. _(Tests + validator green; commit deferred to user.)_

## 4. Layer 3 — agent directory rename

- [x] 4.1 `git mv agents/forge-pr-writer agents/forge-pr-writer` — done (ahead of schedule to keep registry validator green during Layer 2).
- [x] 4.2 Edit `agents/forge-pr-writer/AGENT.md` frontmatter: name, description, tags all updated.
- [x] 4.3 Edit `agents/forge-pr-writer/AGENT.md` body: title, opening paragraph, style guidelines section header all updated.
- [x] 4.4 Grep verified zero `forge-pr-writer` refs outside the archive (which Layer 5b will rewrite).
- [ ] 4.5 Run validator + tests; commit layer 3. _(Both green; commit deferred to user.)_

## 5. Layer 4a — active spec narrative edits (no delta needed)

For each of these specs, the `forge` references are in Purpose narrative or scenario URLs, not in requirement clauses — no delta spec needed; just rewrite the wording in place.

- [x] 5.1 `openspec/specs/fdh-scan-security/spec.md`: 3 narrative mentions (forge in purpose + MCP corporativos + fixture name) rewritten to Forge.
- [x] 5.2 `openspec/specs/skill-portability/spec.md`: 2 scenario invocations `forge-installer install` → `fdh install`.
- [x] 5.3 `openspec/specs/hub-profiles/spec.md`: 2 mentions of `forge-pr-writer` → `forge-pr-writer`.
- [x] 5.4 `openspec/specs/portal-web/spec.md`: "Custom forge theme tokens" → "Custom Forge theme tokens".
- [x] 5.5 `openspec/specs/portal-api/spec.md`: `github.com/forge/fdh/pkg/registry` → `github.com/forge/fdh/pkg/registry`.
- [x] 5.6 `openspec/specs/instincts-format-and-storage/spec.md`: "500 forge devs" → "500 Forge devs".
- [x] 5.7 `openspec/specs/hub-skills-registry/spec.md`: `forge-pr-writer` example → `forge-pr-writer`.
- [x] 5.8 `openspec/specs/agent-adapter-map/spec.md`: `~/.config/forge-installer/adapters.yaml` → `~/.config/fdh/adapters.yaml`.
- [x] 5.9 Verified — only the 7 delta-targeted specs still match `forge`; their full rewrite lands at archive-sync time per OpenSpec convention.

## 6. Layer 4b — verify delta specs are accurate against current sources

The delta specs under `openspec/changes/rebrand-to-forge-development-hub/specs/` were drafted during propose. Before apply commits anything to `openspec/specs/`, sanity-check each one.

- [x] 6.1 `fdh-cli-naming` delta verified: MODIFIED blocks copy full original (Go module path, Per-user config dir); 3 REMOVED requirements (Backward-compatible read, fdh config migrate, Legacy stub binary) all present in source spec with Reason + Migration documented.
- [x] 6.2 `fdh-npm-wrapper` delta verified: 7 MODIFIED requirements (Paquete, Postinstall, Proxies, Cross-pkg-manager, Cache hit, Docs lidera npm) + 1 REMOVED (Backwards compat con forge-installer) — all blocks complete.
- [x] 6.3 `fdh-cli-distribution` delta verified: 8 MODIFIED requirements (Homebrew, winget, .deb/.rpm, FDH_PKG_HOST, Firma, Canal npm primary, Fallback Node-less, Brew/winget deferred) all copy full original blocks.
- [x] 6.4 `design-system-skill` delta verified: 6 MODIFIED requirements with one ADDED scenario in "Sync script" for legacy-name normalization.
- [x] 6.5 `hub-agents-primitive` delta verified: 3 MODIFIED + RENAMED block FROM/TO matches source spec header `### Requirement: Primera entry real \`agents/forge-pr-writer/\``.
- [x] 6.6 `skill-installer-cli` delta verified: 8 MODIFIED requirements replacing `forge-installer` with `fdh` in all scenario invocations (also caught the registry.url `skills.forge.internal` → `skills.forge.internal`).
- [x] 6.7 `skill-bundle-and-registry` delta verified: 3 MODIFIED requirements (Registry layout, index.json, Semver) replace scenario invocations.

## 7. Layer 5a — design-system skill body

- [x] 7.1 Updated `skills/design-system/SKILL.md`: 9 occurrences rewritten (frontmatter description, purpose, npm scope, setup section).
- [x] 7.2 Updated `skills/design-system/README.md`: 4 occurrences rewritten.
- [x] 7.3 Delegated to sub-agent: 12 reference files rewritten (`AGENTS.md`, `COMPONENTS.md`, `DESIGN.md`, `components.meta.json`, all 8 `semantic-design/*.md`). Italic brand-history note added to 11 `.md` files; `components.meta.json` got substitutions only (JSON has no comment syntax).
- [x] 7.4 `.ds-version`: added `note:` line documenting legacy package name pending upstream rename.
- [x] 7.5 `sync.mjs`: added `CANONICAL_PKG_NAME` / `LEGACY_PKG_NAME` constants, `readPackageInfo()` detects legacy, `writeDsVersion()` emits the `note:` conditionally, main loop prints a console line when legacy detected.

## 8. Layer 5b — archived OpenSpec changes (content rewrite, dirs untouched)

For each archived change directory under `openspec/changes/archive/YYYY-MM-DD-<name>/`, rewrite the file contents only (do NOT rename the directory). Add the italic note `*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*` immediately under the H1 of each rewritten file.

- [x] 8.1 `2026-05-22-installer-core/`: 8 files rewritten by sub-agent.
- [x] 8.2 `2026-05-23-add-design-system-skill/`: 4 files rewritten.
- [x] 8.3 `2026-05-23-add-fdh-cli-distribution-and-interactive-init/`: 7 files rewritten.
- [x] 8.4 `2026-05-23-dev-portal/`: 8 files rewritten.
- [x] 8.5 `2026-05-23-portal-hardening/`: 5 files rewritten (task plan undercounted — actual contents: proposal.md, design.md, tasks.md + 2 spec files).
- [x] 8.6 `2026-05-23-hub-v2-manifest-state-profiles/`: 15 files rewritten.
- [x] 8.7 `2026-05-23-fdh-cli-npm-distribution/`: 5 files rewritten.
- [x] 8.8 `2026-05-23-add-instinct-collaboration/`: 6 files rewritten.
- [x] 8.9 `_drafts/add-instinct-collaboration/proposal.md`: rewritten.
- [x] 8.10 `_drafts/hub-v2-manifest-state-profiles/proposal.md`: rewritten.
- [x] 8.11 `_drafts/fdh-cli-npm-distribution/proposal.md`: rewritten.
- [x] 8.12 Verified — every remaining `forge` match in archive/_drafts is the italic note string at the top of each file (61 files total).

## 9. Layer 6 — operations runbook

- [x] 9.1 Created `docs/operations/rename-checkout.md` with prerequisites, Windows PowerShell + macOS/Linux command blocks, post-rename steps, `git remote set-url` section, and a troubleshooting section covering common Windows "in use" / macOS "Directory not empty" / VS Code workspace-cache issues.
- [x] 9.2 Cross-linked from `README.md` (under Sibling repos as a third bullet) and from `hub/README.md` (new "Renaming your local checkout" section near the end).

## 10. Layer 7 — final verification

- [x] 10.1 Verified — every remaining `forge` match is one of: (a) this change's own narrative artifacts, (b) the italic notes in archive/draft/reference files, (c) `sync.mjs` legacy detection logic, (d) `docs/operations/rename-checkout.md` (the runbook MUST reference the old path it teaches you to move away from), (e) `hub/README.md` cross-link to the runbook, (f) the 7 delta-targeted active specs (rewrites land at archive-time via spec sync per OpenSpec convention).
- [x] 10.2 `python tools/validate-registry.py` → green. `python tools/regenerate-skills-registry-mirror.py --check` → mirror up to date.
- [x] 10.3 `python -m unittest discover -s tests` → 65/65 green.
- [x] 10.4 `openspec status` → `isComplete: True`, all `applyRequires` artifacts done.
- [ ] 10.5 Open draft PR. _(Deferred to user — needs `gh` and a remote; PR title + body suggested in `openspec/changes/rebrand-to-forge-development-hub/proposal.md`.)_

## 11. Layer 8 — archive

- [ ] 11.1 After PR merge, run `/opsx:archive` to move `openspec/changes/rebrand-to-forge-development-hub/` into `openspec/changes/archive/<archive-date>-rebrand-to-forge-development-hub/`.
- [ ] 11.2 Sync each delta spec into the corresponding `openspec/specs/<capability>/spec.md` per the archive tool's prompts. Verify the resulting active specs contain ZERO `forge` references (modulo any italic note already added in Layer 5).
- [ ] 11.3 Final `grep -ri "forge" openspec/specs/` returns zero matches. Confirm.
