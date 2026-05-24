*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

## Context

Forge is replacing a vendor-provided skill registry (SkillHub-equivalent) with an in-house, vendor-neutral system targeting ~3,000 developers eventually and a 30-developer pilot first. The skills themselves follow the open Agent Skills standard at `agentskills.io` and are consumed by four AI coding agents in production use across the org: Anthropic Claude Code, GitHub Copilot, OpenAI Codex, and OpenCode. Each agent reads `SKILL.md` bundles from its own filesystem locations — the four agents do not share a single canonical path.

Investigation of the four agent docs (links in the change history) surfaced a key simplification: the four agents converge on a small set of read paths. Three of the four (Copilot, Codex, OpenCode) all read from `.agents/skills/` at project scope and `~/.agents/skills/` at user scope. Copilot and OpenCode additionally read from `.claude/skills/` — the same location Claude Code requires. The minimal union covering all four agents could therefore be just two paths per scope, but the team has chosen a deliberately wider belt-and-braces stance for Copilot: write to every path Copilot's documentation lists, not only the convergence path. That yields **three paths per scope** for the full four-agent default: `.claude/skills/`, `.agents/skills/`, and `.github/skills/` at project scope; `~/.claude/skills/`, `~/.agents/skills/`, and `~/.copilot/skills/` at user scope.

This change delivers the first increment — a cross-platform CLI built on these path destinations and a Git-backed registry — and is deliberately scoped so it can deliver real pilot value before any server-side platform is built.

## Goals / Non-Goals

**Goals:**

- A single statically-linked Go binary that installs spec-compliant Agent Skills to all four target agents on macOS, Linux, and Windows.
- Manifest-driven agent description so adding a new agent (e.g. Gemini CLI, Cursor) requires only a YAML edit.
- Byte-identical bundles across agents: zero per-agent rendering, zero source-of-truth divergence.
- A portability lint that catches Claude-only features inside skills declared `portable: true`, before any file is written.
- Provenance that travels with each install via a sidecar plus a single-line breadcrumb in `SKILL.md`.
- A registry abstraction that hides the Git-vs-HTTP distinction so the later `registry-mvp` change is additive, not breaking.
- Deliverable to a 30-dev pilot in a small number of iterations, without requiring a server, OIDC, RBAC, or web UI.

**Non-Goals:**

- HTTP registry server, Postgres, MinIO — deferred to `registry-mvp`.
- Web UI — deferred to `web-ui`.
- OIDC, RBAC, approval workflow, audit log — deferred to `governance`.
- Write-side commands beyond `install`: `update`, `pin`, `unpin`, `remove`, `provision`, `publish` — all deferred to `installer-write-flows`.
- Full security scan engine (secret scanning, semgrep rules, binary rejection) — only the portability lint lands here; the rest follows in `scan-gate`.
- Cosign-based signing enforcement — the sidecar carries a `signature` field for forward compatibility, but verification is opt-in in this increment.
- Air-gapped mirror bundle / export-import — `ops-readiness`.
- Internationalization of CLI strings — defer until UI work; CLI ships English-only.

## Decisions

### Go for the CLI implementation

**Choice:** Go.

**Why:** A single statically-linked binary is the entire deployment story — no runtime to install on 3,000 dev machines, no GC tuning, no path-of-Python-or-Node ambiguity. `go-yaml`, `go-git`, and the standard library cover every dependency we need. Identical language to whatever the future registry server will use (we will recommend Go for the server too in `registry-mvp`), so all libraries (lint engine, hash function, manifest schema) are sharable between client and server.

**Alternatives considered:**

- **Rust** — equally good static-binary story, smaller binary, stricter compile-time guarantees. Rejected because the team's Go fluency is materially higher, and the binary-size win does not move the needle for an internal CLI.
- **TypeScript + pkg/bun** — bundling is workable but produces 60+ MB binaries and `pkg` is in maintenance mode. Operational footprint outweighs ecosystem benefits.
- **Python** — pyinstaller binaries are large, slow to start, and unreliable on Windows. Easy `no`.

### Cobra + Viper for CLI scaffolding

