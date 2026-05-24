# skill-installer-cli Specification

## Purpose
TBD - created by archiving change installer-core. Update Purpose after archive.
## Requirements
### Requirement: Cross-platform single-binary distribution

The CLI SHALL be distributed as a single statically-linked Go binary with no runtime dependencies on the target machine. Release artifacts MUST be produced for macOS arm64, macOS amd64, Linux arm64, Linux amd64, and Windows amd64. The binary SHALL be named `fdh` (or `fdh.exe` on Windows), consistent with the canonical naming defined in `fdh-cli-naming`.

#### Scenario: Binary runs without runtime dependencies

- **WHEN** a developer downloads the binary for their platform and runs `fdh --version`
- **THEN** the binary executes successfully without requiring Go, libc beyond the platform default, or any other runtime to be installed

#### Scenario: All five target platforms produced per release

- **WHEN** a release is built in CI
- **THEN** the release artifacts include exactly five binaries: `fdh-darwin-arm64`, `fdh-darwin-amd64`, `fdh-linux-arm64`, `fdh-linux-amd64`, `fdh-windows-amd64.exe`

### Requirement: install command behavior

The `install <skill>[@version]` command SHALL resolve the named skill from the configured registry and write the bundle to the filesystem locations declared by the target agents. By default, the command MUST install to every agent detected on the host. The default scope MUST be `project` when a project root is detectable (presence of `.git/` or a manifest the configuration recognizes); otherwise `user`. The `--agent` flag MAY be repeated to narrow the agent set, and `--scope user|project` MUST override the default scope.

#### Scenario: Install to all detected agents by default

- **WHEN** a developer runs `fdh install code-review-standard` on a host where all four agents are detected
- **THEN** the bundle is written to each path the adapter map declares for those agents, and exit code is zero

#### Scenario: Install to a single agent via --agent flag

- **WHEN** a developer runs `fdh install code-review-standard --agent claude-code`
- **THEN** the bundle is written only to Claude Code's declared paths, no other agent paths are touched, and exit code is zero

#### Scenario: Install fails when no agents detected

- **WHEN** a developer runs `fdh install code-review-standard` on a host with no detectable agents
- **THEN** the command exits non-zero with a message naming the agents that were probed and the probes that failed, and no files are written

### Requirement: list command output

The `list` command SHALL display every installed skill across every directory the adapter map declares for the chosen scope, including skill name, installed version, target agents satisfied by the install, scope, and a source field derived from the provenance sidecar.

#### Scenario: List shows installed skills with provenance

- **WHEN** a developer has installed two skills and runs `fdh list`
- **THEN** the output table shows both skills, each with their name, version, the agent list from their sidecar, scope, and source registry URL

#### Scenario: List handles missing provenance gracefully

- **WHEN** a developer runs `fdh list` on a directory where a `SKILL.md` exists without a `.skill-meta.yaml` sidecar
- **THEN** the row appears with source `unknown` and the command still exits zero

### Requirement: doctor command behavior

The `doctor` command SHALL detect installed agents via the adapter map's probes, verify each declared read path is writable for the current user, report the registry's reachability when a registry is configured, and exit zero only when no critical issues are found.

#### Scenario: Doctor reports healthy state

- **WHEN** a developer runs `fdh doctor` on a correctly configured host
- **THEN** the report lists each detected agent, every declared path marked writable, registry reachable, and exit code is zero

#### Scenario: Doctor reports unwritable agent path

- **WHEN** a declared agent path is not writable for the current user
- **THEN** the doctor report flags that path with severity `error`, the affected agent is listed as `degraded`, and exit code is non-zero

#### Scenario: Doctor is safe to run anywhere

- **WHEN** `fdh doctor` runs in a directory without any project configuration and without network access
- **THEN** the command completes without raising an unhandled error, reports what it could and could not check, and uses exit code zero unless an explicit configured check failed

### Requirement: search command behavior

The `search <query>` command SHALL search the registry's index for skills whose name, namespace, description, or tags match the query and display the matches. The command MUST NOT perform network I/O beyond the registry refresh that the configured `Registry` implementation declares as its read path.

