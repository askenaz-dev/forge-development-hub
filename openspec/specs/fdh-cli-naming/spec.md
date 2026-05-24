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

The Go module SHALL be `github.com/forge/fdh`. Every internal package import path MUST start with this prefix. The prior module paths `github.com/forge/skill-installer` and `github.com/forge/fdh` MUST NOT appear anywhere in compiled binaries or in `go.mod`.

#### Scenario: Module path consistent across files

- **WHEN** the build succeeds
- **THEN** `grep -r 'github.com/forge' .` and `grep -r 'github.com/forge/skill-installer' .` against the source tree return zero matches (except in migration documentation explicitly explaining the prior paths)

### Requirement: Per-user config directory

The per-user configuration directory SHALL be `~/.config/fdh/` on Linux, `~/Library/Application Support/fdh/` on macOS, and `%APPDATA%\fdh\` on Windows. The supported files inside it are `config.yaml` and `adapters.yaml`, with the same semantics defined by the `installer-core` specs.

#### Scenario: Default config directory used on a fresh machine

- **WHEN** a developer runs `fdh config set registry.url https://example/registry.git` on a machine that has never run the CLI before
- **THEN** the value is persisted to `~/.config/fdh/config.yaml` (or the OS equivalent), and the file did not exist before the command

### Requirement: Release artifact naming

Release archives SHALL be named `fdh-<version>-<goos>-<goarch>.tar.gz` with adjacent `.sha256` files. The five target platforms (darwin/arm64, darwin/amd64, linux/arm64, linux/amd64, windows/amd64) match the `installer-core` release contract.

#### Scenario: Release artifacts published per platform

- **WHEN** a release is built for version v1.0.0
- **THEN** the published artifacts include exactly: `fdh-v1.0.0-darwin-arm64.tar.gz`, `fdh-v1.0.0-darwin-amd64.tar.gz`, `fdh-v1.0.0-linux-arm64.tar.gz`, `fdh-v1.0.0-linux-amd64.tar.gz`, `fdh-v1.0.0-windows-amd64.tar.gz`, plus a `.sha256` for each

