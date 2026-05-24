## Context

The hub currently brands itself as **forge Development Hub** in 83 files: top-level docs, the registry catalog (`hub/registry.yaml`) and its mirror, one agent component (`agents/forge-pr-writer/`), the design-system skill, hook examples, Python validators and tests, ~15 active spec files under `openspec/specs/`, and ~17 archived change directories under `openspec/changes/archive/`. The sibling `fdh` CLI repo (Go binary + npm wrapper) lives at `github.com/forge/fdh` and publishes `@forge/fdh` on npm; the upstream design system lives at `forge/FTI00575-design-system`. Consumers of this hub adopt FDH via `.fdh/manifest.yaml` that resolves component names against `hub/registry.yaml`, so any rename of a component name is a breaking change to those manifests.

Per the propose-phase clarifications, the rebrand is **organization-wide** (the design system is also renamed Forge DS), **historical-record-deep** (archived OpenSpec changes are rewritten), and **assumes the external repos / npm scope are or will be migrated** (this change updates references to point at the new locations even before those external moves finish).

## Goals / Non-Goals

**Goals:**

- Replace every textual occurrence of "forge" / "forge" with "Forge" / "forge" across the repo, preserving the `FDH` acronym and the meaning of each sentence.
- Rename the one component that carries the brand in its identifier: `forge-pr-writer` → `forge-pr-writer` (directory, registry entry, profile references, validator fixtures).
- Update spec requirements that name canonical identifiers (`github.com/forge/fdh`, `@forge/fdh`, `forge-installer`) so that delta specs reflect the new contract.
- Keep the change auditable: each touched file should be a clean find-and-replace except for the directory rename and the small number of files that need re-wording (description text, drift notes).
- Ship a developer runbook for renaming the local checkout from `C:\forge\forge-development-hub` to `C:\forge\forge-development-hub` (and Unix equivalents), since this repo's content cannot rename its own working directory.

**Non-Goals:**

- Performing the actual move of external repos (`github.com/forge/fdh`, `forge/FTI00575-design-system`) or publishing under the new npm scope. Those are sibling-team work.
- Renaming the on-disk archive directories under `openspec/changes/archive/YYYY-MM-DD-<name>/` even when `<name>` contains brand words — the dates and slugs are historical anchors. (Their **contents** are rewritten; their **directory names** stay.)
- Migrating consumer projects' `.fdh/manifest.yaml` / `.fdh/lock.yaml`. We document the breaking change; consumers re-run `fdh install` against the new registry.
- Removing the prior `forge-installer` migration logic from sibling Go code — only the spec requirements are dropped here; that code-level cleanup happens in the `fdh` repo.

## Decisions

### Decision 1: One sweeping change vs. capability-by-capability

**Chosen: one sweeping change.**

A rebrand is fundamentally a coordinated edit — splitting it into per-capability changes would leave the repo in a half-renamed state between merges and would force consumers to follow many partial migrations. We accept a larger PR in exchange for atomic cutover.

**Alternative considered:** seven independent changes (one per Modified Capability). Rejected because (a) the cross-references between files would constantly be inconsistent mid-sequence, and (b) the validators in `tools/` test the registry as a whole — they would fail on any partial state.

### Decision 2: Case-preserving substitution, not blind `sed`

**Chosen: a documented table of substitutions, applied per-file with verification.**

