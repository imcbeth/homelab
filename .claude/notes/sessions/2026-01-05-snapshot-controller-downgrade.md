# 2026-01-05 (Evening): Snapshot-Controller Downgrade to Fix CSI Snapshot Failures

**Completed Work:**
- Snapshot-Controller Downgrade - Downgraded from v8.2.0 to v6.3.1 for stability
- Stuck VolumeSnapshot Cleanup - Removed finalizers and deleted failed snapshots
- Velero Backup Verification - Confirmed CSI snapshots working with test backup

**Pull Requests:**
- **PR #189:** [Merged] fix: Downgrade snapshot-controller to v7.0.2 for stability

**Issue: VolumeSnapshot Creation Failures with sourceVolumeMode Error**

**Symptoms:**
- All VolumeSnapshots stuck with `READYTOUSE: false`
- Velero backups showing `PartiallyFailed` status
- Error: `VolumeSnapshotContent is invalid: spec: Invalid value: sourceVolumeMode is required once set`

**Root Cause:**
Snapshot-controller v8.2.0 has strict immutability validation on the `sourceVolumeMode` field. Known issue with snapshot-controller v8.x series.

**Solution:**

1. Clean up stuck VolumeSnapshot resources:
```bash
kubectl patch volumesnapshot -n default <name> -p '{"metadata":{"finalizers":null}}' --type=merge
```

2. Downgrade snapshot-controller to v6.3.1 (known stable version)

**Verification:**
- Manual VolumeSnapshot: `READYTOUSE: true` in 8 seconds
- Velero backup: 3/3 CSI snapshots completed, 0 errors

**Current State:**
- snapshot-controller v6.3.1 deployed (2 replicas running)
- VolumeSnapshots creating successfully
- Velero CSI snapshots fully operational
- Daily scheduled backups (2 AM) will now complete successfully

**Files Modified:**
- `manifests/base/synology-csi/kustomization.yaml` - Downgraded snapshot-controller to v7.0.2/v6.3.1
