*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

## 1. MH1 — Locale refactor

- [x] 1.1 Create `web/app/[locale]/` and move every existing page directory into it: `page.tsx` (landing), `install/`, `skills/`, `skills/[namespace]/[name]/`, `profile/`, `admin/`, `auth/signin/`, `auth/signout/`, `onboarding/`.
- [x] 1.2 Keep `web/app/layout.tsx` at the top level (Next.js requires the root layout there) and add `web/app/[locale]/layout.tsx` that handles locale-specific provider wiring (`NextIntlClientProvider` moves there).
- [x] 1.3 Restore `web/middleware.ts` to use `createMiddleware({ locales, defaultLocale, localePrefix: "as-needed" })`. Remove the passthrough fallback.
- [x] 1.4 Restore `web/i18n.ts` `getRequestConfig` to read locale from `requestLocale` and load the matching messages file.
- [x] 1.5 Update `LocaleSwitcher` to use `next-intl`'s `useRouter`/`usePathname` so locale changes preserve the current path and query parameters.
- [x] 1.6 Update `app/api/auth/[...nextauth]/route.ts` and `app/api/onboarding/activation/route.ts` to live OUTSIDE the `[locale]` segment (API routes are locale-agnostic).
- [x] 1.7 Smoke: visit `/`, `/skills`, `/en`, `/en/skills`, `/en/install` against the dev server; all return 200 with the correct locale's strings.

## 2. MH2 — Web Dockerfile fix

- [x] 2.1 Generate `web/package-lock.json` by running `npm install --package-lock-only` from `web/`. Commit alongside the existing `web/pnpm-lock.yaml`.
- [x] 2.2 Rewrite `web/Dockerfile`'s `deps` stage to `RUN npm ci --no-audit --no-fund` (no corepack, no pnpm).
- [x] 2.3 Rewrite the `builder` stage to `RUN npm run build`.
- [x] 2.4 Keep `.npmrc` in the repo for the pnpm dev path; the Docker image bypasses it because npm doesn't read `.npmrc` `shamefully-hoist`.
- [x] 2.5 Add a CI step that runs `pnpm install --lockfile-only && npm install --package-lock-only && git diff --quiet` and fails if either lockfile drifts.
- [x] 2.6 Smoke: `docker compose build web` produces a clean image; `docker compose up web` boots and `curl localhost:3000/` returns 200.

## 3. MH3 — Translation parity CI gate

- [x] 3.1 Author `web/scripts/check-i18n-parity.mjs`: load both message JSONs, recurse into nested objects, compute symmetric difference of dotted-key sets, print divergence as `MISSING en: foo.bar`, exit non-zero on any divergence.
- [x] 3.2 Add `"i18n:check": "node scripts/check-i18n-parity.mjs"` to `web/package.json` scripts.
- [x] 3.3 Add a CI job step in `.github/workflows/ci.yml`: `cd web && pnpm i18n:check`.
- [x] 3.4 Smoke: add a temporary extra key in one locale file, confirm the script exits non-zero and names the missing key; remove the test key.

## 4. MH4 — axe-core accessibility CI gate

- [x] 4.1 Add Playwright + `@axe-core/playwright` to `web/devDependencies`.
- [x] 4.2 Initialize Playwright config (`web/playwright.config.ts`) with a `webServer` block that launches `next dev` on a CI-stable port and Chromium-only browser project.
- [x] 4.3 Author `web/tests/a11y/portal.spec.ts`: for each of `/`, `/install`, `/skills`, `/skills/security/owasp-quick-review`, `/onboarding`, navigate, await load, run `new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze()`, assert zero violations with `impact: "serious" | "critical"`.
- [x] 4.4 Add `"a11y": "playwright test --grep @a11y"` script to `web/package.json`. Tag the spec with `@a11y` for grep selectivity.
- [x] 4.5 Add a CI job in `.github/workflows/ci.yml` that installs Playwright browsers (`pnpm exec playwright install --with-deps chromium`) and runs `pnpm a11y`.
- [x] 4.6 Smoke: `pnpm a11y` runs locally against `pnpm dev` and exits zero (modulo any pre-existing violations — fix them as discovered before merging).

## 5. MH5 — Cleanup + verification

- [x] 5.1 Update `docs/KNOWN_ISSUES.md`: remove issues #1 (Web Docker build) and #3 (locale segment). Keep issue #4 (port conflicts). Keep issue #2 (Keycloak issuer) with a note that it remains open and tracked separately.
- [x] 5.2 Update `web/README.md` (or create it if missing) with the full quality-gate command list: `pnpm typecheck`, `pnpm lint`, `pnpm build`, `pnpm i18n:check`, `pnpm a11y`, plus a one-line explanation of each.
- [x] 5.3 Final E2E: bring up the full stack (`docker compose up` — including the now-working web container), drive a manual flow: visit `/`, switch locale to English, browse skills, open a skill detail, copy the install command, navigate to `/onboarding`, advance two steps. Confirm everything works.
- [x] 5.4 Run the full Go test suite + the new Playwright suite + every `pnpm` quality gate; everything green.
- [ ] 5.5 Archive this change via `openspec archive portal-hardening`.
- [ ] 5.6 Archive `dev-portal` via `openspec archive dev-portal` (now that its three documented gaps are closed).