| Match (case-sensitive) | Replacement | Notes |
|---|---|---|
| `forge Development Hub` | `Forge Development Hub` | Repo title |
| `forge developers` | `Forge developers` | Audience phrasing |
| `forge house style` | `Forge house style` | Agent description |
| `forge design system` / `forge DS` | `Forge design system` / `Forge DS` | Skill copy |
| `forge visual identity` | `Forge visual identity` | Skill requirement |
| `Internal forge use only` | `Internal Forge use only` | License footer |
| `forge-pr-writer` | `forge-pr-writer` | Component name (also directory) |
| `forge-identity` | `forge-identity` | Tag |
| `forge-style` | `forge-style` | Tag |
| `@forge/fdh` | `@forge/fdh` | npm scope |
| `@forge-enablers-genai` | `@forge-enablers-genai` | sub-scope used by DS package |
| `github.com/forge/fdh` | `github.com/forge/fdh` | Go module + repo URL |
| `github.com/forge/skill-installer` | `github.com/forge/skill-installer` | Legacy module (now historical) |
| `forge/FTI00575-design-system` | `forge/FTI00575-design-system` | Upstream DS pointer |
| `forge/fdh` (without protocol) | `forge/fdh` | Bare org/repo reference |
| `C:/forge/` / `C:\forge\` | `C:/forge/` / `C:\forge\` | Local-path hints in docs |
| `forge-installer` (binary/dir) | (removed) | Legacy migration window dropped |
| `~/.config/forge-installer/` | (removed) | Legacy config path; dropped from spec |

Validator scripts will be re-run after each batch; CI fails fast if any unintended `forge` survives.

**Alternative considered:** a single global `sed` on the whole tree. Rejected — would mangle the directory names under `openspec/changes/archive/` (which we want to preserve as historical anchors) and would risk corrupting case-sensitive identifiers we want to preserve elsewhere.

### Decision 3: Drop the `forge-installer` legacy compat from `fdh-cli-naming`

The existing spec carries five requirements about reading legacy config from `~/.config/forge-installer/`, a `forge-installer` stub binary, and an `fdh config migrate` subcommand — all part of a 90-day deprecation window after the original `forge-installer` → `fdh` rename. We treat that window as expired (the rename shipped multiple cycles ago) and drop those requirements entirely. The new spec keeps only the forward-looking, non-legacy requirements.

**Alternative considered:** double migration (`forge-installer` → `fdh` → keep, plus a new `@forge/fdh` migration story). Rejected because the user goal is to eliminate "forge" from the contract; carrying forward old migration logic is the opposite of that.

### Decision 4: Rewriting archived OpenSpec changes is content-only

Archive directory names like `openspec/changes/archive/2026-05-23-fdh-cli-npm-distribution/` stay as-is — they encode the archive date and the original change name. We rewrite only the **contents** of files inside them. For archive proposals/designs that explain past decisions ("we chose `@forge/fdh` because…"), we replace the brand verbatim and add a one-line italic note under each rewritten file's H1 of the form: `*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*`

**Alternative considered:** leave archives untouched. Rejected per the user clarification — they explicitly chose "Reescribir también los archives" so the brand is gone everywhere.

### Decision 5: Mirror regeneration runs after every batch

`tools/regenerate-skills-registry-mirror.py --check` is part of CI. Because the source `hub/registry.yaml` changes (description, tags, path), the mirror `skills/registry.yaml` must be regenerated in the same commit/branch. We rerun the mirror script as a final step after every other registry-touching edit, and we treat any `--check` failure as a blocker.

### Decision 6: Repo physical path is operational, not in-scope for content

The hub currently lives at `C:\forge\forge-development-hub` (and equivalents on other OSes). Renaming the parent directory and the repo directory itself is a developer-workstation operation — not something the change can do via file edits. We ship `docs/operations/rename-checkout.md` with the recommended sequence (close editors → `git status` clean → rename dir → reopen) and we update every doc/example that hardcodes the old path. The repo is functional from either path.

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| A consumer's `.fdh/manifest.yaml` pinning `forge-pr-writer` breaks at next `fdh install` | Sibling `fdh` CLI ships a hardcoded alias `forge-pr-writer → forge-pr-writer` for one release cycle; we document the breaking change in `hub/README.md` and call it out in the next release notes. |
| The external repo `github.com/forge/fdh` hasn't actually moved when this lands; doc links break | Add a top-of-`README.md` admonition saying "If you land on this before the external repo move completes, see `docs/operations/rename-checkout.md` for the temporary fallback URLs." Coordinate merge timing with the `fdh` repo owners. |
| Validator regex anywhere accidentally matches the new "forge" word as if it were a special string | `tools/validate-registry.py` is reviewed line-by-line; we add a unit test that asserts the validator behaves the same against a `forge-` fixture as it did against the `forge-` fixture. |
| Spec rewrites accidentally drop required content (e.g., a Scenario block disappears) | Each delta spec is generated by reading the prior spec end-to-end, then producing the delta in OpenSpec change-delta format (`## ADDED Requirements` / `## MODIFIED Requirements` / `## REMOVED Requirements`); a checklist task verifies no scenarios are silently lost. |
| Archive rewrites destroy the historical record of why decisions were made | The `*Brand strings updated…*` note at the top of each rewritten archive file preserves the fact that wording was changed and points at this change for context. |
| Mirror regenerator falls behind the source registry, CI red | Tasks.md sequences the mirror regeneration **last** among registry-touching tasks; the per-batch `--check` invocation catches drift before commit. |
| Design-system upstream rename (`FTI00575-design-system`) doesn't happen on schedule | The skill's `.ds-version` file gets a `note:` field added noting the rename is pending upstream; the sync script tolerates either the old or the new path until the upstream move completes. |

## Migration Plan

1. **Branch + draft** — work on a single feature branch `rebrand/forge-dh`.
2. **Layer 1 — non-spec text** — top-level docs, hub docs, README, hooks, agent body (no directory rename yet). Run validators after each file batch.
3. **Layer 2 — registry rename** — update `hub/registry.yaml` descriptions/tags/path, regenerate `skills/registry.yaml` mirror, update test fixtures, run `python tools/validate-registry.py` and the test suite.
4. **Layer 3 — directory rename** — `git mv agents/forge-pr-writer agents/forge-pr-writer`, fix the `AGENT.md` body, fix every reference (`grep -ri "forge-pr-writer"` must return zero matches after).
5. **Layer 4 — active specs** — write delta specs under `openspec/changes/rebrand-to-forge-development-hub/specs/` for the seven Modified Capabilities. Sweep narrative-only mentions in the other ~8 active specs via text edits in the same tasks.md (no delta spec needed for those).
6. **Layer 5 — archive content rewrite** — sweep `openspec/changes/archive/**` and `openspec/changes/_drafts/**`; add the italic note to each rewritten file.
7. **Layer 6 — operations runbook** — write `docs/operations/rename-checkout.md`.
8. **Layer 7 — final verification** — `grep -ri forge .` returns either zero matches or only matches inside this change's `proposal.md` / `design.md` historical sections and the explicit "updated by rebrand…" notes. CI green.
9. **Archive on apply complete** — `/opsx:archive` then sync delta specs into `openspec/specs/<capability>/spec.md`.

**Rollback:** revert the branch. No state outside the repo has been mutated by this change (sibling repo moves are independent work).

## Open Questions

- Should the change also rename the `_drafts/` proposals that mention forge, or is `_drafts/` considered live working state that the author owns? **Working assumption: rewrite the brand strings inside drafts too, since they will eventually become archives.** Flag for review if the user disagrees.
- Do we add a `legacy_aliases` field to `hub/registry.yaml` so the CLI can resolve `forge-pr-writer` → `forge-pr-writer` for one cycle? **Working assumption: yes, but the implementation of that alias lives in the sibling `fdh` repo's CLI, not in this hub.** This hub just ships the rename.
- Is the upstream design-system actually being renamed in its source org, or only re-pointed via a new remote? Determines whether `.ds-version`'s `note:` is permanent or transient. **Need confirmation from the design-platform team before applying Layer 4 against `design-system-skill`.**
