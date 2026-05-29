---
name: unit-test-generation
description: Generate unit tests that target observable behavior with high signal and low brittleness.
license: MIT
metadata:
  author: qa-platform
  sdlc_phase: testing
---

# Unit-test generation

When generating tests for a function or method, follow this method:

1. State the function's contract in one sentence (inputs, outputs, side effects).
2. List the equivalence classes of inputs. Cover at minimum:
   - the happy path
   - boundary values (empty, max, min, zero)
   - failure modes the function is documented to return
3. For each class, write one test. Each test:
   - has a name that describes the behavior, not the input ("rejects empty username", not "test 4")
   - sets up only what is needed (avoid shared fixtures across unrelated tests)
   - asserts ONLY what is observable from the contract; do not assert internal state
4. Skip tests for trivial getters/setters and for type-system-enforced invariants.
5. Add ONE property-based test for any function operating on numeric ranges or strings.

Quality bar:
- A failing test names the exact contract violation.
- No test depends on the order of any other test.
- Tests run in under one second collectively for typical pure functions.