#### Scenario: Search returns matching skills

- **WHEN** a developer runs `fdh search owasp` against a registry containing a skill named `security/owasp-review`
- **THEN** the result table includes that skill with its latest version, namespace, and description

#### Scenario: Search returns empty result cleanly

- **WHEN** a developer runs `fdh search nonexistent-term`
- **THEN** the command prints an empty result table (or `[]` with `--json`), exits zero, and does not error

### Requirement: config command behavior

The `config get <key>` and `config set <key> <value>` commands SHALL manage a minimal configuration surface persisted under `~/.config/fdh/config.yaml` (or the OS-appropriate equivalent on Windows, per `fdh-cli-naming`). Supported keys MUST include at least `registry.url`, `defaults.scope`, and `cache.dir`. Unknown keys MUST be rejected.

#### Scenario: Set and read back a key

- **WHEN** a developer runs `fdh config set registry.url https://skills.forge.internal` then `fdh config get registry.url`
- **THEN** the second command prints `https://skills.forge.internal` and exits zero

#### Scenario: Reject unknown key

- **WHEN** a developer runs `fdh config set bogus.key value`
- **THEN** the command exits non-zero with an error message listing the supported key set

### Requirement: structured output via --json

Every command SHALL accept a `--json` flag that produces machine-readable JSON instead of the human table format. The JSON schema for each command MUST be stable across patch releases and documented.

#### Scenario: install --json emits structured result

- **WHEN** a developer runs `fdh install code-review-standard --json`
- **THEN** stdout contains a single JSON object describing the install result (skill name, version, written paths, agents, hash, sidecar path) suitable for consumption by an onboarding script

#### Scenario: list --json emits an array of installs

- **WHEN** a developer runs `fdh list --json`
- **THEN** stdout contains a JSON array where each element conforms to the documented installed-skill schema

### Requirement: Cross-platform path and line-ending handling

The CLI SHALL handle filesystem paths, executable bits, and line endings uniformly across macOS, Linux, and Windows. File content MUST be written byte-identically to the registry bundle on every platform. Line endings inside text files MUST be preserved as authored — the installer MUST NOT convert between LF and CRLF.

#### Scenario: Bundle round-trip is byte-identical across OSes

- **WHEN** the same registry bundle is installed on macOS, Linux, and Windows
- **THEN** the resulting `SKILL.md` (computed by stripping the injected `installed_from:` breadcrumb) is byte-identical to the source on all three platforms, including line endings

#### Scenario: Executable bit preserved on Unix

- **WHEN** a bundle's `scripts/run.sh` is published with executable permission and installed on macOS or Linux
- **THEN** the installed file is executable for the current user

#### Scenario: Executable bit absent does not error on Windows

- **WHEN** a bundle's `scripts/run.sh` is installed on Windows
- **THEN** the install completes without error, the file is created, and any executable-bit field in the sidecar reflects what was published

### Requirement: No hidden network egress

The CLI SHALL NOT initiate network I/O except to the configured registry. Any other connectivity check, telemetry emission, or auto-update probe MUST be opt-in via explicit configuration.

#### Scenario: Offline run touches only the registry

- **WHEN** a developer runs `fdh install <skill>` on a host with the registry available but all other outbound traffic blocked
- **THEN** the install succeeds and no non-registry network connections are attempted

### Requirement: Stable, documented exit codes

The CLI SHALL use a documented, stable set of exit codes so onboarding scripts can branch on outcome. The set MUST include at least: `0` success, `1` generic failure, `2` invalid usage, `3` registry unreachable, `4` portability violation, `5` agent not detected, `6` filesystem permission denied.

#### Scenario: Portability violation produces exit code 4

- **WHEN** a developer attempts to install a portable skill whose body fails the portability lint
- **THEN** the command exits with code `4` and the error message identifies the failing rule

#### Scenario: Registry unreachable produces exit code 3

- **WHEN** the configured Git registry path is invalid or unreachable
- **THEN** the command exits with code `3` and the message names the configured registry source

