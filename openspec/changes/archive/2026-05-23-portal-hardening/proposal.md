## Why

The `dev-portal` change shipped 88 of 99 tasks. The remaining gap is a small set of polish items captured in `docs/KNOWN_ISSUES.md` plus two CI gates from M8 (i18n parity + automated accessibility) that the existing `portal-web` spec declares but the implementation hadn't operationalized yet. Closing this gap lets us archive `dev-portal` cleanly and hand the portal to a 30-developer pilot with no documented caveats — and lifts the deferred quality gates from "aspirational" to "enforced in CI", which is a genuine spec-level commitment, not just implementation work.

## What Changes

- **Refactor frontend routing under `app/[locale]/`** so next-intl's middleware-based locale routing works end-to-end. Pages move from `web/app/<page>/` to `web/app/[locale]/<page>/`. The locale switcher in the header (already shipping) becomes functional; `/`, `/en/`, `/es/` resolve as documented.
- **Fix `web/Dockerfile`** so `docker compose up` brings up the web container without manual workarounds. The pnpm-strict-hoist + Next.js 14 styled-jsx interaction is resolved either by switching the install layer to npm/yarn or by adjusting the standalone output trace to follow the hoisted layout. The fix is verified by a clean `docker compose up` against the existing local-dev stack.
- **Add a translation-parity CI gate**: a small script that fails CI when `messages/es.json` and `messages/en.json` disagree on key set. The script runs in the existing CI workflow and is also exposed as `pnpm i18n:check`.
- **Add an axe-core accessibility CI gate**: a Playwright test that visits every public page, runs axe-core against each, and fails CI on any `serious` or `critical` violation. The test is also runnable locally via `pnpm a11y`.
- **Update `KNOWN_ISSUES.md`** to remove the three issues this change closes (issues #1, #2 if Dockerfile fix lands cleanly, and #3 locale refactor). Issue #4 — port conflicts with other locally-running projects — is environmental and stays documented.
- **Update `compose.yml`** to drop the manual port overrides (`18088` / `28080`) and add a short note in `docs/local-dev.md` about how to remap if a developer has other things on the standard ports.

## Capabilities

### New Capabilities

- `portal-quality-gates`: The set of automated quality checks that gate every PR against the portal frontend. Covers translation-key parity, accessibility (axe-core), and bundle-size budgets. The capability declares WHAT the gates check, not which tool implements them — Playwright + axe-core are today's implementation; another stack could substitute without a spec change.

### Modified Capabilities

- `portal-web`: The localized routing requirements need clarification — they currently describe locale-aware URLs but don't pin the `app/[locale]/` segment structure that next-intl's middleware requires. Tightening this spec aligns it with how the routing actually works after this change.

## Impact

- **File reorganization**: every page under `web/app/` (landing, install, skills, skills/[ns]/[name], profile, admin, auth/signin, auth/signout, onboarding) moves under `web/app/[locale]/`. The root layout follows. Mechanical, but touches every page file.
- **next-intl middleware**: restored from passthrough to the real `createMiddleware` call. Removes the local workaround put in place during dev-portal M5 verification.
- **`web/Dockerfile`**: substantively rewritten to produce a working image. The compose file's `web` service starts cleanly after this change.
- **New CI dependencies**: Playwright + @axe-core/playwright at devDependency level. Adds ~150 MB to `node_modules`; CI step adds ~30 seconds.
- **New scripts**: `pnpm i18n:check`, `pnpm a11y` (both also wired into `pnpm ci`).
- **No breaking changes** for the CLI (`fdh`) or the Go portal API. This is frontend + Docker work.
- **Unblocks**: archiving `dev-portal`. After this change ships and is itself archived, the dev-portal change can be archived without leaving documented caveats.
- **Sets up future changes**: `governance-full` (server-side approval workflow) will lean on the portal's i18n and a11y baselines already enforced by this change's gates.
