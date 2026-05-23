# fdh-cli-naming Specification

## Purpose
TBD - created by archiving change dev-portal. Update Purpose after archive.
## Requirements
### Requirement: Canonical CLI binary name

The CLI binary SHALL be named `fdh` (or `fdh.exe` on Windows). Every release artifact, every doc snippet, every install instruction MUST use this name. No alternate names are produced as primary artifacts.

#### Scenario: Binary name on macOS / Linux

- **WHEN** a developer downloads the release archive for macOS or Linux and extracts it
- **THEN** the executable file inside the archive is named `fdh`

#### Scenario: Binary name on Windows

- **WHEN** a developer downloads the release archive for Windows and extracts it
- **THEN** the executable file inside the archive is named `fdh.exe`

### Requirement: Canonical Go module path

The Go module SHALL be `github.com/falabella/fdh`. Every internal package import path MUST start with this prefix. The previous module path `github.com/falabella/skill-installer` MUST NOT appear anywhere in compiled binaries or in `go.mod`.

#### Scenario: Module path consistent across files

- **WHEN** the build succeeds
- **THEN** `grep -r 'github.com/falabella/skill-installer' .` against the source tree returns zero matches (except in migration documentation explicitly explaining the prior path)

### Requirement: Per-user config directory

The per-user configuration directory SHALL be `~/.config/fdh/` on Linux, `~/Library/Application Support/fdh/` on macOS, and `%APPDATA%\fdh\` on Windows. The supported files inside it are `config.yaml` and `adapters.yaml`, with the same semantics defined by the `installer-core` specs.

#### Scenario: Default config directory used on a fresh machine

- **WHEN** a developer runs `fdh config set registry.url https://example/registry.git` on a machine that has never run the CLI before
- **THEN** the value is persisted to `~/.config/fdh/config.yaml` (or the OS equivalent), and the file did not exist before the command

### Requirement: Backward-compatible read of legacy config

For 90 days after the rename ships, the CLI SHALL read configuration from the legacy directory (`~/.config/falabella-installer/` and OS equivalents) if and only if the new `~/.config/fdh/` directory does not contain the requested file. When a legacy file is used, the CLI MUST emit a one-line warning to stderr naming the legacy path and recommending `fdh config migrate`.

#### Scenario: Legacy config still works during deprecation window

- **WHEN** a developer who upgraded from `falabella-installer` to `fdh` has a `~/.config/falabella-installer/config.yaml` but no `~/.config/fdh/config.yaml`, and runs `fdh config get registry.url`
- **THEN** the command prints the value from the legacy file AND prints a deprecation warning to stderr citing the legacy path

#### Scenario: New config wins over legacy when both exist

- **WHEN** both `~/.config/fdh/config.yaml` and `~/.config/falabella-installer/config.yaml` exist
- **THEN** the new path is authoritative; the legacy file is ignored and no warning is emitted

### Requirement: `fdh config migrate` subcommand

The CLI SHALL provide a `fdh config migrate` subcommand that copies any legacy config files from `~/.config/falabella-installer/` to `~/.config/fdh/`, preserving values, then prints a summary of the files moved. Re-running the command on an already-migrated machine MUST be a no-op with a clear "nothing to migrate" message.

#### Scenario: First-time migration

- **WHEN** a developer with a legacy `~/.config/falabella-installer/config.yaml` runs `fdh config migrate`
- **THEN** `~/.config/fdh/config.yaml` is created with identical content, the command prints a summary listing each migrated file, and exit code is zero

#### Scenario: Re-run is idempotent

- **WHEN** a developer runs `fdh config migrate` on a machine where migration already happened (legacy files absent or new files already present)
- **THEN** the command prints "nothing to migrate" and exits zero without modifying any files

### Requirement: Legacy `falabella-installer` stub binary for 90 days

For 90 days after the rename ships, a stub binary SHALL be published under the legacy name `falabella-installer`. The stub MUST: (a) print to stderr a one-line deprecation notice naming the new binary `fdh` and the migration command, (b) if `fdh` is found on `PATH`, forward all arguments and the exit code transparently, (c) if `fdh` is not on `PATH`, print a short install hint and exit with code 127.

#### Scenario: Stub forwards to fdh when present

- **WHEN** a developer runs `falabella-installer doctor` on a machine where `fdh` is on PATH
- **THEN** stderr contains a one-line deprecation notice, stdout contains the doctor output, and the exit code matches what `fdh doctor` would have produced

#### Scenario: Stub instructs install when fdh missing

- **WHEN** a developer runs `falabella-installer install foo/bar` on a machine where `fdh` is not on PATH
- **THEN** stderr instructs the developer to install `fdh` from the documented channel, exit code is 127

### Requirement: Release artifact naming

Release archives SHALL be named `fdh-<version>-<goos>-<goarch>.tar.gz` with adjacent `.sha256` files. The five target platforms (darwin/arm64, darwin/amd64, linux/arm64, linux/amd64, windows/amd64) match the `installer-core` release contract.

#### Scenario: Release artifacts published per platform

- **WHEN** a release is built for version v1.0.0
- **THEN** the published artifacts include exactly: `fdh-v1.0.0-darwin-arm64.tar.gz`, `fdh-v1.0.0-darwin-amd64.tar.gz`, `fdh-v1.0.0-linux-arm64.tar.gz`, `fdh-v1.0.0-linux-amd64.tar.gz`, `fdh-v1.0.0-windows-amd64.tar.gz`, plus a `.sha256` for each

