# Authoring Guide

For **collaborators** adding a component (skill, rule, agent, or hook) to the
hub. It covers the per-kind frontmatter templates, the `hub/registry.yaml`
entry, local validation, the PR flow and the three gates, picking an
`owner_team` / namespace, and both the `fdh skill new/sync/share` path and a
**no-CLI fallback** for external contributors.

New to the primitives? Read the [Hub Guide](./hub-guide.md) first to decide
*which* kind you need. Operating the catalog (defaults, deprecation, releases)
is the [Maintainer Runbook](./maintainer-runbook.md).

---

## What you produce

Adding a component is always the same two-part change:

1. A **source directory** under the kind's root, with the entry file:
   - `skills/<name>/SKILL.md`
   - `rules/<name>/RULE.md`
   - `agents/<name>/AGENT.md`
   - `hooks/<name>/{HOOK.md, hook.json}`
2. A matching **entry in [`hub/registry.yaml`](../hub/registry.yaml)** with the
   correct `kind` and a `path` that points at the directory.

CI runs `python tools/validate-registry.py`, which checks **both halves
together**: the registry entry's fields, and that the entry file carries a valid
SemVer `version`. Get both right and the validation passes.

> **What the validator enforces where.** The validator requires the full field
> set (`name`, `kind`, `description`, `owner_team`, `tags`, `default`,
> `min_fdh_version`, `agents_supported`, `path`) in the **registry entry**, and
> requires **only** a SemVer `version` in the **entry-file frontmatter**. The
> richer frontmatter shown in the templates below (e.g. `kind`,
> `agents_supported`, `tags` inside `RULE.md`) mirrors the real published
> components and is recommended for self-describing sources — but `name`,
> `version`, and `description` are the frontmatter keys the authoring tooling and
> portability lint truly depend on. `default` and `min_fdh_version` live **only**
> in the registry entry; a `default` written into frontmatter is ignored by
> `fdh init`.

---

## Per-kind frontmatter templates

Copy the block for your kind into the entry file. Each field is marked
**REQUIRED** or **optional**. "REQUIRED (validator)" means
`tools/validate-registry.py` fails without it; "REQUIRED (convention)" means the
kind's real published components all carry it and reviewers expect it.

