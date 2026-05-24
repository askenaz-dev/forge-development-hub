*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

## ADDED Requirements

### Requirement: Spec-compliant bundle layout

A skill bundle SHALL conform to the Agent Skills open specification (`agentskills.io`): a directory containing a required `SKILL.md` file at its root and any of the optional subdirectories `scripts/`, `references/`, `assets/`. Additional files and subdirectories MAY exist. The bundle layout MUST be byte-identical across every agent it targets — the system MUST NOT perform per-agent rendering.

#### Scenario: Minimal bundle with only SKILL.md is valid

- **WHEN** a bundle contains exactly one file, `SKILL.md`, with valid frontmatter
- **THEN** the registry accepts the bundle and the installer can install it

#### Scenario: Bundle with optional subdirectories preserved on install

- **WHEN** a bundle contains `SKILL.md`, `scripts/run.sh`, `references/api.md`, and `assets/template.txt`
- **THEN** the installer writes all four files to each destination path with their original relative structure intact

### Requirement: SKILL.md frontmatter validation

Every `SKILL.md` in a bundle SHALL begin with YAML frontmatter delimited by `---` markers. The frontmatter MUST include `name` (string, lowercase kebab-case, 1–64 characters, matching the regex `^[a-z0-9]+(-[a-z0-9]+)*$`) and `description` (string, 1–1024 characters). The `name` field MUST match the bundle's directory name in the registry.

#### Scenario: Valid frontmatter accepted

- **WHEN** a `SKILL.md` declares `name: code-review-standard` and a non-empty description, and the bundle directory is also named `code-review-standard`
- **THEN** validation passes

#### Scenario: Missing required field rejected

- **WHEN** a `SKILL.md` is missing the `description` field
- **THEN** the publish-side validator and the install-side lint both reject the bundle with a message naming the missing field

#### Scenario: Name does not match directory rejected

- **WHEN** a bundle directory is named `code-review-standard` but `SKILL.md` declares `name: code-review`
- **THEN** validation rejects the bundle with a message citing the mismatch

### Requirement: Content-addressed bundle hashing

Every bundle SHALL have a canonical SHA-256 content hash computed over its tree. The hashing algorithm MUST be deterministic across operating systems and MUST be specified precisely enough that two independent implementations produce identical hashes for the same input. The hash MUST be computed over the source bundle BEFORE any install-time modification (notably before the `installed_from:` breadcrumb is injected).

#### Scenario: Same bundle hashes identically on all OSes

- **WHEN** the same bundle is hashed on macOS, Linux, and Windows
- **THEN** all three implementations produce the identical SHA-256 hex digest

#### Scenario: Sidecar hash equals registry hash

- **WHEN** a bundle published with hash `abc123…` is installed on a developer's machine
- **THEN** the `content_hash` field in the `.skill-meta.yaml` sidecar equals `abc123…`, matching the registry's recorded hash exactly

### Requirement: Registry filesystem layout

A registry SHALL be organized so that any conforming `Registry` implementation can discover skills, versions, and bundles deterministically. The layout MUST be:

```
<registry-root>/
├── index.json
├── skills/
│   └── <namespace>/<name>/
│       ├── manifest.json
│       ├── versions/
│       │   └── <semver>/
│       │       ├── bundle/                  # spec-compliant skill directory
│       │       ├── bundle.tar.gz            # archive of bundle/
│       │       ├── bundle.sha256            # canonical hash
│       │       ├── bundle.sig               # optional cosign signature
│       │       ├── scan-report.json
│       │       └── changelog.md
│       └── README.md
└── lockfile.json                            # optional, reserved for reproducible installs
```

#### Scenario: Resolver finds a published version

- **WHEN** a Git registry contains `skills/code-review/standard/versions/1.0.0/bundle.tar.gz` and `index.json` lists `code-review/standard@1.0.0` as the latest version
- **THEN** `fdh install code-review/standard` resolves to that bundle

#### Scenario: Missing bundle.sha256 fails resolution

- **WHEN** a version directory contains `bundle.tar.gz` but not `bundle.sha256`
- **THEN** the registry resolution exits non-zero with a message identifying the missing file

### Requirement: index.json structure

The registry root SHALL contain an `index.json` file that lists every published skill with its namespace, name, latest version, content hash for that latest version, scan-status flag, owner team, description, and tags. The index MUST be regenerable from `manifest.json` files; if the two disagree, `manifest.json` is authoritative.

#### Scenario: Search uses index.json

