# Claude Code - Homelab Current Context

**Last Updated:** 2026-01-21
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

**Phase 3 Priorities (from TODO.md):**
- Network Policies
- Argo Workflows
- Renovate (automated dependency updates)

---

## Recent Sessions

### 2026-01-14 (Evening): Sealed Secrets Ops, Key Backup, B2 Restore, Monitoring & ArgoCD Backup

**Completed Work:**
- Created SEALED-SECRETS.md - Comprehensive operations guide for secret rotation and key management
- Updated secrets/README.md - Added reference to new operations guide
- Updated k8s-docs-n37 secrets-management.md - Added rotation procedures to documentation site
- Backed up sealing key - Stored on Synology NAS
- Tested Velero restore from Backblaze B2 - Full backup/restore cycle validated
- Verified AlertManager email delivery - 121 emails sent, 0 failures
- Checked Trivy vulnerability posture - 10 CRITICAL (blocked on upstream)
- Added ArgoCD daily backup schedule - Velero schedule at 1:30 AM daily
- Updated TODO.md - Marked all High Priority backup tasks complete

**Pull Requests:**
- **PR #240:** [Merged] docs: Add Sealed Secrets operations guide with rotation procedures (homelab)
- **PR #53:** [Merged] docs: Add comprehensive secret rotation procedures (k8s-docs-n37)
- **PR #241-245:** [Merged] Various documentation updates and ArgoCD backup automation

**Key Details:**
- Sealing key backup location: `/Volumes/homes/imcbeth/Documents/sealed-secrets-key-backup-20260114.yaml`
- Velero B2 restore validated with unipoller namespace test
- ArgoCD backup schedule: `velero-daily-argocd` at 1:30 AM, 30-day retention

**Files Modified:**
- `secrets/SEALED-SECRETS.md` (new - ~450 lines)
- `secrets/README.md` (updated)
- `manifests/base/velero/values.yaml` (added daily-argocd schedule)
- `TODO.md` (marked backup tasks complete)

---

### 2026-01-14 (Afternoon): Documentation Update - Sealed Secrets

**Completed Work:**
- Created secrets-management.md - Comprehensive Sealed Secrets documentation
- Added Security section to docs - New category in sidebars
- Updated application docs - cert-manager, external-dns, unipoller, synology-csi
- Updated intro.md - Added January 2026 secrets migration info

**Pull Requests:**
- **PR #237:** [Merged] docs: Update CLAUDE_NOTES with secrets migration completion
- **PR #51:** [Merged] docs: Add Sealed Secrets documentation (k8s-docs-n37)

**Files Modified:**
- `k8s-docs-n37/docs/security/secrets-management.md` (new)
- `k8s-docs-n37/docs/applications/*.md` (updated references)
- `k8s-docs-n37/sidebars.ts` (added Security category)

---

### 2026-01-14 (Morning): Secrets Migration Completion and Cleanup

**Completed Work:**
- Removed External Secrets Operator - Evaluation complete, Sealed Secrets chosen
- Cleaned up secrets directory - Removed 15 obsolete git-crypt files
- Updated secrets/README.md - Documented bootstrap secrets and migration history
- Updated TODO.md - Marked Secrets Management complete, updated sync wave order
- Cleaned up local git branches - Deleted 107 local branches, pruned 85 stale remotes

**Pull Requests:**
- **PR #233-236:** [Merged] ESO removal, secrets cleanup, TODO update

**Secrets Management - Final Architecture:**
```
Sealed Secrets Controller (kube-system)
  └─ Decrypts SealedSecret CRDs at runtime

SealedSecrets in Git (8 total):
  ├─ manifests/base/unipoller/unipoller-sealed.yaml
  ├─ manifests/base/external-dns/cloudflare-sealed.yaml
  ├─ manifests/base/external-dns/unifi-sealed.yaml
  ├─ manifests/base/kube-prometheus-stack/alertmanager-smtp-sealed.yaml
  ├─ manifests/base/kube-prometheus-stack/snmp-exporter-sealed.yaml
  ├─ manifests/base/cert-manager/cloudflare-sealed.yaml
  ├─ manifests/base/synology-csi/client-info-sealed.yaml
  └─ manifests/base/pihole/pihole-web-sealed.yaml

Bootstrap Secret (manual apply):
  └─ secrets/argocd-git-access.yaml

Helm-Managed Secrets (auto-generated):
  └─ kube-prometheus-stack-grafana
```

---

### 2026-01-14 (Early Morning): Secrets Migration from Git-crypt to Sealed Secrets

**Completed Work:**
- Migrated 8 secrets to SealedSecrets (GitOps-compatible)
- Fixed application file encryption - Renamed seal-controller.yaml and eso.yaml
- Updated pre-commit config - Added exclusions for `*-sealed.yaml` files
- Removed Grafana sealed secret - Managed by Helm chart, caused conflicts

**Pull Requests:**
- **PR #224-232:** [Merged] Secret migrations and fixes

**Secrets Migrated:**
| Secret Name | Namespace | Application |
|-------------|-----------|-------------|
| unipoller-secret | unipoller | UniPoller UniFi metrics |
| cloudflare-api-token | external-dns | External DNS Cloudflare |
| unifi-credentials | external-dns | External DNS UniFi webhook |
| alertmanager-smtp-credentials | default | Alertmanager email alerts |
| snmp-exporter-credentials | default | Synology NAS monitoring |
| cloudflare-api-token-secret | cert-manager | DNS01 certificate challenges |
| client-info-secret | synology-csi | Synology CSI driver |
| pihole-web-password | pihole | Pi-hole web interface |

**Issues Resolved:**
1. Git-crypt encrypting non-secret files → Rename to avoid `*secret*` pattern
2. SealedSecret encryption corruption → Use `kubeseal ... > file.yaml`, not copy-paste
3. Grafana secret conflict → Helm chart manages it, don't use SealedSecret

---

### 2026-01-13 (Early Morning): Secrets Management Evaluation - Sealed Secrets vs External Secrets

**Completed Work:**
- Sealed Secrets Deployed - bitnami-labs/sealed-secrets v2.16.2 in kube-system
- External Secrets Operator Deployed - external-secrets v0.10.7 with Kubernetes backend
- ClusterSecretStore Configured - Kubernetes secrets backend for ESO
- Both Solutions Tested - Successfully created and synced test secrets

**Pull Requests:**
- **PR #219-223:** [Merged] Evaluation deployment and fixes

**Evaluation Results:**

| Criteria | Sealed Secrets | External Secrets Operator |
|----------|---------------|---------------------------|
| **Pods** | 1 | 3 |
| **Memory Usage** | 9Mi | 69Mi total |
| **GitOps Native** | Yes | Yes |
| **Secret Rotation** | Manual | Automatic |
| **Dependencies** | None | Requires backend |

**Recommendation:** Sealed Secrets for homelab (7x less memory, simpler architecture)

**Issues Resolved:**
1. Empty kustomization.yaml fails ArgoCD → Add `resources: []`
2. Git-crypt encrypting non-secret files → Avoid "secret" in filenames
3. fsGroup in container securityContext → Use `podSecurityContext` for fsGroup

---

## Session Archive Index

| Date | Title | Key Topics |
|------|-------|------------|
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
