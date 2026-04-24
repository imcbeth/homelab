# 2026-03-01: Istio 1.29.0 Upgrade, Webhook Fix & Blackbox Cleanup

**Completed Work:**
- Verified PRs #485 (homelab) and #69 (k8s-docs-n37) both merged
- Upgraded Istio from 1.28.4 → 1.29.0 (Renovate PR #469 was already merged, applied in-cluster)
- All 11 pods rolled out with 0 restarts across 5 nodes
- Fixed istiod webhook NetworkPolicy (ipBlock → bare port rule for hostNetwork API server)
- Webhook validation controller successfully switched to fail-closed mode after fix
- Removed failing blackbox-exporter direct HTTP probe to argocd-server:80
  - Root cause: ambient mesh ztunnel intercepts outbound → argocd NetworkPolicy blocks non-ingress sources
  - Redundant: HTTPS probe via ingress (argocd.k8s.n37.ca) already covers ArgoCD monitoring
- Ztunnel error logs now clean (was logging timeout errors every 30s)
- Renovate dependency dashboard checked — no pending updates
- Final state: 24/25 apps Synced+Healthy, 5/5 nodes Ready

**Pull Requests:**
- **PR #486:** [Merged] fix: use bare port rule for istiod webhook NetworkPolicy
- **PR #487:** [Merged] fix: remove failing direct argocd HTTP probe from blackbox-exporter

**Issues Resolved:**
1. **istiod webhook validation stuck** — Validation controller couldn't reach webhook (port 15017) because API server (hostNetwork) doesn't match namespaceSelector, and Calico IPIP rewrites source IP. Fix: bare port rule. Webhook now fail-closed.
2. **blackbox-exporter → argocd-server timeout** — Direct probe to argocd-server.argocd:80 blocked by argocd NetworkPolicy when traffic proxied through ztunnel (ambient mesh). Fix: removed redundant probe (HTTPS ingress probe already covers it).

**Key Learning:**
- Istio 1.29.0 enables DNS capture and iptables reconciliation by default for ambient mode
- istiod auto-sets GOMEMLIMIT to 90% of memory limits in 1.29.0
- The ipBlock/IPIP NetworkPolicy pattern continues — any webhook called by kube-apiserver needs bare port rules
- Ambient mesh changes the source identity of outbound traffic — direct service probes from meshed namespaces to non-meshed namespaces may be blocked by destination NetworkPolicies

**Files Modified:**
- `manifests/base/network-policies/istio-system/network-policy.yaml` (webhook ipBlock → bare port)
- `manifests/base/kube-prometheus-stack/values.yaml` (removed blackbox-http job)
