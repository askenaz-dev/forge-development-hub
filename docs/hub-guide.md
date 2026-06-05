# Hub Guide

The canonical overview of the Forge Development Hub: what it is, the four
primitives it publishes, **when to reach for each one**, and how a project
consumes them.

If you want to *author* a component, read this first, then go to the
[Authoring Guide](./authoring-guide.md). If you operate the catalog (mark
defaults, deprecate, publish), see the [Maintainer Runbook](./maintainer-runbook.md).

---

## What the hub is

The hub is the **canonical catalog of AI coding components** for Forge
developers. It is a content repository, not an application: there is no service
to run. It publishes reusable units of agent behaviour and exposes them through
one catalog (`hub/registry.yaml`, schema v2) so that any team can install the
same tooling into any project and get byte-identical results.

Components are **agent-agnostic at the source** and materialized per ecosystem
by the [`fdh` CLI](https://github.com/askenaz-dev/forge-development-hub-cli). One
`SKILL.md` becomes a Claude Code skill, a Codex skill, a Copilot prompt, and an
OpenCode command — authored once, installed everywhere it is supported.

```
hub/registry.yaml         # the catalog: every component, discriminated by `kind`
hub/harnesses.yaml         # curated bundles a project references with one line
skills/<name>/SKILL.md     # source of one skill
rules/<name>/RULE.md       # source of one rule
agents/<name>/AGENT.md     # source of one agent
hooks/<name>/{HOOK.md, hook.json}   # source of one hook
```

The catalog is the single source of truth for what exists and which fields each
component carries; the source directories hold the component body. Both are
validated together in CI (`tools/validate-registry.py`).

---

## The four primitives

The hub publishes **four primitives**, discriminated by the `kind` field in the
catalog. They differ along two axes: **when they run** (always vs. on demand vs.
on an event) and **what they produce** (context vs. an isolated sub-task vs. a
shell command).

| Primitive | When it runs | What it is | Materialized into |
|---|---|---|---|
| `skill` | On demand, when the agent decides it's relevant | A procedure / reference the agent pulls into context to do a multi-step task well | `.claude/skills/<name>/` (and per-agent equivalents) |
| `rule`  | Always on, scoped by a file glob | A single always-loaded guideline ("do / don't") the agent applies while editing | `.claude/rules/<name>.md` (and equivalents) |
| `agent` | On demand, in an isolated sub-context | A specialized sub-agent: its own system prompt, a constrained tool set, an output template | `.claude/agents/<name>.md` |
| `hook`  | On a lifecycle event (SessionStart, PreToolUse, …) | A shell command the *agent host* runs automatically at that event | A managed block inside `.claude/settings.json` |

### Skill — on-demand workflow guidance

A **skill** packages the knowledge and steps for a recurring, non-trivial task so
the agent performs it the house way instead of improvising. It is loaded **only
when relevant** (the agent matches the task against the skill's `description`),
so a skill can be long and detailed without taxing every prompt.

- **Example:** [`skills/devsecops`](../skills/devsecops/SKILL.md) — the
  shift-left security checklist, threat-modeling pass, secret-management rules,
  and incident-response steps a service follows.
- More examples in the catalog: [`design-system`](../skills/design-system/SKILL.md),
  [`spec-driven-development`](../skills/spec-driven-development/SKILL.md),
  [`architecture-patterns`](../skills/architecture-patterns/SKILL.md).

### Rule — always-on guideline scoped by glob

A **rule** is a single, always-loaded constraint that the agent applies to every
edit matching its `scope` glob. One rule states **one concern**; it is advisory
at the agent layer and complements (does not replace) the project's hard lint
gate.

- **Example:** [`rules/no-console-log`](../rules/no-console-log/RULE.md) —
  prohibits `console.*` in committed TS/JS (`scope: ["**/*.{ts,tsx,js,jsx}"]`),
  pointing the agent at the project logger instead.
- More examples:
  [`no-hardcoded-secrets`](../rules/no-hardcoded-secrets/RULE.md),
  [`no-any-cast`](../rules/no-any-cast/RULE.md),
  [`no-todo-comments`](../rules/no-todo-comments/RULE.md).

### Agent — specialized sub-agent with its own tools

An **agent** is a sub-agent the main agent can delegate a bounded task to. It
runs in an **isolated context** with its own system prompt, a **restricted tool
list** (e.g. read-only access), and usually a fixed **output template**. Use it
when you want a repeatable, narrowly-scoped job done in a fresh context without
polluting the main conversation.

- **Example:** [`agents/forge-pr-writer`](../agents/forge-pr-writer/AGENT.md) —
  reads a diff (`tools: [Read, Grep, Bash]`, read-only) and returns a PR
  description in Forge house style; it never commits or pushes.

### Hook — event-triggered command

A **hook** is a shell command bound to an **agent lifecycle event**. The hub
ships the configuration (`hook.json`); the **agent host executes it** — `fdh`
does not run a hook runtime of its own, it only writes the entry into
`.claude/settings.json`. Use a hook for automation that must fire at a precise
moment regardless of what the user is doing.

- **Example:** [`hooks/doctor-on-session-start`](../hooks/doctor-on-session-start/HOOK.md)
  — runs `fdh doctor --quiet` at every Claude Code `SessionStart` so drift is
  surfaced within seconds of opening the editor.

---

## When to use which — decision guide

Work down this list; the **first** match is your primitive.

1. **Does it need to run automatically at a specific lifecycle moment**
   (session start, before/after a tool call, on stop) — with no human asking?
   → **hook**. It's the only primitive bound to an event and executed by the host.

2. **Should it apply to *every* edit of a certain file type, as a single
   always-on "do / don't"?**
   → **rule**. Keep it to one concern and give it a `scope` glob. If you find
   yourself writing several paragraphs of procedure, it's probably a skill.

3. **Is it a bounded, repeatable sub-task you'd want done in a clean context with
   a restricted tool set** (e.g. "write the PR description", "triage this stack
   trace") and a predictable output shape?
   → **agent**. The isolation and tool-allowlist are the point.

4. **Otherwise — is it on-demand know-how for a multi-step task** (a workflow, a
   reference, a checklist) the agent should follow when the situation arises?
   → **skill**. This is the default and most common primitive.

Quick contrasts that catch most mistakes:

- **Rule vs. skill:** a rule is one always-on line of policy; a skill is
  on-demand, can be long, and describes *how to do* something. "Never commit
  `console.log`" is a rule; "how we do a security review" is a skill.
- **Agent vs. skill:** both are on-demand, but an agent runs in its **own
  context with its own tools** and returns a result; a skill enriches the
  **current** agent's context. Reach for an agent when you want isolation and a
  tool allowlist; reach for a skill when you want the current agent to know more.
- **Hook vs. everything:** a hook is the only primitive that fires **without
  anyone asking**, on an event. If the trigger is "the user/agent decided to",
  it's not a hook.

---

## How components are consumed

Two surfaces consume the same catalog.

### `fdh` CLI (install into a project)

A project that adopts the hub owns three artifacts (full schemas in
[`hub/CONSUMER-CONTRACT.md`](../hub/CONSUMER-CONTRACT.md)):

- **`.fdh/manifest.yaml`** — committed; declares intent (a harness, plus
  optional extras).
- **`.fdh/lock.yaml`** — committed; the exact resolution of the last
  `fdh install` (versions, integrity hashes, the hub commit).
- **`~/.fdh/state.json`** — per-machine, not committed; a local inventory.

The flow:

```sh
npx @askenaz-dev/fdh init      # wizard: detect agents, pick a harness, write manifest + lock
fdh install                    # materialize the locked components into your project
fdh update                     # pull newer versions per the catalog
fdh doctor                     # detect drift between lock, on-disk markers, and state
```

`fdh init` resolves the manifest against this hub's catalog and writes a
`.fdh/lock.yaml`. From then on, every developer on the team runs `fdh install`
and gets the same components, regardless of machine.

A **harness** is a named bundle so a project doesn't enumerate every component:

```yaml
# .fdh/manifest.yaml
schema_version: 1
harness: default            # the catalog's default set: one of each primitive
extends:
  add_skills: [tech-stack]  # add on top
  remove_rules: [no-console-log]   # or restrict
```

Harnesses live in [`hub/harnesses.yaml`](../hub/harnesses.yaml) (`default`,
`backend-team`, `frontend-team`, `appsec-team`, …).

### Portal (browse the catalog)

The portal (`fdh.askenaz.dev`) serves the same catalog over HTTP for **browsing
and discovery**: search and filter components, read descriptions, and see each
component's **scan status** badge (`pass` → "Scanned", `warn` → "Warnings",
`fail` → "Failed", `none` → "Unscanned"). Anonymous reads are public; the
portal's OIDC roles gate the web UI only. The portal does not change how
installation works — `fdh` is still the installer.

---

## What is and isn't part of the hub

A component is **published** but not automatically installed. Opening a PR does
not make a component part of anyone's default toolkit; it travels through three
gates — **merge**, **publish**, **adopt** — before it ships by default. That
governance is documented once, in
[`CONTRIBUTING.md`](../CONTRIBUTING.md#the-three-gates-not-automatically-part-of-the-hub);
the [Authoring Guide](./authoring-guide.md) walks an author through it and the
[Maintainer Runbook](./maintainer-runbook.md) covers the admin side.

---

## Where to go next

- **Add a component →** [Authoring Guide](./authoring-guide.md) (per-kind
  templates, registry entry, validation, the PR flow, CLI and no-CLI paths).
- **Operate the catalog →** [Maintainer Runbook](./maintainer-runbook.md) (mark
  `default`, deprecate/yank, release pipeline, CODEOWNERS, `scan_status`).
- **Consumer contract →** [`hub/CONSUMER-CONTRACT.md`](../hub/CONSUMER-CONTRACT.md).
- **Catalog schema →** [`hub/registry.yaml`](../hub/registry.yaml) header
  comments and the `hub-registry-v2` spec in `forge-specs`.
