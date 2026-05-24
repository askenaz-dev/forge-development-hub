*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

## ADDED Requirements

### Requirement: Manifest-driven adapter description

The system SHALL describe every supported AI coding agent via a YAML manifest. Each agent entry MUST declare: a unique identifier (kebab-case), a human-readable display name, one or more detection probes, the set of user-scope read paths, and the set of project-scope read paths. Adding a new supported agent MUST be possible by editing only the YAML manifest with no changes to compiled Go code.

#### Scenario: New agent added via manifest edit

- **WHEN** a maintainer adds a new agent entry to `adapters.yaml` with valid `id`, `detect`, and `paths` fields
- **THEN** the running installer recognizes the agent at next invocation, `doctor` probes it, and `install --agent <new-id>` writes to its declared paths — all without recompilation

### Requirement: Embedded default manifest covers all four pilot agents

The installer binary SHALL embed a default adapter manifest covering claude-code, copilot, codex, and opencode. The default manifest's path declarations MUST match the locations documented by each agent's official skill documentation as of the change being archived.

#### Scenario: Default manifest paths match documented sources

- **WHEN** a developer runs the installer on a fresh machine with no user override file
- **THEN** the four agents are described with the following paths in the embedded manifest:
  - claude-code: user `~/.claude/skills/`, project `.claude/skills/`
  - copilot: user `~/.copilot/skills/` and `~/.agents/skills/`, project `.github/skills/` and `.claude/skills/` and `.agents/skills/`
  - codex: user `~/.agents/skills/`, project `.agents/skills/`
  - opencode: user `~/.agents/skills/` and `~/.claude/skills/`, project `.agents/skills/` and `.claude/skills/`

### Requirement: User-level adapter manifest override

The system SHALL load a user-provided adapter manifest from `~/.config/fdh/adapters.yaml` (or the OS-appropriate equivalent on Windows) if it exists, and that file MUST completely replace the embedded default for any agent it redefines. The merge MUST be per-agent: a user file that defines only `claude-code` MUST leave the other three agents from the embedded default untouched.

#### Scenario: Override replaces a single agent

- **WHEN** a user provides an `adapters.yaml` that redefines `claude-code` paths but does not mention the other three
- **THEN** the running installer uses the user's `claude-code` definition and the embedded defaults for `copilot`, `codex`, and `opencode`

#### Scenario: Invalid override file rejected with clear error

- **WHEN** a user `adapters.yaml` is malformed (invalid YAML or missing required fields)
- **THEN** the installer exits non-zero before any other action, naming the file and the validation error, and does not silently fall back to the embedded default

### Requirement: Agent detection via declared probes

Each agent entry SHALL declare one or more detection probes. A probe is a simple check the installer can evaluate without elevated privileges: presence of a directory, presence of an executable in `PATH`, or a successful shell-out that returns exit code zero. An agent MUST be reported as `detected` if any of its probes succeed.

#### Scenario: Directory probe detects Claude Code via ~/.claude

- **WHEN** the embedded manifest's `claude-code` probe checks for `~/.claude/` and that directory exists
- **THEN** `doctor` reports `claude-code` as detected

#### Scenario: Executable probe detects Codex via codex binary on PATH

- **WHEN** the embedded manifest's `codex` probe checks for a `codex` executable on `PATH` and the binary is installed
- **THEN** `doctor` reports `codex` as detected

#### Scenario: All probes failing reports the agent as not detected

- **WHEN** none of an agent's declared probes succeed on the host
- **THEN** `doctor` reports the agent as `not-detected` along with the list of probes that were attempted

### Requirement: Path writability verification

For each detected agent, `doctor` SHALL verify that every declared read path (user-scope when the relevant scope is being checked, project-scope when a project root is present) is either an existing writable directory or a path whose parent is writable so the installer can create it on demand.

#### Scenario: Writable existing directory is reported healthy

- **WHEN** an agent declares `~/.claude/skills/`, the directory exists, and the current user has write permission
- **THEN** the doctor report marks that path as `writable`

#### Scenario: Missing-but-creatable path reported as ok

- **WHEN** an agent declares `~/.agents/skills/`, the directory does not yet exist, but `~/.agents/` is writable and `mkdir -p` would succeed
- **THEN** the doctor report marks that path as `writable (will be created on install)`

#### Scenario: Unwritable path reported as error

- **WHEN** a declared path's parent directory is not writable by the current user
- **THEN** the doctor report marks the path with severity `error`, includes the underlying permission detail, and the doctor command exits non-zero

### Requirement: Adapter ID stability

Once an agent identifier has shipped in a release, the identifier SHALL remain stable across future releases. Renaming an agent ID MUST be treated as a removal plus addition with a documented migration step.

#### Scenario: ID rename forbidden in patch release

- **WHEN** a release candidate proposes renaming `copilot` to `github-copilot`
- **THEN** the change is rejected by review unless it is paired with a migration plan and at least a minor version bump

### Requirement: Path-set union for multi-agent install

When `install` targets multiple agents, the installer SHALL compute the union of declared paths across the requested agents at the chosen scope, deduplicate that union, and write the bundle to each unique path exactly once. Each written path MUST be recorded in the resulting `.skill-meta.yaml` sidecar.

#### Scenario: Two agents sharing a path write only once

- **WHEN** `install` targets `codex` and `opencode` at project scope (both declare `.agents/skills/`)
- **THEN** the bundle is written to `.agents/skills/<name>/` exactly once and to `.claude/skills/<name>/` exactly once (declared only by `opencode`), and the sidecars list both `codex` and `opencode` as satisfied target agents

#### Scenario: Four-agent install writes the minimum union path set at project scope

- **WHEN** `install` targets all four agents at project scope
- **THEN** the bundle is written to exactly three paths: `.claude/skills/<name>/`, `.agents/skills/<name>/`, and `.github/skills/<name>/`, and each sidecar lists every agent satisfied by that specific path

#### Scenario: Four-agent install writes the minimum union path set at user scope

- **WHEN** `install` targets all four agents at user scope
- **THEN** the bundle is written to exactly three paths: `~/.claude/skills/<name>/`, `~/.agents/skills/<name>/`, and `~/.copilot/skills/<name>/`, and each sidecar lists every agent satisfied by that specific path
