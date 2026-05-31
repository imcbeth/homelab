# 2026-04-23: Zot OCI Registry — Deployment + Pull-Through Fix

## Completed Work

**Zot v2.1.16 Deployed (PR #571):**
- `manifests/applications/zot.yaml` — multi-source ArgoCD app (Helm 0.1.106 + values + SealedSecret)
- `manifests/base/zot/values.yaml` — StatefulSet (persistence: true), 50Gi iSCSI PVC, sync extension for 4 upstreams, search/CVE/metrics/scrub extensions, ingress via nginx+cert-manager
- `manifests/base/zot/zot-htpasswd-sealed.yaml` — SealedSecret for htpasswd auth
- `manifests/base/network-policies/zot/network-policy.yaml` — NetworkPolicy for zot namespace
- `manifests/base/gatekeeper/constraints/allowed-repos.yaml` — added `registry.k8s.n37.ca`
- Synced+Healthy on first try. CVE DB (850MB) downloaded. Ingress at registry.k8s.n37.ca.

**504 Fix — ingress-nginx egress (PR #572):**
- Root cause: ingress-nginx NetworkPolicy had no egress rule to `zot` namespace on port 5000
- Fix: added egress rule to `manifests/base/network-policies/ingress-nginx/network-policy.yaml`

**Pull Timeout Fix — ARM64 platform filter (PR #572):**
- Root cause: on-demand sync downloaded ALL platform variants for multi-arch images (e.g. nginx:latest = 12+ platforms, ~41s). Docker client timed out waiting for manifest HEAD response.
- Fix: added `"platforms": [{"os": "linux", "arch": "arm64"}]` to all 4 upstream sync configs
- Result: first-pull now takes seconds (single platform only)

## Key Gotchas
1. ingress-nginx NetworkPolicy needs an explicit egress rule for EACH backend namespace+port — not just the backend's ingress rule
2. Zot on-demand sync blocks the manifest HTTP response until the entire image is synced. Without platform filter on a pure ARM64 cluster, all AMD64/arm/v7/s390x variants are also downloaded.
3. SealedSecret files must match `*-sealed.yaml` pattern (not `sealed-secret-*.yaml`) to be excluded from yamllint line-length check in pre-commit hooks.

## Pull Requests
- **PR #571:** [Merged] feat: deploy Zot OCI registry v2.1.16
- **PR #572:** [Merged] fix: ingress-nginx egress to zot + arm64-only sync filter
