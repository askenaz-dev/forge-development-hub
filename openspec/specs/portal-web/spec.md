# portal-web Specification

## Purpose
TBD - created by archiving change dev-portal. Update Purpose after archive.
## Requirements
### Requirement: Next.js 14 App Router with TypeScript strict

The frontend SHALL be a Next.js 14 (or later) application using the App Router, React 18 (or later), and TypeScript with `strict: true` in `tsconfig.json`. ESLint and TypeScript MUST both pass in CI.

#### Scenario: TypeScript strict enforced

- **WHEN** a developer writes a file that violates TypeScript strict rules
- **THEN** `next build` and `tsc --noEmit` both fail in CI

#### Scenario: App Router used, not Pages Router

- **WHEN** the codebase is inspected
- **THEN** all routes live under `app/` (not `pages/`), and `next.config.js` has `experimental.appDir` enabled where required by the Next.js version

### Requirement: Page inventory

The frontend SHALL include at minimum the following pages:

- Landing (`/`) — three CTAs: install the CLI, browse skills, sign in.
- Install CLI (`/install`) — per-OS commands with copy-buttons and OS detection.
- Browse skills (`/skills`) — filterable, paginated catalog with search.
- Skill detail (`/skills/[namespace]/[name]`) — rendered SKILL.md + version history + `fdh install` snippet.
- Version detail (`/skills/[namespace]/[name]/versions/[version]`) — version-pinned view with the same content for an older version.
- Profile (`/profile`) — auth-only; displays user info and preferences.
- Admin (`/admin`) — auth-only, role-gated; shell for future admin features (audit log link, refresh trigger, role overview).
- Sign-in (`/auth/signin`) — redirect to Keycloak.
- Sign-out (`/auth/signout`) — confirmation and clear session.

#### Scenario: Every page reachable

- **WHEN** the frontend is built and started
- **THEN** every URL listed above renders without error for an anonymous user OR redirects to sign-in (for auth-only pages) without throwing

### Requirement: Skill detail page renders SKILL.md and shows install snippet

The skill detail page SHALL fetch the raw SKILL.md from the API and render it client-side as HTML with syntax-highlighted code blocks. The page MUST display the exact `fdh install <namespace>/<name>` command in a copy-button-equipped block. The page MUST show: latest version, version history (collapsible), owner team, tags, scan status, and a link to the underlying registry repo for full provenance.

#### Scenario: Markdown renders correctly

- **WHEN** a user visits `/skills/security/owasp-quick-review`
- **THEN** the page shows the SKILL.md content as formatted HTML (headings, lists, code blocks) and the install command `fdh install security/owasp-quick-review` is visible with a copy button

#### Scenario: Copy button copies install command

- **WHEN** a user clicks the copy button next to the install command
- **THEN** the clipboard contains exactly the string `fdh install security/owasp-quick-review` (no trailing newline, no decorations)

### Requirement: Search is server-side, debounced, URL-stateful

The browse page SHALL include a search input that hits `GET /api/v1/skills?q=...` server-side. The input MUST debounce at 250ms, update the URL with `?q=<query>` on every search (so the URL is shareable), and use Next.js routing to avoid full page reloads. An empty query MUST return the unfiltered catalog.

#### Scenario: URL reflects query

- **WHEN** a user types "owasp" into the search input
- **THEN** within 250ms after the user stops typing, the URL becomes `/skills?q=owasp` and the results list updates

#### Scenario: Shareable search URL

- **WHEN** a second user visits the URL `/skills?q=owasp` directly
- **THEN** the search input pre-fills with "owasp" and the filtered results render before client-side JavaScript hydrates

### Requirement: Dark mode with system preference

The frontend SHALL support light, dark, and system-preference theme modes. The default MUST be `system`. A toggle MUST appear in the navigation header. The user's choice MUST persist via `localStorage` and survive hard reloads.

#### Scenario: System preference respected on first visit

- **WHEN** a user with OS dark mode enabled visits the portal for the first time
- **THEN** the portal renders in dark mode without any flash of light theme

#### Scenario: Explicit override persists

- **WHEN** a user toggles to light mode then reloads the page
- **THEN** the portal renders in light mode regardless of OS preference

### Requirement: Internationalization (Spanish + English)

