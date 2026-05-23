## ADDED Requirements

### Requirement: OIDC Authorization Code with PKCE

Authentication SHALL use the OpenID Connect Authorization Code flow with PKCE. The portal MUST NOT use the implicit flow, the password flow, or the hybrid flow. PKCE is mandatory regardless of whether the client is configured as public or confidential.

#### Scenario: PKCE codes generated per session

- **WHEN** a user clicks "Sign in" and is redirected to Keycloak
- **THEN** the redirect URL includes a `code_challenge` parameter and a corresponding `code_verifier` is stored server-side, and after callback the verifier is exchanged for tokens

#### Scenario: Implicit flow not configured

- **WHEN** the portal is inspected
- **THEN** no code path uses `response_type=token` or `response_type=id_token`; only `response_type=code` is permitted

### Requirement: Keycloak as the reference IdP, behind a swappable abstraction

The portal SHALL use Keycloak as its reference identity provider during the MVP. Both the Go backend and the Next.js frontend MUST configure OIDC purely via the standard discovery URL, client ID, and client secret (or PKCE-only equivalents) — no Keycloak-specific API calls beyond standard OIDC endpoints. Replacing Keycloak with another conforming OIDC provider (e.g., Entra ID) MUST be possible via configuration alone.

#### Scenario: Provider configuration is purely OIDC standard

- **WHEN** the portal is configured with a different OIDC discovery URL
- **THEN** the portal's login flow works without code changes (only configuration changes), regardless of whether the underlying IdP is Keycloak

### Requirement: Anonymous browsing permitted on catalog pages

The portal SHALL allow anonymous (unauthenticated) users to browse the catalog (landing, browse, search, skill detail, version detail) without redirecting to sign-in. Anonymous users see read-only views and the "Sign in" CTA in the header.

#### Scenario: Anonymous skill browsing

- **WHEN** an unauthenticated user visits `/skills/security/owasp-quick-review`
- **THEN** the page renders the skill detail without redirecting to sign-in

### Requirement: Authentication required for profile and admin

The portal SHALL require authentication for `/profile` and `/admin` and any future authenticated-only routes. Unauthenticated requests MUST be redirected to `/auth/signin` with a `redirect_to` query parameter that is honored after successful sign-in.

#### Scenario: Anonymous redirect to sign-in

- **WHEN** an unauthenticated user visits `/profile`
- **THEN** the response is a redirect to `/auth/signin?redirect_to=%2Fprofile`

#### Scenario: Post-sign-in redirect honored

- **WHEN** a user signs in after being redirected from `/profile`
- **THEN** after successful authentication they land on `/profile`, not the default post-sign-in destination

### Requirement: Role mapping from JWT claims

JWT claims from the IdP SHALL be mapped to portal roles via a configuration map. Recognized portal roles are exactly: `anonymous`, `consumer`, `author`, `reviewer`, `publisher`, `admin`. The mapping configuration MUST accept arbitrary claim names (e.g. `groups`, `roles`, `wids`) and arbitrary claim values, mapping each to one or more portal roles.

#### Scenario: Group claim maps to portal role

- **WHEN** the configuration declares `groups: { "fdh-authors": "author" }` and a user's JWT contains `"groups": ["fdh-authors", "other-group"]`
- **THEN** that user's portal role is `author`

#### Scenario: Highest-precedence role wins

- **WHEN** a user's JWT maps to both `consumer` and `admin` via different claim values
- **THEN** the user's effective portal role is `admin` (precedence order: anonymous < consumer < author < reviewer < publisher < admin)

#### Scenario: Authenticated user with no mapped role defaults to consumer

- **WHEN** an authenticated user has no JWT claim that maps to any portal role
- **THEN** their portal role is `consumer`

### Requirement: Session storage is HTTP-only secure cookies

User sessions in the frontend SHALL be stored as HTTP-only, `Secure`, `SameSite=Lax` cookies. The cookie MUST contain only an opaque session identifier (not the raw JWT). The Next.js server-side session store maps the identifier to the underlying tokens. Cookies MUST expire and not be accessible to JavaScript.

#### Scenario: Cookie is HTTP-only

- **WHEN** a user signs in successfully
- **THEN** the `Set-Cookie` response header includes `HttpOnly`, `Secure`, and `SameSite=Lax`, and `document.cookie` in the browser does not expose the session cookie

#### Scenario: Cookie carries opaque identifier only

- **WHEN** the session cookie value is inspected
- **THEN** the value is an opaque token (UUID or signed identifier), not a JWT and not user-identifying information

### Requirement: Sign-out clears session everywhere

The `/auth/signout` route SHALL: clear the local session cookie, call the IdP's RP-initiated logout endpoint (if available), and redirect to the landing page. Subsequent requests MUST behave as anonymous.

#### Scenario: Sign-out clears session

- **WHEN** an authenticated user visits `/auth/signout`
- **THEN** the response includes `Set-Cookie` with `Max-Age=0` for the session cookie, the user is redirected to `/`, and subsequent requests show `/auth/me` returning `{"role": "anonymous"}`

### Requirement: Token validation on every API request

Every authenticated request to the portal API SHALL include a bearer token, validated against the IdP's published JWKS. Tokens MUST be cached locally with a maximum age of 5 minutes; the JWKS itself MAY be cached for longer (up to 1 hour) with key rotation respected via the `kid` claim.

#### Scenario: Invalid token rejected

- **WHEN** a request arrives with a JWT signed by an unknown key or with an expired `exp`
- **THEN** the API responds 401 with body `{"error": "unauthorized", "reason": "<short>"}` and the response body does not echo the token

#### Scenario: Key rotation handled

- **WHEN** the IdP rotates its signing key and issues new tokens with a new `kid`
- **THEN** the API fetches the updated JWKS, validates the new tokens, and continues to validate any still-unexpired old tokens

### Requirement: Configurable IdP via environment variables

The OIDC configuration SHALL be supplied via environment variables: `OIDC_DISCOVERY_URL`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET` (or empty for public clients), `OIDC_REDIRECT_URI`, `OIDC_SCOPES` (default `openid profile email`), and `OIDC_ROLE_MAP_PATH` (path to a YAML file declaring the claim → role map). No OIDC values MAY be hard-coded in source.

#### Scenario: Configuration changes require no rebuild

- **WHEN** an operator changes `OIDC_DISCOVERY_URL` and restarts the API
- **THEN** the API picks up the new value at startup without recompilation
