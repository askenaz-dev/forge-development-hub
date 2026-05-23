# skill-portability Specification

## Purpose
TBD - created by archiving change installer-core. Update Purpose after archive.
## Requirements
### Requirement: Skill portability declaration

Every skill SHALL declare its portability class via the `portable` field in `SKILL.md` frontmatter. The field accepts boolean values. When the field is omitted, the default value is `true`. The portability class determines which agents the skill may be installed to.

#### Scenario: Default portability is true

- **WHEN** a `SKILL.md` does not declare a `portable` field
- **THEN** the system treats the skill as `portable: true` and applies the portable lint rules

#### Scenario: Explicit portable: true honored

- **WHEN** a `SKILL.md` declares `portable: true`
- **THEN** the skill is subject to the full set of portable lint rules

#### Scenario: Explicit portable: false honored

- **WHEN** a `SKILL.md` declares `portable: false`
- **THEN** the skill is exempt from the portable lint rules but MUST declare a `compatibility` allowlist (see compatibility requirement)

### Requirement: Compatibility allowlist for non-portable skills

A skill with `portable: false` SHALL declare a `compatibility` field listing the agent identifiers it supports. The list MUST be non-empty and MUST contain only identifiers defined in the active adapter map. A portable skill MAY also declare `compatibility` (purely informational); the portable lint rules still apply to it.

#### Scenario: Non-portable skill without compatibility rejected

- **WHEN** a skill declares `portable: false` and omits `compatibility` (or declares it as an empty list)
- **THEN** validation rejects the skill with exit code 4 and a message naming the missing field

#### Scenario: Unknown agent ID in compatibility rejected

- **WHEN** a skill declares `compatibility: [claude-code, jetbrains-junie]` but `jetbrains-junie` is not in the active adapter map
- **THEN** validation rejects the skill citing the unknown identifier

### Requirement: Portable lint forbids agent-specific frontmatter

In a portable skill, the SKILL.md frontmatter SHALL contain ONLY keys from the portable frontmatter allowlist. The allowlist consists exactly of: `name`, `description`, `license`, `metadata`, `compatibility`, `portable`, and the install-injected `installed_from`. Any other frontmatter key in a portable skill MUST cause the portability lint to fail.

#### Scenario: allowed-tools forbidden in portable skill

- **WHEN** a portable skill declares `allowed-tools: Bash`
- **THEN** the portability lint fails with exit code 4 and a message naming `allowed-tools` as a Claude-only field

#### Scenario: disable-model-invocation forbidden in portable skill

- **WHEN** a portable skill declares `disable-model-invocation: true`
- **THEN** the portability lint fails citing the disallowed key

#### Scenario: context: fork forbidden in portable skill

- **WHEN** a portable skill declares `context: fork`
- **THEN** the portability lint fails citing the disallowed key

#### Scenario: when_to_use forbidden in portable skill

- **WHEN** a portable skill declares `when_to_use:` content
- **THEN** the portability lint fails citing the disallowed key

#### Scenario: metadata block accepted in portable skill

- **WHEN** a portable skill declares `metadata: { author: team-x, version: "1.0" }`
- **THEN** the lint accepts the skill

### Requirement: Portable lint forbids Claude-only body substitutions

In a portable skill, the SKILL.md body SHALL NOT contain the Claude-only substitution tokens `$ARGUMENTS`, `$ARGUMENTS[<n>]`, `$0` through `$9`, `${CLAUDE_SESSION_ID}`, or `${CLAUDE_SKILL_DIR}`. Detection is by literal string match; documentation that quotes these tokens inside fenced code blocks marked as `text` or `markdown` MUST still trip the lint (the conservative position is intentional — if the token appears, the file will misbehave in non-Claude agents).

#### Scenario: $ARGUMENTS in body fails the lint

- **WHEN** a portable skill's body contains the literal string `$ARGUMENTS`
- **THEN** the portability lint fails citing the line number and the disallowed token

#### Scenario: ${CLAUDE_SKILL_DIR} in body fails the lint

- **WHEN** a portable skill's body contains `${CLAUDE_SKILL_DIR}`
- **THEN** the portability lint fails citing the disallowed token

### Requirement: Portable lint forbids dynamic context injection markers

In a portable skill, the SKILL.md body SHALL NOT contain Claude Code's dynamic context injection syntax: the inline form `` !`<cmd>` `` recognized when `!` appears at the start of a line or after whitespace, nor the fenced form opened with ` ```! `.

#### Scenario: Inline backtick injection fails the lint

- **WHEN** a portable skill's body contains the line `Diff: !` `git diff HEAD` ` `
- **THEN** the portability lint fails citing the dynamic-injection rule

#### Scenario: Fenced ```! block fails the lint

- **WHEN** a portable skill's body contains a fenced block opening with ` ```! `
- **THEN** the portability lint fails citing the dynamic-injection rule

### Requirement: Installer enforces compatibility at write time

The installer SHALL enforce a skill's `compatibility` declaration when computing which agents will receive the bundle. If `install` is invoked targeting an agent not in the skill's compatibility list, the installer MUST refuse to write to that agent's paths.

#### Scenario: Install to incompatible agent refused

- **WHEN** a skill declares `portable: false` and `compatibility: [claude-code]`, and a developer runs `falabella-installer install <skill> --agent copilot`
- **THEN** the command exits with code 4 and the message names the violation; no files are written to copilot's paths

#### Scenario: Default-all-agents narrows to compatibility list

- **WHEN** a skill declares `portable: false` and `compatibility: [claude-code, opencode]`, and a developer runs `falabella-installer install <skill>` without an `--agent` flag on a host where all four agents are detected
- **THEN** the bundle is written only to the paths required by `claude-code` and `opencode`; `copilot` and `codex` are skipped and reported in the output as `not-compatible`

#### Scenario: Portable skill installs to every detected agent

- **WHEN** a portable skill is installed without `--agent` on a host where all four agents are detected
- **THEN** the bundle is written to the union path set for all four agents and all four are listed in the sidecar

### Requirement: Portability lint runs before every install

The installer SHALL run the portability lint over the resolved bundle before writing any file to disk. A lint failure MUST abort the install with no partial writes. The same lint engine SHALL be exposed as a library function so future changes (`scan-gate`, CI publish flow) can call it identically.

#### Scenario: Lint runs on install

- **WHEN** `install` resolves a bundle whose SKILL.md violates a portable lint rule
- **THEN** no destination paths are written, exit code is 4, and the message names the failing rule and line

#### Scenario: Lint engine is reusable

- **WHEN** the codebase is compiled
- **THEN** a public Go package exposes the lint engine such that a future publish-side or CI-side caller can invoke it on a bundle directory without duplicating logic

