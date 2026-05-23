## ADDED Requirements

### Requirement: Landing page primary CTAs

The portal landing page SHALL display three primary calls-to-action above the fold: "Install the CLI", "Browse skills", "Sign in". Each CTA MUST be a single click away from completing its first useful step.

#### Scenario: CTAs visible above the fold

- **WHEN** a first-time visitor opens the portal on a 1366×768 desktop viewport
- **THEN** all three CTAs are visible without scrolling

#### Scenario: One-click navigation

- **WHEN** a visitor clicks "Install the CLI"
- **THEN** they land directly on `/install` without intervening modals or interstitials

### Requirement: OS-detected install commands

The `/install` page SHALL detect the visitor's operating system from the `User-Agent` header and display the appropriate install command first. Commands for the four other supported platforms (the five total are macOS arm64, macOS amd64, Linux arm64, Linux amd64, Windows amd64) MUST also be visible, expandable, or selectable via tabs.

#### Scenario: macOS visitor sees mac command first

- **WHEN** a user on macOS visits `/install`
- **THEN** the macOS install command is shown as the primary, default-selected option

#### Scenario: Windows visitor sees Windows command first

- **WHEN** a user on Windows visits `/install`
- **THEN** the Windows install command (using PowerShell `Invoke-WebRequest`) is shown as the primary, default-selected option

#### Scenario: All five platforms reachable

- **WHEN** a user opens `/install` on any platform
- **THEN** the page exposes install commands for all five supported platforms (macOS arm64/amd64, Linux arm64/amd64, Windows amd64) via tabs or expandable panels

### Requirement: Copy-buttons on every install command

Every command block on `/install` and on skill detail pages SHALL display a "Copy" button that, when clicked, copies the exact command (no leading prompt, no decorations, no trailing newline) to the clipboard. The button MUST show a brief confirmation state ("Copied!") after click and revert after 2 seconds.

#### Scenario: Clipboard receives clean command

- **WHEN** a user clicks the Copy button on the macOS install command
- **THEN** the clipboard contains exactly the command string (e.g. `curl -fsSL https://... | sh`) with no surrounding whitespace or shell prompts

### Requirement: Sample SHA-256 verification step

The `/install` page SHALL display the SHA-256 checksum for each platform's release archive and the exact one-line shell command (or PowerShell equivalent) the user can run to verify it before extracting.

#### Scenario: Checksum visible per platform

- **WHEN** a user views the macOS section of `/install`
- **THEN** the page shows the SHA-256 of `fdh-<version>-darwin-arm64.tar.gz` and the command `shasum -a 256 -c fdh-<version>-darwin-arm64.tar.gz.sha256`

### Requirement: First-install wizard

The portal SHALL provide a guided "first install" wizard accessible from the landing page. The wizard MUST walk through the following steps in order, each on its own screen, each with a way to mark "done" or "skip":

1. Detect your OS and pick the right binary.
2. Download and verify the checksum.
3. Place `fdh` on your `PATH` and run `fdh --version` to confirm.
4. Configure the registry URL (`fdh config set registry.url ...`).
5. Run `fdh doctor` and confirm at least one agent is detected.
6. Install a recommended starter skill.
7. Open the agent (Claude Code / Copilot / Codex / OpenCode) and confirm the skill appears.

The wizard MUST be re-enterable: a user who closes the wizard can resume from the last completed step.

#### Scenario: Wizard progress persists

- **WHEN** a user completes steps 1–3 of the wizard, closes the browser, and reopens the portal an hour later
- **THEN** the wizard offers to resume at step 4

#### Scenario: Wizard is skippable

- **WHEN** a user clicks "Skip walkthrough" from any wizard step
- **THEN** they land on the browse page, the wizard does not auto-reopen, and a small banner offers to resume the wizard later

### Requirement: Activation events emitted as structured logs

Each wizard step completion (including skip) SHALL emit a structured log line on the frontend server with `event=activation`, `step=<step-name>`, `user_id=<sub-or-anonymous-id>`, `locale=<es|en>`, `os=<darwin|linux|windows>`, and a generated `wizard_session_id`. The same events MUST be exposed on the portal's `GET /api/v1/admin/activation` endpoint (admin-only) for inspection during the pilot.

#### Scenario: Step completion emits log line

- **WHEN** a user completes wizard step 5 (`doctor-passed`)
- **THEN** the frontend server emits a single JSON log line with `event: "activation"`, `step: "doctor-passed"`, the wizard session id, and the user identifier (anonymous if not signed in)

### Requirement: Recommended starter skills

The wizard's step 6 SHALL recommend a starter skill based on the user's most likely workflow. The MVP recommendation policy MUST suggest one of the seed skills from `installer-core` (e.g., `code-review/checklist`) and explain why. The recommendation MUST be configurable via an admin-editable list, defaulting to the `code-review/checklist` skill.

#### Scenario: Default starter recommendation

- **WHEN** an unauthenticated user reaches wizard step 6 with default configuration
- **THEN** the wizard suggests installing `code-review/checklist` with a one-paragraph explanation of why it's a good first skill

### Requirement: Skill detail page exposes the install command

Every skill detail page (`/skills/[namespace]/[name]`) SHALL display the exact `fdh install <namespace>/<name>` command in a prominent, copy-button-equipped block at the top of the page, above the rendered SKILL.md content.

#### Scenario: Install command visible without scroll

- **WHEN** a user lands on `/skills/security/owasp-quick-review`
- **THEN** the install command block is visible without scrolling on a 1366×768 viewport

### Requirement: Per-agent install variants surfaced

The skill detail page SHALL offer expandable variants of the install command for single-agent installs (e.g. `fdh install <ns>/<name> --agent claude-code`). The four supported agents MUST be listed; the default copy-button copies the all-agents form.

#### Scenario: Single-agent variant copyable

- **WHEN** a user expands the "Just Claude Code" variant and clicks its copy button
- **THEN** the clipboard contains `fdh install <ns>/<name> --agent claude-code`

### Requirement: "What's next" panel

Every page that completes a user action (wizard step 7, post-install success state) SHALL display a "What's next" panel suggesting two to three follow-up actions: browse more skills, sign in to save favorites, share the portal with a teammate.

#### Scenario: Post-install panel visible

- **WHEN** a user completes the wizard
- **THEN** the final screen shows a "What's next" panel with at least two suggested next steps and visible navigation back to `/skills`
