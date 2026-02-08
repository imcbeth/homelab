# Claude Code - Homelab Current Context

**Last Updated:** 2026-02-08
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

**OPA Gatekeeper:** Enforcing (2026-02-07)
- Helm chart 3.21.1, sync-wave -6
- 2 ArgoCD apps: `gatekeeper` (Helm + ConstraintTemplates) and `gatekeeper-policies` (Constraints)
- 5 ConstraintTemplates, 5 Constraints (deny mode, 0 violations)
- PodMonitor + Grafana dashboard for metrics
- NetworkPolicy configured for gatekeeper-system

**Phase 4 Status:** In Progress
- Storage performance + network utilization dashboards deployed
- SealedSecrets key rotation enabled (30d)
- OPA Gatekeeper in deny mode (0 violations)
- OOM fixes: Grafana sidecars (256Mi), Loki sidecar/canary, Falco redis (700Mi maxmemory)
- ArgoCD MCP RBAC configured (readonly for MCP service account)
- k8s-docs-n37 documentation synced (PR #64 merged)
- Next: Trivy vulnerability dashboard, Ingress hardening, APM dashboard

---

## Recent Sessions

### 2026-02-07 (Evening): ArgoCD MCP RBAC Fix

**Completed Work:**
- Diagnosed ArgoCD MCP returning empty results (JWT valid, but zero RBAC permissions)
- Added readonly RBAC policy for MCP service account in argocd-config.yaml
- Fixed stuck ArgoCD sync (argocd-redis-secret-init hook job blocking)
- Verified all 24 apps visible via MCP after fix

**Pull Requests:**
- **PR #409:** [Merged] fix: add RBAC policy for ArgoCD MCP service account

**Issues Resolved:**
1. **ArgoCD MCP empty results** - Root cause: `mcp` account had `apiKey` capability but no RBAC permissions (empty `policy.csv`). Fix: Added `configs.rbac.policy.csv` with readonly role in Helm values.
2. **ArgoCD sync stuck on hook job** - `argocd-redis-secret-init` blocking. Fix: Patched `status.operationState` to null.

**Files Modified:**
- `manifests/base/argocd/argocd-config.yaml` (RBAC policy added)

---

### 2026-02-07: OOM Fixes, Gatekeeper Deny Mode & Docs Sync

**Completed Work:**
- Fixed 12 Gatekeeper resource-limit violations across multiple apps
- Switched OPA Gatekeeper from dryrun to deny mode (0 violations)
- Fixed OOMKilled containers: Grafana sidecars (256Mi), Loki sidecar/canary, Falco redis-stack
- Configured Falco redis-stack maxmemory (700Mi)
- Synced k8s-docs-n37 documentation (10 files updated)
- Cleaned up stale PVs

**Pull Requests:**
- **PR #405:** [Merged] fix: increase Grafana sidecar and Loki memory limits for OOMKill prevention
- **PR #407:** [Merged] fix: limit Falco redis to 700mb maxmemory
- **PR #408:** [Merged] fix: add missing resource limits for Gatekeeper violations
- **PR #64 (k8s-docs-n37):** [Merged] docs: sync cluster state for February 2026

**Issues Resolved:**
1. **Grafana sidecar OOMKill** - k8s-sidecar watching ConfigMaps across many namespaces needs 256Mi+
2. **Falco redis-stack memory** - Modules (RediSearch, TimeSeries, JSON, Bloom, Gears) consume significant memory; needs `maxmemory` config
3. **Loki canary value path** - `monitoring.selfMonitoring.lokiCanary.resources` is ignored; use top-level `lokiCanary.resources`

**Files Modified:**
- `manifests/base/kube-prometheus-stack/values.yaml` (sidecar resources)
- `manifests/base/loki/values.yaml` (sidecar + canary resources)
- `manifests/base/falco/values.yaml` (redis maxmemory)
- `manifests/base/gatekeeper/constraints/` (dryrun → deny)
- Multiple k8s-docs-n37 files (10 files, 142 insertions)

---

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

---

## Session Archive Index

| Date | Title | Key Topics |
|------|-------|------------|
| 2026-01-30 | Dependency Updates, Docs & Argo Alerts | Renovate PRs, Istio 1.28.3, 8 workflow alerts |
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