The frontend SHALL support at minimum two locales: Spanish (`es`, default) and English (`en`). Every user-facing string MUST be externalized to message tables. A locale switcher MUST appear in the navigation. The chosen locale MUST persist via cookie and override browser language detection.

Pages SHALL live under a `[locale]` dynamic segment (`web/app/[locale]/...`) so the next-intl middleware can rewrite incoming URLs to the appropriate locale. The default locale (`es`) MUST serve without a URL prefix; other locales MUST serve under `/<locale>/...`. The locale switcher MUST function end-to-end — clicking "English" on a Spanish page MUST navigate the user to the same content in English.

#### Scenario: Default locale is Spanish

- **WHEN** a user with no locale preference visits the portal for the first time
- **THEN** the page renders in Spanish

#### Scenario: Browser language detected when no preference

- **WHEN** a user whose browser reports `Accept-Language: en` visits the portal with no locale cookie
- **THEN** the page renders in English

#### Scenario: Explicit choice persists

- **WHEN** a user clicks the locale switcher to English and reloads
- **THEN** the page renders in English regardless of browser language

#### Scenario: Default locale URL has no prefix

- **WHEN** a user visits `/` or `/skills` (no locale prefix)
- **THEN** the page renders in Spanish and the URL does not gain a prefix

#### Scenario: Non-default locale URL carries the prefix

- **WHEN** a user navigates to the English version of the skills page
- **THEN** the URL is `/en/skills` and the page renders in English

#### Scenario: Locale switcher rewrites the path

- **WHEN** a user on `/skills` clicks the English option in the locale switcher
- **THEN** the URL becomes `/en/skills` and the content re-renders in English

### Requirement: WCAG 2.1 AA accessibility floor

The frontend SHALL meet WCAG 2.1 AA accessibility. Specifically: all interactive elements are keyboard-reachable; focus is visible and not removed; color contrast is at least 4.5:1 for normal text and 3:1 for large text; every image has alt text or is marked decorative; every form input has a `<label>`; the page has a `<main>` landmark; headings form a valid hierarchy.

#### Scenario: Automated audit clean

- **WHEN** an automated accessibility test (axe-core via Playwright) runs against every page
- **THEN** zero violations of severity "serious" or "critical" are reported

#### Scenario: Keyboard-only navigation

- **WHEN** a tester uses only Tab, Shift+Tab, and Enter to navigate the landing page
- **THEN** every CTA, every link in the nav, and the search input are reachable in document order

### Requirement: Tailwind CSS + shadcn/ui as the design system

The frontend SHALL use Tailwind CSS for utility-first styling and shadcn/ui components vendored into the repository (not consumed as a runtime dependency). Custom Forge theme tokens MUST be defined in `tailwind.config.ts` (or equivalent). Component variants MUST follow shadcn/ui patterns.

#### Scenario: shadcn/ui components vendored

- **WHEN** the codebase is inspected
- **THEN** components live under `components/ui/` as TypeScript source (not imported from a node_modules package), and `package.json` does not list shadcn/ui as a dependency

### Requirement: Server-side rendering with selective client hydration

Pages that show registry content (landing, browse, skill detail) SHALL render server-side using React Server Components. Interactive components (search input, dark-mode toggle, copy buttons) MUST be marked `"use client"` and live in their own files. The first paint of any catalog page MUST NOT depend on client-side JavaScript fetching data.

#### Scenario: First paint shows content

- **WHEN** a user visits `/skills` with JavaScript disabled
- **THEN** the catalog list renders fully (the search input may be inert but the list is present)

### Requirement: API client generated from OpenAPI

The frontend's API client SHALL be generated from the portal API's OpenAPI specification using `openapi-typescript` (or equivalent). The generated types MUST be committed and CI MUST fail if they drift from the spec.

#### Scenario: Spec drift fails CI

- **WHEN** the OpenAPI spec changes but the generated types are not regenerated
- **THEN** CI fails on a "types out of date" check before tests run

### Requirement: Production build performance

The production build SHALL produce a Lighthouse Performance score of at least 90 on the landing page and at least 85 on the skill detail page, measured against a deployed instance with a representative dataset. Total JS payload for the landing page MUST be under 200 KB gzipped.

#### Scenario: Landing page bundle size

- **WHEN** a CI step measures `next build` output
- **THEN** the landing page's first-load JS is reported under 200 KB gzipped

