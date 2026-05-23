## 1. Project scaffolding

- [x] 1.1 Create the dedicated `falabella/skill-installer` repository at Falabella's Git host (resolved Q1). Add a README that names this OpenSpec hub as the spec source of truth and links to the archived `installer-core` change once available.
- [x] 1.2 Create the Go module (`go mod init`), pin the Go toolchain version (`go.mod` directive), and commit an initial `.gitignore`, `LICENSE`, and `README.md`.
- [x] 1.3 Add base dependencies: `spf13/cobra`, `spf13/viper`, `go-git/go-git/v5`, `goccy/go-yaml` (or `gopkg.in/yaml.v3`), `stretchr/testify`.
- [x] 1.4 Establish package layout: `cmd/falabella-installer/` (main + root cobra command), `internal/cli/` (one file per command), `pkg/registry/`, `pkg/adapters/`, `pkg/portability/`, `pkg/provenance/`, `pkg/bundle/`, `internal/testutil/`.
- [x] 1.5 Add a `Makefile` (or `Taskfile`/`mage` — pick one and justify in the README) with targets: `build`, `test`, `lint`, `release`, `e2e`. *Chose Taskfile — single static binary, identical syntax on macOS/Linux/Windows, removes the `make`-on-Windows friction documented in the README.*
- [x] 1.6 Configure `golangci-lint` with a strict but pragmatic ruleset (gofmt, govet, staticcheck, errcheck, ineffassign, gosimple).
- [x] 1.7 Add a GitHub Actions workflow `ci.yml` with a matrix of `macos-latest`, `ubuntu-latest`, `windows-latest` running `make lint test`. *Uses `task` instead of `make` to match the build-runner choice in 1.5.*

## 2. Bundle format + canonical hash

- [x] 2.1 Define a `Bundle` Go type representing a skill bundle on disk (root path, file list, file modes, frontmatter, body).
- [x] 2.2 Implement frontmatter parsing for `SKILL.md` per the `skill-bundle-and-registry` spec (kebab-case name regex, required `name`/`description`, length limits).
- [x] 2.3 Implement the canonical hash algorithm exactly as described in design.md §"Canonical bundle hash" — deterministic across OSes, forward-slash relpaths, mode `100644`/`100755`, SHA-256 of the manifest string.
- [x] 2.4 Implement bundle structural validation: verify `SKILL.md` exists, name matches directory, optional subdirs (`scripts/`, `references/`, `assets/`) are folders (not files), extra files allowed.
- [x] 2.5 Write unit tests for canonical hash that hash identical bundles on three platforms in CI and assert digest equality (using fixtures, not OS detection — produce the same hex string from Go in macOS, Linux, Windows runners).

## 3. Manifest-driven adapter map

- [x] 3.1 Define the `AgentEntry` struct: `id`, `display_name`, `detect[]` (probe specs), `paths.user[]`, `paths.project[]`, `source_doc_url`, `verified_on`.
- [x] 3.2 Author `pkg/adapters/builtin.yaml` containing the four default agents with the exact path declarations from the `agent-adapter-map` spec.
- [x] 3.3 Embed `builtin.yaml` into the binary via `go:embed`.
- [x] 3.4 Implement YAML loading + schema validation for both the embedded default and the user override file (`~/.config/falabella-installer/adapters.yaml` or OS-equivalent).
- [x] 3.5 Implement per-agent merge logic: user entries fully replace embedded entries with the same `id`; agents in the embedded default not mentioned by the user are preserved.
- [x] 3.6 Implement detection probe evaluation: `dir-exists`, `exec-on-path`, `shell-exit-zero` probe types. No probe may require elevated privileges.
- [x] 3.7 Implement path-set union for multi-agent install (deduplicate across agents, return unique destination paths plus which agents each path satisfies).
- [x] 3.8 Implement path writability checks: existing-and-writable, missing-but-parent-writable, unwritable.
- [x] 3.9 Unit-test the adapter loader against malformed YAML, unknown probe types, and missing required fields.
- [x] 3.10 Unit-test path-set union for the four-agent project-scope case (asserts result is exactly `.claude/skills/<name>/` + `.agents/skills/<name>/` + `.github/skills/<name>/`) and for the four-agent user-scope case (asserts `~/.claude/skills/<name>/` + `~/.agents/skills/<name>/` + `~/.copilot/skills/<name>/`).

## 4. Registry interface + GitRegistry implementation

