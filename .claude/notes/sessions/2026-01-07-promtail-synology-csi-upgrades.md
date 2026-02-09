# 2026-01-07 (All Day): Vulnerability Remediation - Promtail & Synology CSI Upgrades

**Completed Work:**
- CLAUDE_NOTES.md Maintenance - Archived old sessions to CLAUDE_NOTES_2025.md
- Trivy Documentation - Created comprehensive operational documentation for Trivy Operator
- Promtail Upgrade - Helm chart 6.16.6 → 6.17.1 (app 3.0.0 → 3.5.1)
- Synology CSI Partial Upgrade - Sidecars upgraded, node plugin rolled back
- Grafana Restoration - Fixed iSCSI mount issue after CSI upgrade

**Pull Requests:**
- **PR #198:** [Merged] docs: Archive old CLAUDE_NOTES sessions
- **PR #199:** [Merged] feat: Upgrade Promtail to 6.17.1
- **PR #200:** [Merged] feat: Upgrade Synology CSI sidecars
- **PR #201:** [Merged] fix: Rollback synology-csi node to v1.2.0

**Vulnerability Remediation Results:**

**Promtail (100% Success):**
- CRITICAL: 7 → 0
- HIGH: 34 → 4 (88% reduction)
- Deployment: Rolling update, zero downtime

**Synology CSI (Partial Success with Rollback):**
- Upgraded: csi-attacher v4.0.0 → v4.10.0, csi-node-driver-registrar v2.3.0 → v2.15.0, csi-snapshotter v4.2.1 → v7.0.2
- Rolled Back: synology-csi (node) v1.2.1 → v1.2.0 (iscsiadm regression)
- Sidecar containers now have 0 CRITICAL vulnerabilities

**Issue: Synology CSI v1.2.1 iSCSI Mount Failure**

**Symptoms:**
```
MountVolume.SetUp failed: env: can't execute 'iscsiadm': No such file or directory
```

**Root Cause:**
synology-csi v1.2.1 node plugin introduced regression where container cannot access `iscsiadm` binary from host filesystem.

**Solution:**
Rolled back node.yml: synology-csi v1.2.1 → v1.2.0

**Current State:**
- Promtail: Fully upgraded, 0 CRITICAL vulnerabilities
- Synology CSI: Partial upgrade (sidecars upgraded, node plugin on v1.2.0)
- All PVCs operational (Prometheus 50Gi, Grafana 5Gi, Loki 20Gi, Trivy 5Gi)
- Cluster CRITICAL reduced from 43 → 28 (35% improvement)

**Files Modified:**
- `manifests/applications/promtail.yaml` - Updated chart version 6.16.6 → 6.17.1
- `manifests/base/synology-csi/controller.yml` - Updated csi-attacher v4.10.0
- `manifests/base/synology-csi/node.yml` - Updated csi-node-driver-registrar v2.15.0, synology-csi v1.2.0 (rollback)
