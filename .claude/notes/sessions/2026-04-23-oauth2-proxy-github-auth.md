---
date: 2026-04-23
title: "oauth2-proxy GitHub Authentication"
---

## Completed Work

**oauth2-proxy (PR #576, merged):**
- `manifests/applications/oauth2-proxy.yaml` — ArgoCD Application, sync-wave -3, three-source pattern
- `manifests/base/oauth2-proxy/values.yaml` — GitHub provider, `github-user: imcbeth`, cookie domain `.k8s.n37.ca`, `upstream: static://202` (validate-only), `skip-provider-button: true`
- `manifests/base/oauth2-proxy/oauth2-proxy-secret-sealed.yaml` — client-id, client-secret, cookie-secret sealed for `oauth2-proxy` namespace
- `manifests/base/network-policies/oauth2-proxy/namespace.yaml` + `network-policy.yaml` — namespace pre-created for network-policies app (wave -40); ingress from ingress-nginx :4180; egress to GitHub API (0.0.0.0/0:443 excluding RFC1918)
- Updated ingress-nginx NetworkPolicy: egress to oauth2-proxy :4180 for auth_request subrequests
- Updated Uptime Kuma ingress: `auth-url` (internal ClusterIP), `auth-signin` (external), `auth-response-headers`

## Key Gotchas

- `auth-url` must use internal ClusterIP (`oauth2-proxy.oauth2-proxy.svc.cluster.local:4180`) not the external hostname — external URL causes hairpin NAT issues (same pattern as blackbox-exporter)
- Always add `namespace.yaml` to `network-policies/` when adding a new namespace NetworkPolicy — the network-policies app runs at wave -40 before any app creates the namespace
- `$escaped_request_uri` is NOT in ingress-nginx v1.14.x's allowlist — use `$uri` (path only) in auth-signin `rd=` parameter

## Adding Auth to Future Services

Add these 3 annotations to any ingress:
```
nginx.ingress.kubernetes.io/auth-url: "http://oauth2-proxy.oauth2-proxy.svc.cluster.local:4180/oauth2/auth"
nginx.ingress.kubernetes.io/auth-signin: "https://oauth.k8s.n37.ca/oauth2/start?rd=$scheme://$host$uri"
nginx.ingress.kubernetes.io/auth-response-headers: "X-Auth-Request-User,X-Auth-Request-Email"
```

## Pull Requests

- **PR #576:** [Merged] feat: deploy oauth2-proxy with GitHub authentication
