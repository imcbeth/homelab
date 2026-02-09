# 2026-01-23: Renovate PR Merge & Velero v1.17 Breaking Change Fix

**Context:** Reviewed and merged Renovate dependency update PRs, fixed Velero CrashLoopBackOff after chart upgrade.

## Completed Work

- Reviewed and merged 20 Renovate PRs for automated dependency updates
- Fixed Velero CrashLoopBackOff after v11.3.2 chart upgrade
- Fixed ArgoCD apps not syncing new chart versions from git
- All 14 ArgoCD applications now Synced and Healthy

## Pull Requests

- **PR #261-265:** [Merged] Grouped minor updates (ArgoCD, monitoring, networking, security, backup)
- **PR #270:** [Merged] kube-prometheus-stack major update to v81.2.2
- **PR #271:** [Merged] Velero major update to v11.3.2
- **PR #254-260, #266-269:** [Merged] Docker image updates

## Issues Resolved

1. **Velero CrashLoopBackOff** - Error: `unknown flag: --keep-latest-maintenance-jobs`
   - Root cause: Velero v1.17 removed this CLI flag (deprecated since v1.14)
   - Fix: ArgoCD wasn't syncing new chart version; recreating the Application forced correct sync
   - New approach: Uses `--repo-maintenance-job-configmap` instead of CLI flag

2. **ArgoCD not syncing chart versions** - Apps showed old targetRevision despite git updates
   - Fix: Delete and recreate ArgoCD Application to force sync from git
   - Affected: velero, kube-prometheus-stack, sealed-secrets

## Chart Version Updates

| Chart | Old Version | New Version |
|-------|-------------|-------------|
| velero | 8.2.0 | 11.3.2 |
| kube-prometheus-stack | 80.6.0 | 81.2.2 |
| argocd | 7.8.2 | 7.8.7 |
| loki | 6.27.0 | 6.28.0 |
| promtail | 6.17.1 | 6.17.2 |
| sealed-secrets | 2.17.1 | 2.17.2 |
| trivy-operator | 0.28.1 | 0.28.2 |

## Final Cluster Status

- 14/14 applications Synced and Healthy
- Velero v1.17.2 operational with B2 backups
- All scheduled backups running successfully
