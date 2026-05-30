# Contributing to the Forge Development Hub

This hub publishes four component primitives — **skills, rules, agents, hooks** —
consumed by the `fdh` CLI. Contribution is **GitHub-governed** and explicit: a PR
may be opened, but a component is **not part of the hub until it is reviewed,
merged, published, and (for default installs) adopted**. This document describes
that flow and the permission model (capability `hub-contribution-policy`).

## The authoring → contribution flow

```
  new ──▶ iterate ──▶ sync ──▶ share ──▶ review ──▶ publish ──▶ adopt
  (fdh)   (edit)      (fdh)    (fdh→PR)  (gate 1)   (gate 2)    (gate 3)
```

1. **`fdh skill new <name>`** — scaffold a canonical source (`version: 0.1.0`) and
   materialize it into your agents. Author it locally.
2. **Iterate** on the canonical source; **`fdh skill sync <name>`** propagates edits.
3. **`fdh skill share <name> --repo <hub checkout>`** — validates, copies the bundle
   in, adds a `registry.yaml` entry (`default: false`), commits
   `feat(<name>): add skill`, and opens a PR. **It never merges.**

## The three gates ("not automatically part of the hub")

| Gate | What it controls | Mechanism |
|---|---|---|
| **1 — Merge** | The contribution PR can't merge without review | Required CI checks + a **non-author CODEOWNERS approval**; **no self-merge** |
| **2 — Publish** | A version isn't published until a publisher acts | **Publisher** merges the release-please PR → tag `<kind>/<name>@<semver>` → signed bundle |
| **3 — Adopt** | A merged component isn't auto-installed | Stays `default: false` until an **admin** sets `default: true` or adds it to a profile |

A component can be merged and published yet remain opt-in forever (gate 3 never flipped).

## Permission model — two parallel surfaces

Contribution authorization lives on **GitHub** (not the portal). The portal's OIDC
roles govern the **web UI only**. They are kept coherent by **aligned naming** —
not by identity federation.

| Responsibility | GitHub mechanism | Portal OIDC role | Aligned name |
|---|---|---|---|
| Browse the catalog | public | `anonymous` / `consumer` | — |
| `fdh skill share` (open PR) | Write (or fork) | `author` | — |
| Approve a contribution PR | CODEOWNERS review | `reviewer` | per-namespace team |
| Merge the release PR (publish) | Maintain/Admin, restricted | `publisher` | — |
| Set `default` / profiles | Admin on `hub/` | `admin` | — |

**Naming coherence (task 1.4):** a namespace's GitHub team, its CODEOWNERS owner,
and the Keycloak group that maps to `reviewer` for that namespace SHARE A NAME
(e.g. `appsec` for the `security` namespace). No Keycloak↔GitHub identity
federation is required — the shared names give the operational benefit without it.

### Team / namespace seed map

Provisioned by an **org owner via the GitHub web UI** (the EMU CLI auth cannot
create teams). Until then, CODEOWNERS routes everything to the maintainer.

| Namespace | `owner_team` → GitHub team |
|---|---|
| security | `appsec` |
| design | `design-systems`, `accessibility`, `product-design` |
| operations | `sre` |
| architecture | `architecture-guild` |
| cicd | `platform-engineering` |
| code-review / development | `dx-platform` |
| requirements | `product-platform` |
| testing | `qa-platform` |

## Branch protection (gate 1 + gate 2 enforcement)

Strict protection on `main` is provided **as code** in
[`scripts/setup-branch-protection.sh`](scripts/setup-branch-protection.sh) — an
org/repo admin runs it once the CI workflows have run (so the required check
names exist):

- Required status checks: `validate-registry`, `commitlint`.
- ≥1 approving review from CODEOWNERS; dismiss stale approvals.
- No self-merge; admin bypass disabled (break-glass is an audited, deliberate act).
- Release-PR merge restricted to the publisher team.

## Public vs internal/closed deployment

- **Public hub** (`agent-skills.askenaz.dev`): anonymous reads; org members with
  Write contribute via branch + PR; external contributors via fork + PR.
- **Internal/closed** (corporate self-host): compose **(a)** registry serving with
  `Bearer` / `Basic` / `mTLS` auth (the existing `hub-http-registry` mirror auth)
  and **(b)** a restricted contribution policy (who may open/merge PRs). The
  consume side (`/v1/*`) stays portable to any static host; the `fdh`-based
  contribute side assumes a GitHub-like host.

## Adding a new component (summary)

See [`hub/README.md`](hub/README.md) for the mechanics. In short: author with
`fdh <kind> new`, `fdh <kind> share` to open the PR (entry `default: false`,
frontmatter `version: 0.1.0`), get a CODEOWNERS review, a publisher merges the
release PR, and an admin decides adoption.
