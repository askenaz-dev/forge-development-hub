# Contributing to the Forge Development Hub

This hub publishes four component primitives — **skills, rules, agents, hooks** —
consumed by the `fdh` CLI. Contribution is explicit: a PR may be opened (via the
**CLI path**, governed by your GitHub permissions, or the parallel **web-PR
path**, governed by your portal role — see
[Two ways to *propose*](#two-ways-to-propose-the-cli-path-and-the-web-pr-path)),
but a component is **not part of the hub until it is reviewed, merged, published,
and (for default installs) adopted**. Both paths are propose-only and subject to
the same gates; neither can merge. This document describes that flow and the
permission model (capabilities `hub-contribution-policy`, `portal-gitops-write`).

## Documentation

This page is the canonical reference for the **gates and permission model**. For
the rest, see [`docs/`](docs/):

- **[Authoring Guide](docs/authoring-guide.md)** — start here to add a component:
  per-kind frontmatter templates, the `registry.yaml` entry, local validation,
  and both the `fdh skill new/sync/share` path and a no-CLI (fork + manual edit +
  PR) fallback.
- **[Hub Guide](docs/hub-guide.md)** — what the hub is and **when to use** a
  skill vs. rule vs. agent vs. hook.
- **[Maintainer Runbook](docs/maintainer-runbook.md)** — for admins: marking
  `default`, deprecating/yanking, the release pipeline, CODEOWNERS, and
  `scan_status`.

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
| **3 — Adopt** | A merged component isn't auto-installed | Stays `default: false` until an **admin** sets `default: true` or adds it to a harness |

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
| Set `default` / harnesses | Admin on `hub/` | `admin` | — |

**Naming coherence (task 1.4):** a namespace's GitHub team, its CODEOWNERS owner,
and the Keycloak group that maps to `reviewer` for that namespace SHARE A NAME
(e.g. `appsec` for the `security` namespace). No Keycloak↔GitHub identity
federation is required — the shared names give the operational benefit without it.

### Two ways to *propose*: the CLI path and the web-PR path

There are **two parallel ways to open a contribution PR**, each with its own
authorization surface. Both are **propose-only** and both land on the *same* PR
subject to the *same* gates — neither can merge or publish on its own
(capability `portal-gitops-write`).

| | **CLI path** (`fdh <kind> share`) | **Web-PR path** (portal) |
|---|---|---|
| Who authorizes | Your **GitHub** permissions (Write/fork), via `gh` | Your **portal role** (`author` / `publisher` / `admin`), via your portal session |
| Who authors the PR | You (your GitHub identity) | The **bot** (a portal-owned GitHub App) |
| GitHub account required | Yes | **No** — a portal user with no GitHub identity can still propose |
| What it can do | Open a PR; never merges | Open a PR; **never merges** |

The web-PR path is mediated by a portal-owned **GitHub App ("the bot")**. When an
authorized portal user triggers an import, a harness edit, or a curate action,
the portal validates their role, then the bot opens a PR on this repo. The portal
**never persists catalog CONFIG** — the PR is the only artifact, so Git stays the
source of truth (there is no draft store and no shadow catalog).

Portal role → web action (re-enforced server-side, not just in the UI):

| Portal role | Web action it unlocks | What the bot edits |
|---|---|---|
| `author`+ | **Import** a component | adds `skills/<name>/` + a `registry.yaml` entry (`default: false`) |
| `publisher`+ | **Edit a harness** | edits only `hub/harnesses.yaml` |
| `admin` | **Curate** (`default` flag, deprecate/yank) | edits `hub/registry.yaml` (+ the `default` harness atomically) |

### Both paths are subject to the same three gates

A web-PR-path PR is **just another non-merging PR**. It passes through the exact
[three gates](#the-three-gates-not-automatically-part-of-the-hub) above:

1. **Required CI** (`validate-registry`, `commitlint`) re-runs the same registry,
   bundle/frontmatter, and security-scan checks on the PR — the authoritative
   gate. (The portal also runs these validators server-side *before* opening the
   PR, so a bad bundle fails fast with an actionable error instead of a red PR —
   but CI is still the gate, never skipped.)
2. **A non-author CODEOWNERS review** is required, from a reviewer who is **not**
   the PR author. The bot authors web-path PRs and is **deliberately excluded
   from CODEOWNERS** (see `.github/CODEOWNERS`), so it can never satisfy its own
   review.
3. **No self-merge.** Branch protection blocks the author from merging; publish
   (gate 2) and adoption (gate 3) remain human publisher/admin actions.

### The bot is Level-1: propose-only, cannot merge

The GitHub App is scoped to **`forge-development-hub` only**, with **Contents:
write** + **Pull requests: write** and **no** Administration permission and **no**
merge capability. This is the security spine: **a leaked bot token cannot corrupt
the catalog.** The worst it can do is open spammy PRs, which a human declines —
because branch protection still requires passing CI *and* a non-bot CODEOWNERS
approval *and* no self-merge before anything lands. The App's private key lives
only in the API pod (wired via `secretKeyRef`), never in the browser or the web
pod, and the installation token it mints is short-lived.

### No GitHub identity federation (out of scope)

The two surfaces stay **parallel**; they are **not** federated. A web-PR-path PR
is authored by the bot, and the **PR body credits the requesting portal user and
role** for attribution and audit — that credit is *not* an authorization signal
(authorization is the role gate, enforced regardless of the credited name). An
optional future "link your GitHub account" feature, which would let the portal
open PRs authored by the *user's* GitHub identity, is **explicitly out of scope**
for this change; attribution remains PR-body credit only.

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

- **Public hub** (`fdh.askenaz.dev`): anonymous reads; org members with
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
