# BFF proxy security prior art

This is a source comparison, not a claim that every proxy needs the same architecture.
Use it to justify the narrowest boundary for the actual product flow.

## Primary guidance

### Next.js Backend for Frontend

Next.js documents Route Handlers, Proxy, and Pages Router API Routes as publicly reachable
HTTP endpoints, not private implementation details. Its BFF guide says to validate before
forwarding, authenticate and authorize protected access, verify payload type and size, and
be deliberate about which request and response headers cross the boundary.

- <https://nextjs.org/docs/app/guides/backend-for-frontend>

**Implication:** UI constraints are not access controls. Apply the route, method, identity,
payload, and header contract inside the public server boundary before the outbound request.

### OWASP SSRF Prevention

When the target applications are known in advance, OWASP treats a positive allowlist as
the viable case. It warns that complete URLs are difficult to validate because parsers can
be abused, and recommends disabling redirect following to prevent validation bypass.

- <https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html>
- <https://owasp.org/Top10/2021/A10_2021-Server-Side_Request_Forgery_%28SSRF%29/>

**Implication:** a BFF with one configured upstream should accept a route capability or a
canonical relative path, not an arbitrary destination URL. A denylist is defense in depth,
not the primary destination control.

### OWASP REST, authorization, and business flows

OWASP REST guidance recommends an allowlist of HTTP methods and `405` for unsupported
methods. Authorization guidance places checks server-side/gateway-side on every request.
API6:2023 describes valid but repeatable business actions as a separate abuse class:
per-request input validity does not establish that repeated use is legitimate.

- <https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html>
- <https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html>
- <https://owasp.org/API-Security/editions/2023/en/0xa6-unrestricted-access-to-sensitive-business-flows/>
- <https://cheatsheetseries.owasp.org/cheatsheets/Business_Logic_Security_Cheat_Sheet.html>

**Implication:** bind route, method, role, and body policy to every ingress. Keep replay,
idempotency, metered usage (e.g. elapsed time), and distributed quotas at a persistent authority shared by all
instances.

### OWASP upload and resource budgets

OWASP recommends explicit file/request limits to reduce resource exhaustion.

- <https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html>
- <https://cheatsheetseries.owasp.org/cheatsheets/Denial_of_Service_Cheat_Sheet.html>
- <https://asvs.dev/v5.0.0/V5-File-Handling/>

**Implication:** file size alone is incomplete. Bound file count, total bytes, field count,
and total field bytes before expensive processing.

## Mature open-source patterns

### Backstage

Backstage's proxy backend is configured as a map of server-owned endpoint prefixes to
targets. Each endpoint can restrict `allowedMethods`, `allowedHeaders`, and credential
policy.

- Docs: <https://backstage.io/docs/plugins/proxying/>
- Config source: <https://github.com/backstage/backstage/blob/master/plugins/proxy-backend/config.d.ts>

**Pattern:** explicit proxy capabilities, not a browser-selected arbitrary destination.

### Grafana

Grafana proxy routes are declared in plugin configuration and can add server-side secrets.
Grafana also exposes a separate egress allowlist for user-generated server requests.

- Proxy routes: <https://grafana.com/developers/plugin-tools/how-to-guides/data-source-plugins/add-authentication-for-data-source-plugins>
- Request security: <https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/configure-request-security/>

**Pattern:** server-registered route templates plus an independent egress boundary.

### Next.js image optimizer

Next.js deprecated broad `images.domains` in favor of `remotePatterns`, which can pin
protocol, hostname, port, pathname, and search. Its documentation recommends being as
specific as possible and notes that redirect following needs its own bound.

- Docs: <https://nextjs.org/docs/pages/api-reference/components/image#remotepatterns>
- Matcher source: <https://github.com/vercel/next.js/blob/canary/packages/next/src/shared/lib/match-remote-pattern.ts>

**Pattern:** exact component matching for a frontend-owned server fetch surface.

## Supplemental public proxy implementations

These are lower-authority implementation examples, useful for test ideas rather than as
standards.

- `arcademan21/nextjs-proxy` recommends server-defined named routes, rejects unknown
  route names, keeps detailed denial reasons out of public responses, and tests
  transform-rewritten destinations again:
  <https://github.com/arcademan21/nextjs-proxy>
- `pajarrahmansyah/passit` uses config-bound base URLs and per-route timeouts:
  <https://github.com/pajarrahmansyah/passit>

## Multipart library behavior

Formidable defaults are intentionally broad (`maxFields: 1000`,
`maxFieldsSize: 20 MiB`), so product routes should supply smaller limits. Node `form-data`
creates a new multipart boundary; its documentation recommends sending `getHeaders()` so
the outbound `Content-Type` matches the regenerated body.

- Formidable options: <https://github.com/node-formidable/formidable#options>
- Node form-data headers/boundary: <https://github.com/form-data/form-data#headers-getheaders-headers-userheaders>

## Decision rule

For a small BFF:

1. Use named capabilities when changing the client contract is cheap.
2. Otherwise accept only canonical relative paths that match an anchored route family.
3. Keep a compact route-method-auth policy next to the proxy boundary.
4. Use a separate upload allowlist when only a few endpoints legitimately accept
   multipart; do not force parsed multipart fields through a JSON-specific interceptor.
5. Add a framework only after route growth or repeated policy drift makes the small table
   harder to understand than the abstraction.
