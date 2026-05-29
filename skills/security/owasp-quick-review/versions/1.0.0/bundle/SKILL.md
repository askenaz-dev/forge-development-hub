---
name: owasp-quick-review
description: Run an OWASP top-10 sweep over a change set and report findings with severity.
license: MIT
metadata:
  author: appsec
  sdlc_phase: security
---

# OWASP quick review

For every change in scope, check the categories below in order. For each
finding produce: severity (low/medium/high/critical), exact file and line,
short description, suggested remediation.

1. Broken access control — every endpoint enforces authorization;
   horizontal/vertical privilege escalation paths considered.
2. Cryptographic failures — TLS in transit, well-known algorithms at
   rest, key material managed by the platform (not embedded in source).
3. Injection — parameterized queries, validated user input on every
   path that reaches a sink (SQL, OS exec, LDAP, NoSQL, XPath).
4. Insecure design — sensitive workflows include audit logging, secure
   defaults, and explicit fail-closed behavior.
5. Security misconfiguration — default credentials removed; admin
   endpoints not exposed without authn; CORS scoped narrowly.
6. Vulnerable components — declared dependencies advanced past known
   CVEs; transitive dependencies bounded.
7. Auth and identity failures — session lifetimes bounded; MFA where
   risk warrants; secure cookie flags set.
8. Software/data integrity failures — supply chain (signed artifacts,
   verified plugins); CI/CD steps require approvals for prod.
9. Logging and monitoring — every authn event logged; PII redacted in
   logs; alerts on anomalous behavior.
10. Server-side request forgery — every URL fetched from user input
    routed through an allowlist.

When no findings exist in a category, say "no concerns" explicitly so the
reviewer can distinguish "checked and clean" from "not checked".
