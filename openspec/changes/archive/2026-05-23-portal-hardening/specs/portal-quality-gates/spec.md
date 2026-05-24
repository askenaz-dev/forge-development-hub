*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

## ADDED Requirements

### Requirement: Translation-key parity is enforced in CI

CI SHALL run a check that fails when the set of keys in `web/messages/es.json` and `web/messages/en.json` differ. The failure message MUST list every key present in one file but missing from the other so the developer can fix the gap without manual diffing.

#### Scenario: Identical key sets pass

- **WHEN** both message files declare the same set of keys (regardless of values)
- **THEN** the parity check exits zero

#### Scenario: Missing key in the secondary locale fails

- **WHEN** `messages/es.json` adds a new key not present in `messages/en.json`
- **THEN** the parity check exits non-zero and prints the missing key under the `en` locale's report

#### Scenario: Extra key in the primary locale fails

- **WHEN** `messages/en.json` adds a key not present in `messages/es.json`
- **THEN** the parity check exits non-zero and prints the missing key under the `es` locale's report

### Requirement: Translation-parity check exposed as a single command

The check SHALL be runnable locally via `pnpm i18n:check` (or the equivalent `npm run i18n:check`) without additional setup beyond the standard dependency install. The same command runs in CI.

#### Scenario: Local invocation works after `pnpm install`

- **WHEN** a developer runs `pnpm install` followed by `pnpm i18n:check` on a clean checkout
- **THEN** the command runs to completion without further setup, returning the parity check result

### Requirement: Accessibility (axe-core) tests gate every PR

CI SHALL run a Playwright suite that loads every public page (`/`, `/install`, `/skills`, a representative `/skills/[ns]/[name]`, `/onboarding`), runs `@axe-core/playwright` against the rendered DOM, and fails the build when any rule of severity `serious` or `critical` reports a violation.

#### Scenario: Clean pages pass

- **WHEN** every covered page passes axe-core with zero `serious` or `critical` findings
- **THEN** the a11y job exits zero

#### Scenario: Critical violation fails the build

- **WHEN** any covered page introduces a `critical` axe-core violation (e.g. a button with no accessible name)
- **THEN** the a11y job exits non-zero, the build is blocked, and the report names the page + violated rule

#### Scenario: Authenticated pages excluded from the smoke

- **WHEN** the suite runs without a configured authenticated session
- **THEN** `/profile` and `/admin` are explicitly skipped (they require a real Keycloak session in the runner, out of scope for this gate)

### Requirement: A11y check is runnable locally

The a11y suite SHALL be runnable locally via `pnpm a11y` against a developer's dev server with no environment configuration beyond having the dev server running. Playwright's browser binaries MUST install on first run; the command MUST NOT require a separate `npx playwright install` step the developer has to remember.

#### Scenario: First-run on a fresh checkout

- **WHEN** a developer runs `pnpm install` then `pnpm a11y` on a freshly cloned repo
- **THEN** Playwright fetches its browser binaries automatically and the suite executes against the running dev server, producing a single pass/fail summary

### Requirement: Lockfile consistency between pnpm and npm

When both `pnpm-lock.yaml` and `package-lock.json` are present in `web/`, CI SHALL run a step that verifies both lockfiles agree with `web/package.json` — i.e. running `pnpm install --lockfile-only` followed by `npm install --package-lock-only` produces no diff in the working tree. The check pinpoints which lockfile needs regeneration when they drift.

#### Scenario: Both lockfiles in sync pass

- **WHEN** both lockfiles match `package.json`
- **THEN** the consistency check exits zero

#### Scenario: One lockfile out of date fails

- **WHEN** `package.json` is edited but only one of the two lockfiles is regenerated
- **THEN** the consistency check exits non-zero and names the lockfile that diverges

### Requirement: Quality gates documented for contributors

The portal's contributor docs (`web/README.md` or equivalent) SHALL document every quality gate, the command to run it locally, and the expected output. New contributors MUST NOT have to read CI YAML to discover what runs on their PR.

#### Scenario: Quality-gate commands documented

- **WHEN** a new contributor reads the web README
- **THEN** they see the commands `pnpm typecheck`, `pnpm lint`, `pnpm build`, `pnpm i18n:check`, `pnpm a11y`, and an explanation of what each gate enforces

## MODIFIED Requirements
