## MODIFIED Requirements

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

## REMOVED Requirements

### Requirement: Backward-compatible read of legacy config

**Reason:** The 90-day deprecation window for reading from `~/.config/forge-installer/` has expired, and the Forge rebrand drops every legacy `forge` artifact from the contract. The CLI no longer reads from `forge-installer` paths.

**Migration:** Developers who still have `~/.config/forge-installer/config.yaml` should manually copy values into `~/.config/fdh/config.yaml` (or run `fdh config set` for each key). Past this rebrand, the CLI silently ignores the legacy directory.

### Requirement: `fdh config migrate` subcommand

**Reason:** The subcommand existed solely to bridge from `forge-installer` to `fdh`. With the legacy directory no longer read, the migrate command has no input source and is removed.

**Migration:** Re-create config values via `fdh config set <key> <value>`. The CLI rejects `fdh config migrate` with a usage error pointing at the manual procedure documented in `docs/operations/rename-checkout.md`.

### Requirement: Legacy `forge-installer` stub binary for 90 days

**Reason:** The Forge rebrand eliminates every `forge-*` artifact. The 90-day stub window is closed. Publishing a binary literally named `forge-installer` would contradict the rebrand goal.

**Migration:** Scripts that still invoke `forge-installer` must update to `fdh`. The sibling `fdh` CLI repo ships a one-release-cycle hardcoded alias in its argv handler that prints a deprecation notice and forwards to `fdh`, but no separately-named binary is shipped.
