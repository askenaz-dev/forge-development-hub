## Context

The `installer-core` change shipped a working CLI (`falabella-installer`) and a Git-backed registry good enough for a 30-developer pilot. Scaling to the full Falabella engineering org requires a discoverable, browseable web product — not "read READMEs in the registry's GitHub UI" — with the same identity (Keycloak) and roles the rest of Falabella's developer tooling uses. The original build prompt anticipated this in three separate changes (`registry-mvp`, `governance`, `web-ui`), but the user has chosen to deliver a focused subset of all three as a single coherent product (`dev-portal`) so the portal MVP is one decision unit rather than three sequenced ones. The naming rename (`falabella-installer` → `fdh`) lands in the same change so docs and install snippets never reference a stale name.

This change does NOT replace the Git-backed registry with Postgres + MinIO — that storage upgrade stays in a future `registry-storage` change. The portal API reads from the same `pkg/registry.GitRegistry` the CLI uses; both share refreshes. A future change can swap `GitRegistry` for an `HTTPRegistry` without touching the portal.

## Goals / Non-Goals

**Goals:**

- A modern, professional web portal Falabella developers want to use, with full SSR, dark mode, accessibility, and Spanish + English.
- Keycloak OIDC integration that uses Falabella's existing IdP without code-level coupling to Keycloak.
- A first-install onboarding wizard that walks "I just heard about this" → "my first skill is installed" in under 5 minutes.
- A versioned, OpenAPI-documented HTTP API the portal consumes (and that future automation can also consume).
- Rename `falabella-installer` → `fdh` cleanly: new binary, new module, new config directory, with a 90-day back-compat stub.
- Local-dev parity: `docker compose up` brings Keycloak + API + Web online together.
- Production-shaped deploy: Helm chart targeting Falabella's existing Kubernetes platform.

**Non-Goals:**

- Server-side approval workflow / publish-from-portal — deferred to `installer-write-flows` and `governance-full`.
- Postgres + MinIO storage — deferred to `registry-storage`.
- Full audit log + SIEM export — deferred to `governance-full`.
- Skill scanning visualization — deferred to `scan-gate-ui` (the gate engine itself extends `pkg/portability` in a separate change).
- Real adoption analytics dashboards — the portal emits activation events in this change so a future `analytics` change has data to display.
- A mobile app or PWA installability beyond what Next.js gives for free.
- SAML support beyond what the OIDC abstraction implicitly allows.
- Migration of existing pilot devs is announced and supported but not automated org-wide.

## Decisions

### Frontend: Next.js 14 (App Router) + React 18 + TypeScript + Tailwind CSS + shadcn/ui

**Choice:** Next.js 14 with the App Router, React Server Components for SSR-heavy content (skill catalog, skill detail), React 18 client components for interactive pieces (search debounce, copy buttons, dark-mode toggle). TypeScript strict mode. Tailwind CSS for utility-first styling. shadcn/ui as the component library, vendored into the repo (not a runtime dependency).

**Why:** Next.js is the most-trodden path for modern developer-tools UIs (Vercel docs, Linear marketing, Stripe docs, GitHub Copilot). The App Router's Server Components let the skill catalog render server-side with no client-side waterfall, while the search box stays a small interactive client island. Tailwind + shadcn/ui is the standard combination for shipping a high-quality design system fast without coupling to a heavy UI framework — components are owned and vendored, so we customize freely.

**Alternatives considered:**

- **Astro.** Strong for content-first sites. Loses on the interactive portions (admin shell, search UX) where Next's RSC model is more flexible.
- **Plain React + Vite + react-router.** Lighter, no SSR. Loses SEO and first-paint speed for the catalog pages where it matters.
- **Remix.** Equally good technically; chose Next for ecosystem familiarity in the Falabella org.

### Backend: Go, separate process from the frontend

**Choice:** A new Go binary `fdh-portal-api` in the same module as the CLI (`github.com/falabella/fdh/cmd/fdh-portal-api/`). It depends on the same `pkg/registry`, `pkg/bundle`, `pkg/portability` libraries the CLI already uses. The frontend (Node.js) talks to the backend (Go) over JSON HTTP behind a single Ingress.

