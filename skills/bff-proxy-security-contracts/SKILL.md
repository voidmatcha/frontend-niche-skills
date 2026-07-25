---
name: bff-proxy-security-contracts
description: "Use for pre-release security review or remediation when a frontend repository owns server-side BFF/API proxy code: Next.js API Routes or Route Handlers, Remix loaders/actions that relay requests, `/api/proxy` or `?cmd=` catch-all gateways, multipart upload proxies, or WebView-facing server adapters. Covers client-selected target SSRF, named-route/path/method allowlists, alternate-ingress policy drift, auth/body/header capability boundaries, multipart budgets and regenerated boundaries, redirect/error handling, adversarial release gates, and distinguishing gateway mitigations from upstream business-flow or operational controls. Client-only XSS/CSP/cookie review belongs to frontend-security-baseline; browser drag/drop/file picker behavior belongs to file-ingest-contracts."
---

# BFF proxy security contracts

A frontend-owned server route is still a server trust boundary. The dangerous shape is a
thin relay that lets the browser choose a destination, method, headers, or business action
and assumes the upstream will reject anything unintended. Treat each proxy route as a
small capability, not as a transparent tunnel.

## Boundary with sibling skills

- Use **frontend-security-baseline** for browser XSS, CSP, token storage, cookies, CSRF,
  redirects, and client-bundled secrets.
- Use **frontend-auth-flow-contracts** for login/signup/callback/passkey UI behavior.
- Use **file-ingest-contracts** for drag/drop, picker, paste, `accept`/`file.type`, and
  preview URL lifecycle in the browser.
- Use this skill for frontend-owned **server** routes that build or relay upstream HTTP
  requests, including upload-specific or WebView-specific gateway endpoints.
- This does not replace upstream object authorization, persistent replay/idempotency,
  authoritative metering of business value (elapsed time, credits, usage), or a full
  backend threat model.

Read [prior-art](./references/prior-art.md) when the decision needs source-backed comparison
with OWASP, the Next.js BFF guidance, Backstage, Grafana, Formidable, or public proxy
implementations.

## Default workflow

1. **Inventory every ingress.** Find normal request, multipart upload, streaming, callback,
   WebSocket/SSE, admin/tool, and versioned endpoints that can reach the same upstream
   operation. A policy on `/api/request` is not effective if `/api/upload` reaches the same
   action without it.
2. **Write a capability matrix before changing code.** For each ingress, record:
   client selector, server-owned target, allowed methods, auth/role requirement, accepted
   query/body/file shape, forwarded headers, redirect behavior, response handling, timeout,
   and size/rate budgets.
3. **Prefer server-owned routes.** Let the client choose a semantic route name or a
   canonical relative path that must match an anchored positive allowlist. When the
   destination is known in advance, do not accept a complete URL.
4. **Parse once, compare exact components.** Use one URL parser for validation and request
   construction. Pin scheme, origin, port, and pathname as applicable. Keep query
   parameters separate from the route selector. Do not use a denylist or regex as the only
   defense for an arbitrary URL.
5. **Bind policy to the capability, not the transport.** Method, auth, role, body, and
   response rules must apply to every ingress that can invoke the operation. An upload
   endpoint should expose only upload capabilities, not every same-origin API path.
6. **Bound multipart and streaming work before parsing.** Set maximum files, per-file and
   aggregate sizes, field count, total field bytes, and request timeout where product
   latency permits. Preserve or regenerate the correct multipart boundary, and clean up
   temporary files on success, parse error, abort, and upstream failure.
7. **Forward the minimum.** Build a small header allowlist; do not relay browser cookies,
   `Authorization`, hop-by-hop headers, or upstream debug metadata by default. Server-owned
   credentials and role claims must override, not merge behind, client values.
8. **Fail closed without leaking internals.** Disable redirects or validate every hop.
   Return stable public errors; log a correlation key plus method, canonical route, and
   status without credentials, raw bodies, or upstream stack messages.
9. **Separate gateway mitigation from authoritative business controls.** A per-request
   numeric cap can block one oversized payload, but it does not stop replay of many valid
   requests. Persistent state, idempotency, metered business-value checks (elapsed
   time, credits, usage), quotas, and distributed rate limits belong where all
   instances and ingress paths share authority.