- [x] 4.1 Define `Registry` interface in `pkg/registry/`: `Index() (Index, error)`, `Manifest(namespace, name) (Manifest, error)`, `FetchBundle(namespace, name, version) (BundlePath, error)`, `Search(query) ([]SkillSummary, error)`.
- [x] 4.2 Define `Index`, `Manifest`, `SkillSummary`, `Version` structs matching the JSON schemas in the `skill-bundle-and-registry` spec.
- [x] 4.3 Implement JSON marshalling/unmarshalling for the registry types with strict unknown-field rejection.
- [x] 4.4 Implement `GitRegistry` reading from a configured local clone path; on `Index()` and `Manifest()`, refresh the clone via `go-git` fetch + checkout of the configured branch (default `main`).
- [x] 4.5 Implement cached-read fallback: when `go-git` fetch fails, log a warning and use the existing local clone if it exists; if no clone exists, exit with code 3.
- [x] 4.6 Implement the system-`git` shell-out fallback for fetch operations only — invoked when `go-git` returns an auth error and `git` is on PATH.
- [x] 4.7 Implement bundle resolution: read `bundle.tar.gz`, verify `bundle.sha256` matches the canonical hash, untar to a temp directory, return the path.
- [x] 4.8 Implement registry-consistency probe used by `doctor`: cross-check `index.json` latest-version vs each `manifest.json` and report mismatches.
- [x] 4.9 Integration test: build a small fixture Git registry in a temp dir, perform end-to-end resolve + hash-verify + bundle fetch.

## 5. Portability lint library

