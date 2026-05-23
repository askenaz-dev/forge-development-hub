## ADDED Requirements

### Requirement: Sidecar provenance file written on every install

On every successful install, the installer SHALL write a `.skill-meta.yaml` file in the same directory as the installed `SKILL.md`. The sidecar MUST be written once per destination path; if a skill installs to two destination paths (the dual-write case), two sidecars are written, each describing that specific copy. The sidecar's filename SHALL begin with `.` so it is treated as hidden on Unix-like filesystems.

#### Scenario: Dual-write produces two sidecars

- **WHEN** a portable skill is installed to all four agents at project scope, resulting in writes to `.claude/skills/<name>/` and `.agents/skills/<name>/`
- **THEN** a `.skill-meta.yaml` is written next to each of the two `SKILL.md` files, and the two sidecars are content-equivalent except for the `path` field

#### Scenario: Sidecar absent before install, present after

- **WHEN** a developer runs `install` for a skill that has never been installed in this directory
- **THEN** `.skill-meta.yaml` did not exist before the command and exists after, and the file is readable by the installing user

### Requirement: Sidecar schema

The `.skill-meta.yaml` sidecar SHALL conform to a versioned schema. The schema MUST include the following fields, all required unless marked optional:

- `schema_version` — integer, currently `1`
- `registry` — string, the canonical registry URL or local path the bundle was fetched from
- `namespace` — string, the registry namespace (e.g. `security`)
- `name` — string, the skill name
- `version` — string, semver
- `content_hash` — string, the canonical SHA-256 of the bundle at publish time (MUST equal the registry's recorded hash)
- `installed_by` — string, in the form `<user>@<host>`
- `installed_at` — string, ISO 8601 UTC timestamp with `Z` suffix
- `target_agents` — list of strings, the agent identifiers this install satisfies
- `scope` — string, one of `user` or `project`
- `path` — string, the absolute path of this specific install destination
- `installer_version` — string, the version of the installer binary that wrote this file
- `signature` (optional) — string, present only when a signature was verified at install time

#### Scenario: Sidecar contains all required fields

- **WHEN** `install` writes a sidecar for `security/owasp-review@1.2.0` for a developer `alice@laptop` targeting `claude-code` and `opencode` at project scope
- **THEN** the resulting `.skill-meta.yaml` includes `schema_version: 1`, the registry URL, `namespace: security`, `name: owasp-review`, `version: 1.2.0`, a non-empty `content_hash`, `installed_by: alice@laptop`, a valid ISO 8601 UTC `installed_at`, `target_agents: [claude-code, opencode]`, `scope: project`, the absolute `path`, and the installer's version string

#### Scenario: Optional signature field present when verified

- **WHEN** the installer verifies a cosign signature against `bundle.sig` before writing
- **THEN** the `signature` field is present in the sidecar containing the verified signature identifier

### Requirement: Frontmatter breadcrumb injected

In addition to the sidecar, the installer SHALL inject exactly one line into the installed `SKILL.md`'s frontmatter: `installed_from: <registry>/<namespace>/<name>@<version>`. No other modification to `SKILL.md` is permitted. The injection MUST be idempotent: re-installing the same version over an existing install MUST result in a single `installed_from` entry, not duplicates.

#### Scenario: Breadcrumb present after install

- **WHEN** `install` writes `SKILL.md` to a destination path
- **THEN** the destination file's frontmatter contains exactly one `installed_from: …@<version>` line

#### Scenario: Re-install over existing file produces a single breadcrumb

- **WHEN** a developer runs `install` for the same skill version twice in succession against the same destination
- **THEN** the destination `SKILL.md` contains exactly one `installed_from:` line, not two, and the line reflects the latest install

#### Scenario: Bundle SKILL.md body unchanged

- **WHEN** the installed `SKILL.md` is compared to the bundle's source `SKILL.md`, ignoring the injected `installed_from` line
- **THEN** the two files are byte-identical including all other frontmatter keys, the trailing `---`, and the markdown body

### Requirement: Canonical hash computed pre-injection

The bundle's canonical content hash SHALL be computed over the source bundle as published in the registry, BEFORE any install-time modification including the `installed_from` breadcrumb. This ensures the hash recorded in the sidecar equals the hash the registry records, regardless of how many times or where the skill is installed.

#### Scenario: Sidecar hash equals registry hash

- **WHEN** the registry records `content_hash: abc123…` for `security/owasp-review@1.2.0` and the skill is installed on three different machines
- **THEN** all three resulting sidecars contain `content_hash: abc123…`

#### Scenario: Breadcrumb does not affect hash

- **WHEN** the same bundle is installed twice and the two installed `SKILL.md` files differ only in their `installed_from` lines
- **THEN** the recorded `content_hash` in both sidecars is identical and equals the registry's recorded hash

### Requirement: list reads provenance from sidecars

The `list` command SHALL read every `.skill-meta.yaml` sidecar reachable under the configured adapter paths and use those sidecars as the authoritative source of installed-skill state. The command MUST NOT infer installed state from `SKILL.md` content alone.

#### Scenario: Sidecar drives list output

- **WHEN** two installed skills both have well-formed sidecars
- **THEN** `list` produces one row per `(name, scope, agent-set)` tuple drawn from the sidecars

#### Scenario: Missing sidecar produces "unknown" row

- **WHEN** an installed `SKILL.md` is present but its sidecar is missing or unreadable
- **THEN** `list` includes a row for that skill with `source: unknown`, `version: unknown`, and `agents: <inferred from path>`, and the command exits zero

#### Scenario: Corrupted sidecar treated as unknown, not as failure

- **WHEN** a `.skill-meta.yaml` fails to parse (invalid YAML or missing `schema_version`)
- **THEN** `list` treats the entry as unknown, emits a warning naming the file, and continues processing other entries

### Requirement: Portability lint allows `installed_from`

The portability lint SHALL explicitly permit the `installed_from` key in the portable frontmatter allowlist, in addition to the keys defined in the skill-portability spec. No other install-time injection is permitted.

#### Scenario: installed_from in portable skill passes the lint

- **WHEN** a portable skill's frontmatter (post-install) contains `installed_from: …@<version>` alongside `name`, `description`, and `metadata`
- **THEN** the portability lint passes

#### Scenario: Other install-injected keys forbidden

- **WHEN** a future implementation attempts to inject any key other than `installed_from` into a portable skill's frontmatter
- **THEN** the lint fails and the install is aborted

### Requirement: Sidecar removal on uninstall (forward declaration)

When a future `remove` command lands, removing a skill MUST also remove its `.skill-meta.yaml` sidecars from every destination path. This requirement is declared here so the install path writes sidecars in locations the future remove path can find deterministically.

#### Scenario: Sidecar location predictable

- **WHEN** a skill has been installed via the dual-write strategy
- **THEN** every sidecar is at exactly `<dest-path>/.skill-meta.yaml`, never anywhere else, so a future `remove` can locate them by walking the same path set the adapter map declares