## Pre-release prevention gate

Use this before an external assessment, not only after a finding arrives.

1. **Trace sources to outbound sinks.** Start from query, route params, headers, cookies,
   JSON/form bodies, and multipart metadata that can influence `fetch`, Axios, proxy
   middleware, SDK clients, redirects, or server-side file transfer.
2. **Search for sibling ingress.** For every protected business action, find normal,
   upload, streaming, callback, legacy, versioned, admin/tool, and WebView-facing paths
   that can invoke it. One guarded transport does not protect another.
3. **Block release on missing capability contracts.** A relay is not ready when the
   request can choose a complete destination, an unknown same-origin path, an unsupported
   method, client-supplied auth or identity headers that bypass validation or override
   server-injected credentials, an unbounded body/file shape, or a redirect hop outside
   the validated target.
4. **Run negative proof, not source-only review.** Exercise malformed and alternate
   selectors, verify rejection before parser/outbound invocation, use a local OOB listener
   for SSRF, and compare protected state before and after forbidden mutations.
5. **Run positive compatibility proof.** Exercise every legitimate route family,
   including Unicode or whitespace path segments when user text enters the path, and
   confirm multipart reconstruction uses the generated boundary.
6. **Assign residual ownership explicitly.** Classify each remaining item as:
   - **code-local:** this frontend-owned server boundary can decide and enforce it;
   - **upstream:** authoritative ownership, metered usage (e.g. elapsed time), replay/idempotency, shared quota,
     or distributed concurrency must be enforced where persistent state is shared;
   - **operational:** credential rotation, historical log investigation, session/token
     migration, and production egress policy require deployment authority.
7. **Do not overclaim completion.** A request-size or per-request-value cap can close the
   published payload while repeated valid requests still abuse the business flow. Likewise,
   code remediation is not proof that exposed credentials were rotated or that past abuse
   did not occur. Mark those as release follow-up instead of lowering the gate.

## Trap-first review map

| Trap | Why it fails | Prefer |
| --- | --- | --- |
| `fetch(base + req.query.url)` or Axios with a client URL | Authority/userinfo, parser, redirect, and internal-target tricks turn the BFF into an SSRF primitive. | Server-owned named routes; otherwise strict canonical relative-path/origin allowlist and redirects off. |
| A generic same-origin path is considered safe | Same-origin still exposes unintended privileged business actions and can bypass per-route policy. | Capability allowlist of route + method + auth + body/file contract. |
| Security middleware runs only on the JSON/form route | Multipart, streaming, legacy, or alternate-version endpoints can invoke the same action without the rule. | Inventory all ingress paths and test policy equivalence. |
| Upload route checks only file size | Fields can retain large memory budgets; file count, total bytes, parse cleanup, or boundary reconstruction can still fail. | Explicit files/size/fields/field-bytes budgets plus correct regenerated `Content-Type` boundary. |
| Forward all request headers | Browser-controlled auth, cookies, forwarding metadata, and hop-by-hop headers cross trust boundaries. | Small allowlist; inject server-owned credentials after validation. |
| Add an in-memory rate limiter in a clustered/serverless deployment | Each process sees a partial history, so the control can be bypassed by instance selection or restart. | Shared persistent store or authoritative upstream quota; label local caps as mitigation only. |
| Echo `error.message` or log the whole Axios config | Upstream internals, credentials, cookies, and injected body data leak to clients or logs. | Stable public error plus redacted structured log fields. |

## Quick probes

Treat these as leads; confirm the source-to-sink and every alternate ingress.

```sh
# Client-selected targets and string-concatenated upstream URLs
rg -n "req\\.(query|body).*(url|uri|target|endpoint|cmd)|SERVER_URL.*\\+|baseURL.*\\+" src app pages server

# Catch-all API/BFF and upload/stream variants
rg -n "\\[\\.\\.\\.|/api/(proxy|request|upload)|multipart|formidable|multer|FormData|WebSocket|EventSource" .

# Broad header/error forwarding and redirects
rg -n "req\\.headers|headers:\\s*req\\.headers|Authorization|Cookie|maxRedirects|redirect:|error\\.message|axiosRequestConfig" src app pages server

# Process-local abuse controls that may not cover cluster/serverless topology
rg -n "new Map\\(|rateLimit|rateLimiter|setInterval|LRU|memoryStore|cluster|serverless" src app pages server
```

