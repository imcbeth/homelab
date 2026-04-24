# 2025-12-27/28 (Overnight): Velero Deployment and AlertManager SMTP Email Notifications

**Completed Work:**
- Deployed Velero v1.15.0 with Kopia file-level backup support
- Configured daily PVC backups (Prometheus, Loki, Grafana, Pi-hole)
- Configured weekly cluster resource backups
- Created 7 Velero backup monitoring PrometheusRule alerts
- Configured AlertManager SMTP email notifications (Gmail, critical-only)
- Tested end-to-end email delivery successfully

**Pull Requests:**
- **PR #149:** [Merged] feat: Deploy Velero with Kopia file-level backup
- **PR #150:** [Merged] feat: Add Velero backup monitoring alerts
- **PR #152:** [Merged] fix: Create kustomization.yaml to explicitly list resources
- **PR #155:** [Merged] fix: Use smtp_auth_username instead of smtp_auth_username_file

**Backup Schedules:**
- **daily-critical-pvcs:** 2 AM daily, 30-day retention, ~80Gi
- **weekly-cluster-resources:** 3 AM Sunday, 90-day retention, ~100Mi

**Velero Backup Monitoring Alerts (7 alerts):**
- VeleroBackupFailed (critical)
- VeleroBackupDelayed (critical)
- VeleroBackupStorageLocationUnavailable (critical)
- VeleroBackupMetricAbsent (critical)
- VeleroBackupDurationHigh (warning)
- VeleroVolumeSnapshotLocationUnavailable (warning)
- VeleroPartialBackupFailure (warning)

**Key Issues Resolved:**
1. **values.yaml treated as K8s manifest** → Create kustomization.yaml with explicit resource list
2. **Git-crypt encrypted secrets in ArgoCD** → Exclude from kustomization, apply manually
3. **Base64 control characters** → Use `echo -n` when encoding
4. **AlertManager smtp_auth_username_file not supported** → Use plain string for username
5. **PrometheusRule not picked up** → Add `release: kube-prometheus-stack` label

**Files Modified:**
- `manifests/base/velero/values.yaml`
- `manifests/applications/velero.yaml`
- `manifests/base/kube-prometheus-stack/velero-alerts.yaml`
- `manifests/base/kube-prometheus-stack/values.yaml` (AlertManager SMTP)
- `manifests/base/kube-prometheus-stack/kustomization.yaml`
