*Brand strings updated 2026-05-23 by the rebrand-to-forge-development-hub change; original wording used "forge".*

## 1. CLI rename — `fdh` → `fdh`

- [x] 1.1 Create new repository `forge/fdh` at the Git host; mirror branch protection and CI variables from `forge/skill-installer`.
- [x] 1.2 Initial commit: copy the current `forge/skill-installer` tree into the new repo unchanged so history is preserved by `git push --mirror` (alternative: fresh init — pick one and justify in the new repo's README).
- [x] 1.3 Rename Go module: `go mod edit -module github.com/forge/fdh` and run a tree-wide find/replace from `github.com/forge/skill-installer` to `github.com/forge/fdh`.
- [x] 1.4 Rename the binary directory: `cmd/fdh/` → `cmd/fdh/`. Update `Taskfile.yml` `BINARY` variable, `go build` paths, and the `release.yml` workflow's artifact names to `fdh-<version>-<os>-<arch>.tar.gz`.
- [x] 1.5 Move config directory defaults: change `defaultConfigDir()` in `internal/cli/root.go` to return `<user-config>/fdh` instead of `<user-config>/fdh`.
- [x] 1.6 Implement legacy config read fallback: `defaultConfigDir()` callers also check `<user-config>/fdh/<file>` when the new path is absent; emit a one-line deprecation warning to stderr on use.
- [x] 1.7 Add `fdh config migrate` subcommand that copies `~/.config/fdh/*` to `~/.config/fdh/*`, preserving values, idempotent on re-run.
- [x] 1.8 Build the stub binary `cmd/fdh-stub/main.go`: 30-line program that prints the deprecation notice, looks up `fdh` on PATH, forwards args and exit code, or exits 127 with install hint if missing.
- [x] 1.9 Update `release.yml` to publish BOTH `fdh` (primary) and `fdh` (stub) binaries for 90 days; document the sunset date in `docs/release.md`.
- [x] 1.10 Update every doc under `docs/` to reference `fdh` and the new config directory; preserve a single `docs/migration.md` page explaining the rename.
- [x] 1.11 Update README, CHANGELOG, and the OpenSpec hub's CLAUDE.md (if it references the binary name).
- [x] 1.12 Run the full test suite on the renamed module and binary; confirm all 97+ tests pass.
- [x] 1.13 Publish a deprecation announcement: Slack post + release notes calling out the rename, the 90-day stub, and the one-line migration command.

## 2. Portal API scaffolding

- [x] 2.1 Create `cmd/fdh-portal-api/main.go` with a basic `net/http` server, graceful shutdown on SIGTERM, and a `/healthz` endpoint returning `{"status":"ok"}`.
- [x] 2.2 Add `internal/portalapi/` package: `server.go` (handler registration), `middleware.go` (logging, trace context, request ID), `errors.go` (typed errors with HTTP status mapping).
- [x] 2.3 Define the OpenAPI 3.1 spec at `internal/portalapi/openapi.yaml` covering every endpoint declared in the `portal-api` spec.
- [x] 2.4 Wire `oapi-codegen` (or equivalent) into the build: regenerate Go server stubs from `openapi.yaml` on every build; commit the generated code; CI fails if regen produces a diff.
- [x] 2.5 Implement `GET /api/v1/skills` handler: reads from `pkg/registry`, applies filters from query params, paginates with cursor-based opaque tokens.
- [x] 2.6 Implement `GET /api/v1/skills/{namespace}/{name}` handler.
- [x] 2.7 Implement `GET /api/v1/skills/{namespace}/{name}/versions/{version}` handler.
- [x] 2.8 Implement `GET /api/v1/skills/{namespace}/{name}/versions/{version}/skill-md` handler — serves raw markdown.
- [x] 2.9 Implement `GET /api/v1/auth/me` handler (returns anonymous when no auth context attached).
- [x] 2.10 Implement `GET /readyz` returning 503 until the first registry read succeeds, 200 thereafter.
- [x] 2.11 Implement the 60-second auto-refresh goroutine; expose interval via env var `FDH_PORTAL_REFRESH_INTERVAL` (default `60s`).
- [x] 2.12 Implement `POST /api/v1/refresh` (auth-gated, role >= publisher) that forces an immediate refresh and returns the resulting index summary.
- [x] 2.13 Implement SIGHUP handler to trigger an immediate refresh.

## 3. Portal API auth + observability

- [x] 3.1 Add `internal/portalapi/auth/` package: OIDC token validation via `go-oidc`, JWKS caching with `kid`-based rotation, role-map loader from a YAML file referenced by `OIDC_ROLE_MAP_PATH`.
- [x] 3.2 Add an auth middleware that extracts and validates the bearer token, attaches a `User` to the request context (anonymous when no token), and uses the role-map to derive a portal role.
- [x] 3.3 Implement role precedence resolution: `anonymous < consumer < author < reviewer < publisher < admin`.
- [x] 3.4 Add `GET /metrics` Prometheus handler with request count, request duration histogram (by route + status), registry refresh metrics, in-memory cache size, and standard Go runtime metrics.
- [x] 3.5 Wire OpenTelemetry tracing: instrument all HTTP handlers, propagate W3C trace context, export via OTLP to `OTEL_EXPORTER_OTLP_ENDPOINT`.
- [x] 3.6 Wire structured `slog` JSON logger; every request log line includes `time`, `level`, `msg`, `trace_id`, `route`, `status`, `latency_ms`, `user_id`.
- [x] 3.7 Unit + integration tests: anonymous request returns 200 to public routes; invalid token returns 401; valid token populates `User` correctly; role precedence resolution matches the spec.

## 4. Frontend scaffolding

- [x] 4.1 Create the `web/` directory at the repo root (or in a separate `forge/fdh-portal-web` repo — decide and document). `pnpm create next-app` with TypeScript, Tailwind, ESLint, App Router.
- [x] 4.2 Configure `tsconfig.json` with `strict: true`, `noUncheckedIndexedAccess: true`. CI runs `tsc --noEmit`.
- [x] 4.3 Configure ESLint with `next/core-web-vitals` plus a small custom rule set (no console.log in production code, sorted imports).
- [x] 4.4 Vendor shadcn/ui: run `npx shadcn-ui init`, copy the core components (button, card, input, dialog, tabs, dropdown-menu, sheet, scroll-area) into `components/ui/`.
- [x] 4.5 Author Forge theme tokens in `tailwind.config.ts`: primary/secondary/accent/neutral/semantic colors, the brand font family (Geist or the org font), spacing scale.
- [x] 4.6 Implement the navigation shell: header with logo, primary nav, search box, locale switcher, theme toggle, sign-in CTA / user menu.
- [x] 4.7 Implement the footer: build version, links to docs, terms, accessibility statement.
- [x] 4.8 Implement the layout root with `<html lang>` driven by locale, `<main>` landmark, skip-to-content link.

## 5. Frontend pages — public

- [x] 5.1 Landing page (`/`): hero section, three CTAs above the fold, brief feature list, social proof placeholder.
- [x] 5.2 Install CLI page (`/install`): OS detection via `User-Agent` header (server-side), per-platform tabs, copy-buttons, SHA-256 verification commands.
- [x] 5.3 Browse page (`/skills`): server-rendered list, filters (namespace, tag, scan status), pagination, debounced search input (250ms).
- [x] 5.4 Search URL state: search query in `?q=...` reflected by Next.js router; back/forward navigation works.
- [x] 5.5 Skill detail page (`/skills/[namespace]/[name]`): renders SKILL.md client-side via `react-markdown` + `rehype-highlight`; shows the `fdh install` command with a copy button at the top; lists version history (collapsible); shows owner team + tags + scan status.
- [x] 5.6 Version detail page (`/skills/[namespace]/[name]/versions/[version]`): like skill detail but pinned to a specific version.
- [x] 5.7 Per-agent install variants on the skill detail page: expandable section with the four `--agent <id>` variants, each with its own copy button.
- [x] 5.8 404 / error pages with branded layouts.

## 6. Frontend pages — authenticated

- [x] 6.1 Configure Auth.js (`@auth/nextjs`) with the Keycloak provider; environment-driven config (`KEYCLOAK_ISSUER`, `KEYCLOAK_CLIENT_ID`, `KEYCLOAK_CLIENT_SECRET`).
- [x] 6.2 Implement the sign-in flow: `/auth/signin` redirects to Keycloak with PKCE; callback at `/auth/callback`; honor `redirect_to` query param.
- [x] 6.3 Implement the sign-out flow: clear session cookie, call Keycloak's RP-initiated logout, redirect to landing.
- [x] 6.4 Implement Profile page (`/profile`): displays user info from `/api/v1/auth/me`, locale and theme preferences (already managed elsewhere — show here for reference), placeholder for favorites.
- [x] 6.5 Implement the auth middleware (Next.js middleware.ts) that gates `/profile`, `/admin`, and any other `auth-required` route, redirecting anonymous users to `/auth/signin` with `redirect_to`.
- [x] 6.6 Implement Admin shell (`/admin`): role-gated (`admin` only), shows: total skills, total versions, last refresh timestamp, button to trigger `POST /api/v1/refresh`, link to `/api/v1/admin/activation` log.

## 7. Onboarding wizard

- [x] 7.1 Create the wizard route at `/onboarding` with seven sequential screens matching the steps in the `portal-onboarding` spec.
- [x] 7.2 Persist wizard progress to a session-id-keyed cookie; resume from last completed step on return.
- [x] 7.3 Emit `event=activation` structured log lines on every step completion (or skip), including `step`, `wizard_session_id`, `user_id`, `locale`, `os`.
- [x] 7.4 Implement `GET /api/v1/admin/activation` (Go) returning a paginated list of recent activation events from the in-memory ring buffer.
- [x] 7.5 Implement the recommended-starter-skill mechanism: server-side config map (default `code-review/checklist`); rendered as a callout on step 6.
- [x] 7.6 Implement the "What's next" panel as a shared component used by the wizard final screen and by post-install success states.

## 8. Internationalization

- [x] 8.1 Install and configure `next-intl`; locales `es` (default) and `en`.
- [x] 8.2 Externalize every user-facing string into per-page message tables (`messages/es.ts`, `messages/en.ts`).
- [x] 8.3 Implement locale-aware routing: `/es/skills` and `/en/skills` resolve to the same content with translated UI; the default locale serves without a prefix.
- [x] 8.4 Implement the locale switcher in the navigation; persist choice in a cookie.
- [ ] 8.5 Add a CI check that verifies every key in `messages/es.ts` exists in `messages/en.ts` and vice versa.
- [x] 8.6 Translate the wizard screens, the install page, the skill detail strings, and all navigation chrome.

## 9. Accessibility + dark mode

- [x] 9.1 Implement the theme provider: `system` default, `light`/`dark` overrides, persisted to `localStorage`, no flash on first paint (next-themes pattern).
- [x] 9.2 Theme toggle in the navigation.
- [ ] 9.3 Add an `<axe-core>` Playwright accessibility test that runs against every page and fails CI on `serious` or `critical` violations.
- [ ] 9.4 Manual keyboard-navigation audit: Tab through landing, install, browse, skill detail; document any focus-order issues.
- [x] 9.5 Color-contrast audit using the Tailwind theme tokens; bump any pair below 4.5:1 for body text or 3:1 for large text.
- [x] 9.6 Verify every form input has a `<label>`, every image has alt text or `role="presentation"`, every page has a single `<h1>` and a logical heading hierarchy.

## 10. Local-dev infrastructure

- [x] 10.1 Add `compose.yml` at the repo root: services for `keycloak`, `fdh-portal-api`, `fdh-portal-web`, plus a pre-built fixture registry mounted as a volume.
- [x] 10.2 Author a Keycloak realm export `compose/keycloak/realm-fdh.json` with: realm `fdh-dev`, OIDC client `fdh-portal` (confidential with client_secret `dev-secret`), redirect URIs for `http://localhost:3000/auth/callback`, three test users with different group memberships.
- [x] 10.3 Add `compose.fixture.yml` overlay: runs `scripts/build-fixture-registry` against a volume mount so the API and Web see the 8 SDLC seed skills.
- [x] 10.4 Document the local-dev flow in `docs/local-dev.md`: clone → `docker compose up` → wait for healthy → open `http://localhost:3000`.
- [x] 10.5 Add `air` (or equivalent) configuration so the Go API hot-reloads on file changes; the Next.js dev server already supports hot reload.

## 11. Production deployment (Helm)

- [x] 11.1 Create `deploy/helm/fdh-portal/` with `Chart.yaml`, `values.yaml`, and templates.
- [x] 11.2 Define two Deployments: `fdh-portal-api` (Go) and `fdh-portal-web` (Next.js Node runtime). HPA on CPU. Resource requests/limits in `values.yaml` defaults.
- [x] 11.3 Define one Ingress fronting both at `https://fdh.forge.internal`: `/api/*` → API service, all other paths → Web service.
- [x] 11.4 Define the Keycloak client secret as a Kubernetes Secret referenced from the API deployment; document the platform-team handoff in `docs/deploy.md`.
- [x] 11.5 Define a Prometheus ServiceMonitor scraping `/metrics` from the API.
- [x] 11.6 Define an OpenTelemetry collector connection via `OTEL_EXPORTER_OTLP_ENDPOINT` env var bound from a values setting.
- [x] 11.7 Smoke-test the chart against a real (or kind) cluster: deploy, verify `/healthz`, `/readyz`, anonymous catalog load, OIDC redirect.
- [x] 11.8 Document the operator runbook (`docs/runbook.md`): how to refresh the registry, how to roll a new version, how to debug a failing OIDC flow.

## 12. Documentation

- [x] 12.1 Update `docs/getting-started.md` to use `fdh` everywhere and add a "Where the portal lives" section pointing at `https://fdh.forge.internal`.
- [x] 12.2 Add `docs/portal-admin.md`: covers admin-shell features, role mappings, refresh procedure, activation log inspection.
- [x] 12.3 Add `docs/migration.md`: explains the `fdh` → `fdh` rename, the 90-day stub, and the `fdh config migrate` command with examples.
- [x] 12.4 Update `docs/quickstart.md` to mention the portal as the recommended discovery path, with the CLI install commands also presented inline for advanced users.
- [x] 12.5 Author `docs/keycloak-setup.md`: the one-page handoff for the platform identity team — realm name, client ID, redirect URIs, required claims, role mapping examples.

## 13. Final acceptance

- [ ] 13.1 Run the full Go test suite + Playwright E2E suite + accessibility tests; everything green on macOS, Linux, and Windows.
- [ ] 13.2 Lighthouse audit on the landing page (target: Performance ≥ 90) and the skill detail page (target: Performance ≥ 85). Address any regressions.
- [ ] 13.3 Confirm bundle size: landing page first-load JS ≤ 200 KB gzipped.
- [ ] 13.4 Deploy to a staging cluster, run an end-to-end smoke (anonymous browse → OIDC login → admin refresh → wizard completion → CLI install of recommended skill).
- [ ] 13.5 Pilot dry-run with 5 developers: each completes the wizard and reports issues; capture every blocker in the change history.
- [ ] 13.6 Cut the v1.0.0 release of the `fdh` CLI and the portal images. Coordinate with the platform team to flip the production Keycloak client from "test" to "active".
- [ ] 13.7 Update the OpenSpec hub's CLAUDE.md to reflect the FDH product identity.
- [ ] 13.8 Archive this change via `/opsx:archive dev-portal` once the pilot dry-run passes and the four open questions in design.md are resolved.
