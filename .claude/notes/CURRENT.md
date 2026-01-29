# Claude Code - Homelab Current Context

**Last Updated:** 2026-01-28
**Repository:** imcbeth/homelab
**Cluster:** 5x Raspberry Pi 5 (16GB each) Kubernetes Homelab

---

## Quick Start

1. Read this file for recent session context
2. Check `TODO.md` for current priorities
3. Reference `.claude/notes/REFERENCE.md` for patterns and gotchas
4. Grep `.claude/notes/sessions/` for historical lookups

---

## Current State

**Secrets Management:** Complete
- 8 SealedSecrets deployed, git-crypt migration finished
- Sealing key backed up to Synology NAS
- Bootstrap secret: `secrets/argocd-git-access.yaml` (manual apply)
- Grafana password: Helm-managed (do NOT create SealedSecret)

**Backup Strategy:** Complete
- Daily ArgoCD config backup (1:30 AM)
- Daily critical PVC backup (2:00 AM)
- Weekly full cluster backup (3:00 AM Sunday)
- Backblaze B2 restore tested and validated

**Monitoring:** Operational
- AlertManager email: 121 sent, 0 failed
- Trivy scanning: 10 CRITICAL (blocked on upstream)
- All Prometheus targets healthy

**Dependency Management:** Complete
- Renovate GitHub App deployed
- Weekend schedule (Sat/Sun 6am-9pm)
- Grouped updates: ArgoCD, monitoring, networking, security, backup

**Network Policies:** Complete (9 namespaces)
- All namespaces isolated: localstack, unipoller, loki, trivy-system, velero, argo-workflows, cert-manager, external-dns, metallb-system
- ArgoCD Application at sync-wave -40
- **Gotcha:** K8s API egress requires both ClusterIP (10.96.0.1:443) AND control plane network (10.0.10.0/24:6443)

