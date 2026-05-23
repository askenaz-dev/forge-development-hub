## Why

The `installer-core` change delivered a working CLI for a 30-developer pilot, but the Git-backed registry is only browseable through whichever Git host hosts the repo, and the CLI's name (`falabella-installer`) reflects the implementation rather than the product the org wants to invest in. To grow adoption from 30 pilot developers to the full Falabella engineering org, three things must land together: (1) a modern, professional web portal where developers discover, browse, and learn to install skills; (2) Keycloak single sign-on so the portal honors Falabella's existing identity provider and can carry roles into governance work later; (3) a product-grade CLI name — `fdh` (Falabella Development Hub) — that the portal, docs, and Slack culture can all stand behind. Doing this as one change keeps the rename and the portal aligned so the docs and install snippets never reference a stale binary name.

## What Changes

- **BREAKING — Rename the CLI from `falabella-installer` to `fdh`.** The repository moves from `falabella/skill-installer` to `falabella/fdh`; the Go module becomes `github.com/falabella/fdh`; the binary is `fdh` / `fdh.exe`; the per-user config directory moves from `~/.config/falabella-installer/` to `~/.config/fdh/`. A back-compat stub binary keeps `falabella-installer` working for a 90-day deprecation window, printing a one-line notice and forwarding to `fdh`.
- Add a **portal API**: a Go HTTP service (new binary `fdh-portal-api`) that reads the existing Git-backed registry through `pkg/registry.GitRegistry` and exposes the catalog over a versioned JSON API (`/api/v1/...`) with OpenAPI documentation, Prometheus metrics, OpenTelemetry traces, and health/readiness endpoints.
- Add a **portal web frontend**: a Next.js 14 (App Router) application with React 18, TypeScript strict, Tailwind CSS, and shadcn/ui components. Pages: landing, install-CLI walkthrough (per-OS detection + copy-buttons), browse, search (debounced server-side), skill detail (rendered SKILL.md + version history + copy-able `fdh install` command), profile (auth-only), and admin shell (auth + admin role). Full SSR, system-preference dark mode, WCAG 2.1 AA accessibility, internationalization in Spanish and English at minimum.
- Add **Keycloak OIDC authentication**: backend uses standard OIDC code flow with PKCE against the existing Falabella Keycloak; the OIDC abstraction is configurable so Entra ID or another conforming IdP can swap in. Anonymous browsing is permitted for read-only catalog pages; authenticated views unlock profile, favorites (groundwork — full list lands in a later change), and admin features (role-gated via JWT claims). Sessions are HTTP-only secure cookies; logout invalidates server-side state.
- Add a **first-install onboarding wizard**: a guided flow from "I just heard about this tool" to "my first skill is installed". OS-detected install commands, automated `fdh doctor` walkthrough, registry-URL configuration, and a recommended starter-skill install — all skippable but trackable so we can later measure activation funnel.
- Ship **local-dev infrastructure** (Docker Compose bringing up Keycloak + API + Web together) and **production deployment infrastructure** (Helm chart for Falabella's existing Kubernetes cluster).

## Capabilities

### New Capabilities

- `fdh-cli-naming`: The official naming, paths, configuration layout, and back-compat behavior for the renamed CLI. Covers binary name, Go module path, config directory, adapter override path, and the deprecation stub.
- `portal-api`: The portal's HTTP API contract — endpoints, JSON schemas (locked by OpenAPI), refresh model, observability surface, and the relationship to the underlying `pkg/registry` interface.
- `portal-web`: The portal's web frontend — page inventory, routing, design system, dark mode, accessibility floor, internationalization, and the install-command rendering contract.
- `portal-authn`: The authentication and authorization model — OIDC code flow with PKCE, Keycloak as the reference IdP with a swappable abstraction, anonymous vs. authenticated routes, role mapping from JWT claims to portal roles, session storage rules.
- `portal-onboarding`: The first-install user experience — landing-page CTAs, per-OS install commands, the guided wizard flow, and the activation-event taxonomy the portal must emit so adoption can be measured.

### Modified Capabilities

- `skill-installer-cli`: Binary name and config paths change as part of the rename. Existing command surface, output formats, exit codes, and behavior are unchanged; only the binary's name and configuration directory shift.

## Impact

- **Repository rename**: `falabella/skill-installer` becomes `falabella/fdh`. The old repo retains a `README.md` and a stub binary release pointing to the new location for 90 days, then archived.
- **Go module rename**: every import of `github.com/falabella/skill-installer/...` becomes `github.com/falabella/fdh/...`. Mechanical refactor across all source files and tests.
- **Per-user config migration**: `fdh` reads from `~/.config/fdh/config.yaml` (and `~/.config/fdh/adapters.yaml`) but for the 90-day deprecation window also reads the old `~/.config/falabella-installer/config.yaml` if the new file is absent and emits a one-line warning. A `fdh config migrate` command performs the move explicitly.
- **New product surface**: two new long-running services (portal API + portal web) joining the deployment footprint, plus a Keycloak realm/client configuration to be coordinated with the platform identity team.
- **Pilot developers** in the 30-dev `installer-core` pilot have to reinstall once. A one-line migration command is provided.
- **Deployment infra**: Helm chart, Docker images for two services, environment configuration documented, observability wiring (Prometheus scrape config + OTel collector endpoint).
- **Sets up future changes**: `installer-write-flows` adds publish/update/pin/remove/provision and gains a portal-side "Publish your skill" UI; `governance-full` extends `portal-authn` with server-side approval workflow + audit log; `scan-gate-ui` visualizes scan results on each skill page; `analytics` records adoption metrics that the portal already emits as activation events.
