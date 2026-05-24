## MODIFIED Requirements

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

### Requirement: Semver-based versioning, immutable once published

Versions SHALL use semantic versioning (`MAJOR.MINOR.PATCH`). Pre-release and build metadata suffixes (e.g. `-rc.1`, `+build.42`) are permitted. Once a version directory exists in the registry, its bundle content and hash MUST be immutable.

#### Scenario: Republish under same version rejected by publish flow

- **WHEN** a future publish flow attempts to write `versions/1.0.0/` when that directory already exists with content
- **THEN** the publish operation exits non-zero (this requirement applies even though the publish command itself lands in a later change — the immutability invariant holds for any actor writing to the registry, including manual git pushes flagged by CI)

#### Scenario: Pre-release versions resolvable

- **WHEN** a registry contains `versions/2.0.0-rc.1/`
- **THEN** `fdh install code-review/standard@2.0.0-rc.1` resolves and installs that version
