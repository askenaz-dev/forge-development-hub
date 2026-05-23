## ADDED Requirements

### Requirement: Versioned HTTP API under /api/v1

The portal API SHALL expose every endpoint under a `/api/v1/` prefix. Breaking changes to any endpoint MUST be released under a new version prefix; the v1 contract MUST remain stable for the lifetime of v1.

#### Scenario: Stable v1 endpoint

- **WHEN** a v1 endpoint's response schema needs a breaking change
- **THEN** the new shape ships under `/api/v2/...` and `/api/v1/...` continues to return the original shape until a deprecation period passes

### Requirement: Skills catalog endpoint

The API SHALL expose `GET /api/v1/skills` returning a paginated list of skills with filter parameters `?q=<query>&namespace=<ns>&tag=<tag>&scan_status=<status>&limit=<n>&cursor=<token>`. The response includes the skill's namespace, name, description, latest version, latest content hash, scan status, owner team, and tag list.

#### Scenario: Default listing

- **WHEN** a client calls `GET /api/v1/skills` with no parameters
- **THEN** the API returns a JSON object with `items` (an array of skill summaries) and `next_cursor` (a string or null), using a default page size of 50

#### Scenario: Search by query string

- **WHEN** a client calls `GET /api/v1/skills?q=owasp`
- **THEN** the response contains only skills whose namespace, name, description, or tags match `owasp` case-insensitively

#### Scenario: Filter by namespace

- **WHEN** a client calls `GET /api/v1/skills?namespace=security`
- **THEN** every item in the response has `"namespace": "security"`

### Requirement: Skill detail endpoint

The API SHALL expose `GET /api/v1/skills/{namespace}/{name}` returning the full manifest for that skill, including its description, owner team, tags, every published version with its content hash, publish timestamp, publisher identifier, scan status, optional signature pointer, and changelog URL.

#### Scenario: Existing skill returns 200

- **WHEN** a client calls `GET /api/v1/skills/security/owasp-quick-review`
- **THEN** the response status is 200 and the body matches the manifest structure declared in the OpenAPI spec

#### Scenario: Unknown skill returns 404

- **WHEN** a client calls `GET /api/v1/skills/foo/bar` for a skill not in the registry
- **THEN** the response status is 404 and the body is `{"error": "skill_not_found", "namespace": "foo", "name": "bar"}`

### Requirement: Skill version detail endpoint

The API SHALL expose `GET /api/v1/skills/{namespace}/{name}/versions/{version}` returning that specific version's metadata: content hash, publish info, scan status, signature, and a link to fetch the rendered SKILL.md body.

#### Scenario: Specific version retrieval

- **WHEN** a client calls `GET /api/v1/skills/security/owasp-quick-review/versions/1.0.0`
- **THEN** the response includes the content hash for that version and a `skill_md_url` field pointing at the rendered SKILL.md endpoint

### Requirement: Rendered SKILL.md endpoint

The API SHALL expose `GET /api/v1/skills/{namespace}/{name}/versions/{version}/skill-md` returning the raw markdown source of the SKILL.md for that version as `text/markdown; charset=utf-8`. The frontend renders the markdown client-side; the API does not transform it.

#### Scenario: Markdown returned as-is

- **WHEN** a client calls the skill-md endpoint for a valid version
- **THEN** the response Content-Type is `text/markdown; charset=utf-8`, the body is the raw bundle SKILL.md (with the breadcrumb omitted — this is the pre-install source), and a `Cache-Control` header allows caching for at least 60 seconds

### Requirement: Current-user endpoint

The API SHALL expose `GET /api/v1/auth/me` returning information about the requesting user: subject identifier (`sub`), display name, email, mapped portal role (`anonymous`, `consumer`, `author`, `reviewer`, `publisher`, or `admin`), and the raw Keycloak group/role claims for transparency.

#### Scenario: Anonymous request

- **WHEN** an unauthenticated client calls `GET /api/v1/auth/me`
- **THEN** the response is 200 with body `{"role": "anonymous"}` (no `sub`, `name`, or `email` fields)

#### Scenario: Authenticated request

- **WHEN** an authenticated client with `groups: ["fdh-authors"]` calls `GET /api/v1/auth/me`
- **THEN** the response includes `role: "author"`, the user's `sub`, display name, and email, and the raw `claims` array contains `"fdh-authors"`