**Why:** Reuse of `pkg/registry` and `pkg/bundle` is the single biggest win — there is exactly one definition of "what is the registry layout" and "what is a valid bundle". Running the frontend on Node lets us use the standard Next.js production runtime (no SSG-only constraints) and keeps the design space open for future server-side personalization. Two containers, one deployment unit.

**Alternatives considered:**

- **Embed Next.js's static export into the Go binary via go:embed.** Single binary, simplest deploy. Loses RSC/SSR — every personalized view would need to be client-side, which hurts the install-command snippet experience.
- **Single TypeScript/Node backend (no Go).** Would force porting `pkg/registry`, `pkg/bundle`, `pkg/portability` to TS or calling the Go libs as a sidecar. Pure duplication; rejected.
- **Direct frontend → Git registry (no backend).** Possible via static export of the index. Loses search, version history dynamics, and any future scan-result rendering. Rejected.

### Auth: OIDC Authorization Code with PKCE; Keycloak as the reference IdP; abstracted

**Choice:** The backend uses `github.com/coreos/go-oidc/v3` and `golang.org/x/oauth2` for OIDC. The frontend uses Auth.js (formerly NextAuth) with its Keycloak provider for the user-facing flow. Sessions are HTTP-only secure cookies signed by the Next.js server; the cookie carries an opaque session ID that maps to the JWT held server-side. The Go backend validates the JWT presented by the frontend via a service-to-service token exchange (or proxies via the Next.js server, with the Next.js server attaching the JWT to its outbound API calls — TBD based on Keycloak realm config). PKCE is mandatory.

**Why:** Auth.js is the standard for Next.js auth; `go-oidc` is the standard for Go OIDC. Both are well-maintained, have Keycloak provider configs documented, and abstract over the wire. The OIDC abstraction at the backend level means the IdP can be replaced (e.g., Entra ID) by changing the discovery URL — no provider-specific code paths.

Anonymous browsing of catalog pages is permitted; only profile and admin views require auth. This matches developer-tools convention (Stripe docs, Vercel docs) and reduces friction for browsing.

Roles flow from Keycloak as the `groups` (or `roles`) JWT claim, mapped to portal roles `consumer | author | reviewer | publisher | admin` via a small `claim_role_map` configuration. Unmapped claims default to `consumer`. Anonymous = `anonymous` (no portal role at all).

**Alternatives considered:**

- **SAML.** Keycloak supports both; OIDC is the modern standard and simpler to wire on the Next.js side via Auth.js. SAML support remains possible later via a different Auth.js provider, no portal code change.
- **Custom session JWT issued by our backend.** More control, more rope. The Auth.js cookie + Keycloak token model is enough.

### Database / state: none for the MVP; everything reads from Git

**Choice:** No database in this change. The portal API caches the Git registry contents in-memory and refreshes on a 60-second interval (configurable) or on SIGHUP. The frontend is stateless beyond the session cookie. Activation events emitted by the onboarding wizard go to a structured log line (`event=activation step=cli-installed user_id=...`) for future analytics ingestion; no database write.

**Why:** The portal's MVP scope is read-only with respect to the registry. Adding Postgres just to hold favorites or activation telemetry inflates the deployment footprint without changing the user-visible value. Both can be added in the future without breaking the portal's contracts — favorites become a thin REST endpoint backed by Postgres; activation telemetry becomes whatever ingestion pipeline the analytics team prefers.

**Alternatives considered:**

- **Postgres for sessions + favorites + activation telemetry.** Right answer eventually; wrong answer for an MVP that ships in 6–8 weeks.
- **SQLite embedded in the API.** Tempting for sessions, but Auth.js's cookie model already handles sessions and SQLite plus a long-running Go service is awkward on Kubernetes.

### CLI rename: new module, new binary, 90-day back-compat stub