## Verification ladder

1. **Pure policy tests:** known-good route/method pairs, unknown paths, prefix/suffix
   lookalikes, case variants, duplicate slash, dot segments, encoded separators,
   backslashes, userinfo, fragments, arrays, and missing values.
2. **Handler tests:** verify rejection occurs before parser/upstream invocation; verify each
   legitimate capability reaches the next intended gate.
3. **Multipart tests:** assert field/file budgets and that outgoing `Content-Type` uses the
   regenerated form boundary rather than the browser's original boundary.
4. **OOB SSRF test:** run a local listener and verify malicious selectors produce no
   connection. A status code alone is not enough.
5. **State-invariant test:** query state, attempt the forbidden mutation through every
   ingress, query again, and compare.
6. **Replay/concurrency test:** send many individually valid requests when the business
   action grants value. Record this as upstream/operational follow-up if the BFF cannot
   authoritatively decide.

## PR-worthiness gate

File a finding or patch when all hold:

1. A frontend-owned server route constructs or relays an upstream request.
2. Client-controlled data selects or materially changes target, method, auth, headers,
   body/file shape, or business action.
3. The relevant rule is absent, fail-open, or inconsistent across ingress paths.
4. The fix is bounded: named route/capability table, strict allowlist, one shared policy
   seam, multipart budget, header minimization, redirect/error hardening, or a regression
   test covering the boundary.

Reject weak findings:

- A canonical relative path matched against an anchored positive allowlist is not the same
  as regex-validating an arbitrary URL.
- A configured upstream base URL is not client-controlled by itself.
- Do not demand request-time private-IP resolution when the client cannot affect scheme,
  host, or port and redirects are disabled. Treat DNS/egress controls as defense in depth;
  add dynamic-target SSRF controls when a request can influence the destination.
- Missing gateway rate limiting is not automatically a code bug when an authoritative
  upstream already enforces persistent quotas; verify the real owner first.
- Do not replace a small capability allowlist with a policy framework unless route growth
  or repeated drift provides evidence.

## Output shape

- **Ingress/capability:** which browser-facing server route reaches which upstream action.
- **Trust break:** exact client-controlled selector/header/body/file and the missing rule.
- **Cross-ingress check:** normal/upload/stream/versioned paths that can invoke the action.
- **Minimal fix:** named route, anchored route-method-auth policy, boundary/budget, or
  redacted error change.
- **Verification:** policy test, pre-forward handler test, OOB connection count, and state
  invariant.
- **Residual owner:** code-local, upstream/shared infrastructure, or operational
  credential/log follow-up.
- **Release verdict:** PASS, BLOCK, or PASS with named upstream/operational follow-up;
  never fold unresolved authority or credential work into a generic “fixed” claim.

## Sources

- OWASP SSRF Prevention Cheat Sheet: <https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html>
- OWASP REST Security Cheat Sheet: <https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html>
- OWASP Authorization Cheat Sheet: <https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html>
- OWASP File Upload Cheat Sheet: <https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html>
- OWASP API6:2023 Unrestricted Access to Sensitive Business Flows: <https://owasp.org/API-Security/editions/2023/en/0xa6-unrestricted-access-to-sensitive-business-flows/>
- Next.js Backend for Frontend guide: <https://nextjs.org/docs/app/guides/backend-for-frontend>
- Backstage proxy route configuration: <https://backstage.io/docs/plugins/proxying/>
- Next.js strict remote URL patterns: <https://nextjs.org/docs/pages/api-reference/components/image#remotepatterns>
- Grafana proxy routes and request security: <https://grafana.com/developers/plugin-tools/how-to-guides/data-source-plugins/add-authentication-for-data-source-plugins>, <https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/configure-request-security/>
