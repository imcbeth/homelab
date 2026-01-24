# Claude Code - Homelab Current Context

**Last Updated:** 2026-01-24
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

**Network Policies:** Partially Complete (5 namespaces)
- localstack, unipoller, loki, trivy-system, velero isolated
- ArgoCD Application at sync-wave -40
- Remaining: cert-manager, external-dns, metallb-system

**Phase 3 Priorities (from TODO.md):**
- Argo Workflows
- Service mesh evaluation

---

## Recent Sessions

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

### 2026-01-23 (Evening): Renovate PR Merge & Velero v1.17 Breaking Change Fix

**Completed Work:**
- Reviewed and merged 20 Renovate PRs for automated dependency updates
- Fixed Velero CrashLoopBackOff after v11.3.2 chart upgrade
- Fixed ArgoCD apps not syncing new chart versions from git
- All 14 ArgoCD applications now Synced and Healthy

**Pull Requests:**
- **PR #261-265:** [Merged] Grouped minor updates (ArgoCD, monitoring, networking, security, backup)
- **PR #270:** [Merged] kube-prometheus-stack major update to v81.2.2
- **PR #271:** [Merged] Velero major update to v11.3.2
- **PR #254-260, #266-269:** [Merged] Docker image updates

**Issues Resolved:**
1. **Velero CrashLoopBackOff** - Error: `unknown flag: --keep-latest-maintenance-jobs`
   - Root cause: Velero v1.17 removed this CLI flag (deprecated since v1.14)
   - Fix: ArgoCD wasn't syncing new chart version; recreating the Application forced correct sync
   - New approach: Uses `--repo-maintenance-job-configmap` instead of CLI flag

2. **ArgoCD not syncing chart versions** - Apps showed old targetRevision despite git updates
   - Fix: Delete and recreate ArgoCD Application to force sync from git
   - Affected: velero, kube-prometheus-stack, sealed-secrets

**Chart Version Updates:**
| Chart | Old Version | New Version |
|-------|-------------|-------------|
| velero | 8.2.0 | 11.3.2 |
| kube-prometheus-stack | 80.6.0 | 81.2.2 |
| argocd | 7.8.2 | 7.8.7 |
| loki | 6.27.0 | 6.28.0 |
| promtail | 6.17.1 | 6.17.2 |
| sealed-secrets | 2.17.1 | 2.17.2 |
| trivy-operator | 0.28.1 | 0.28.2 |

**Final Cluster Status:**
- 14/14 applications Synced and Healthy
- Velero v1.17.2 operational with B2 backups
- All scheduled backups running successfully

---

### 2026-01-21 (Evening): Restructure CLAUDE_NOTES.md for Efficient Context

**Completed Work:**
- Restructured CLAUDE_NOTES.md into modular `.claude/notes/` system
- Created CURRENT.md (242 lines) - last 5 sessions + current state
- Created REFERENCE.md (164 lines) - stable gotchas, patterns, architecture
- Created 14 individual session files in `sessions/` for historical lookup
- Updated `/catch-up` skill to use new structure
- Moved CLAUDE_NOTES_2025.md to sessions/ARCHIVE-2025.md
- Deleted monolithic CLAUDE_NOTES.md (3,259 lines)

**Pull Requests:**
- **PR #247:** [Merged] refactor: Restructure CLAUDE_NOTES.md for efficient session context

**Problem Solved:**
CLAUDE_NOTES.md grew to 3,259 lines (~40K tokens) - exceeding Claude's 25K token read limit. The `/catch-up` skill could no longer read the full file.

**New Structure:**
```
.claude/notes/
├── CURRENT.md       # 242 lines - always readable
├── REFERENCE.md     # 164 lines - stable patterns/gotchas
└── sessions/        # 15 archived session files (grep-able)
```

**Benefits:**
- 93% reduction in primary context file
- Always-readable current context
- Searchable history via grep
- Sustainable growth through natural archiving

**Files Modified:**
- `.claude/notes/CURRENT.md` (new)
- `.claude/notes/REFERENCE.md` (new)
- `.claude/notes/sessions/*.md` (14 new files)
- `.claude/skills/catch-up/SKILL.md` (updated)
- `CLAUDE_NOTES.md` (deleted)

---

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

## Session Archive Index

| Date | Title | Key Topics |
|------|-------|------------|
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