**Choice:** Move the Go module from `github.com/falabella/skill-installer` to `github.com/falabella/fdh`. The binary becomes `fdh` (`.exe` on Windows). The per-user config directory moves to `~/.config/fdh/` (and the OS equivalents). For 90 days, the old binary `falabella-installer` continues to ship as a 30-line stub: it prints a deprecation notice to stderr and forwards every argument to the `fdh` binary if found on PATH, else suggests the install command. The Go module rename is a mechanical refactor handled in one PR; no API change.

A `fdh config migrate` subcommand performs the move from the old config directory to the new one explicitly.

**Why:** The "Falabella Development Hub" brand is what the product wants to stand on; `falabella-installer` was always a working title. Renaming once, early, before the broader rollout, is much cheaper than living with a misleading name. The 90-day stub keeps pilot devs unbroken; the migrate subcommand makes the user-visible move explicit and forgiving.

**Alternatives considered:**

- **No rename, keep `falabella-installer`.** Cheaper today; permanent friction in marketing and docs. Rejected.
- **Symlink `fdh` → `falabella-installer`.** Works on Unix; flaky on Windows. The stub-binary approach is OS-uniform.
- **Big-bang break.** Acceptable but unfriendly to the 30 existing pilot users. 90-day overlap is cheap.

### Local dev: Docker Compose bringing up Keycloak + API + Web

**Choice:** A `docker compose up` in the new repo brings up three services: Keycloak (with a pre-seeded realm + test users), the Go API (built locally or via `air` for live reload), and the Next.js dev server. Compose volumes mount the source tree so file changes hot-reload. A `compose.fixture.yml` overlay also boots the fixture skill registry from `scripts/build-fixture-registry/`.

**Why:** Local development needs to be one command. Keycloak is heavy (~400MB image, ~30s startup) but a single dev container suffices for the whole team and dispenses with "configure your local Keycloak manually" friction. The fixture overlay gives every developer the 8 SDLC seed skills from `installer-core` to work against.

### Production deploy: Helm chart, Falabella's existing Kubernetes platform

**Choice:** A Helm chart at `deploy/helm/fdh-portal/` deploys API + Web as separate Deployments (HPA-enabled), with a single Ingress fronting both at `https://fdh.falabella.internal`. Keycloak is NOT deployed by this chart — the platform identity team operates the canonical Keycloak; the chart only takes a values file with the OIDC discovery URL, client ID, and a Kubernetes secret reference for the client secret. Prometheus ServiceMonitor and OTel collector wiring are included.

**Why:** Keycloak is platform-team property; we consume it. The Ingress design lets future products under the FDH umbrella (e.g., a "Pipelines" portal) join the same domain without DNS shuffling.

### i18n: next-intl on the frontend, Spanish + English at parity

**Choice:** `next-intl` library for translations + locale-aware routing. Two locales: `es` (default) and `en`. Source strings live in TypeScript objects per page; a small CI check verifies every key is translated in every locale.

**Why:** Spanish is the org's primary language; English is required for the broader engineering org and non-Spanish contractors. Adding more locales later is additive.

### Design system: Tailwind tokens + shadcn/ui vendored

**Choice:** A Tailwind theme with Falabella-flavored color tokens (primary, secondary, accent, neutral, semantic). shadcn/ui components copied into `web/components/ui/` so we customize freely. Lucide icons. Geist font family (or the Falabella brand font if one exists).

**Why:** This stack ships polished UI fast and is universally familiar in the dev-tools world. shadcn/ui being vendored (not a dependency) means we own the components and can tune them.

### Observability: Prometheus + OpenTelemetry + structured logs

**Choice:** Go API exposes `/metrics` for Prometheus, traces export via OTLP to whatever collector the Falabella platform team operates, logs are JSON to stdout with `slog`. The Next.js app emits the same OTel trace context via `@vercel/otel` (which works for any Node host, not just Vercel).

**Why:** Standard, swappable, the rest of Falabella's platform uses the same shapes.

## Risks / Trade-offs