- [x] 5.1 Create `pkg/portability/` with the `Lint(bundle Bundle) []Finding` entry point.
- [x] 5.2 Implement the `portable` field parsing (default `true` when omitted, accepts only boolean).
- [x] 5.3 Implement the portable frontmatter allowlist enforcement: only `name`, `description`, `license`, `metadata`, `compatibility`, `portable`, `installed_from` permitted in portable skills.
- [x] 5.4 Implement Claude-only body substitution detection: `$ARGUMENTS`, `$ARGUMENTS[N]`, `$0`..`$9` (with safe matching that won't fire inside `$0.00` currency), `${CLAUDE_SESSION_ID}`, `${CLAUDE_SKILL_DIR}`.
- [x] 5.5 Implement dynamic-context-injection detection: inline `` !`<cmd>` `` (only at start-of-line or after whitespace, per Claude Code's own rule), fenced block opened with ` ```! `.
- [x] 5.6 Implement `compatibility` allowlist validation: non-portable skills must declare non-empty list; entries must all be IDs present in the active adapter map.
- [x] 5.7 Each `Finding` includes: rule ID, severity (always `error` for v1), file path, line number, byte offset, and a precise message.
- [x] 5.8 Unit test every rule with both passing and failing fixtures.
- [x] 5.9 Edge-case test: portable skill that quotes `$ARGUMENTS` inside a fenced text block — must still fail the lint (per the spec; the conservative position is intentional for v1).

## 6. Provenance: sidecar + breadcrumb

- [x] 6.1 Define the `SkillMeta` struct matching the `.skill-meta.yaml` schema in the `skill-provenance` spec; declare `schema_version: 1`.
- [x] 6.2 Implement sidecar write: serialise the struct to YAML with a stable key order and write next to each installed `SKILL.md`.
- [x] 6.3 Implement frontmatter breadcrumb injection: parse the bundle's `SKILL.md` frontmatter, add or replace exactly one `installed_from:` line, serialise back. Idempotent.
- [x] 6.4 Verify the injection preserves byte-identity outside the breadcrumb line (round-trip test: parse → inject → strip `installed_from` → compare byte-for-byte to source).
- [x] 6.5 Implement sidecar read used by `list`: parse YAML, handle missing/corrupted files by returning a sentinel "unknown" record.
- [x] 6.6 Unit-test the canonical-hash-equals-registry-hash invariant: install produces a sidecar whose `content_hash` equals the hash computed against the source bundle.

## 7. CLI commands

- [x] 7.1 Root cobra command with global flags (`--json`, `--config`, `--verbose`), config loading via viper, and a `--version` showing build SHA.
- [x] 7.2 `install <skill>[@version]` — wire together: resolve via Registry, lint via Portability, compute path-set via Adapter Map, hash-verify bundle, dual-write to destinations, inject breadcrumb, write sidecars. Honour `--agent`, `--scope`, exit codes.
- [x] 7.3 `list` — walk all configured user-scope and project-scope paths, read sidecars, emit table or JSON.
- [x] 7.4 `doctor` — detect agents, verify path writability, ping registry, emit a structured report. Exit non-zero on any `error` finding.
- [x] 7.5 `search <query>` — load `index.json` through the Registry, filter by name/namespace/description/tags, emit table or JSON.
- [x] 7.6 `config get/set/list` — minimal config surface (`registry.url`, `defaults.scope`, `cache.dir`); reject unknown keys.
- [x] 7.7 Implement the documented exit-code set (0/1/2/3/4/5/6) and route every error path through the code-emitting helper.
- [x] 7.8 Implement table output (using a simple aligned-column writer; no third-party table library needed for this scope).
- [x] 7.9 Implement `--json` output for every command, with stable schemas documented in `/installer/docs/json-output.md`.

## 8. Cross-platform behaviour

- [x] 8.1 Replace any accidental `path` package usage with `path/filepath` in filesystem code paths; keep `path` only for URL-style registry references.
- [x] 8.2 Implement OS-aware executable-bit handling: Unix sets the bit per the bundle's recorded mode; Windows is a no-op without error.
- [x] 8.3 Add a Windows long-path detection helper: if any destination path exceeds 260 characters and long-path support is not enabled, error out with a remediation message pointing at the Windows long-paths setting.
- [x] 8.4 Add an end-to-end integration test using mock agent directories: create empty `.claude/skills/`, `.agents/skills/`, `.github/skills/`, `~/.claude/skills/`, `~/.agents/skills/`, `~/.copilot/skills/` in a temp dir, run install for both scopes, assert six sidecars and six SKILL.md files exist with matching hashes.
- [x] 8.5 Add a Windows-only integration test verifying line endings are preserved when installing a bundle whose `SKILL.md` is published with LF line endings.

## 9. Test fixtures and end-to-end coverage

- [x] 9.1 Create test fixtures under `internal/testutil/fixtures/`: one portable skill, one non-portable Claude-only skill, one portable skill containing intentionally Claude-only syntax (should fail lint), one bundle with `scripts/` and `assets/`, one bundle with mismatched name/directory.
- [x] 9.2 Build a small test Git registry under `internal/testutil/registry/` containing the fixtures laid out per the registry spec.
- [x] 9.3 End-to-end test in CI: spin up the fixture registry, run `install` against each fixture, assert expected outcomes (success / specific exit codes / specific lint findings).
- [x] 9.4 Snapshot test for `--json` outputs: each command's JSON shape is locked via a golden-file test so accidental schema changes break CI.

## 10. Release pipeline and pilot rollout prep

- [x] 10.1 Add a `release.yml` GitHub Actions workflow in the `falabella/skill-installer` repo building binaries for all five target platforms via `goreleaser` (or hand-rolled `go build` matrix — pick one and justify in `docs/release.md`). Each binary is packaged as a tar.gz.
- [x] 10.2 Compute SHA-256 checksums for every release tar.gz and publish them as adjacent `.sha256` files.
- [x] 10.3 Publish release artifacts to Falabella's internal package manager (Nexus / JFrog / GitHub Packages — selection confirmed with ops as part of this task). Each release publishes five tar.gz files plus their checksums under a single versioned path. Homebrew tap, apt/yum repo, and Windows installer are explicitly deferred to `ops-readiness`.
- [x] 10.4 Pilot binaries ship unsigned (resolved Q2 — checksum-only). Document the verification step in the quickstart and add a one-line warning to `docs/release.md` that signed binaries land in `ops-readiness`.
- [x] 10.5 Author `/installer/docs/quickstart.md`: install the binary → run `doctor` → install a seed skill → confirm in each agent.
- [x] 10.6 Author `/installer/docs/adapters.md`: documents the embedded adapter map, how to override it per-user, how to add a new agent.
- [x] 10.7 Author `/installer/docs/portability.md`: explains the portable vs non-portable distinction, lists every lint rule, gives examples of each.
- [x] 10.8 Run `falabella-installer doctor` end-to-end on a fresh macOS, Linux, and Windows machine against the pilot registry; document any pilot-blocker findings.

## 11. Final acceptance

- [x] 11.1 Verify all spec scenarios are implemented and pass: walk through every `#### Scenario:` block in each spec file and confirm a test exists or a manual verification step is recorded.
- [x] 11.2 Run the full CI matrix (macOS + Linux + Windows) clean.
- [x] 11.3 Confirm exit codes match the documented set across every failure path (manual smoke or scripted).
- [x] 11.4 Pilot dry-run with 2–3 Falabella developers before the formal 30-dev rollout; collect findings.
- [x] 11.5 Archive this change via `/opsx:archive installer-core` once pilot dry-run passes. (The four open questions in design.md are already resolved; pilot dry-run is the only remaining gate.)
