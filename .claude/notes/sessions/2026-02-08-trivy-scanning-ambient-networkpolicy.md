### 2026-02-08: Trivy Vulnerability Scanning & Ambient Mesh NetworkPolicy Fix

**Completed Work:**
- Fixed trivy-operator vulnerability scanning (was completely broken, now generating 58+ reports)
- Root cause 1: NetworkPolicy blocked HBONE port 15008 (ztunnel tunnel traffic) between operator and trivy-server
- Root cause 2: Gatekeeper require-labels constraint blocked scan job pods (no `app.kubernetes.io/name` label)
- Root cause 3: `sbomGenerationEnabled: true` is a v0.29.0 bug preventing VulnerabilityReports (fixed in prior PR #410)
- Enhanced Trivy security dashboard with vulnerability panels (stats, trends, donut chart, table)
- Enabled vulnerability PrometheusRule alerts (CriticalVulnerabilitiesDetected, HighVulnerabilityCount)
- Fixed all 5 ambient mesh namespace NetworkPolicies with bare HBONE port 15008 rules + link-local health probes

**Pull Requests:**
- **PR #411:** [Merged] fix: allow HBONE port 15008 in trivy NetworkPolicy for ambient mesh
- **PR #412:** [Merged] fix: add HBONE port 15008 rules to all ambient mesh NetworkPolicies

**Issues Resolved:**
1. **Trivy vulnerability scanning inert** - Operator couldn't reach trivy-server via HBONE tunnel. Fix: bare port 15008 ingress/egress in NetworkPolicy.
2. **Gatekeeper blocking scan job pods** - Scan jobs lack `app.kubernetes.io/name`. Fix: exempt trivy-system from require-labels constraint.
3. **Ambient mesh NetworkPolicy pattern incorrect** - All 5 ambient namespaces had namespace-scoped port 15008 rules. In ambient mode, ztunnel rewrites dest port to 15008 for ALL traffic, so bare (source-agnostic) rules are needed.

**Key Learning:**
- In Istio ambient mesh, ztunnel rewrites the destination port to 15008 for ALL inter-pod traffic
- NetworkPolicies must use bare `ports: [{port: 15008}]` rules (no `from`/`to` selector) for HBONE
- Link-local 169.254.7.127/32 must be allowed for ztunnel health probes
- ArgoCD selfHeal will revert manual kubectl changes; must merge PRs before testing

**Files Modified:**
- `manifests/base/network-policies/trivy-system/network-policy.yaml` (HBONE fix)
- `manifests/base/network-policies/loki/network-policy.yaml` (HBONE fix)
- `manifests/base/network-policies/unipoller/network-policy.yaml` (HBONE fix)
- `manifests/base/network-policies/argo-workflows/network-policy.yaml` (HBONE fix)
- `manifests/base/network-policies/localstack/network-policy.yaml` (HBONE fix)
- `manifests/base/gatekeeper/constraints/require-labels.yaml` (trivy-system exemption)