### Requirement: OpenAPI spec is the source of truth

The portal API SHALL ship with an OpenAPI 3.1 specification (`openapi.yaml`) that defines every endpoint, request shape, response shape, and error type. Go server stubs MUST be generated from this spec via a code generator; the frontend's API client MUST also be generated from the same spec. CI MUST fail if the spec and the generated code disagree.

#### Scenario: Spec drift caught in CI

- **WHEN** a developer edits a handler signature in Go without updating the OpenAPI spec
- **THEN** CI fails on the OpenAPI-vs-Go consistency check and the build does not proceed

### Requirement: Health and readiness probes

The API SHALL expose `GET /healthz` (always 200 if the process is running) and `GET /readyz` (200 once the registry has been successfully read at least once, 503 otherwise). These endpoints MUST NOT require authentication.

#### Scenario: Liveness probe always green

- **WHEN** Kubernetes calls `GET /healthz` on a running API pod
- **THEN** the response is 200 with body `{"status": "ok"}` regardless of registry state

#### Scenario: Readiness probe gated on registry

- **WHEN** the API has just started and has not yet completed its first registry read
- **THEN** `GET /readyz` returns 503; once the first read succeeds, subsequent calls return 200

### Requirement: Registry refresh model

The API SHALL refresh its in-memory view of the registry on a configurable interval (default 60 seconds). The API SHALL also expose `POST /api/v1/refresh` (authenticated, requires role `publisher` or above) that triggers an immediate re-read and returns the new index version. A `SIGHUP` signal MUST also trigger an immediate refresh.

#### Scenario: Scheduled refresh

- **WHEN** the API has been running with the default 60-second interval and a new commit lands on the registry's `main` branch
- **THEN** within at most 60 seconds plus one fetch cycle, subsequent calls to `GET /api/v1/skills` reflect the new commit

#### Scenario: Forced refresh

- **WHEN** a publisher calls `POST /api/v1/refresh` after pushing a new commit
- **THEN** the API performs a fetch + checkout, the call returns 200 with the resulting index summary, and subsequent reads reflect the new commit immediately

### Requirement: Prometheus metrics endpoint

The API SHALL expose `GET /metrics` in Prometheus exposition format. Metrics MUST include: request counts and latency by route, registry refresh count + duration + last error, in-memory cache size, and standard Go runtime metrics (memory, goroutines).

#### Scenario: Metrics endpoint scrapeable

- **WHEN** a Prometheus scrape hits `GET /metrics`
- **THEN** the response is 200 with `Content-Type: text/plain; version=0.0.4` and includes at minimum the histogram `fdh_portal_api_request_duration_seconds` labeled by `route` and `status`

### Requirement: OpenTelemetry trace context

The API SHALL accept and propagate W3C Trace Context headers (`traceparent`, `tracestate`). Outbound calls to git (for fetch) MUST be wrapped in a trace span. Spans MUST be exported via OTLP to the endpoint configured by the `OTEL_EXPORTER_OTLP_ENDPOINT` environment variable.

#### Scenario: Incoming traceparent propagated

- **WHEN** a request arrives with a valid `traceparent` header and the API performs a registry fetch
- **THEN** the fetch span carries the trace ID from the incoming header, visible in the exported trace data

### Requirement: Structured JSON logs

The API SHALL emit logs to stdout in JSON format using `log/slog`. Every log line MUST include `time` (RFC3339), `level`, `msg`, `trace_id` (if available), `route` (for request logs), and `user_id` (for authenticated requests). User identifiers MUST be the Keycloak `sub` claim, never the email or display name.

#### Scenario: Request log shape

- **WHEN** an authenticated request to `GET /api/v1/skills` completes
- **THEN** stdout contains a JSON log line with `level: "INFO"`, `msg: "request"`, the route, the user_id, the response status, and the request latency

### Requirement: Reuse of pkg/registry from the CLI module

The portal API SHALL consume the same `github.com/falabella/fdh/pkg/registry` package that the CLI consumes. Both MUST agree on the `Registry` interface, the JSON shapes, and the canonical hash. No portal-specific fork of these types is permitted.

#### Scenario: Single registry implementation

- **WHEN** the codebase is compiled
- **THEN** the portal API's `RegistryService` accepts `*registry.GitRegistry` and `registry.Registry` directly from the shared package; no duplicate type definitions exist