- **Risk: Keycloak realm configuration friction during platform handoff.** Setting up a confidential OIDC client in the platform team's Keycloak (realm, redirect URIs, scopes, group mappings) requires coordination outside this repo. → **Mitigation:** ship the local-dev Keycloak with the canonical realm export the platform team can review; provide a one-page "what we need from Keycloak" doc as part of the rollout.

- **Risk: Next.js App Router learning curve.** RSC vs client components, the `use client` boundary, streaming, suspense — the model is powerful but trips up engineers new to it. → **Mitigation:** the design document lays out which pages are server vs client; CI rejects `use client` files that import `"react-server"`-only modules; we keep the surface area small for the MVP.

- **Risk: The portal API's 60-second registry refresh is too slow for an author who just published.** → **Mitigation:** expose a `POST /api/v1/refresh` endpoint (auth-protected, role: `publisher` or above) that forces an immediate re-read. Documented in the publish-flow docs.

- **Risk: Rename causes pilot disruption.** The 30 pilot devs need to re-install. → **Mitigation:** 90-day stub keeps the old binary working; release notes link to the one-line migration; `fdh config migrate` automates the config move; Slack announcement coordinates the cutover.

- **Risk: Spec drift between OpenAPI and Go handlers.** Hand-maintained OpenAPI plus hand-written Go handlers always diverges eventually. → **Mitigation:** generate Go server stubs from OpenAPI using `oapi-codegen` so the spec IS the contract; route definitions stay in spec; handler bodies stay in Go. The frontend's API client is similarly generated from the OpenAPI spec via `openapi-typescript`.

- **Risk: Anonymous browsing leaks information that should be authenticated.** Skill descriptions, owner teams, scan status — are these acceptable to expose pre-login? → **Mitigation:** for the MVP, treat the registry contents as "internal" not "secret" — anyone inside Falabella's network can read them. Anonymous browsing is permitted only on the portal's domain (the Ingress is on the internal network). If a skill needs to be private to a team, that's a future change (`portal-access-control`).

- **Risk: Two long-running services raise operational cost.** Compared to one CLI binary, the portal is a real service to operate. → **Mitigation:** keep the surface small, autoscale on CPU, define SLOs and alerts in the Helm chart, document the runbook (which itself becomes the first "real" use of the `operations/runbook-template` seed skill).

- **Trade-off: No database in the MVP.** This means the portal cannot remember favorites, cannot persist activation telemetry, and cannot serve install-count metrics. Those features are designed in but their data layer is future. The user experience says "Favorites coming soon" rather than hiding the affordance.

- **Trade-off: Single Keycloak in the design.** The OIDC abstraction is real and Entra ID could swap in, but for the MVP we test only against Keycloak. Other IdPs are theoretically supported and pragmatically untested.

## Migration Plan

The rollout sequences as eleven milestones. Each milestone is a coherent deliverable that can be demonstrated and reviewed independently; the next one begins as soon as the previous one is accepted. No calendar dates — milestones gate on completion criteria, not on time.

