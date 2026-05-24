*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

## Context

`dev-portal` delivered the portal MVP — Next.js 14 frontend, Go HTTP API, Keycloak OIDC integration, docker-compose stack, Helm chart, and 88 of 99 implementation tasks. Three known issues remained when the live smoke test wrapped:

1. `next-intl` middleware-based routing was disabled because the pages were scaffolded directly under `app/` instead of `app/[locale]/`.
2. The `web/Dockerfile` build failed because pnpm's strict isolation hides `styled-jsx` (an implicit Next.js 14 runtime dependency) from the top-level node_modules, and the standalone-output trace doesn't follow the hoisted layout reliably.
3. The translation-parity CI check and the axe-core accessibility test referenced in the `portal-web` spec (M8 group) had not been implemented.

Each of these is a small, contained fix. Bundling them in one change keeps the cognitive overhead low: one branch, one review, one archive. The change also pins the quality gates to a new capability `portal-quality-gates` so the next time someone wonders "what stops a PR from regressing i18n or a11y?", there's a spec to point at.

## Goals / Non-Goals

**Goals:**

- `web/app/[locale]/` is the canonical page tree; next-intl middleware is back to its proper routing role; the locale switcher in the header actually switches locales.
- `docker compose up` brings up the web container cleanly on macOS, Linux, and Windows hosts.
- Every PR runs a translation-parity check and an axe-core a11y test; both gate merges.
- `KNOWN_ISSUES.md` shrinks to only the items still open after this change.
- `dev-portal` becomes archivable.

**Non-Goals:**

- New product surface (no new pages, no new API endpoints).
- Lighthouse Performance score as a gating CI step — recorded locally for the pilot; gating lands when a sample CI runner with a stable performance profile is identified (`ops-readiness`).
- Real-user-monitoring instrumentation — separate change.
- Migrating from pnpm to npm/yarn project-wide — only the Docker image's install layer may change tooling if the npm-in-Docker route is chosen.
- Full WCAG 2.1 AAA pass — AA is the floor, AAA is aspirational.

## Decisions

### Locale routing: move pages to `app/[locale]/` and restore the next-intl middleware

**Choice:** Every page under `web/app/` moves to `web/app/[locale]/`. The root `app/layout.tsx` stays at the top level (Next.js requires it there); a `app/[locale]/layout.tsx` becomes the locale-scoped layout. The middleware reverts from passthrough to `createMiddleware({ locales, defaultLocale, localePrefix: "as-needed" })`. The locale switcher rewrites the URL between `/` (Spanish, default), `/en/...`, and `/es/...`.

**Why:** This is the canonical next-intl v4 setup for App Router. The temporary passthrough we shipped in `dev-portal` was a known-bad workaround. The refactor is mechanical: file moves + import path updates + restoring 6 lines of middleware code.

**Alternatives considered:**

- **Static export per locale with no middleware.** Loses RSC freshness for the catalog pages. Rejected.
- **Subdomain-per-locale (`es.fdh.forge.internal`, `en.fdh.forge.internal`).** Cleaner separation but doubles the TLS cert work and requires DNS coordination. Out of proportion for two languages.

### Docker web build: switch the install layer to npm + keep pnpm for local dev

**Choice:** The Dockerfile's `deps` stage runs `npm ci` instead of `pnpm install --frozen-lockfile`. A `package-lock.json` is generated from the same `package.json` and committed alongside `pnpm-lock.yaml`. Local developers continue to use pnpm (faster, less disk); CI and Docker use npm (flatter trees, no styled-jsx hoist problem).

**Why:** Two lockfiles in the repo are a maintenance tax, but a small one. The alternative is fighting pnpm's strict hoisting + Next.js 14's implicit runtime dependencies in Docker for every release. The cost of "remember to update both lockfiles" is well-known and tooling-supportable (a CI step that runs `pnpm install --lockfile-only && npm install --package-lock-only` and fails if either lockfile drifts). The benefit is: Docker builds always work, the standalone output's file trace always resolves, and we stop spending time on hoist edge cases.

**Alternatives considered:**

- **Stay on pnpm with `shamefully-hoist=true` in Docker.** The hoist works for `next` but `output: "standalone"` still misses `styled-jsx` in some edge cases because the file tracer doesn't follow the pnpm symlink layout reliably. We saw this fail in the dev-portal verification.
- **Pin Next.js to a version that declares `styled-jsx` explicitly.** Next 14 is what works with the rest of our stack (Auth.js v5 beta, next-intl v4); changing Next is a much bigger refactor.
- **Switch the whole project to npm.** Loses pnpm's content-addressable store benefits in dev. Worse trade.

### Quality gates: Playwright + axe-core for a11y, a tiny Node script for parity

**Choice:**

