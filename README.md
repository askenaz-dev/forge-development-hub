# Forge Development Hub

The canonical catalog of AI coding components (skills, rules, agents, hooks) published for Forge developers. Discovered, installed, and updated via the `fdh` CLI.

## Try it in 30 seconds

```sh
npx @askenaz-dev/fdh init
```

That runs a wizard: detects which AI agent(s) you have installed (Claude Code, Codex, Copilot, OpenCode), lets you pick a profile, and materializes the right files into your project. No prior install of `fdh` needed.

To make it permanent:

```sh
npm i -g @askenaz-dev/fdh
```

> **Don't have Node?** The CLI also ships as a POSIX one-liner, PowerShell script, `.deb`/`.rpm` packages, and eventually Homebrew / winget. See [`fdh/docs/quickstart.md`](https://github.com/askenaz-dev/forge-development-hub-cli/blob/main/docs/quickstart.md).

## What you get

`fdh init` resolves your project's `.fdh/manifest.yaml` against this hub's catalog (`hub/registry.yaml`) and produces a `.fdh/lock.yaml` snapshot. After that, every developer in your team runs `fdh install` and gets byte-identical AI tooling, regardless of their machine.

Four primitives, all listed in one catalog:

| Primitive | What it does | Example |
|---|---|---|
| `skill` | On-demand workflow guidance | `design-system` — Forge DS rules + component catalog |
| `rule` | Always-on guideline scoped by glob | `no-console-log` — prohibits `console.log` in TS/JS |
| `agent` | Specialized subagent + tools | `forge-pr-writer` — generates PR descriptions in house style |
| `hook` | Event-triggered command | `doctor-on-session-start` — runs `fdh doctor --quiet` at session start |

Curated bundles (`profiles.yaml`) let you grab a set with a single line:

```yaml
# .fdh/manifest.yaml
profile: minimal     # exercises all four primitives end-to-end
```

## Repository layout

```
hub/
├── registry.yaml          # schema v2, all 4 primitives discriminated by `kind`
├── profiles.yaml          # curated bundles consumers reference
├── README.md              # layout + add-a-component flow
└── CONSUMER-CONTRACT.md   # schemas of .fdh/manifest.yaml, .fdh/lock.yaml, ~/.fdh/state.json

skills/<name>/SKILL.md     # one directory per skill
rules/<name>/RULE.md       # one directory per rule
agents/<name>/AGENT.md     # one directory per agent
hooks/<name>/{HOOK.md, hook.json}

openspec/                  # the spec-driven workflow that drives this repo
tools/                     # python validators (CI invokes these)
tests/                     # python unit tests + manifest fixtures
.github/workflows/         # CI: catalog + profiles + fixtures
```

## Adding a component

See `hub/README.md` for the full how-to. tl;dr:

1. Create `<kind>s/<name>/` with the entrypoint file (`SKILL.md`, `RULE.md`, `AGENT.md`, or `HOOK.md`).
2. Add an entry to `hub/registry.yaml` with the matching `kind` and `path`.
3. Optionally reference it from a profile in `hub/profiles.yaml`.
4. Run `python tools/validate-registry.py`.
5. Open a PR — CI runs all validators on every push.

## Sibling repos

- **[`askenaz-dev/forge-development-hub-cli`](https://github.com/askenaz-dev/forge-development-hub-cli)** — the Go CLI + Next.js portal API. Lives in `C:/forge/fdh/`. Houses the `npm/` wrapper that ships `@askenaz-dev/fdh`.
- **Renaming your local checkout?** See [`docs/operations/rename-checkout.md`](docs/operations/rename-checkout.md) for the step-by-step move from `C:\forge\forge-development-hub` to a new location.

## Specs & changes

This repo uses OpenSpec for change management. Every non-trivial change passes through:

1. **Explore** (`/opsx:explore`) — thinking partner mode, no code written.
2. **Propose** (`/opsx:propose`) — scaffolds proposal + design + specs + tasks.
3. **Apply** (`/opsx:apply`) — implements the tasks top-down, marks done.
4. **Archive** (`/opsx:archive`) — moves the change to `openspec/changes/archive/YYYY-MM-DD-<name>/` and syncs delta specs into `openspec/specs/<capability>/spec.md`.

Active changes live under `openspec/changes/`; current capabilities under `openspec/specs/`. Run `openspec list --json` to see what's in flight.

## Validation locally

```sh
python tools/validate-registry.py                                # catalog + 4 kinds + profiles
python tools/validate-manifest.py tests/fixtures/manifests/<...>.yaml
python -m unittest discover -s tests                             # unit tests
```

CI runs all of these on every PR touching `hub/`, `skills/`, `rules/`, `agents/`, `hooks/`, `tools/`, or `tests/`.

## License

MIT — see [LICENSE](LICENSE) if present, otherwise contact the maintainers.
