# 2026-01-05 (Early Morning): Loki Memory Optimization + Velero CSI Snapshot Integration

**Completed Work:**
- Loki Memory Limits - Implemented proper memory management for singleBinary mode
- Velero CSI Snapshots - Configured CSI snapshot support for PVC backups
- Snapshot Controller - Deployed snapshot-controller for Kubernetes CSI functionality
- Log-Based Alerting - Temporarily disabled due to ruler/singleBinary compatibility

**Pull Requests:**
- **PR #182:** [Merged] Implement proper Loki memory limits without external caches
- **PR #186:** [Merged] Temporarily disable log-based alerts for Loki memory limits
- **PR #187:** [Merged] Configure Velero to use CSI snapshots only
- **PR #188:** [Merged] Add snapshot-controller to Synology CSI deployment

**Loki Memory Optimization:**

Solution:
1. Ingestion rate limits: 10MB/sec, 20MB burst
2. GOMEMLIMIT: 700MiB (Go runtime memory cap)
3. Memory request: 512Mi (up from 384Mi)
4. Internal cache management (no external memcached)

**Velero CSI Configuration:**
```yaml
configuration:
  features: EnableCSI
  defaultVolumesToFsBackup: false  # Disable Kopia
snapshotsEnabled: true
```

**Key Issues Resolved:**
- Loki distributed mode triggered by cache config in singleBinary - set `replicas: 0` for caches
- Velero CSI + Kopia conflict - use CSI exclusively
- CSI snapshots not being created - deploy snapshot-controller alongside CSI driver

**Current State:**
- Loki memory optimized for singleBinary mode (512Mi request, 768Mi limit)
- Loki running without external cache dependencies
- Velero using CSI snapshots exclusively
- snapshot-controller deployed and processing VolumeSnapshot requests
- Log-based alerting temporarily disabled

**Files Modified:**
- `manifests/base/loki/values.yaml` - Memory limits, ingestion rates, GOMEMLIMIT
- `manifests/base/loki/loki-alerts.yaml.disabled` - Temporarily disabled
- `manifests/base/velero/values.yaml` - CSI snapshot configuration
- `manifests/base/synology-csi/kustomization.yaml` - Added snapshot-controller