- `scripts/check-i18n-parity.mjs` — reads `messages/es.json` and `messages/en.json`, computes the symmetric difference of their key sets, prints any divergence, and exits non-zero on disagreement. ~30 lines of code, no extra dependencies (uses `fs` and `JSON.parse`).
- `tests/a11y/portal.spec.ts` — a Playwright test that boots the dev server, navigates to every public page, runs `@axe-core/playwright` against each, and fails the test on any `serious` or `critical` violation. Auth-gated pages are excluded (separate concern; they need a real Keycloak in the test runner).

Both gates run in the existing CI workflow as new jobs alongside the existing typecheck + build steps. Both have a local shortcut: `pnpm i18n:check` and `pnpm a11y`.

**Why:** Playwright + axe-core is the most-trodden path for app-level a11y testing. The parity script is small enough that pulling in a dedicated i18n linter library would be heavier than the script itself.

### KNOWN_ISSUES.md: shrink to only what's still open

**Choice:** After this change, `docs/KNOWN_ISSUES.md` retains only port-conflict caveats (issue #4) and any net-new issues discovered during verification. Issues #1 (Docker web), #2 (Keycloak issuer), and #3 (locale segment) are removed once their fixes verify.

Note that issue #2 (Keycloak issuer URL mismatch in compose) is NOT in this change's scope. The fix is documented in `KNOWN_ISSUES.md` as "front Keycloak with a reverse proxy"; doing it requires a 4th compose service (nginx) and we'd rather not grow compose for an issue that only matters when the API is dockerized, which is itself an optional local-dev mode. If we hit it during verification, it gets handled in a follow-up.

## Risks / Trade-offs

- **Risk: The locale refactor breaks every page's URL.** → **Mitigation:** Playwright a11y suite (added in this same change) doubles as a smoke test that hits every page after the refactor — if a route is broken, the a11y test catches it before merge.

- **Risk: Two lockfiles drift apart.** → **Mitigation:** a CI step verifies both lockfiles are consistent with `package.json` by running `pnpm install --lockfile-only && npm install --package-lock-only` and checking the working tree is clean. Failure pinpoints which file needs regeneration.

- **Risk: axe-core flags pre-existing a11y issues we hadn't noticed.** → **Mitigation:** the test is added in the same PR as the page moves. Any finding either gets fixed in the same PR or is added to a deliberate `axe.disableRules([...])` list with a tracking comment. The default policy is fix-now; only intentional exceptions get suppressed.

- **Trade-off: Two lockfiles = small maintenance tax.** Documented; the CI consistency check makes it a known-finite cost.

- **Trade-off: Lighthouse is observed but not gated.** A baseline number is recorded; making it a gate happens once a stable runner profile is available. Until then, performance is monitored, not enforced.

## Migration Plan

The change sequences as five milestones, executed in order:

- **MH1 — Locale refactor.** Move every page under `web/app/[locale]/`. Restore the next-intl middleware. Update the locale switcher to use `next-intl/navigation` properly. Verify by visiting `/`, `/es/skills`, `/en/skills`, `/en/install` against the dev server — all return 200 with the right locale's strings.
- **MH2 — Web Dockerfile fix.** Generate `package-lock.json`. Rewrite the Dockerfile's deps stage to use npm. Verify `docker compose up web` produces a healthy container.
- **MH3 — Translation parity CI gate.** Add `scripts/check-i18n-parity.mjs`, expose via `pnpm i18n:check`, wire into `.github/workflows/ci.yml`. Verify a deliberate test-only divergence fails the script.
- **MH4 — axe-core a11y CI gate.** Install Playwright + `@axe-core/playwright`. Write `tests/a11y/portal.spec.ts` covering 5 public pages. Wire into CI as a new job. Verify against the running dev server.
- **MH5 — KNOWN_ISSUES.md cleanup + verification.** Remove the three closed issues. Run the full local stack (`docker compose up`) end-to-end; verify the demo flow from the dev-portal verification run still works against the cleaned-up setup.

**Rollback:** every milestone's commits are independently revertable. If MH1's locale refactor breaks something subtle, revert that commit; the other milestones are unaffected. Lockfiles can be regenerated from `package.json` at any time.

## Open Questions

- **Q1.** Does Forge's CI runner have enough memory to run Playwright + a Chromium download in addition to the existing Go + Next build? If not, the a11y job needs its own runner or has to run on a self-hosted agent. **Pragmatic default:** assume GitHub Actions hosted runners suffice (they do for most projects this size); switch to self-hosted if the job times out in real CI.
- **Q2.** Keep both `pnpm-lock.yaml` and `package-lock.json` in the repo, or drop the pnpm one entirely? Keeping both lets local devs choose; dropping pnpm simplifies the story. **Default:** keep both for the pilot, revisit after one quarter of pilot use.
- **Q3.** Should this change also lift the deferred Lighthouse check from observation to gating? **Default:** no — the gate needs a stable runner profile we don't have yet. Observe in this change, gate in `ops-readiness`.
