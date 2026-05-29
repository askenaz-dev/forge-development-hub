---
name: accessibility-audit
description: Audit a UI for WCAG 2.2 AA issues and report findings with severity and remediation.
license: MIT
metadata:
  author: accessibility
  sdlc_phase: design
---

# Accessibility audit (WCAG 2.2 AA)

Walk the UI and report each finding with: WCAG criterion, severity, location, and fix.

- Perceivable: text contrast >= 4.5:1 (3:1 large), non-text 3:1, captions, meaningful alt text, no color-only meaning.
- Operable: full keyboard access, visible focus, no traps, target size >= 24px (2.2), skip links, no seizure-risk motion.
- Understandable: labels & instructions, consistent navigation, error identification + suggestions.
- Robust: valid semantics, name/role/value for custom controls, status messages via live regions.

Report order: critical (blocks a task) -> serious -> moderate -> minor. Confirm 'no issues' per area explicitly when clean.