**Argo Workflows:** Deployed (2026-01-24)
- Argo Workflows v3.7.8 (Helm chart 0.47.1) at sync-wave -8
- 16 ArgoCD applications total, all Synced and Healthy
- B2 artifact storage working (PRs #287-289 fixed credentials)
- NetworkPolicy enabled (PR #291 fixed K8s API egress)
- UI accessible at https://workflows.k8s.n37.ca (PR #293)

**External-DNS:** Fixed (2026-01-25)
- Root cause: domain-filter=k8s.n37.ca rejected the n37.ca zone
- Fix: Changed to domain-filter=n37.ca (PRs #295-296)
- All 4 A records + TXT ownership records now auto-managed

**Istio Ambient Mesh:** Deployed (2026-01-28)
- 29 pods across 6 namespaces with mTLS (HBONE protocol)
- Namespaces: default, loki, argo-workflows, localstack, unipoller, trivy-system
- Resource usage: ~38m CPU, ~145Mi memory (istiod + cni + ztunnel)
- Waypoint proxies: Skipped (L4 mTLS sufficient, add later if L7 needed)
- **Gotcha:** Transparent proxy preserves source IPs; NetworkPolicies need HBONE port 15008 from source namespace

**Phase 3 Status:** Complete
- Service mesh deployed (Istio Ambient selected over Linkerd)

---

## Recent Sessions

### 2026-01-28: Istio Ambient NetworkPolicy Fixes

**Completed Work:**
- Fixed critical NetworkPolicy issues for Istio Ambient transparent proxy
- Updated all meshed namespace policies with HBONE port 15008 rules
- 29 pods now have mTLS across 6 namespaces
- Documented NetworkPolicy pattern for transparent proxy architecture

**Pull Requests:**
- **PR #315:** [Merged] fix: Add HBONE ingress rules for Istio ambient mesh
- **PR #316:** [Merged] fix: Correct HBONE ingress selector for Istio ambient mesh
- **PR #317:** [Merged] fix: Allow application ports from istio-system for ambient mesh
- **PR #318:** [Merged] fix: Add HBONE port 15008 for Istio ambient transparent proxy
- **PR #319:** [Merged] docs: Add session notes for Istio Ambient NetworkPolicy fixes

**Key Technical Learning:**
Istio Ambient uses transparent proxy (TPROXY) which preserves source IPs. NetworkPolicies must:
1. Allow HBONE port 15008 from the actual source namespace (not just istio-system)
2. Include port 15008 in both ingress AND egress rules for mesh communication
3. Allow app ports from istio-system for ztunnel-terminated connections

**Resource Usage:**
| Component | Instances | CPU | Memory |
|-----------|-----------|-----|--------|
| istiod | 1 | ~3m | ~39Mi |
| istio-cni-node | 5 | ~5m | ~68Mi |
| ztunnel | 5 | ~30m | ~38Mi |

**Files Modified:**
- `manifests/base/network-policies/{loki,localstack,argo-workflows,unipoller,trivy-system}/network-policy.yaml`

---

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

---

### 2026-01-24 (Late Night): Argo Workflows Completion & Ingress

**Completed Work:**
- Verified B2 artifact storage working (ran artifact-test workflow successfully)
- Fixed NetworkPolicy K8s API egress - requires both ClusterIP AND control plane network
- Added nginx ingress for Argo Workflows UI at workflows.k8s.n37.ca
- Updated NetworkPolicies for velero and trivy-system with same API egress fix
- Discovered external-dns-cloudflare not syncing (investigating)

**Pull Requests:**
- **PR #290:** [Merged] docs: Mark Argo Workflows B2 artifact storage as fixed
- **PR #291:** [Merged] fix: Add control plane network to NetworkPolicy API egress rules
- **PR #292:** [Merged] docs: Update session notes - NetworkPolicy fix complete
- **PR #293:** [Merged] feat: Add nginx ingress for Argo Workflows UI

**Key Discovery - NetworkPolicy K8s API Egress:**
With Calico CNI, K8s API access requires BOTH:
1. ClusterIP service: `10.96.0.1/32:443`
2. Control plane network: `10.0.10.0/24:6443`

**Files Created/Modified:**
- `manifests/base/argo-workflows/ingress.yaml` (new)
- `manifests/base/network-policies/argo-workflows/network-policy.yaml` (enabled + fixed)
- `manifests/base/network-policies/velero/network-policy.yaml` (API egress fix)
- `manifests/base/network-policies/trivy-system/network-policy.yaml` (API egress fix)

**Known Issues:**
- external-dns-cloudflare stuck after startup (no sync logs)
- TLS certificate pending DNS-01 challenge (manual A record added)

---

### 2026-01-24 (Night): Argo Workflows Deployment

**Completed Work:**
- Deployed Argo Workflows v3.7.8 (Helm chart 0.47.1) at sync-wave -8
- Configured Pi-optimized resource limits (Controller: 100m/256Mi, Server: 50m/128Mi)
- Created SealedSecret for B2 credentials (`homelab-workflows` bucket)
- Added test WorkflowTemplates (hello-world, artifact-test)
- Created NetworkPolicy for argo-workflows namespace (temporarily disabled)
- Test workflow executed successfully

**Pull Requests:**
- **PR #277:** [Merged] feat: Add Argo Workflows for CI/CD pipeline automation
- **PR #280:** [Merged] fix: Set default serviceAccountName for Argo Workflows
- **PR #281:** [Merged] fix: Update Argo Workflows B2 credentials
- **PR #282:** [Merged] fix: Correct NetworkPolicy DNS and API rules
- **PR #283:** [Merged] fix: Temporarily disable argo-workflows NetworkPolicy
- **PR #284:** [Merged] fix: Disable archiveLogs until B2 permissions are fixed
- **PR #285:** [Merged] docs: Mark Argo Workflows as deployed in TODO.md

**Issues Resolved:**
1. **Workflow pods using wrong service account** - Added `serviceAccountName: argo-workflow` to workflowDefaults
2. **NetworkPolicy blocking K8s API** - Fixed in PR #291
3. **B2 "not entitled" error** - Fixed in PRs #287-289

**Files Created:**
- `manifests/applications/argo-workflows.yaml`
- `manifests/base/argo-workflows/values.yaml`
- `manifests/base/argo-workflows/b2-credentials-sealed.yaml`
- `manifests/base/argo-workflows/test-workflow.yaml`
- `manifests/base/network-policies/argo-workflows/network-policy.yaml`

**Final Cluster Status:**
- 16/16 ArgoCD applications Synced and Healthy
- Test workflow: Succeeded

---

### 2026-01-24 (Evening): Network Policies Implementation

**Completed Work:**
- Implemented Kubernetes NetworkPolicies for 5 namespaces
- Created ArgoCD Application for GitOps deployment (sync-wave -40)
- Validated all policies don't break existing functionality
- All tests passed: Prometheus scraping, Velero backups, Loki logs

**Pull Requests:**
- **PR #274:** [Merged] feat: Add NetworkPolicies for namespace isolation
- **PR #57:** [Merged] docs: Add Network Policies documentation (k8s-docs-n37)

**NetworkPolicies Deployed:**
| Namespace | Ingress Allowed | Egress Allowed |
|-----------|-----------------|----------------|
| localstack | velero, ingress-nginx, prometheus | DNS only |
| unipoller | prometheus | DNS, UniFi (10.0.1.1) |
| loki | promtail, prometheus, grafana | DNS, alertmanager |
| trivy-system | prometheus | DNS, K8s API, registries |
| velero | prometheus | DNS, localstack, B2, K8s API |

**Files Created:**
- `manifests/base/network-policies/kustomization.yaml`
- `manifests/base/network-policies/{localstack,unipoller,loki,trivy-system,velero}/network-policy.yaml`
- `manifests/applications/network-policies.yaml`

**Verification Results:**
- Prometheus → all namespace metrics: Working
- Velero → B2 backup storage: Available
- Promtail → Loki: Connected (label limit warning is pre-existing)
- ArgoCD UI: HTTP 200

---

## Session Archive Index

| Date | Title | Key Topics |
|------|-------|------------|
| 2026-01-23 | Renovate PR Merge & Velero Fix | 20 PRs merged, Velero v1.17 breaking change |
| 2026-01-21 | Restructure CLAUDE_NOTES.md | Modular notes system, 93% reduction |
| 2026-01-14 | Sealed Secrets Ops & Backups | Key backup, B2 restore test, ArgoCD backup |
| 2026-01-14 | Documentation Update - Sealed Secrets | k8s-docs-n37, Security section |
| 2026-01-14 | Secrets Migration Completion | ESO removal, 8 SealedSecrets final |
| 2026-01-14 | Secrets Migration Git-crypt to Sealed | 8 secrets migrated, encryption fixes |
| 2026-01-13 | Secrets Management Evaluation | Sealed Secrets vs ESO, memory comparison |
| 2026-01-12 | Predictive Disk Space & NAS Health Alerts | storage-alerts, predict_linear(), SNMP |
| 2026-01-11 | Major Vulnerability Remediation Day | ArgoCD, MetalLB, CSI upgrades |
| 2026-01-07 | Promtail & Synology CSI Upgrades | Promtail 6.17.1, CSI rollback |
| 2026-01-05 | Trivy Operator Deployment | Security scanning, alerts, dashboard |
| 2026-01-05 | Snapshot-Controller Downgrade | CSI snapshots, v8.x issues |
| 2026-01-05 | Loki Memory Optimization | singleBinary, GOMEMLIMIT, Velero CSI |
| 2025-12-28 | Log-Based Alerting + Dashboards | 43 dashboards, 11 Loki alerts |
| 2025-12-28 | Custom Grafana Dashboards | 4 dashboards, 38 panels |
| 2025-12-27 | Velero + AlertManager SMTP | Backup schedules, email alerts |
| 2025-12-27 | External-DNS Deployment | Cloudflare, UniFi, split-horizon |
| 2025-12-27 | Loki + Promtail Hardening | jqPathExpressions, tolerations |
| 2025-12-26 | Loki + Promtail Deploy | Log aggregation stack |
| 2025-12-26 | Calico hostNetwork Issues | CNI routing limitation |
| 2025-12-26 | Monitoring Stack Fixes | node-exporter, Grafana PVC |

See `.claude/notes/sessions/` for full session details.

---

## Session Documentation Workflow

When documenting a new session:

1. **Add to this file** (CURRENT.md) at the top of "Recent Sessions"
2. **If CURRENT.md has >5 sessions**, move the oldest to a new file in `sessions/`:
   - Name format: `YYYY-MM-DD-slugified-title.md`
   - Add one-line entry to "Session Archive Index"
3. **If new gotchas discovered**, update `.claude/notes/REFERENCE.md`
4. **Update "Current State"** section if project state changed

### Session Template
```markdown
### YYYY-MM-DD (Time of Day): Brief Session Title

**Completed Work:**
- Item 1
- Item 2

**Pull Requests:**
- **PR #XXX:** [Status] Description

**Issues Resolved:**
- Problem → Root Cause → Solution

**Files Modified:**
- `path/to/file.yaml` (description)
```
