### 2026-04-17: Cluster Health + Renovate Batch

**Completed Work:**

**iSCSI Recovery (3 volumes):**
- `trivy-server-0` CrashLoopBackOff (47d): deleted stuck PVC `pvc-72cd5620` (iSCSI on node03, pod on node01) → new LUN `pvc-e11eb24a` provisioned → 1/1 Running
- `kube-prometheus-stack-grafana` Init:0/1 (13h): deleted dead-session PVC `pvc-ad5666f9` + force-removed finalizer → new PVC `pvc-fe45711b` → 3/3 Running
- `prometheus-0` Init:0/1: iSCSI REOPEN loop fixed by NAS target disable/re-enable + `kubectl delete volumeattachment csi-221f...` → 2/2 Running, all data preserved

**Renovate Batch (8 PRs merged):**
- #539: sealed-secrets 2.18.4→2.18.5 (patch)
- #538: falco 8.0.1→8.0.2 (patch)
- #533: unifi-poller v2.38.0→v2.39.0 (patch)
- #535: vpa 4.10.2→4.11.0 (minor)
- #534: argo-cd 9.4.17→9.4.18 + argo-workflows 1.0.6→1.0.10
- #541 (manual, superseded #540): argo-cd 9.4.18→9.5.2
- #537: prometheus image v3.10.0→v3.11.2
- #536: kube-prometheus-stack 82.15.1→82.18.0 + alloy 1.6.2→1.7.0
- **SKIPPED #531 & #532**: velero binary v1.18.0 + chart v12 — still blocked (backup-queue "Queued" phase issue)

**Key Learnings:**
- iSCSI REOPEN fix: NAS target disable/re-enable clears stale session state on NAS. `kubectl delete volumeattachment` forces CSI to do clean detach/reattach cycle from node side.
- `scsi disk sda State: transport-offline` = iSCSI session exists but I/O fails → block device present but ENXIO on read/write.
- Renovate PRs that touch same file conflict after sequential merges — create manual fix PR.
