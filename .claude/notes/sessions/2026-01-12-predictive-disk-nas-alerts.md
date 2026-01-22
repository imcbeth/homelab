# 2026-01-12 (Evening): Predictive Disk Space & NAS Health Alerts

**Completed Work:**
- Storage Alerts PrometheusRule - Created 13 new alerts for proactive storage monitoring
- Predictive Alerting - Using `predict_linear()` to warn before disks fill up
- Synology NAS Health Monitoring - Disk failures, RAID degradation, temperature alerts via SNMP

**Pull Requests:**
- **PR #217:** [Merged] feat: Add predictive disk space and NAS health alerts

**New Alerts Deployed:**

| Category | Alert Name | Severity | Condition |
|----------|------------|----------|-----------|
| **Node Filesystem** | NodeFilesystemSpaceLow | warning | <20% free |
| | NodeFilesystemSpaceCritical | critical | <10% free |
| | NodeFilesystemSpacePredicted | warning | Predict full in 24h |
| | NodeFilesystemInodesLow | warning | <20% free inodes |
| **Persistent Volumes** | PersistentVolumeSpaceLow | warning | <20% free |
| | PersistentVolumeSpaceCritical | critical | <10% free |
| | PersistentVolumeSpacePredicted | warning | Predict full in 4h |
| **Synology NAS** | SynologyDiskStatusAbnormal | critical | Disk status != Normal |
| | SynologyDiskTemperatureHigh | warning | >50°C |
| | SynologyDiskTemperatureCritical | critical | >60°C |
| | SynologyRAIDDegraded | critical | RAID not normal |
| | SynologyVolumeSpaceLow | warning | <20% free |
| | SynologyVolumeSpaceCritical | critical | <10% free |

**Technical Details:**

Predictive Alert Formula:
```promql
predict_linear(node_filesystem_avail_bytes{...}[6h], 24*3600) < 0
```

Synology SNMP Metrics:
- `diskStatus{job="snmp-synology"}` - Disk health (1=Normal, 5=Crashed)
- `diskTemperature{job="snmp-synology"}` - Disk temperature in Celsius
- `raidStatus{job="snmp-synology"}` - RAID status (1=Normal)

**Files Modified:**
- `manifests/base/kube-prometheus-stack/storage-alerts.yaml` (new - 13 alerts)
- `manifests/base/kube-prometheus-stack/kustomization.yaml` (added storage-alerts.yaml)