- **WHEN** a developer runs `fdh search` against a Git registry
- **THEN** the search reads `index.json` and does not need to walk every `manifest.json` to produce results

#### Scenario: Index and manifest disagreement detected

- **WHEN** `index.json` lists `code-review/standard@1.0.0` but the version's `manifest.json` lists the latest as `1.1.0`
- **THEN** `doctor` reports a registry-consistency warning naming the affected skill

### Requirement: manifest.json structure

Each skill folder under `skills/<namespace>/<name>/` SHALL contain a `manifest.json` declaring: namespace, name, description, owner team, available versions (each with semver, content hash, publish timestamp, optional signature pointer, and scan status), tags, and the version currently considered `latest`. Once a version entry is published, the entry SHALL be immutable; only the `latest` pointer and new version entries MAY change.

#### Scenario: New version appended without rewriting history

- **WHEN** a new version `1.1.0` is published for an existing skill
- **THEN** `manifest.json` gains a new version entry and updates `latest`; existing version entries remain byte-identical

#### Scenario: Mutating a published version detected

- **WHEN** `manifest.json` shows a version's content hash differs from the actual `bundle.sha256` on disk
- **THEN** `install` for that version exits non-zero with an integrity-violation error and does not write any files

### Requirement: Semver-based versioning, immutable once published

Versions SHALL use semantic versioning (`MAJOR.MINOR.PATCH`). Pre-release and build metadata suffixes (e.g. `-rc.1`, `+build.42`) are permitted. Once a version directory exists in the registry, its bundle content and hash MUST be immutable.

#### Scenario: Republish under same version rejected by publish flow

- **WHEN** a future publish flow attempts to write `versions/1.0.0/` when that directory already exists with content
- **THEN** the publish operation exits non-zero (this requirement applies even though the publish command itself lands in a later change — the immutability invariant holds for any actor writing to the registry, including manual git pushes flagged by CI)

#### Scenario: Pre-release versions resolvable

- **WHEN** a registry contains `versions/2.0.0-rc.1/`
- **THEN** `fdh install code-review/standard@2.0.0-rc.1` resolves and installs that version

### Requirement: Hash verification before write

The installer SHALL compute the SHA-256 hash of any bundle retrieved from a registry and compare it against `bundle.sha256` before writing any file to the target filesystem. A hash mismatch MUST abort the install with exit code 1 and write no files.

#### Scenario: Matching hash proceeds with install

- **WHEN** the computed hash equals `bundle.sha256`
- **THEN** the installer proceeds to write the bundle to all target paths

#### Scenario: Hash mismatch aborts without writing

- **WHEN** the computed hash differs from `bundle.sha256`
- **THEN** no destination paths are touched, the command exits non-zero, and the error message includes both hashes for diagnosis

### Requirement: Registry interface abstraction

A Go interface `Registry` SHALL abstract registry access so call sites depend on the interface and not on any concrete implementation. The interface MUST cover at minimum: `Index() (Index, error)`, `Manifest(namespace, name) (Manifest, error)`, `FetchBundle(namespace, name, version) (BundlePath, error)`, `Search(query) ([]SkillSummary, error)`. A `GitRegistry` implementation MUST exist in this change; future implementations (e.g. `HTTPRegistry`) MUST be substitutable without changes to command code.

#### Scenario: GitRegistry satisfies the interface

- **WHEN** the codebase is compiled
- **THEN** `*GitRegistry` is statically verified to satisfy `Registry` and is the only implementation registered in this change

#### Scenario: Future HTTPRegistry can replace GitRegistry without refactor

- **WHEN** a hypothetical `HTTPRegistry` implementation is added in a later change
- **THEN** no command-level code (install/list/doctor/search/config) needs modification beyond config-driven registry selection

### Requirement: GitRegistry read behavior

The `GitRegistry` implementation SHALL operate on a local clone of the registry repository, refreshing it via `git fetch` and `git checkout` against a configured branch (default `main`). Read operations MUST be repeatable from cache when the remote is unreachable.

#### Scenario: Read from cache when remote unreachable

- **WHEN** the configured registry remote is unreachable but a local clone exists
- **THEN** `search` and `install` succeed against the cached clone and emit a warning that the cache was used

#### Scenario: Fresh clone when no cache exists

- **WHEN** `GitRegistry` is invoked for the first time on a new machine with an unreachable remote
- **THEN** the operation exits with code 3 (registry unreachable) and a message instructing the developer to run on a connected machine first