**Choice:** `spf13/cobra` for command parsing, `spf13/viper` for config.

**Why:** Established, stable, well-trodden. The two libraries integrate cleanly. Most public Go CLIs (`kubectl`, `gh`, `helm`) use Cobra; developers will recognize the conventions.

**Alternatives considered:** `urfave/cli` is fine but Cobra has stronger sub-command ergonomics and richer help generation. `kong` is elegant but less familiar. The cost of choosing differently is small; Cobra wins on familiarity.

### Manifest-driven adapter map (YAML, embedded + override)

**Choice:** A single YAML file embedded into the binary at build time, overridable per-agent by a user file at `~/.config/fdh/adapters.yaml`. Adding a new agent means editing the embedded default in the source tree (a YAML diff) — no Go code change.

**Why:** This is the most direct expression of the vendor-neutrality requirement. The build prompt's "adapter interface" pattern is fine, but in practice every adapter would have the same shape: declare an ID, declare detection probes, declare paths. Lifting that into data and writing one writer that consumes the data is shorter, more auditable, and easier to extend. Per-agent override lets unusual environments (mono-machine special builds, on-prem agent forks) re-point paths without forking the installer.

**Alternatives considered:**

- **One Go file per adapter** — straightforward but adds compile-time friction every time we add an agent. The Agent Skills ecosystem is growing fast (the agentskills.io showcase lists 40+ products); we will be adding adapters frequently.
- **Plugin system (Go plugins, WASM)** — overkill for what is essentially a path map and a few exec probes.

### `go-git` for the GitRegistry backend, with `git` shell-out as the fallback for fetch

**Choice:** Use `go-git` (`github.com/go-git/go-git/v5`) for all read operations (clone, fetch, checkout, walk). Shell out to the system `git` only if a credential-dependent operation fails and the system `git` is available — this preserves the user's existing Git credential setup (helper, SSH keys, Kerberos).

**Why:** `go-git` keeps the static-binary promise (no required runtime `git`), is correct for read paths, and is faster on small repos. The shell-out fallback is purely for credentialed corporate-network edge cases where `go-git`'s HTTPS/SSH auth implementations lag behind the system's credential helpers. For the pilot a clean read-only HTTPS clone of a shared registry repo will work fine with `go-git` alone; the fallback is insurance, not the primary path.

**Alternatives considered:**

- **Always shell out to `git`** — relies on a runtime dependency we promised to avoid, complicates Windows testing.
- **`go-git` only with no fallback** — would block deployment behind whatever auth method fails in someone's corporate environment. The fallback is small insurance.

### Canonical bundle hash: SHA-256 over a normalized tree manifest

**Choice:** The bundle's canonical hash is the SHA-256 of a deterministic "tree manifest" computed as follows:

1. Walk the bundle directory.
2. List every file with a path relative to the bundle root, using forward slashes regardless of OS.
3. Sort the file list lexicographically.
4. For each file, emit a line: `<mode> <sha256-of-content> <relpath>\n`, where `<mode>` is `100644` for regular files and `100755` for executable regular files (Unix `x` bit set). On Windows, `<mode>` is read from the bundle's source (the registry side records it during publish); the installer does not infer mode from the Windows filesystem.
5. Concatenate the lines into a single byte string. The bundle hash is the SHA-256 of that string in lowercase hex.

**Why:** This is the Git-tree-hash idea simplified — deterministic across OSes, reproducible, and not dependent on tar / zip determinism (both of which are notoriously fiddly across platforms). It also lets the registry record file modes independently of whatever filesystem holds the bundle.

**Alternatives considered:**

- **Hash `bundle.tar.gz` directly** — depends on tar implementation (file ordering, sticky timestamps, gzip headers). Reproducible-tar tooling exists but is one more thing to get right.
- **Git tree SHA** — appealing because the registry IS a Git repo, but it locks us to SHA-1 (Git default) and makes the hash dependent on Git's internal hashing rather than a hash we control. SHA-1 is also weakening; explicit SHA-256 is more durable.

### Fan-out write across the path-set union

