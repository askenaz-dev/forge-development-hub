---
name: adr-generation
description: Draft an architecture decision record (ADR) for a design choice and its alternatives.
license: MIT
metadata:
  author: architecture-guild
  sdlc_phase: architecture
---

# ADR generation

Produce an ADR in markdown using these sections, in order:

- Title: ADR-<NNNN> — short imperative phrase.
- Status: one of Proposed, Accepted, Superseded, Deprecated.
- Context: 2-4 paragraphs on the forces at play. What problem? What
  constraints? Who is affected?
- Decision: 1-2 paragraphs stating exactly what was decided. Use the
  active voice ("We will use ...").
- Consequences: positive and negative outcomes the decision creates, plus
  obligations it imposes on future work.
- Alternatives considered: at least two, each with a one-paragraph
  description and an explicit rejection reason.
- References: links to related ADRs, RFCs, vendor docs.

Quality bar before publishing:
- A reviewer who reads ONLY the Decision section can understand what was
  chosen.
- The Alternatives section is balanced (each option steel-manned), not a
  straw-man comparison.
- Consequences explicitly name the team or system that inherits each cost.
