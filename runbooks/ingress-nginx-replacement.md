# ingress-nginx Replacement Plan

**Why:** ingress-nginx is retired upstream. Controller v1.15.1 (2026-03-19) is
the final release and still carries the CRITICAL CVEs Trivy reports, so there is
nothing left to upgrade to.
**Current:** chart 4.15.1, controller v1.15.1, 2 replicas, LoadBalancer `10.0.10.10`
**Drafted:** 2026-11-15
**Status:** Phase 0 **passed** 2026-11-15 (#1180, #1181, #1183) — see
"Phase 0 results" below. Phase 1 not started.

## TL;DR

**Recommended: Istio's Gateway API implementation**, on the istiod we already run.

- The Gateway API CRDs are installed (6) and the `istio` GatewayClass is
  `Accepted` (293 days). No new controller to run on the Pis.
- It covers the one hard requirement — oauth2-proxy forward-auth on 5 hosts —
  through Envoy `ext_authz` (an `extensionProviders` entry plus a `CUSTOM`
  AuthorizationPolicy). That is the piece to prototype first.
- **The public site is not at risk.** `lifeonabike.ca` reaches the cluster
  through the Cloudflare tunnel straight to `web.lifeonabike:80`, and GitHub
  webhooks go to the EventSource directly. ingress-nginx serves only LAN
  traffic: the `*.k8s.n37.ca` hosts and LAN-side `lifeonabike.ca`.

Cut over **per host**, behind a second MetalLB IP, not as a big-bang swap.

## What has to be replaced

Live inventory, 2026-11-15 (10 Ingresses):

| Host | Namespace | nginx features in use |
|------|-----------|-----------------------|
| workflows.k8s.n37.ca | argo-workflows | **forward-auth**, rate limit 50 rps / 20 conns |
| falco.k8s.n37.ca | falco | **forward-auth**, rate limit 50 / 20 |
| flink.k8s.n37.ca | flink-demo | **forward-auth**, timeouts 3600 s |
| status.k8s.n37.ca | uptime-kuma | **forward-auth**, timeouts 3600 s, `server-snippets` (WebSocket upgrade headers) |
| argocd.k8s.n37.ca | argocd | **HTTPS backend**, `rewrite-target: /`, rate limit 50 / 20 |
| grafana.k8s.n37.ca | default | rate limit 100 / 20 |
| localstack.k8s.n37.ca | localstack | rate limit 50 / 20 |
| registry.k8s.n37.ca | zot | `proxy-body-size: 0`, timeouts 600 s |
| oauth.k8s.n37.ca | oauth2-proxy | none (no class set) |
| lifeonabike.ca, www | lifeonabike | `ssl-redirect` (LAN path only) |

Forward-auth = `auth-url` to `oauth2-proxy.oauth2-proxy:4180/oauth2/auth`,
`auth-signin` redirect to `https://oauth.k8s.n37.ca/oauth2/start?rd=...`, and
`auth-response-headers` passing `X-Auth-Request-User` / `-Email` upstream.

Controller-wide hardening in `manifests/base/ingress-nginx/values.yaml`
(security headers, `ssl-protocols: TLSv1.2 TLSv1.3`) must be carried over too.

## Options considered

| | Istio Gateway API | Envoy Gateway | Traefik |
|---|---|---|---|
| New controller | **no** (istiod 1.30.8) | yes | yes |
| Forward-auth | ext_authz via mesh config + `CUSTOM` AuthorizationPolicy | `SecurityPolicy.extAuth` (native) | `forwardAuth` middleware (native) |
| Rate limiting | EnvoyFilter only (not Gateway API) | `BackendTrafficPolicy` (native) | middleware (native) |
| HTTPS backend | `BackendTLSPolicy` / DestinationRule | `BackendTLSPolicy` | ServersTransport |
| Fits the ambient mesh | native | separate data plane | separate data plane |

Envoy Gateway maps the feature list most directly, and Traefik is the closest to
annotation-style config. Both add a controller and a data plane to keep patched
on 5 Pis. Istio wins on not adding anything — **if** forward-auth works, which is
why Phase 0 tests exactly that.

**Rate limiting is the one feature Istio makes awkward, and it is the least
needed.** Every rate-limited host is LAN-only (`*.k8s.n37.ca` is NXDOMAIN
publicly). Proposal: drop per-host limits at cutover and record that decision,
rather than carry EnvoyFilters. Revisit only if a host is ever exposed publicly.

## Prerequisites (all currently missing)

1. **external-dns:** both deployments watch `--source=ingress`, `service`, `crd`.
   Add `--source=gateway-httproute` to `external-dns-unifi` (the LAN records), or
   records will not follow hosts as they move.
2. **cert-manager:** no Gateway API support is enabled. Turn on its Gateway API
   integration (chart `config.enableGatewayAPI`, verify the key for 1.21) so
   Gateway listeners can get certificates the way Ingress TLS does now.
3. **Istio mesh config:** add an `extensionProviders` entry (type
   `envoyExtAuthzHttp`) pointing at `oauth2-proxy.oauth2-proxy.svc:4180`, with
   `headersToUpstreamOnAllow` for the two `X-Auth-Request-*` headers and
   `headersToDownstreamOnDeny` including `location` and `set-cookie` so the
   sign-in redirect reaches the browser.
4. **NetworkPolicy:** the gateway pod's namespace needs ingress from the LAN on
   443/80 and egress to every backend and to oauth2-proxy. Backends currently
   admit `ingress-nginx` by namespace; each needs the gateway's namespace added
   (and, for non-meshed backends, the real app port — see REFERENCE.md "HBONE
   bypass requires BOTH ends ambient-meshed").

## Phase 0 — prototype one host (exit criteria are the unknowns)

Pick **falco.k8s.n37.ca**: forward-auth, low traffic, nothing depends on it.

- Create a `Gateway` (class `istio`) on a **second MetalLB IP** (e.g.
  `10.0.10.11`; pool is `.10-.99`, only `.10` used) and an `HTTPRoute` for falco.
- Point only a test client at it (`curl --resolve falco.k8s.n37.ca:443:10.0.10.11`).

Verify, and stop if any fails:
- [ ] Unauthenticated request returns a **302 to `oauth.k8s.n37.ca/oauth2/start`**
      with `rd=` set to the original URL (ext_authz deny path).
- [ ] After GitHub sign-in the UI loads, and the backend sees
      `X-Auth-Request-User` (allow path).
- [ ] The oauth2-proxy cookie set on `oauth.k8s.n37.ca` is honoured for
      `falco.k8s.n37.ca` (cookie domain unchanged from today).
- [ ] TLS certificate issued by cert-manager for the listener.
- [ ] Gateway pod resource use on a Pi is acceptable next to ingress-nginx.

If forward-auth cannot be made to work cleanly, switch the recommendation to
**Envoy Gateway** (native `extAuth`) and redo Phase 0 there.

## Phase 0 results (2026-11-15)

The prototype (`manifests/base/istio-gateway/`, Application `istio-gateway`)
serves falco.k8s.n37.ca on 10.0.10.11. Forward-auth through Istio **works**,
after two fixes that Phase 1 depends on:

1. **The post-sign-in return URL was relative.** An ext_authz check carries only
   the path, so oauth2-proxy encoded `/path` in `state` and the user would have
   landed on `oauth.k8s.n37.ca/path`. Fixed by having the extension provider set
   `x-auth-request-redirect: "https://%REQ(:authority)%%REQ(:path)%"` on every
   check (#1181). oauth2-proxy still validates it against `--whitelist-domain`.
2. **Envoy's HTTP ext_authz allows only `200`.** oauth2-proxy answered
   authenticated checks from its `static://202` upstream, which Envoy treated as
   a denial and returned to the browser (`response_code 202`,
   `response_flags UAEX`). Fixed with `static://200` (#1183); nginx's
   `/oauth2/auth` flow is unaffected.

Verified: valid TLS from the existing certificate (ReferenceGrant), signed-out
→ 302 to GitHub with an absolute return URL, and a real browser sign-in reached
the Sidekick UI (gateway counters: `200` from `falco-falcosidekick-ui`). The
gateway had to live in `istio-system`: Gatekeeper's `allowed-repos` rejects
`registry.istio.io` elsewhere.

**Testing tip:** DNS resolves every host to 10.0.10.10 (ingress-nginx), so a
plain browser visit tests nginx, not the gateway. Without editing `/etc/hosts`:
`open -na "Google Chrome" --args --user-data-dir=/tmp/chrome-proto-gateway --host-resolver-rules="MAP <host> 10.0.10.11" https://<host>/`.
Envoy counters are the ground truth for where a request went:
`kubectl exec -n istio-system <gateway pod> -- pilot-agent request GET stats | grep istio_requests_total`.

## Phase 1 — migrate host by host

For each host, in this order (lowest risk first): localstack, grafana, falco,
flink, workflows, status (WebSockets — test a live dashboard), argocd (HTTPS
backend; also check the argocd CLI/gRPC path), registry (large pushes — push a
multi-GB image), oauth (last of the auth hosts' dependencies), lifeonabike LAN.

Per host:
1. Add the `HTTPRoute` (and `BackendTLSPolicy` / timeouts as needed).
2. Move the DNS record to the new IP (external-dns, once it reads HTTPRoutes).
3. Test from a LAN client; keep the Ingress in place for instant rollback.
4. After a day without issues, delete the Ingress.

Rollback for any host: point its record back at `10.0.10.10`.

## Phase 2 — remove ingress-nginx

Only once no Ingress references class `nginx`:
- Delete the `ingress-nginx-config` Application and its namespace.
- Move the Gateway to `10.0.10.10` if a stable well-known IP is wanted, or
  leave it on `.11` and update the UniFi wildcard/records.
- Remove `ingress-nginx` from NetworkPolicy `from` lists across namespaces
  (`scripts/networkpolicy-port-audit.py` will not catch stale namespace
  references — grep for it).
- Update k8s-docs-n37 (`docs/applications/ingress-nginx.md` and the networking
  overview) and the CLAUDE.md cluster table.

## Related

- **O8 in TODO.md** — in ambient namespaces, NetworkPolicy application-port
  rules do not restrict meshed-to-meshed traffic. Istio AuthorizationPolicy is
  the enforcement point there, and this migration introduces the first one
  (the `CUSTOM` ext_authz policy). Worth designing both together.