- **M1 — CLI rename complete.** `falabella/fdh` repository exists. CLI renamed: module path, binary name, config directory. Back-compat stub binary for `falabella-installer` published with 90-day deprecation notice. `fdh config migrate` command lands. Full test suite passes against the renamed module on macOS, Linux, Windows. Existing pilot devs can reinstall.
- **M2 — Portal API skeleton.** Go binary `fdh-portal-api` boots, serves `/healthz` and `/readyz`, reads from the shared `pkg/registry`. Catalog endpoints (`GET /api/v1/skills`, `GET /api/v1/skills/{ns}/{name}`, version detail, raw SKILL.md) return real data from the fixture registry. OpenAPI 3.1 spec committed; CI verifies generated Go server stubs match the spec.
- **M3 — Portal API auth + observability.** OIDC token validation via `go-oidc` with JWKS caching and `kid` rotation. Role-map loader (claim → portal role). `GET /api/v1/auth/me` returns anonymous or authenticated user info correctly. Prometheus `/metrics` endpoint, OpenTelemetry trace export, structured `slog` JSON logs. 60-second auto-refresh + SIGHUP + `POST /api/v1/refresh`.
- **M4 — Frontend scaffold.** Next.js 14 App Router project up. Tailwind + shadcn/ui vendored. Falabella theme tokens defined. Navigation header, layout root, footer, theme provider (light/dark/system) all in place. ESLint + TypeScript strict in CI. Builds cleanly; `next build` produces an empty-content production bundle.
- **M5 — Public pages.** Landing, install-CLI (with OS detection + per-platform tabs + SHA-256 commands), browse, search (debounced + URL-stateful), skill detail (rendered SKILL.md + version history + per-agent install variants + copy buttons), version detail, 404. Anonymous access works end-to-end against the fixture registry.
- **M6 — Authenticated pages.** Auth.js configured with Keycloak provider. Sign-in flow with PKCE. Sign-out flow with RP-initiated logout. Profile page reads `/api/v1/auth/me`. Admin shell role-gated. Middleware redirects anonymous users to sign-in for protected routes with `redirect_to` honored.
- **M7 — Onboarding wizard.** Seven-step wizard from "detect your OS" to "open your agent and confirm the skill appears". Progress persists per wizard session. Activation events emitted as structured logs. `GET /api/v1/admin/activation` exposes recent events for inspection. "What's next" panels appear after completion.
- **M8 — i18n + accessibility polish.** `next-intl` wired with `es` (default) and `en`. Every user-facing string externalized. Locale switcher in navigation. CI check for translation parity between locales. Axe-core accessibility test runs against every page in CI; zero `serious`/`critical` violations. Manual keyboard-navigation audit clean.
- **M9 — Local-dev infrastructure.** `docker compose up` brings up Keycloak (with pre-seeded realm + test users), API, Web, and the fixture registry. `compose.fixture.yml` overlay rebuilds the 8 SDLC seed skills on demand. `docs/local-dev.md` covers the one-command flow.
- **M10 — Production deployment.** Helm chart at `deploy/helm/fdh-portal/` deploys API + Web behind a single Ingress at `https://fdh.falabella.internal`. Prometheus ServiceMonitor + OTel collector wiring. Kubernetes Secret references for the Keycloak client secret. Smoke test against a real (or `kind`) cluster passes.
- **M11 — Docs + pilot acceptance.** `docs/getting-started.md` updated to feature the portal. `docs/portal-admin.md`, `docs/migration.md`, `docs/keycloak-setup.md`, `docs/runbook.md` all authored. Lighthouse Performance ≥ 90 on landing, ≥ 85 on skill detail. Pilot dry-run with 5 developers completes. Five open questions in this design resolved. v1.0.0 release cut.

**Rollback strategy:** The portal is purely additive — the CLI continues to work against the same Git registry whether the portal is up or down. The Helm chart is a clean `helm uninstall` away from gone. The CLI rename has the 90-day stub buying time; if the rename itself proves disruptive, the stub can be extended.

**Per-milestone gate:** every milestone ends with a demoable artifact (running binary, deployed service, video walkthrough, or test report) recorded in the change's history. The next milestone does not start until the gate is signed off — either by self-review against the spec's scenarios or by a teammate review, whichever the org prefers.

## Open Questions

- **Q1.** Which Keycloak realm and client config? Confidential client (client_secret in K8s secret) is the assumed default; public client + PKCE-only is possible too. Decision needed from the platform identity team before phase 4.
- **Q2.** Does Falabella have an existing brand design system / Figma library we should align with, or do we author the FDH visual identity inside this change?
- **Q3.** Is the portal's domain `fdh.falabella.internal`, or is it joining an existing dev-tools subdomain like `tools.falabella.internal/fdh`? Affects Ingress + Keycloak redirect URI configuration.
- **Q4.** Internal-network anonymous browsing — confirmed acceptable, or do we need anonymous → login gate from day one?
- **Q5.** Activation telemetry sink — the portal will emit structured log events; what's the ingestion path the analytics team prefers (Loki / Datadog / Splunk / Kafka)?
