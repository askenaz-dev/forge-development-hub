---
name: design-system
description: Use when the user wants to build, design, style, modify, or review any UI — React/Next/Vue components, screens, forms, buttons, layouts, dashboards, charts, modals, tables, navigation — or when the user mentions Tailwind, CSS, dark mode, accessibility, WCAG, design tokens, colors, typography, spacing, or Falabella visual identity. ALWAYS load this skill BEFORE writing UI code so design system rules, tokens, and the component catalog are in context.
version: 0.1.0
ds-version: 1.0.1
---

## Purpose

This skill loads the Falabella design system contract into context before any UI is generated. The upstream source of truth is the `@falabella-enablers-genai/ui` package (repo `FTI00575-design-system`); a pinned snapshot of its documentation lives under `references/`. Treat `references/` as canonical for this session: do not invent tokens, components, or APIs that are not in `references/COMPONENTS.md` or `references/AGENTS.md`. The pinned upstream version is in `.ds-version`.

## Rules (non-negotiable)

These 20 rules apply to ALL generated UI. Violations are caught in review.

### Tokens

1. **Never use raw values.** Every color, spacing, font-size, shadow, and radius MUST reference a design token via CSS custom property (`var(--token-name)`) or the framework equivalent.
2. **Never reference primitive tokens in components.** Components use semantic or component-level tokens only. Primitives (`color.gray.500`, `space.4`) feed semantics; they are not consumed by UI code.
3. **Token resolution order:** Component token → Semantic token → Primitive. Always use the most specific available.

### Colors

4. **Text/background contrast:** WCAG 2.1 AA minimum (4.5:1 normal text, 3:1 large text and UI elements).
5. **Dark mode:** All color decisions must work in both `light` and `dark`. Use semantic tokens — they resolve per theme.
6. **Status colors:** `error` = red family, `success` = green, `warning` = yellow. Never repurpose for decorative use.

### Typography

7. **Font sizes:** Use type scale tokens only (`type.display.*`, `type.heading.*`, `type.body.*`, `type.code.*`). No arbitrary sizes.
8. **Max reading width:** Body text containers must not exceed `65ch`.
9. **Minimum font size:** `type.body.xs` (12px / 0.75rem). Nothing smaller.

### Spacing

10. **Use the spacing scale.** All margins, paddings, gaps use `space.*` tokens. No arbitrary pixels.
11. **Consistency rule:** Same relationship = same spacing. If two cards have `space.6` gap, all card grids use `space.6`.

### Components

12. **Use existing components first.** Before custom UI, check `references/COMPONENTS.md` for an existing component.
13. **States are mandatory.** Every interactive element handles `default`, `hover`, `focus-visible`, `active`, `disabled`. No exceptions.
14. **Focus ring:** All focusable elements show `shadow.focus` on `:focus-visible`.

### Accessibility

15. **Semantic HTML first.** Use `<button>`, `<a>`, `<input>`, `<nav>`, `<main>`. Only add ARIA when native semantics are insufficient.
16. **`prefers-reduced-motion`:** All animations disabled or reduced when this media query matches.
17. **Touch targets:** Minimum 44×44px for all interactive elements.
18. **Icon-only buttons:** Must have `aria-label`.

### Responsive

19. **Mobile-first.** Base styles = mobile. Use `min-width` media queries to add complexity.
20. **Breakpoints:** Only the defined breakpoints (`sm: 640px`, `md: 768px`, `lg: 1024px`, `xl: 1280px`, `2xl: 1536px`).

## How to access the DS

Read these references on demand (do NOT pre-load all of them — they are large):

- `references/AGENTS.md` — full upstream agent instructions including code-generation patterns and proposal protocol. Read when the user asks "how do I propose a new token/component" or when generating non-trivial component code.
- `references/COMPONENTS.md` — catalog of 43 components (26 UI + 17 chart) with import statements, props, CVA variants, and usage examples. **Read this before using any component by name.**
- `references/DESIGN.md` — 1:1 index that routes you to the right `semantic-design/*.md` for a given concern.
- `references/semantic-design/ds-react.md` — React usage patterns (cn, forwardRef, displayName).
- `references/semantic-design/tokens.md` — token naming, CSS variable mapping.
- `references/semantic-design/actions.md` — buttons, links, action patterns.
- `references/semantic-design/forms.md` — inputs, selects, checkboxes, switches.
- `references/semantic-design/surfaces.md` — cards, dialog, popover.
- `references/semantic-design/feedback.md` — badge, status, toast, tooltip.
- `references/semantic-design/navigation.md` — tabs, menus, sidebar.
- `references/semantic-design/layout.md` — grids, data table, charts.
- `references/components.meta.json` — machine-readable metadata for every component (use for filtering/discovery).

## Setup in a consumer project

The consumer project needs access to the Falabella private npm scope.

**1. Configure `.npmrc`** (repo root or `~/.npmrc`):

```
@falabella-enablers-genai:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=${GITHUB_PKG_TOKEN}
```

**2. Generate a GitHub Personal Access Token** with `read:packages` scope at <https://github.com/settings/tokens> and export it as `GITHUB_PKG_TOKEN` in your shell profile.

**3. Recommended path — CLI flow (`genai-ds`):** copies component source into the consumer project, giving full ownership.

```bash
npx @falabella-enablers-genai/cli init           # bootstrap config
npx @falabella-enablers-genai/cli add button     # copy Button into the project
```

**Alternative — npm package import** (runtime dependency, no source copy):

```bash
npm install @falabella-enablers-genai/ui
```

Then in the consumer's global CSS:

```css
@import "@falabella-enablers-genai/ui/tokens.css";
@import "@falabella-enablers-genai/ui/styles.css";
```

`tokens.css` already includes `:root` and `.dark`. There is no separate dark mode subpath.

## Drift detection

Before generating UI:

1. **Component absent from catalog:** if the user requests a component name not listed in `references/COMPONENTS.md`, stop. Re-read `references/COMPONENTS.md` (it may have changed since you indexed). If still absent, do NOT invent it — either compose existing components or surface the gap and propose an RFC per `references/AGENTS.md` "Proposing Design Changes".
2. **Stale snapshot:** read `.ds-version`. If `sync-date` is more than 60 days before today, warn the user that this snapshot may be out of date and suggest running `scripts/sync.mjs --source <path-to-DS-clone>` or `fdh update` (when available).
3. **Token absent:** every `var(--token-name)` emitted must map to something documented in `references/AGENTS.md` (sections "How to Read Tokens" and "Rules → Tokens"). If a needed token does not exist, surface the gap with a concrete example and propose an RFC; do not fabricate.
