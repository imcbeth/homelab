### 2026-01-25 (Early Morning): External-DNS, Grafana & Promtail Fixes

**Completed Work:**
- Diagnosed and fixed external-dns-cloudflare not creating DNS records
- Diagnosed and fixed Grafana pod mount failure (fsGroup race condition)
- Diagnosed and fixed promtail pod not ready (missing K8s API egress in loki NetworkPolicy)
- All 16 ArgoCD applications now Synced and Healthy

**Pull Requests:**
- **PR #295:** [Merged] fix: Add zone-name-filter for external-dns Cloudflare (partial fix)
- **PR #296:** [Merged] fix: Use n37.ca domain filter for external-dns Cloudflare (final fix)
- **PR #297:** [Merged] docs: Update session notes with external-dns fix
- **PR #298:** [Merged] fix: Add fsGroupChangePolicy for Grafana to fix Synology CSI race
- **PR #300:** [Merged] docs: Update TODO.md with completed infrastructure fixes
- **PR #301:** [Merged] fix: Add K8s API egress to loki NetworkPolicy for promtail

**Issues Resolved:**
1. **external-dns not creating records** - Debug showed "zone n37.ca not in domain filter"
   - Root cause: domain-filter=k8s.n37.ca fails because k8s.n37.ca is a subdomain, not the zone name
   - Fix: Changed to domain-filter=n37.ca (the actual Cloudflare zone)
   - Note: At info log level, no-op syncs don't produce logs (appears stuck but is working)

2. **Grafana pod FailedMount** - `applyFSGroup failed: lstat grafana.db-journal: no such file or directory`
   - Root cause: Race condition between fsGroup recursive application and SQLite journal file lifecycle
   - Fix: Added `fsGroupChangePolicy: OnRootMismatch` to skip recursive fsGroup traversal

3. **Promtail pod not ready** - `dial tcp 10.96.0.1:443: i/o timeout` for pod discovery
   - Root cause: Loki NetworkPolicy was missing K8s API egress rules (same issue as argo-workflows PR #291)
   - Fix: Added K8s API egress rules (ClusterIP 10.96.0.1:443 + control plane 10.0.10.0/24:6443)
   - All 5 promtail pods now healthy after restart

**DNS Records Created:**
- A records: argocd.k8s.n37.ca, grafana.k8s.n37.ca, localstack.k8s.n37.ca, workflows.k8s.n37.ca
- TXT ownership: external-dns-a-*.k8s.n37.ca

**Files Modified:**
- `manifests/base/external-dns/deployment-cloudflare.yaml` (domain-filter fix)
- `manifests/base/kube-prometheus-stack/values.yaml` (fsGroupChangePolicy fix)
- `manifests/base/network-policies/loki/network-policy.yaml` (K8s API egress fix)
