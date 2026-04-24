# Homelab TODO

## Phase 5: Observability & Hardening

### Completed
- [x] Ingress hardening (security headers, rate limiting, Helm migration)
- [x] NetworkPolicy for istio-system (bare HBONE rules, istiod xDS, ztunnel data plane)
- [x] Gatekeeper exclusion audit (10 → 2 remaining: kube-system, tigera-operator)
- [x] Linkerd dead code cleanup
- [x] DNS egress AND semantics fix across all NetworkPolicies

### In Progress
- (none)

### Recently Completed
- [x] Documentation sync — k8s-docs-n37 PR #67 (9 files, 283 insertions)

### Backlog
- [ ] Istio ambient mesh alerting — PrometheusRule alerts for XDS push failures, proxy disconnections, high convergence time
- [ ] Grafana alerting on APM dashboard — alert rules for active TCP connections drop, connected proxies < 5, OOMKills
- [ ] tigera-operator Gatekeeper exclusion — last removable exclusion, requires patching upstream release manifest
- [ ] NetworkPolicy coverage expansion — 11/25 namespaces covered, remaining: default, monitoring, argocd, pihole, falco, kube-system, gatekeeper-system, calico-system, tigera-operator, sealed-secrets, synology-csi, external-dns (wait — some already have them, audit needed)
