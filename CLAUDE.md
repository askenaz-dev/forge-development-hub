# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A workflow hub, not an application. There is no application source code here — only an OpenSpec workspace (`openspec/`) and the same set of OpenSpec skills mirrored across four AI coding tool ecosystems. Real work begins by creating a change under `openspec/changes/<name>/`; the codebase the change targets lives elsewhere or is added later.

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
