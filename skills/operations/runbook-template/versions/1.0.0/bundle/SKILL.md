---
name: runbook-template
description: Author or update a service runbook that on-call engineers can follow under pressure.
license: MIT
metadata:
  author: sre
  sdlc_phase: operations
---

# Runbook template

Every service-level runbook must contain the sections below in this order.
On-call engineers read top-to-bottom under stress; do not bury actionable
information.

## Service summary
One paragraph: what the service does, who owns it, the SLO it commits to,
and the SLO it currently meets.

## On-call expectations
- Pager response time
- Escalation path (primary -> secondary -> service owner -> incident manager)
- Communication channels (the chat room or bridge to join)

## Symptoms and triage
A table mapping alert names to first-response actions. Each row:
- Alert: the exact alert string the on-call sees in pager text.
- First check: the single command or dashboard URL to look at.
- If green: a follow-up question to narrow scope.
- If red: a one-line summary of the most likely cause and the section to jump to.

## Common incidents
For each incident archetype:
- Detection: how it manifests
- Diagnosis: the queries, logs, or dashboards that confirm it
- Mitigation: the immediate action (failover, scale, restart, disable feature)
- Resolution: the fix that closes the underlying cause
- Postmortem trigger: when this incident requires a postmortem

## Standard operations
- Deploy / rollback
- Scale up / down
- Toggle feature flags
- Rotate credentials
Each operation lists the exact command, its expected output, and the
fast-path rollback.

## Known limitations
Things the service deliberately does not handle, with the workaround.

## Last-resort contacts
A short list. Test every contact quarterly.

Quality bar:
- Anyone with platform familiarity but no prior context on this service
  can mitigate a P1 with this runbook alone.
- Every command in the runbook has been executed within the last 90 days.
- No section says "ask the team" without naming a fallback.
