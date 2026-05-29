---
name: user-story-generation
description: Turn a feature request into well-formed user stories with explicit acceptance criteria.
license: MIT
metadata:
  author: product-platform
  sdlc_phase: requirements
---

# User-story generation

When asked to break a feature request into user stories, follow this structure
for each story:

- Title: a single imperative sentence under 10 words.
- Narrative: "As a <role>, I want <capability>, so that <outcome>." Each
  clause is required and concrete; reject vague roles ("user" by itself) or
  outcomes ("be better").
- Acceptance criteria: between three and seven scenarios in Given/When/Then
  form. Each scenario MUST be independently testable.
- Non-goals: a short list of things the story explicitly does NOT cover.
- Open questions: anything the author needs the requester to clarify before
  estimation.

After drafting, verify each story against this checklist:
- INVEST: Independent, Negotiable, Valuable, Estimable, Small, Testable.
- No implementation detail leaks (no "use Postgres", "add a Redis cache").
- Every acceptance criterion maps to observable behavior, not internal state.
