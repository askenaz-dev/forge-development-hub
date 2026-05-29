---
name: design-system-usage
description: Apply a design system consistently: tokens, components, spacing, states, and accessibility.
license: MIT
metadata:
  author: design-systems
  sdlc_phase: design
---

# Design-system usage

When building or reviewing UI, apply the design system instead of ad-hoc styles.

- Tokens: use semantic tokens (color.fg.default, space.4) — never raw hex or magic px.
- Components: reuse existing components before creating new ones; extend via documented variants/props.
- States: design every interactive element for default, hover, focus-visible, active, disabled, loading, and error.
- Spacing & layout: use the spacing scale and a consistent grid; align to the baseline.
- Accessibility: 4.5:1 text contrast, visible focus rings, hit targets >= 44px, labels on every control.

Before shipping, verify: no hard-coded values, all states covered, keyboard-navigable, and dark/light parity.
