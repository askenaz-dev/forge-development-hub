*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

## Why

Forge's ~3,000 developers use a mix of AI coding agents (Claude Code, GitHub Copilot, OpenAI Codex, OpenCode) and need a governed, vendor-neutral way to share procedural knowledge as Agent Skills (the open `agentskills.io` standard). Third-party skill registries create vendor lock-in we cannot accept. We need to prove the core distribution rail — a cross-platform CLI that installs spec-compliant skills into the correct location for every supported agent — works end-to-end with a real 30-developer pilot **before** investing in a registry server, web UI, or governance plane. This change delivers that rail; later changes layer the server-side platform on top of the same interfaces.

## What Changes

- Add a new Go-based CLI (`fdh`, working name) shipped as a single statically-linked binary for macOS (arm64/amd64), Linux (arm64/amd64), and Windows (amd64).
- Define a canonical skill bundle layout that is byte-identical across all four agents and strictly conformant to the open Agent Skills specification (`SKILL.md` + optional `scripts/`, `references/`, `assets/`).
- Introduce a **manifest-driven agent adapter map** (YAML, embedded in the binary, overridable at `~/.config/fdh/adapters.yaml`) that declares each agent's read paths. Adding a new agent is a config change, not a code change.
- Implement **fan-out installation**: the same byte-identical bundle is copied to every path in the union declared by the target agents at the chosen scope. For the full four-agent default this is three paths per scope — project: `.claude/skills/<name>/`, `.agents/skills/<name>/`, `.github/skills/<name>/`; user: `~/.claude/skills/<name>/`, `~/.agents/skills/<name>/`, `~/.copilot/skills/<name>/`. No symlinks. The fan-out is the union of every documented read path across the target agents (belt-and-braces stance for Copilot's three documented locations).
- Introduce **portability classes** for skills: `portable: true` (the default; restricted to the agentskills.io intersection — `name`, `description`, optional `license`/`metadata`/`compatibility`) installs to all four agents; `portable: false` skills declare a `compatibility:` allowlist and the installer refuses to write them to agents outside that list. A portability lint enforces these rules at install time.
- Introduce **provenance tracking**: a `.skill-meta.yaml` sidecar next to each installed `SKILL.md` carries rich provenance (registry URL, namespace, version, content hash, installed-by, install timestamp, target agents). A single `installed_from:` line is also injected into the `SKILL.md` frontmatter as a breadcrumb. The bundle's canonical content hash is computed **before** breadcrumb injection so the source-of-truth hash is stable across installs.
- Define a `Registry` interface in Go with a `GitRegistry` implementation that reads a shared Git repository laid out as the spec-compliant registry described in `design.md`. The interface is designed so a future `HTTPRegistry` implementation can replace it without changes to call sites.
- Ship five CLI commands in this increment: `install`, `list`, `doctor`, `search`, `config`. All produce a human table by default and structured JSON via `--json`.
- All commands and the adapter map must pass tests on macOS, Linux, and Windows in CI from day one.

## Capabilities

### New Capabilities

- `skill-installer-cli`: The cross-platform command-line interface — command surface, argument shape, output formats (table + JSON), exit codes, and the cross-platform behavior contract for path handling, executable bits, and line endings.
- `agent-adapter-map`: The manifest-driven description of each supported AI coding agent — name, detection probes, the user-scope and project-scope read paths it consumes, and the doctor checks that validate those paths at runtime.
- `skill-bundle-and-registry`: The on-disk shape of a skill bundle (spec-compliant) and of a registry (Git-backed for this increment; the interface is registry-agnostic). Includes content-addressing rules, the `index.json` and `manifest.json` envelopes, and version directory layout.
- `skill-portability`: The two skill classes (`portable: true` / `portable: false`), the `compatibility` allowlist, the lint rules that distinguish them, and the installer's behavior when a non-portable skill targets an incompatible agent.
- `skill-provenance`: The `.skill-meta.yaml` sidecar schema, the `installed_from:` frontmatter breadcrumb, the rule that the canonical content hash is computed pre-injection, and how `list` reads provenance back to display installed-skill state.

### Modified Capabilities

None. This is the first capability-bearing change in the project.

## Impact

- **New code**: a fresh dedicated `forge/skill-installer` repository (separate from this OpenSpec hub) containing the Go CLI, adapter manifest, and a unit-plus-integration test suite covering all three target operating systems. The OpenSpec hub continues to hold the specs of record.

- **New distribution channel**: release artifacts (tar.gz per platform with adjacent SHA-256 checksum files) published to Forge's internal package manager (Nexus / JFrog / GitHub Packages — final hosting selection by ops).
- **New artifact**: a separate skill registry Git repository — provisioning is out of scope for this change but the layout it must follow is specified here. The pilot team will create and seed it.
- **CI/CD**: a GitHub Actions workflow (portable to other CI systems) that builds, tests, and produces signed release binaries for the three OS / four architecture combinations.
- **Pilot rollout**: targets 30 developers; install flow uses a shared Git clone of the registry, not a remote server. Bandwidth and operational impact are negligible.
- **No backwards-compatibility concerns**: this is a net-new system. No existing tools, paths, or workflows are modified.
- **Sets up future changes**: `installer-write-flows` (update / pin / remove / provision / publish), `registry-mvp` (HTTP server, Postgres, MinIO), `scan-gate` (full security scan engine — schema + secret + semgrep + binary rejection), `governance` (OIDC, RBAC, approval workflow, audit log), `web-ui`, and `ops-readiness` will all build on the interfaces introduced here. No breaking changes are anticipated; later increments extend the specs introduced now.
