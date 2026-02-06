# Claude Code - Homelab Current Context

**Last Updated:** 2026-02-05
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
- Argo Workflows v3.7.8 (Helm chart 0.47.3) at sync-wave -8
- B2 artifact storage working (PRs #287-289 fixed credentials)
- NetworkPolicy enabled (PR #291 fixed K8s API egress)
- UI accessible at https://workflows.k8s.n37.ca (PR #293)

**ArgoCD:** 24 apps (22 + gatekeeper + gatekeeper-policies) (2026-02-06)
- ServerSideApply drift fully resolved for istio-ztunnel and tigera-operator
- Server-Side Apply enabled on ArgoCD itself (#376)

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
- ArgoCD: 22 apps total, all Synced and Healthy (ServerSideApply drift fully resolved)
- **Gotcha:** Transparent proxy preserves source IPs; NetworkPolicies need HBONE port 15008 from source namespace

**Argo Workflows Alerting:** Complete (2026-01-30)
- 8 PrometheusRule alerts deployed (PR #354)
- Alerts: Failed, Error, ControllerErrors, Stuck, QueueBacklog, NotLeader, Down, HighFailureRate
- All alerts active in Prometheus, currently inactive (healthy state)

**Calico APIServer:** Deployed (2026-02-05)
- APIServer CR enables v3 API for operator IPPool management
- Fixed IPPool ownership error (RestoreV3Metadata annotation fix)

**OPA Gatekeeper:** Deployed (2026-02-06)
- Helm chart 3.21.1, sync-wave -6
- 2 ArgoCD apps: `gatekeeper` (Helm + ConstraintTemplates) and `gatekeeper-policies` (Constraints)
- 5 ConstraintTemplates, 5 Constraints (all dryrun mode)
- Initial audit: 156 resource-limit, 20 allowed-repo, 15 label violations
- NetworkPolicy configured for gatekeeper-system

**Phase 4 Status:** In Progress
- Storage performance + network utilization dashboards deployed
- SealedSecrets key rotation enabled (30d)
- OPA Gatekeeper deployed (dryrun mode)
- Next: Switch Gatekeeper to deny mode, Ingress hardening, APM dashboard

---

## Recent Sessions

### 2026-02-06: OPA Gatekeeper Deployment

**Completed Work:**
- Deployed OPA Gatekeeper v3.21.1 for Kubernetes admission control
- Created 5 ConstraintTemplates (Rego): resource limits, allowed repos, required labels, block NodePort, container limits
- Created 5 Constraints in dryrun mode for audit-first rollout
- Split into 2 ArgoCD Applications (gatekeeper + gatekeeper-policies) to handle CRD ordering
- Created NetworkPolicy for gatekeeper-system namespace
- Created k8s-docs-n37 application guide and updated runtime-security docs
- Updated sidebar navigation in k8s-docs-n37

**Pull Requests:**
- **PR #389:** [Merged] feat: deploy OPA Gatekeeper for admission control
- **PR #390:** [Merged] fix: remove duplicate source path from gatekeeper Application
- **PR #391:** [Merged] fix: add sync waves for gatekeeper CRD ordering
- **PR #392:** [Merged] fix: split gatekeeper constraints into separate ArgoCD Application

**Issues Resolved:**

1. **Duplicate resources in ArgoCD multi-source app**
   - Root cause: Source 2 had both `path` and `ref`, causing it to render manifests AND serve as a values ref
   - Fix: Removed `path` from the ref source

2. **ConstraintTemplate/Constraint CRD ordering**
   - Root cause: ArgoCD validates ALL resources before syncing ANY; constraint CRDs only exist after Gatekeeper processes ConstraintTemplates
   - Fix: Split into two Applications - gatekeeper (wave -6) for Helm+Templates, gatekeeper-policies (wave -5) for Constraints with generous retries

**Audit Results (dryrun):**
- 156 resource-limit violations
- 20 allowed-repo violations
- 15 require-label violations
- 0 block-nodeport violations
- 0 container-limit violations

**Files Created/Modified:**
- `manifests/applications/gatekeeper.yaml` (new)
- `manifests/applications/gatekeeper-policies.yaml` (new)
- `manifests/base/gatekeeper/` (new directory - values, kustomization, constraint-templates, constraints)
- `manifests/base/network-policies/gatekeeper-system/network-policy.yaml` (new)
- `manifests/base/network-policies/kustomization.yaml` (added gatekeeper-system)
- `TODO.md` (marked OPA Gatekeeper items done)

---

### 2026-02-05 (Evening): Storage Dashboard, Tigera Fix, Network Dashboard & Cleanup

**Completed Work:**
- Created storage performance Grafana dashboard (5 sections: PVC overview/trends, iSCSI LUN performance, node disk I/O, Synology RAID health)
- Diagnosed and fixed tigera-operator IPPool ownership error (root cause: `RestoreV3Metadata()` wiped `managed-by` label from in-memory IPPool via `projectcalico.org/metadata` annotation)
- Deployed Calico APIServer CR to enable v3 API for operator IPPool reconciliation
- Created network utilization Grafana dashboard (5 sections: WAN, switch ports, node network, Synology NAS, WiFi clients)
- Enabled SealedSecrets key rotation (30-day period)
- Validated all dashboard panels have live Prometheus data
- Updated TODO.md with completed items

**Pull Requests:**
- **PR #383:** [Merged] feat: add storage performance Grafana dashboard
- **PR #385:** [Merged] fix: deploy Calico APIServer and fix IPPool ownership error
- **PR (pending):** feat: add network utilization dashboard, enable SealedSecrets key rotation

**Issues Resolved:**

1. **tigera-operator "Cannot update an IP pool not owned by the operator"**
   - Root cause: `RestoreV3Metadata()` in the operator reads `projectcalico.org/metadata` annotation and calls `SetLabels()` with stored labels. The annotation had no labels stored, so it wiped the `managed-by: tigera-operator` label from the in-memory object before the ownership check ran.
   - Fix: Patched annotation to include the `managed-by` label; deployed Calico APIServer for v3 API access.
   - **Key Learning:** The `projectcalico.org/metadata` annotation on Calico CRDs stores v3 metadata including labels. If this annotation lacks labels, `RestoreV3Metadata()` will wipe all labels from the object in-memory.

2. **tigera-operator "Unable to modify IP pools while Calico API server is unavailable"**
   - Root cause: No Calico APIServer CR deployed; operator can't use v3 API for pool reconciliation.
   - Fix: Created `apiserver.yaml` with `APIServer` CR (`spec: {}`)

**Files Created/Modified:**
- `manifests/base/grafana/dashboards/storage-performance-dashboard.yaml` (new)
- `manifests/base/grafana/dashboards/network-utilization-dashboard.yaml` (new)
- `manifests/base/grafana/dashboards/kustomization.yaml` (added both dashboards)
- `manifests/base/tigera-operator/apiserver.yaml` (new)
- `manifests/applications/tigera-operator.yaml` (APIServer ignoreDifferences)
- `manifests/base/sealed-secrets/values.yaml` (key rotation enabled)
- `TODO.md` (marked completed items)

---

### 2026-02-05: ArgoCD ServerSideApply OutOfSync Fixes

**Completed Work:**
- Fixed istio-ztunnel perpetual OutOfSync caused by ServerSideApply defaulting
- Fixed tigera-operator OutOfSync caused by operator-populated defaults on Installation CR
- All 22 ArgoCD applications now Synced and Healthy (first time with full clean board)

**Pull Requests:**
- **PR #379:** [Merged] fix: add ignoreDifferences for istio-ztunnel DaemonSet drift
- **PR #380:** [Merged] fix: broaden ignoreDifferences for ztunnel K8s-defaulted fields
- **PR #381:** [Merged] fix: add missing ignoreDifferences for tigera-operator Installation CR

**Issues Resolved:**

1. **istio-ztunnel OutOfSync**
   - Root cause: ServerSideApply causes Kubernetes to populate default values (imagePullPolicy, revisionHistoryLimit, readinessProbe defaults, dnsPolicy, restartPolicy, schedulerName, terminationMessage settings, fieldRef.apiVersion, projected/configMap defaultMode, securityContext) that aren't in the Helm chart template
   - Fix: Added comprehensive `ignoreDifferences` with `jqPathExpressions` covering all defaulted fields + `RespectIgnoreDifferences=true`
   - Note: Initial PR #379 with just label/annotation ignores was insufficient; PR #380 added the remaining K8s-defaulted fields

2. **tigera-operator OutOfSync**
   - Root cause: Tigera operator populates defaults on Installation CR at runtime (finalizers, ipPool defaults: allowedUses, assignmentMode, disableBGPExport, disableNewAllocations, plus cni, logging, nodeUpdateStrategy, etc.)
   - Fix: Added `metadata/finalizers` to jsonPointers and ipPool defaults to `jqPathExpressions`
   - Note: Existing ignoreDifferences already covered most fields; only finalizers and ipPool defaults were missing

**Key Learning:**
- `ignoreDifferences` with label/annotation ignores alone is NOT sufficient for ServerSideApply DaemonSet drift
- Must enumerate ALL Kubernetes-defaulted fields in `jqPathExpressions`
- Application manifests in `manifests/applications/` are NOT auto-deployed by ArgoCD self-management; they require `kubectl apply` to update the Application spec in-cluster
- Always test `ignoreDifferences` changes by applying directly before creating PRs

**Cluster Status:**
- 22/22 ArgoCD applications Synced and Healthy
- All Renovate dependency updates flowing cleanly (15+ PRs merged since last session)

**Files Modified:**
- `manifests/applications/istiod.yaml` (istio-ztunnel ignoreDifferences + RespectIgnoreDifferences)
- `manifests/applications/tigera-operator.yaml` (Installation CR ignoreDifferences)

---

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
1. **Metrics-Server ServiceMonitor DOWN** - Helm chart doesn't support `scheme: https`; added third ArgoCD source for manual manifests
2. **Trivy Dashboard Empty** - NetworkPolicy blocked intra-namespace communication; added egress/ingress rules

**Files Modified:**
- `manifests/base/argo-workflows/values.yaml` (ServiceMonitor config)
- `manifests/base/grafana/dashboards/argo-workflows-dashboard.yaml` (new)
- `manifests/applications/metrics-server.yaml` (third source)
- `manifests/base/network-policies/trivy-system/network-policy.yaml`

---

### 2026-01-29 (Morning/Afternoon): Blackbox-Exporter Fix & Documentation

**Completed Work:**
- Fixed blackbox-exporter hairpin NAT issue with hostAliases
- Updated k8s-docs-n37 documentation with recent fixes
- Extracted reusable patterns as learned skills

**Pull Requests:**
- **PR #327:** [Merged] fix: Add hostAliases to blackbox-exporter for hairpin NAT
- **PR #59 (k8s-docs-n37):** docs: Add troubleshooting sections for recent fixes

**Files Modified:**
- `manifests/base/kube-prometheus-stack/blackbox-exporter-deployment.yaml`

---

### 2026-01-28: Istio Ambient Mesh Fixes (Labels, Sync, NetworkPolicies)

**Completed Work:**
- Fixed Promtail label limit (selective labelmap for Loki 15-label max)
- Added ignoreDifferences for Istio ArgoCD webhook/label drift
- Fixed NetworkPolicies for Istio Ambient transparent proxy (HBONE port 15008)
- 29 pods with mTLS across 6 namespaces

**Pull Requests:**
- **PR #315-319:** [Merged] Istio Ambient NetworkPolicy fixes
- **PR #320-322:** [Merged] Istio ArgoCD sync fixes
- **PR #324-325:** [Merged] Promtail label limit fixes

**Files Modified:**
- `manifests/base/promtail/values.yaml`
- `manifests/applications/istio-base.yaml`, `istio-cni.yaml`, `istiod.yaml`
- `manifests/base/network-policies/{loki,localstack,argo-workflows,unipoller,trivy-system}/network-policy.yaml`

---

## Session Archive Index

| Date | Title | Key Topics |
|------|-------|------------|
| 2026-01-29 | Monitoring Fixes & Docs | Metrics-server, Trivy, hairpin NAT, learned skills |
| 2026-01-28 | Istio ArgoCD Sync & Labels | ignoreDifferences, Promtail labelmap, HBONE NetworkPolicies |
| 2026-01-25 | External-DNS, Grafana & Promtail | Domain-filter fix, fsGroup race, K8s API egress |
| 2026-01-24 | Argo Workflows & Network Policies | Deployment, B2 artifacts, ingress, 5 namespace policies |
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
