# Claude Code - Homelab Current Context

**Last Updated:** 2026-01-30
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
- Trivy scanning: VulnerabilityReports now generating (NetworkPolicy fixed)
- All Prometheus targets healthy (metrics-server HTTPS scraping fixed)
- Argo Workflows: Grafana dashboard deployed with ServiceMonitor
- Promtail: Using selective labelmap to stay under Loki's 15 label limit
- Blackbox-exporter: Uses hostAliases for internal HTTPS probes (hairpin NAT fix)

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

**Istio Ambient Mesh:** Updated (2026-01-30)
- Upgraded from 1.24.2 → 1.28.3 (PR #308)
- 29 pods across 6 namespaces with mTLS (HBONE protocol)
- Namespaces: default, loki, argo-workflows, localstack, unipoller, trivy-system
- Resource usage: ~38m CPU, ~145Mi memory (istiod + cni + ztunnel)
- Waypoint proxies: Skipped (L4 mTLS sufficient, add later if L7 needed)
- ArgoCD: 22 apps total, all Healthy (3 show OutOfSync - cosmetic ServerSideApply quirk)
- **Gotcha:** Transparent proxy preserves source IPs; NetworkPolicies need HBONE port 15008 from source namespace

**Argo Workflows Alerting:** Complete (2026-01-30)
- 8 PrometheusRule alerts deployed (PR #354)
- Alerts: Failed, Error, ControllerErrors, Stuck, QueueBacklog, NotLeader, Down, HighFailureRate
- All alerts active in Prometheus, currently inactive (healthy state)

**Phase 4 Status:** In Progress
- Argo Workflows alerting complete
- Next: Storage performance dashboard, OPA Gatekeeper, Ingress hardening

---

## Recent Sessions

### 2026-01-30: Dependency Updates, Documentation Sync & Argo Workflows Alerting

**Completed Work:**
- Merged 5 Renovate PRs for dependency updates
- Updated k8s-docs-n37 documentation to match current cluster state
- Created and deployed Argo Workflows AlertManager rules
- Upgraded Istio from 1.24.2 to 1.28.3

**Pull Requests:**
- **PR #278:** [Merged] chore(deps): ArgoCD ecosystem patch (argo-workflows 0.47.1→0.47.2, argocd 9.3.4→9.3.7)
- **PR #279:** [Merged] chore(deps): busybox 1.36→1.37
- **PR #305:** [Merged] chore(deps): UniFi Poller v2.21.0→v2.28.0
- **PR #307:** [Merged] chore(deps): Istio 1.24.2→1.24.6 (patch)
- **PR #308:** [Merged] chore(deps): Istio 1.24→1.28.3 (minor)
- **PR #354:** [Merged] feat: Add Argo Workflows AlertManager rules

**k8s-docs-n37 Updates:**
- New: `docs/applications/argo-workflows.md` - Argo Workflows v0.47.1 documentation
- New: `docs/applications/localstack.md` - LocalStack AWS emulator docs
- Updated: `docs/applications/kube-prometheus-stack.md` - Version 81.2.2, ignoreDifferences config
- Updated: `docs/intro.md` - CNI migration, Service Mesh, Runtime Security sections

**Argo Workflows Alerts Created:**
| Alert | Severity | Description |
|-------|----------|-------------|
| ArgoWorkflowFailed | warning | Workflows ending in Failed state |
| ArgoWorkflowError | critical | Workflows in Error state (system failures) |
| ArgoWorkflowControllerErrors | warning | Controller errors by cause |
| ArgoWorkflowStuck | warning | Workflows running >1 hour |
| ArgoWorkflowQueueBacklog | warning | Queue depth >10 items for 15m |
| ArgoWorkflowControllerNotLeader | critical | Lost leader election |
| ArgoWorkflowControllerDown | critical | Controller metrics absent |
| ArgoWorkflowHighFailureRate | warning | >30% failure rate over 24h |

**Cluster Status:**
- 22 ArgoCD applications, all Healthy
- 3 OutOfSync (istio-cni, istiod, tigera-operator) - cosmetic ServerSideApply quirk
- All Argo Workflows alerts active in Prometheus, currently inactive (healthy)

**Files Created/Modified:**
- `manifests/base/kube-prometheus-stack/argo-workflows-alerts.yaml` (new)
- `manifests/base/kube-prometheus-stack/kustomization.yaml` (added alerts)

---

### 2026-01-29 (Evening): Monitoring Fixes & Network Policy Documentation

**Completed Work:**
- Created Argo Workflows Grafana dashboard with ServiceMonitor
- Fixed metrics-server ServiceMonitor (was showing DOWN in Prometheus)
- Fixed Trivy NetworkPolicy blocking vulnerability scans
- Documented network segmentation strategy in k8s-docs-n37

**Pull Requests:**
- **PR #330:** [Merged] feat: Add Argo Workflows Grafana dashboard and enable ServiceMonitor
- **PR #331:** [Merged] fix: Enable metrics-server HTTPS scraping and Trivy intra-namespace communication
- **PR #332:** docs: Mark network policies documentation as complete
- **PR #60 (k8s-docs-n37):** docs: Update NetworkPolicies documentation with current implementation

**Issues Resolved:**

1. **Metrics-Server ServiceMonitor DOWN**
   - Root cause: Helm chart doesn't support `scheme: https` or `tlsConfig`
   - Manual `servicemonitor.yaml` existed but wasn't applied (ArgoCD `ref:` only source)
   - Fix: Disabled Helm ServiceMonitor, added third ArgoCD source to apply manual manifests

2. **Trivy Dashboard Empty / No VulnerabilityReports**
   - Root cause: NetworkPolicy blocked intra-namespace communication
   - Scan jobs couldn't connect to trivy-server (port 4954)
   - Fix: Added egress/ingress rules for intra-namespace traffic

**Argo Workflows Dashboard Panels:**
- Overview: Total/Running/Succeeded/Failed/Error counts, Controller health
- Trends: Status over time, Operation duration percentiles (p50/p95/p99)
- Controller: Memory, CPU, Goroutines
- Queue: Depth and add rate
- Pods: Workflow pod counts and status table

**Network Policy Documentation (k8s-docs-n37):**
- Updated from 5 to 9 protected namespaces
- Added Istio Ambient mesh patterns (HBONE port 15008)
- Added K8s API dual-egress pattern explanation
- Architecture diagrams and troubleshooting guides

**Files Modified:**
- `manifests/base/argo-workflows/values.yaml` (ServiceMonitor config)
- `manifests/base/grafana/dashboards/argo-workflows-dashboard.yaml` (new)
- `manifests/base/grafana/dashboards/kustomization.yaml`
- `manifests/applications/metrics-server.yaml` (third source)
- `manifests/base/metrics-server/values.yaml` (disable Helm ServiceMonitor)
- `manifests/base/network-policies/trivy-system/network-policy.yaml`

---

### 2026-01-29 (Afternoon): Documentation Updates

**Completed Work:**
- Updated k8s-docs-n37 documentation with recent fixes
- Added hairpin NAT troubleshooting to blackbox-exporter.md
- Added Promtail selective labelmap section to loki.md
- Expanded Istio ArgoCD OutOfSync fix in istio.md
- Extracted reusable patterns as learned skills

**Pull Requests:**
- **PR #59 (k8s-docs-n37):** docs: Add troubleshooting sections for recent fixes

**Learned Skills Extracted:**
- `~/.claude/skills/learned/kubernetes-hairpin-nat-workaround.md`
- `~/.claude/skills/learned/promtail-loki-label-limit.md`

---

### 2026-01-29 (Morning): Blackbox-Exporter Hairpin NAT Fix

**Completed Work:**
- Diagnosed blackbox-exporter failing to probe internal HTTPS endpoints
- Root cause: DNS resolves to external MetalLB IP (10.0.10.10), causing hairpin NAT timeout
- Fix: Added `hostAliases` to resolve internal hostnames to ingress ClusterIP (10.98.168.24)

**Pull Requests:**
- **PR #327:** [Merged] fix: Add hostAliases to blackbox-exporter for hairpin NAT

**Key Learning:**
Pods inside the cluster cannot reach external IPs that route back to the same cluster (hairpin NAT). Solution: Use `hostAliases` to map hostnames directly to internal ClusterIPs.

**Hostnames Fixed:**
- argocd.k8s.n37.ca
- grafana.k8s.n37.ca
- workflows.k8s.n37.ca
- localstack.k8s.n37.ca

**Files Modified:**
- `manifests/base/kube-prometheus-stack/blackbox-exporter-deployment.yaml`

---

### 2026-01-28 (Late Night): Promtail Label Limit Fix

**Completed Work:**
- Fixed promtail errors: "has 17 label names; limit 15"
- Istio pods (ztunnel, istio-cni-node) have 17+ Kubernetes labels
- Initial `labeldrop` approach failed (relabel_configs process original labels)
- Implemented selective `labelmap` to only capture essential labels

**Pull Requests:**
- **PR #324:** [Merged] fix: Drop noisy labels in promtail (didn't work)
- **PR #325:** [Merged] fix: Use selective labelmap in promtail for Loki label limit

**Key Learning:**
Promtail `labeldrop` in relabel_configs doesn't work after `labelmap` because relabel_configs process against the original label set, not transformed labels. Solution: use selective `labelmap` regex to only capture needed labels.

**Selective Labelmap Pattern:**
```yaml
- action: labelmap
  regex: __meta_kubernetes_pod_label_(app|app_kubernetes_io_name|app_kubernetes_io_instance|app_kubernetes_io_component|app_kubernetes_io_part_of|k8s_app|service_name)
```

**Label Count After Fix:**
- Fixed: namespace, pod, container, node (4)
- Mapped: up to 7 essential labels
- Auto: filename, stream (2)
- **Total: max 13 labels** (under 15 limit)

**Files Modified:**
- `manifests/base/promtail/values.yaml`

---

### 2026-01-28 (Evening): Istio ArgoCD Sync Fixes

**Completed Work:**
- Added `ignoreDifferences` to Istio ArgoCD applications for webhook caBundle drift
- Switched from jsonPointers to jqPathExpressions for broader label/annotation matching
- Added RespectIgnoreDifferences sync option
- Cleaned up temporary `istio-1.24.2/` directory

**Pull Requests:**
- **PR #320:** [Merged] docs: Update CURRENT.md with Istio Ambient session
- **PR #321:** [Merged] fix: Add ignoreDifferences for Istio webhook drift
- **PR #322:** [Merged] fix: Improve Istio ignoreDifferences with jqPathExpressions

**ArgoCD Status After Fixes:**
- 18/20 applications Synced and Healthy
- 2 apps (istio-cni, istiod) show OutOfSync but Healthy
- OutOfSync is cosmetic - Istio Helm chart adds operator labels at runtime

**Key Learning:**
Istio's Helm chart dynamically adds labels like `install.operator.istio.io/owning-resource` and `operator.istio.io/component` that cause perpetual drift. Using `jqPathExpressions` with broad label ignores helps but doesn't fully resolve. The apps function correctly despite the OutOfSync status.

**Files Modified:**
- `manifests/applications/istio-base.yaml` (ignoreDifferences)
- `manifests/applications/istio-cni.yaml` (ignoreDifferences + RespectIgnoreDifferences)
- `manifests/applications/istiod.yaml` (ignoreDifferences + RespectIgnoreDifferences)

---

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
