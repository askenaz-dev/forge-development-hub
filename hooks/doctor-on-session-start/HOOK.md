---
name: doctor-on-session-start
kind: hook
version: 0.1.0 # x-release-please-version
description: "Runs fdh doctor --quiet at every Claude Code SessionStart to surface drift early."
agents_supported: [claude-code]
tags: [doctor, drift-detection, session-lifecycle]
owner_team: dx-platform
---

# doctor-on-session-start

## What

This hook runs `fdh doctor --quiet` automatically every time a Claude Code session starts. If `fdh doctor` detects drift (a managed component on disk doesn't match the lockfile, a `.fdh/manifest.yaml` references a profile that no longer exists, your `~/.fdh/state.json` lost a project entry, etc.), the warning is surfaced in the session output before the developer starts work.

The intent: **catch broken setups within seconds of opening the editor, rather than at the next failed `fdh install` half a day later.**

## Why

In a multi-machine, multi-project workflow, the state of a developer's hub-managed components can drift silently:

- A teammate edited the manifest and the developer pulled without re-running `fdh install`.
- An OS update wiped `node_modules/@askenaz-dev/fdh/bin/` and the wrapper can't find the binary.
- The developer cloned a repo on a fresh laptop and forgot the install step.
- Someone hand-edited a managed skill, breaking its hash.

`fdh doctor --quiet` is fast (<1s in normal cases) and emits nothing on the happy path. When something is wrong, it prints one or two actionable lines.

## Configuration

The hook is delivered as `hook.json` and installed by `fdh install` into the managed block of `.claude/settings.json`. The materialized entry looks like:

```json
{
  "event": "SessionStart",
  "matcher": "*",
  "command": "fdh doctor --quiet",
  "timeout_seconds": 10,
  "_fdh_managed": "doctor-on-session-start"
}
```

Field reference:

- **`event: "SessionStart"`** — fires when Claude Code starts a new session in this workspace. Other supported events for future hooks: `PreToolUse`, `PostToolUse`, `Stop`.
- **`matcher: "*"`** — applies to every session, no per-tool filtering.
- **`command: "fdh doctor --quiet"`** — the binary installed via the `@askenaz-dev/fdh` npm package (or via brew/install.sh fallback).
- **`timeout_seconds: 10`** — generous upper bound; doctor normally returns in <1s. Sessions never block longer than this on hook execution.
- **`_fdh_managed: "doctor-on-session-start"`** — marker so `fdh uninstall doctor-on-session-start` removes this entry without touching the developer's own hooks. **Do not remove this field manually.**

## Where the command must exist

`fdh` must be on `PATH` for the hook to work. If `fdh doctor` is missing, Claude Code logs the failure to its own event log and the session continues normally — the hook is best-effort, not a hard requirement. The session is not blocked.

## How to modify or disable

- **Modify the hook for the whole hub:** edit `hooks/doctor-on-session-start/hook.json`, then have consumers run `fdh update`.
- **Disable for one project:** remove the hook from that project's `.fdh/manifest.yaml` and run `fdh install`. The managed block in `.claude/settings.json` is automatically cleaned up.
- **Disable globally for your user:** `fdh uninstall --scope user doctor-on-session-start`.
- **Customize the `--quiet` behavior:** see `fdh doctor --help` for verbosity flags. If you want a slightly more verbose default, fork this hook into a project-local variant (rename to `doctor-on-session-start-verbose` and adjust the `command`).

## Other agents

At the time of this change, only Claude Code natively supports the `SessionStart` event in this format. For other agents, `fdh install` skips materialization with an informational message. If/when other agents (Codex, Copilot, OpenCode) add native session-lifecycle hooks, this component will be extended to cover them.

## Runtime: who executes the hook?

`fdh` does **not** implement a hook runtime of its own. The execution is the responsibility of the agent (Claude Code reads `.claude/settings.json` at session start and runs the listed hooks). `fdh` only writes the configuration into the right place; the agent does the rest. This keeps `fdh` simple and decoupled from agent internals.