New components **start at `version: 0.1.0`** — the release pipeline owns bumps
from there (see [Maintainer Runbook → Release](./maintainer-runbook.md#release--versioning-pipeline)).
SemVer is enforced: `MAJOR.MINOR.PATCH` (optionally `-prerelease`).

### `SKILL.md` → `skills/<name>/SKILL.md`

```markdown
---
name: <kebab-case-name>          # REQUIRED — must equal the directory name
version: 0.1.0                    # REQUIRED (validator) — SemVer; new = 0.1.0
description: >                    # REQUIRED — one paragraph. Start broad, then
  What this skill is and, crucially, WHEN to use it. The agent matches a task
  against this text to decide whether to load the skill, so end with a
  "Use when ..." clause.
license: MIT                     # optional — defaults to the repo license
metadata:                        # optional — free-form, for discovery/cross-links
  author: <owner_team>
  sdlc_phase: <e.g. security | design | testing>
  related_skills:
    - <namespace>/<other-skill>
---

# <Skill title>

<Body: the procedure, references, checklists. Skills can be long — they load
only when relevant.>
```

> Mirrors [`skills/devsecops/SKILL.md`](../skills/devsecops/SKILL.md). Skills
> may also ship `references/`, `scripts/`, and a `README.md` alongside
> `SKILL.md` (see [`skills/design-system/`](../skills/design-system/)).

### `RULE.md` → `rules/<name>/RULE.md`

```markdown
---
name: <kebab-case-name>          # REQUIRED — must equal the directory name
kind: rule                       # REQUIRED (convention) — self-describes the source
version: 0.1.0                    # REQUIRED (validator) — SemVer; new = 0.1.0
scope: ["**/*.{ts,tsx,js,jsx}"]  # REQUIRED (convention) — glob(s) the rule applies to
severity: warning                # optional — info | warning | error (advisory hint)
agents_supported: [claude-code, codex, copilot, opencode]   # REQUIRED (convention)
description: "One line: what is prohibited/required and what to do instead."  # REQUIRED
tags: [typescript, quality]      # optional in frontmatter (REQUIRED in registry entry)
owner_team: <team-slug>          # optional in frontmatter (REQUIRED in registry entry)
---

# <name>

## Rule
<The single do/don't, stated plainly.>

## Why
<Rationale.>

## What to use instead
<The sanctioned alternative.>
```

> Mirrors [`rules/no-console-log/RULE.md`](../rules/no-console-log/RULE.md).
> Keep one rule to **one concern**.

### `AGENT.md` → `agents/<name>/AGENT.md`

```markdown
---
name: <kebab-case-name>          # REQUIRED — must equal the directory name
kind: agent                      # REQUIRED (convention)
version: 0.1.0                    # REQUIRED (validator) — SemVer; new = 0.1.0
description: "One line: what the sub-agent does, from what input."  # REQUIRED
agents_supported: [claude-code]  # REQUIRED (convention) — agents that run sub-agents
tools: [Read, Grep, Bash]        # REQUIRED (convention) — the agent's tool allowlist
tags: [pr, code-review]          # optional in frontmatter (REQUIRED in registry entry)
owner_team: <team-slug>          # optional in frontmatter (REQUIRED in registry entry)
---

# <name>

You are the **<role>** agent. <System prompt: what you do, your output template,
and explicitly what you DON'T do — e.g. never commit or push.>
```

> Mirrors [`agents/forge-pr-writer/AGENT.md`](../agents/forge-pr-writer/AGENT.md).
> Constrain `tools` to the minimum the agent needs.

### `HOOK.md` (+ `hook.json`) → `hooks/<name>/`

A hook is **two files**: `HOOK.md` (frontmatter + human docs) and `hook.json`
(the machine-readable hook config the agent host consumes).

`hooks/<name>/HOOK.md`:

```markdown
---
name: <kebab-case-name>          # REQUIRED — must equal the directory name
kind: hook                       # REQUIRED (convention)
version: 0.1.0                    # REQUIRED (validator) — SemVer; new = 0.1.0
description: "One line: what command runs, on which event, and why."  # REQUIRED
agents_supported: [claude-code]  # REQUIRED (convention) — hosts that support the event
tags: [drift-detection, session-lifecycle]   # optional (REQUIRED in registry entry)
owner_team: <team-slug>          # optional in frontmatter (REQUIRED in registry entry)
---

# <name>

## What
<What the hook does and the lifecycle moment it fires at.>

## Configuration
<Document the hook.json fields and the materialized settings.json entry.>
```

`hooks/<name>/hook.json`:

```json
{
  "event": "SessionStart",
  "matcher": "*",
  "command": "fdh doctor --quiet",
  "description": "Run fdh doctor at session start to surface drift early.",
  "timeout_seconds": 10
}
```

> Mirrors [`hooks/doctor-on-session-start/`](../hooks/doctor-on-session-start/HOOK.md)
> and its [`hook.json`](../hooks/doctor-on-session-start/hook.json). Supported
> events: `SessionStart`, `PreToolUse`, `PostToolUse`, `Stop`.

---

## The `hub/registry.yaml` entry

Add one block to the `components:` list. **Every field below is REQUIRED** —
`tools/validate-registry.py` rejects an entry missing any of them.

```yaml
  - name: <kebab-case-name>      # REQUIRED — unique within the kind; == directory name
    kind: skill                  # REQUIRED — skill | rule | agent | hook (no defaulting)
    description: <one line>       # REQUIRED — non-empty
    owner_team: <team-slug>       # REQUIRED — non-empty; routes review (see namespaces)
    tags: [<list>]                # REQUIRED — list (may be a short list; not empty-checked)
    default: false                # REQUIRED — bool. New components are ALWAYS false (gate 3)
    min_fdh_version: "0.4.0"      # REQUIRED — SemVer; min CLI that can install this
    agents_supported: [claude-code, codex, copilot, opencode]  # REQUIRED — non-empty subset
    path: skills/<name>           # REQUIRED — must exist AND match the kind's directory
```

Field rules the validator enforces:

- **`name`** — kebab-case (`^[a-z][a-z0-9]*(-[a-z0-9]+)*$`), unique per `kind`.
- **`kind`** — exactly one of `skill | rule | agent | hook`. No silent default.
- **`agents_supported`** — non-empty; values must be a subset of
  `[claude-code, codex, copilot, opencode]`.
- **`min_fdh_version`** — SemVer.
- **`path`** — the directory must exist, must be unique, and must sit under the
  kind's root (`kind: rule` ⇒ `path: rules/<name>`). A directory under a kind
  root with **no** entry is an "orphan" and fails CI; an entry pointing at a
  **missing** directory also fails.
- **`default`** — for a brand-new component this is **always `false`**. Flipping
  it to `true` is an admin action (gate 3), not part of your contribution PR.

To put the component in a curated bundle, also reference it by name under the
right kind in [`hub/harnesses.yaml`](../hub/harnesses.yaml) — but a new component
is normally *not* added to a harness in the same PR (that, too, is adoption).

---

## `owner_team` and namespace selection

`owner_team` is the team accountable for the component. It does three things: it
**routes the review** (via CODEOWNERS), it is the **namespace** the published
artifact is grouped under, and it is the **aligned name** that ties the GitHub
team, the CODEOWNERS owner, and the portal `reviewer` role together (no identity
federation — just a shared name). Pick from the seeded map:

| Namespace / concern | `owner_team` |
|---|---|
| Security | `appsec` |
| Design system / a11y / product design | `design-platform` (a.k.a. `design-systems`, `accessibility`, `product-design`) |
| Operations / SRE | `sre` |
| Architecture | `architecture-guild` |
| CI/CD / platform bootstrap | `platform-engineering` |
| Code review / general DX | `dx-platform` |
| Requirements / product | `product-platform` |
| Testing / QA | `qa-platform` |

(Source: [`CONTRIBUTING.md` → team / namespace seed map](../CONTRIBUTING.md#team--namespace-seed-map).)
If your component doesn't fit, use `dx-platform` and call it out in the PR so a
maintainer can route it. Until a namespace's GitHub team is provisioned,
CODEOWNERS routes its reviews to the catch-all maintainer — your PR still gets a
required review either way.

---

## Local validation

Run the same check CI runs, from the repo root, before you open the PR:

```sh
python tools/validate-registry.py
```

It exits `0` and prints a one-line summary on success
(`registry valid: schema_version=2, …`), or exits non-zero listing each problem
(missing field, bad SemVer, kind/path mismatch, orphan directory, an unremoved
`fdh evolve` draft banner, …). Fix every line before pushing.

Also handy while iterating:

```sh
# Validate a consumer manifest fixture against the catalog
python tools/validate-manifest.py tests/fixtures/manifests/minimal-valid.yaml

# Unit tests
python -m unittest discover -s tests
```

PyYAML is the only dependency: `pip install pyyaml`.

---

## Path A — author with the `fdh` CLI (recommended)

The `fdh` CLI scaffolds, materializes, and contributes a component end to end.
The flow (capability `fdh-component-authoring`) is, using a skill as the example
(`rule` / `agent` / `hook` work the same, with `fdh <kind> …`):

```
new ──▶ iterate ──▶ sync ──▶ share ──▶  (review ▶ publish ▶ adopt — the 3 gates)
```

1. **Scaffold and materialize.**
   ```sh
   fdh skill new card-grid
   ```
   Writes a canonical, agent-agnostic source bundle (by default under
   `.fdh/authoring/card-grid/`, override with `--dir`) with `SKILL.md` at
   `version: 0.1.0`, then **materializes** it into each agent you select in the
   wizard (`.claude/skills/card-grid/`, the Codex skills dir, …) so it works
   immediately. The multi-select is pre-checked from the same host detection as
   `fdh init`; `agent`/`hook` kinds only offer the agents that support them. A
   `hook new` run also prompts for the event and writes `hook.json`. `new`
   **validates and stops** — it does not commit or open a PR. The canonical
   source and its materialized copies are **unmanaged** (no `.fdh-managed.yaml`),
   so `fdh install`/`update` never clobbers your work in progress.

2. **Iterate, then propagate.** Edit the canonical source, then:
   ```sh
   fdh skill sync card-grid       # regenerate every selected agent's copy from source
   fdh skill sync card-grid --check   # report drift only, don't overwrite
   ```
   `sync` reports drift if you edited a materialized copy directly, and by
   default overwrites it from the canonical source (`--force` to overwrite
   without prompting).

3. **Open the contribution PR.**
   ```sh
   fdh skill share card-grid --repo <path-to-hub-checkout>
   ```
   `share` validates the bundle (layout, frontmatter, portability lint, security
   scan); copies it into `skills/card-grid/`; adds a `hub/registry.yaml` entry
   with **`default: false`** and `agents_supported` populated from the bundle;
   creates a branch; commits `feat(card-grid): add skill`; pushes; and opens a
   PR via `gh`, printing the URL and a notice that the component is **not part of
   the hub until reviewed and merged**. **It never merges.** If validation or the
   security scan fails, `share` aborts **before** any push. If you lack Write on
   the hub, `share` uses (or creates) **your fork** and opens the PR from there —
   no upstream Write required.

After `share`, your work is in CI for the three gates below.

---

## Path B — no-CLI contributor (fork + manual edit + PR)

You do **not** need Go or the `fdh` CLI to contribute. Anything `fdh skill share`
automates can be done by hand; CI runs the same checks either way.

1. **Fork** `askenaz-dev/forge-development-hub` on GitHub and clone your fork.
   (Org members with Write can branch directly instead of forking.)
2. **Create the source directory and entry file** for your kind, using the
   matching [template above](#per-kind-frontmatter-templates). Start at
   `version: 0.1.0`. For a hook, add `hook.json` too.
3. **Add the `hub/registry.yaml` entry** with `kind`, a `path` that matches the
   directory, all [required fields](#the-hubregistryyaml-entry), and
   **`default: false`**.
4. **Validate locally** (Python + PyYAML, no Go needed):
   ```sh
   pip install pyyaml
   python tools/validate-registry.py
   ```
5. **Commit with a scoped conventional message** — CI's `commitlint` requires
   it, and the scope drives versioning:
   ```sh
   git commit -m "feat(card-grid): add skill"
   ```
   The scope (`card-grid`) **must match the component name**; a `feat`/`fix`
   commit touching a component directory with an unknown scope fails CI.
6. **Open the PR** (web UI or `gh pr create`) from your fork's branch to
   `askenaz-dev/forge-development-hub:main`. In the body, name the `owner_team`
   and say what the component does.

That's the whole "fork + manual edit + PR" path — byte-for-byte what the CLI
produces, just typed by hand.

---

## The PR flow and the three gates

A PR does **not** make your component part of the hub. It passes through three
gates (full reference and the permission model live in
[`CONTRIBUTING.md`](../CONTRIBUTING.md#the-three-gates-not-automatically-part-of-the-hub)):

| Gate | What it controls | Who acts |
|---|---|---|
| **1 — Merge** | The PR can't merge without green CI **and** a non-author CODEOWNERS approval. Required checks include registry/bundle/frontmatter validation, security scan, conventional-commit scope lint, and "no draft banner". No self-merge. | **reviewer** (CODEOWNERS) |
| **2 — Publish** | A version is published only when a **publisher** merges the release PR → tag `<kind>/<name>@<semver>` → signed bundle. Merging your PR alone does not publish. | **publisher** |
| **3 — Adopt** | A merged, published component stays `default: false` until an **admin** sets `default: true` or adds it to a harness. It can stay opt-in forever. | **admin** |

As the **author**, your job ends at "PR open, CI green, review requested." The
later gates are someone else's — don't set `default: true` yourself, and don't
expect a merge to auto-publish or auto-adopt.

### What CI checks on your PR

`validate-registry` (the workflow that runs `tools/validate-registry.py`) and
`commitlint` are the **required status checks** named in branch protection.
Between them they verify:

- the registry schema, every entry's required fields, kind/path coherence, and
  no orphan directories;
- every component entry file declares a SemVer `version`;
- no entry file still carries the `fdh evolve` draft banner (`> ⚠️ DRAFT`) —
  curate the draft before merging;
- harness references (if you touched `harnesses.yaml`) resolve to real
  components;
- your commits are conventional and scoped to a real component.

Make `python tools/validate-registry.py` pass locally and your commit message
conventional, and the PR's required checks will be green.

---

## Checklist

- [ ] Decided the **kind** ([Hub Guide decision guide](./hub-guide.md#when-to-use-which--decision-guide)).
- [ ] Created `<kind>s/<name>/` with the entry file from the template,
      `version: 0.1.0`. (Hooks: `hook.json` too.)
- [ ] Added the `hub/registry.yaml` entry: matching `kind` + `path`, all
      required fields, `default: false`.
- [ ] `python tools/validate-registry.py` passes locally.
- [ ] Conventional, scoped commit: `feat(<name>): add <kind>`.
- [ ] PR opened to `askenaz-dev/forge-development-hub:main`; `owner_team` named
      in the body.

---

## See also

- [Hub Guide](./hub-guide.md) — primitives and when to use which.
- [Maintainer Runbook](./maintainer-runbook.md) — defaults, deprecation,
  release, CODEOWNERS, `scan_status`.
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — the gates and permission model
  (canonical).
- [`hub/registry.yaml`](../hub/registry.yaml) — catalog schema (header
  comments).
- [`hub/CONSUMER-CONTRACT.md`](../hub/CONSUMER-CONTRACT.md) — what consumers own.
