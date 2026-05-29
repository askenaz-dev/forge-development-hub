# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A workflow hub, not an application. There is no application source code here — the same set of OpenSpec skills mirrored across four AI coding tool ecosystems, and four top-level directories of canonical, agent-agnostic **components** (`skills/`, `rules/`, `agents/`, `hooks/`) that the `fdh` CLI copies into consumer projects.

**The OpenSpec workspace moved to the `forge-specs` repo** (a sibling under the same container folder, e.g. `C:\forge`). Specs and changes for the whole system — including the `hub-*` specs this repo implements — now live there; run `openspec` from `forge-specs/`, not here. This repo no longer contains an `openspec/` directory. To work on specs and code together, clone `forge-specs` and run `scripts/meta-clone` to lay this repo and `fdh` out as siblings.

## Canonical components — four primitives

Since `hub-v2-manifest-state-profiles`, the hub publishes **four primitives** discriminated by a `kind` field in the catalog:

| Primitive | Where it lives | What it is | Materialized into the consumer |
|---|---|---|---|
| `skill`  | `skills/<name>/SKILL.md` | On-demand workflow guidance (procedures, references) | `.claude/skills/<name>/` (and equivalents) |
| `rule`   | `rules/<name>/RULE.md`   | Always-on guideline scoped by glob | `.claude/rules/<name>.md` (and equivalents) |
| `agent`  | `agents/<name>/AGENT.md` | Specialized subagent (system prompt + tools + template) | `.claude/agents/<name>.md` |
| `hook`   | `hooks/<name>/{HOOK.md, hook.json}` | Event-triggered command (SessionStart, PreToolUse, etc.) | Managed block inside `.claude/settings.json` |

The authoritative catalog lives in **`hub/registry.yaml`** (schema v2). Hub admins edit it to declare each component's metadata (`name`, `kind`, `description`, `owner_team`, `tags`, `default`, `min_fdh_version`, `agents_supported`, `path`). The `default: true|false` flag here is the single source of truth — any `default` declared inside a component's own frontmatter is ignored by `fdh init`. CI validates the registry on every PR (`.github/workflows/validate-registry.yml`, runs `python tools/validate-registry.py`); see `hub/README.md` for the "add a new component" flow.

Curated bundles of components live in **`hub/profiles.yaml`** (a profile references components from one or more kinds). A consumer references a profile from its `.fdh/manifest.yaml` and may extend or restrict it.

`skills/registry.yaml` is a generated mirror of `hub/registry.yaml` kept for 60 days post-`hub-v2-manifest-state-profiles` apply; **do not edit it directly** — edit `hub/registry.yaml` and run `python tools/regenerate-skills-registry-mirror.py`.

## Consumer contract — manifest + lock + state

A consumer project that adopts FDH owns three artifacts (schemas documented in [`hub/CONSUMER-CONTRACT.md`](hub/CONSUMER-CONTRACT.md)):

- **`.fdh/manifest.yaml`** — committed; declarative intent ("I want profile X plus these extras"). Edited by humans.
- **`.fdh/lock.yaml`** — committed; reproducible snapshot of the last `fdh install` (`hub_commit`, expanded components, integrity hashes). Written by `fdh install`.
- **`~/.fdh/state.json`** — NOT committed; per-machine inventory enabling `fdh list-installed`, `fdh repair`, `fdh uninstall --dry-run`. Written by every `fdh` command.

Each installed component in a consumer carries a `.fdh-managed.yaml` marker so `fdh doctor` can detect drift between the lockfile, the markers, and the disk. A sectioned block in `.gitignore` (`# >>> fdh:managed-paths >>>` … `# <<< fdh:managed-paths <<<`) automatically excludes materialized component directories from git; everything outside that block is the developer's own.

The four mirrored ecosystems are kept structurally identical:

| Directory      | Tool             | Contains                                |
| -------------- | ---------------- | --------------------------------------- |
| `.claude/`     | Claude Code      | `commands/opsx/*.md`, `skills/openspec-*/SKILL.md` |
| `.codex/`      | OpenAI Codex     | `skills/openspec-*/SKILL.md`            |
| `.github/`     | GitHub Copilot   | `prompts/opsx-*.prompt.md`, `skills/openspec-*/SKILL.md` |
| `.opencode/`   | OpenCode         | `commands/opsx-*.md`, `skills/openspec-*/SKILL.md` |

When you change a skill or command in one ecosystem, propagate the edit to the other three. The four `opsx-*` files (apply / archive / explore / propose) carry near-identical content with only filename-convention differences per tool.

## The OpenSpec workflow

Every non-trivial change moves through four phases driven by the `openspec` CLI:

1. **Explore** (`/opsx:explore`) — thinking partner mode, read-only; never writes code.
2. **Propose** (`/opsx:propose`) — `openspec new change "<name>"` scaffolds `openspec/changes/<name>/`, then generates `proposal.md`, `design.md`, `tasks.md` (artifact set is schema-defined).
3. **Apply** (`/opsx:apply`) — read every file in the `contextFiles` from `openspec instructions apply --change "<name>" --json`, work tasks top-down, flip `- [ ]` → `- [x]` immediately on completion.
4. **Archive** (`/opsx:archive`) — moves `openspec/changes/<name>/` → `openspec/changes/archive/YYYY-MM-DD-<name>/`. If delta specs exist under `openspec/changes/<name>/specs/`, sync them into `openspec/specs/<capability>/spec.md` before archiving.

The CLI's JSON output is the source of truth for what files to read and what state the change is in — do not infer artifact paths or completion from filenames alone.

```
openspec list --json                                  # active changes
openspec status --change "<name>" --json              # schema, artifacts, applyRequires
openspec instructions <artifact-id> --change "<name>" --json
openspec instructions apply --change "<name>" --json  # contextFiles + progress
openspec new change "<name>"
```

## Authoring artifacts

`openspec instructions` returns four fields used differently:

- `template` — the structure to write into the output file.
- `instruction` — schema-specific guidance for what content goes in it.
- `context` and `rules` — constraints on **you**, not content. Do **not** copy `<context>`, `<rules>`, or `<project_context>` blocks into the artifact file.
- `dependencies` — read these completed artifacts before writing the new one.

Loop the build order from `openspec status`'s `artifacts` array until every ID in `applyRequires` has `status: "done"`.

## Phase rules that bite

- **Explore mode never implements.** Reading, searching, and creating OpenSpec artifacts is allowed; writing application code is not. If the user asks to implement during explore, tell them to exit and propose.
- **Apply pauses, doesn't guess.** Stop on ambiguous tasks, on errors, or when implementation reveals a design issue — surface options and wait. Update task checkboxes the moment a task is complete, not in a batch at the end.
- **Archive prompts for selection.** Never auto-select a change to archive; always run `openspec list --json` and ask. Warn on incomplete artifacts or tasks but allow the user to proceed.
- **Spec sync is a separate step.** On archive, if `openspec/changes/<name>/specs/` exists, diff each delta against `openspec/specs/<capability>/spec.md` and offer to sync before moving the directory.

## Configuration

`openspec/config.yaml` (`schema: spec-driven`) holds optional project-wide `context:` and per-artifact `rules:` blocks. Currently empty templates — populate them once real domain context exists rather than inventing it.

## Prerequisites

The `openspec` CLI must be installed and on `PATH`; every skill and slash command shells out to it. The repo itself has no build, test, or lint commands — those will come from the projects that OpenSpec changes eventually target.