**Choice:** Every install writes the bundle to each path in the union of paths declared by the target agents at the chosen scope. For the full four-agent default with the belt-and-braces Copilot stance, the project-scope union is `.claude/skills/<name>/`, `.agents/skills/<name>/`, and `.github/skills/<name>/`; the user-scope union is `~/.claude/skills/<name>/`, `~/.agents/skills/<name>/`, and `~/.copilot/skills/<name>/`. Each bundle copy gets its own `.skill-meta.yaml` sidecar.

**Why:** Writing to every documented path is the union of what the four target agents read (verified against each agent's official docs). The cost is two extra copies of typically-tiny markdown files. The benefit is zero cross-platform symlink complexity (Windows symlinks require admin or Developer Mode; junction points and reparse points are flaky for our needs), zero installer-side concept of "the linked source path" — every install is self-contained — and resilience against any one agent quietly changing which of its documented paths it actually reads.

**Alternatives considered:**

- **Symlink `.claude/skills/` → `.agents/skills/` (or vice versa)** — Windows kills this approach.
- **Hardlink per-file** — directories themselves can't be hardlinked; we'd be hardlinking the contents only, which is more complex than copy and saves no meaningful disk on text-only skills.
- **Single canonical location + per-agent config override** — requires reaching into each agent's config to redirect its skill read path, which several of the four agents do not support at all.

The 2x-disk cost on text-only bundles is negligible. If `assets/` grows to include large binaries the math changes — but binaries in bundles are already discouraged (and will be policy-restricted in `scan-gate`).

### Provenance: sidecar + single-line frontmatter breadcrumb

**Choice:** Rich provenance lives in `.skill-meta.yaml` next to each installed `SKILL.md`. A single line is injected into `SKILL.md`'s frontmatter: `installed_from: <registry>/<namespace>/<name>@<version>`. Nothing else is added or modified.

**Why:** Splits the concerns. The sidecar carries everything we want to query (hash, agents, scope, installer version, timestamps, signature) and can grow over time without touching `SKILL.md`. The breadcrumb is the "if someone copies this file elsewhere with a plain `cp`, can I trace where it came from?" property — one line, easy to read, registry-routable. The canonical content hash is computed pre-injection so the breadcrumb does not destabilize the hash chain.

**Alternatives considered:**

- **Everything in frontmatter** — installs would modify `SKILL.md` with ~10 lines. Bigger blast radius if anything goes wrong; hash-stability requires either pre-injection hashing (same as now) or a complicated "exclude these keys" hash. Provenance grows over time; frontmatter shouldn't.
- **Sidecar only, no breadcrumb** — a plain `cp` of `SKILL.md` elsewhere loses all traceability. The single line buys back that property cheaply.

### Portability lint as a library, called from install (and later from publish + CI)

**Choice:** The lint is a Go package (`pkg/portability`) with a single entry point: `func Lint(bundle Bundle) []Finding`. The CLI's `install` command calls it pre-write; later changes (`installer-write-flows` for `publish`, `scan-gate` for the broader engine, CI workflows) will call the same function.

**Why:** Single source of truth for "is this skill portable?". The build prompt explicitly asks for the same scan engine in both publish-time and registry-time gates; this is the same idea narrowed to just the portability subset for this increment.

**Alternatives considered:**

- **Lint as a binary plugin** — overkill; library is fine.
- **Inline the rules in the install command** — guarantees drift the moment a second caller appears.

### Cross-platform: `path/filepath` everywhere, never `path`

**Choice:** All filesystem path manipulation uses `path/filepath` (the OS-aware variant). The `path` package is reserved for URL-style references inside the registry (which always use forward slashes). Executable bits are handled in code paths that explicitly test for the bit and degrade gracefully on Windows (no error, no warning — the bit simply isn't applicable). Line endings are preserved byte-identically; the installer never normalizes LF↔CRLF.

**Why:** Boring, durable, hits every Go-on-Windows gotcha at the source. The line-endings rule is critical: the canonical bundle hash is computed over file bytes, so any silent normalization would make the hash mismatch on platforms where the silent normalization happens.

### Test matrix: macOS, Linux, Windows — all three required in CI

**Choice:** GitHub Actions matrix builds against `macos-latest`, `ubuntu-latest`, `windows-latest`. Every PR must pass all three. Integration tests use a local filesystem registry rooted in a temp directory and four "mock agent dirs" — empty directories matching the adapter map's path declarations — so the install path is exercised end-to-end without depending on real agent binaries.

**Why:** Windows is the path that finds most bugs; making it a first-class CI target catches them at PR time, not at pilot rollout.

### Installer source tree and distribution channel

**Choice:** The installer lives in its own dedicated repository (e.g. `forge/skill-installer`) at Forge's Git host — separate from this OpenSpec hub. The specs that govern it live here under `openspec/changes/installer-core/` and, after archive, under `openspec/specs/`. Built binaries are published to Forge's internal package manager (Nexus, JFrog Artifactory, or GitHub Packages — final hosting choice is an ops decision) as standard tar.gz artifacts with adjacent SHA-256 checksum files. For the pilot, binaries ship unsigned; pilot devs verify the checksum after download. Code signing is deferred to the `ops-readiness` change.

**Why:** A separate repo for the implementation keeps the OpenSpec hub focused on workflow and spec authority while letting the installer have its own CI, release cadence, issue tracker, and access controls. The private-package-manager distribution path matches how Forge distributes its internal tooling today; it avoids a public Homebrew tap and removes the need to manage an apt/yum repo for the pilot. tar.gz + SHA-256 is the lowest-friction artifact shape every major package manager (Nexus raw repo, JFrog Generic, GitHub Packages release assets) can host without per-product packaging work. Signing is real work — keys, attestation, supply-chain — and is correctly scoped to `ops-readiness` rather than blocking pilot.

**Alternatives considered:**

- **`/installer` inside this hub repo** — keeps everything in one place but conflates spec authority with implementation, gives both audiences (OpenSpec users vs CLI users) the same issue tracker, and forces the same access policy on both. Rejected.
- **Public Homebrew tap + apt/yum repo + Winget** — the build prompt's original distribution shape. Right destination eventually; wrong shape for a 30-dev internal pilot where every channel is friction to set up.
- **Signed pilot binaries from day one** — correct for production. For a 30-dev internal pilot with checksum verification documented in the quickstart, unsigned is materially simpler and the residual risk is acceptable.

## Risks / Trade-offs

- **Risk: The portability lint over-rejects (false positives) and frustrates authors.** Specifically, a portable skill that quotes `$ARGUMENTS` inside a fenced text/markdown block (e.g. documenting how a Claude-only skill works) trips the lint. → **Mitigation:** the lint message must be precise (file, line, exact rule) and the docs must explicitly cover this case. The conservative "if the token appears, fail" position is intentional for v1; if pilot feedback shows real friction, we add an explicit `# lint-ignore: $ARGUMENTS` opt-out comment in a later change.

- **Risk: `go-git` auth fails in Forge's corporate network environment.** Internal HTTPS may use proxies or cert pinning that `go-git` does not handle as gracefully as the system `git`. → **Mitigation:** the system-`git` fallback for fetch operations covers this. Pilot's first integration step is verifying `go-git` against the actual corporate Git host; if it works, no fallback is needed in practice.

- **Risk: Windows path-length limits (260 chars) bite for deeply nested skills.** A skill like `~/.agents/skills/security/dependency-cve-advisor/references/owasp-top-ten-2023/long-filename.md` can hit the limit. → **Mitigation:** the integration test suite includes a "long-path" case. The installer emits a clear error pointing the user at the Windows long-path setting (registry key + manifest opt-in) rather than failing cryptically.

- **Risk: Three-path fan-out triples disk for skills with large `assets/`.** A skill with 100MB of templates would consume 300MB. → **Mitigation:** the policy direction (which lands fully in `scan-gate`) is that binaries are disallowed and `assets/` is text-only. The bundle-format spec is already designed for this; this risk only materializes if policy is violated.

- **Risk: The registry-as-Git-repo model strains at scale beyond the pilot.** Cloning a 5,000-skill registry over Git is slow on a fresh machine. → **Mitigation:** explicitly accepted for the pilot. The `registry-mvp` change introduces an HTTP server with paged search and resolution; the `Registry` interface in this change is designed for that substitution.

- **Risk: Adapter map drift from upstream agent docs.** If Claude Code, Copilot, Codex, or OpenCode changes its read paths, our embedded default goes stale. → **Mitigation:** the embedded default is loud about its provenance (each agent entry carries a `source_doc_url:` field and a `verified_on:` date). A CI job in a later change can re-fetch these and diff.

- **Trade-off: `portable` default is `true`.** This means a Claude-only skill author has to remember to set `portable: false`. The error message when they forget is precise (lint identifies the offending key/token) and exit code 4 is unambiguous. The reverse default (`portable: false` by default) would frustrate the majority of seed skills (which are portable) for the sake of catching a minority case where the lint already catches the violation anyway.

## Migration Plan

This change is greenfield — there is nothing to migrate **from**. The pilot rollout plan, however, is:

1. **Internal review and approval of this change's artifacts** before any code is written.
2. **Implement and ship the installer-core binary** to the 30-pilot devs via Forge's internal package manager (Nexus / JFrog / GitHub Packages — selection made by the ops team). For every release, the build pipeline produces five tar.gz archives (one per platform), each with a sibling SHA-256 checksum file, all published to the same versioned path in the package manager. Pilot devs download the archive for their platform, verify the checksum per the quickstart, and place the binary on `PATH`. macOS Homebrew tap, Linux apt/yum repo, and Windows MSI / Winget are deferred to `ops-readiness`.
3. **Provision a shared `skill-registry` Git repository** (location TBD by platform team; Forge's internal GitLab or GitHub Enterprise instance, either is fine — the registry is host-agnostic by design). Seed it with 2–3 portable skills (the `seed-skills` change) so the pilot has something to install.
4. **Pilot devs run `fdh doctor`** on a fresh checkout to verify the installer detects their installed agents and finds the registry.
5. **Pilot devs run `fdh install <skill>`** for one of the seed skills and verify that the skill appears in all detected agents' UIs.
6. **Collect feedback for one to two weeks** before starting `installer-write-flows` (which adds `update`, `pin`, `remove`, `provision`, and `publish`).

**Rollback:** the installer writes only to known, scoped paths (`~/.claude/skills/`, `~/.agents/skills/`, `.claude/skills/`, `.agents/skills/`). A pilot dev who wants to roll back removes the installed skill directories and uninstalls the binary; nothing else on their machine is touched. There is no system-level state, no daemon, no PATH manipulation, no registry write.

## Open Questions

All four open questions raised in earlier drafts have been resolved by the team. They are recorded here for the change history; see the corresponding Decision section above for the codified outcome.

- **Q1. Installer source tree location.** *Resolved:* dedicated repository (e.g. `forge/skill-installer`) at Forge's Git host; binaries distributed via an internal package manager (Nexus / JFrog / GitHub Packages — final hosting selection by ops). See decision "Installer source tree and distribution channel" above.

- **Q2. Code-signing for pilot binaries.** *Resolved:* the pilot ships unsigned binaries paired with SHA-256 checksum files. Pilot devs verify the checksum after download per the quickstart. Code signing is in scope for the `ops-readiness` change, not for this one.

- **Q3. Copilot path coverage — convergence-only vs belt-and-braces.** *Resolved:* belt-and-braces. The adapter map writes to every documented Copilot path: `~/.copilot/skills/` and `~/.agents/skills/` at user scope; `.github/skills/`, `.claude/skills/`, and `.agents/skills/` at project scope. The full four-agent default thus writes to three paths per scope (not two). See `agent-adapter-map/spec.md` for the codified manifest and updated path-union scenarios.

- **Q4. Default `--scope`.** *Resolved:* the spec's "project when a `.git/` directory is detected at or above the working directory, otherwise user" default stands. Skills are typically project-coupled in dev workflows; the explicit `--scope user` flag remains available when a developer wants the install in their home directory regardless of context.
