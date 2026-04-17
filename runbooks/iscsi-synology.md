# Troubleshooting: Synology iSCSI Storage Issues

This cluster uses the Synology CSI driver (`csi.san.synology.com`) with iSCSI LUNs provisioned on the NAS at `10.0.1.204`. All PVCs use the `synology-iscsi-retain` StorageClass with `Retain` reclaim policy.

---

## Quick Diagnostics

```bash
# Check all PV states — any "Released" = orphaned LUN on NAS
kubectl get pv

# Check VolumeAttachments — one per active PVC, node shows where iSCSI session lives
kubectl get volumeattachment

# Check which node the iSCSI session is on vs where the pod is scheduled
kubectl get volumeattachment <name> -o jsonpath='{.spec.nodeName}'
kubectl get pod <name> -n <ns> -o jsonpath='{.spec.nodeName}'

# Check CSI node pod logs for login errors
kubectl logs -n synology-csi <synology-csi-node-pod> -c csi-plugin --since=30m

# List active iSCSI node entries on a node
kubectl exec -n synology-csi <synology-csi-node-pod> -c csi-plugin -- \
  ls /host/etc/iscsi/nodes/
```

---

## Issue: "Portal doesn't exist" Warning in NAS Logs

**Symptom:** Synology DSM logs show:
```
Initiator [iqn.2004-10.com.ubuntu:01:65feca77e5f9] failed to login to iSCSI Target
[k8s-csi-pvc-<uuid>] due to Portal doesn't exist.
```

**Cause:** A Released PV still has an associated iSCSI target entry on the NAS, but the target's portal is broken or the LUN was deleted from DSM while the K8s PV object and iscsid node entries still exist.

**Diagnosis:**
```bash
# Find the Released PV
kubectl get pv | grep Released

# Check which target it maps to
kubectl get pv <pv-name> -o jsonpath='{.spec.csi.volumeHandle}'
# Cross-reference with DSM: Storage Manager → iSCSI Manager → Target
# Look for target named k8s-csi-pvc-<uuid>

# Find stale iscsid entries on nodes
for pod in $(kubectl get pods -n synology-csi -l app=synology-csi-node -o name); do
  echo "=== $pod ==="
  kubectl exec -n synology-csi $pod -c csi-plugin -- \
    ls /host/etc/iscsi/nodes/ 2>/dev/null | grep <pv-short-uuid>
done
```

**Fix:**
1. On Synology DSM: **Storage Manager → iSCSI Manager → Target** → find the target → Delete (confirm LUN deletion when prompted)
2. Delete the Released PV from Kubernetes:
   ```bash
   kubectl delete pv <pv-name>
   ```
3. Remove stale iscsid entries from affected nodes:
   ```bash
   # Find the full IQN of the stale target (e.g. iqn.2000-01.com.synology:da-nas.pvc-<uuid>)
   kubectl exec -n synology-csi <node-pod> -c csi-plugin -- \
     rm -rf "/host/etc/iscsi/nodes/iqn.2000-01.com.synology:da-nas.pvc-<uuid>"
   ```

**Note:** All 5 nodes share the same iSCSI initiator IQN (`iqn.2004-10.com.ubuntu:01:65feca77e5f9`) because they were cloned from the same image. This is expected for this cluster.

---

## Issue: Pod Stuck in Init:0/1 — iSCSI REOPEN Loop

**Symptom:** Pod stays in `Init:0/1`, CSI node logs show repeated `REOPEN` attempts. DSM shows the target as healthy but the K8s iSCSI session is in a broken state.

**Cause:** The NAS iSCSI session was interrupted (NAS restart, network blip) and `iscsid` is caught in a reconnect loop — the session object exists on the NAS but the node's TCP connection is stale.

**Diagnosis:**
```bash
# Check CSI node logs for REOPEN
kubectl logs -n synology-csi <node-pod> -c csi-plugin --since=10m | grep -i "reopen\|login\|error"

# Check VolumeAttachment status
kubectl get volumeattachment | grep <pv-short-uuid>
kubectl describe volumeattachment <name>

# On Synology DSM: Storage Manager → iSCSI Manager → check target connection status
```

**Fix (in order):**
1. On Synology DSM: disable the iSCSI target, wait 10 seconds, re-enable it. This clears the stale session state on the NAS side.
2. Delete the VolumeAttachment to force the CSI external-attacher to do a clean detach/re-attach:
   ```bash
   kubectl delete volumeattachment <name>
   ```
3. The CSI driver will log out, log back in, and re-attach. The pod will mount and start.

**Data is safe.** The `Retain` policy means the LUN is never deleted by Kubernetes operations.

---

## Issue: Pod Stuck in Init:0/1 — VolumeAttachment Node Mismatch

**Symptom:** After a cluster restart, a StatefulSet pod (e.g. Prometheus) is scheduled on a different node than where the VolumeAttachment shows the LUN is attached. Synology NAS enforces exclusive iSCSI access per LUN — second node's login is rejected.

**Diagnosis:**
```bash
# Find the PVC UUID for the pod
kubectl get pvc -n <namespace>

# Check VolumeAttachment node vs pod node
kubectl get volumeattachment | grep <pvc-short-uuid>
# Compare .spec.nodeName to pod's .spec.nodeName
```

**Fix:** Delete the pod — the StatefulSet will reschedule it to the node that holds the VolumeAttachment:
```bash
kubectl delete pod <pod-name> -n <namespace>
```

The Synology CSI driver maintains exclusive node-level iSCSI sessions. Kubernetes schedules StatefulSet pods near their VolumeAttachments after the first deletion.

---

## Issue: scsi disk State: transport-offline

**Symptom:** `iscsiadm -m session -P 3` on the node shows `scsi disk sda State: transport-offline`. The block device exists but all I/O returns `ENXIO` (no such device or address). Kubelet logs show `readdirent ... input/output error`.

**Cause:** The iSCSI TCP session exists at the OS level but the underlying SCSI transport is offline — the NAS dropped the connection at the block layer without cleanly closing the iSCSI session.

**Fix:** Same as REOPEN loop — disable/re-enable the NAS target, then delete the VolumeAttachment. The `transport-offline` state is NOT btrfs corruption; it resolves completely with a clean re-attach.

---

## Orphaned LUN Cleanup (Routine Maintenance)

The `Retain` reclaim policy means PV objects and NAS LUNs survive PVC deletion. Periodically audit for Released PVs and clean them up.

```bash
# List all Released PVs with their original claim
kubectl get pv -o custom-columns=\
'NAME:.metadata.name,CAPACITY:.spec.capacity.storage,\
STATUS:.status.phase,CLAIM:.spec.claimRef.namespace,\
PVC:.spec.claimRef.name,AGE:.metadata.creationTimestamp' | grep Released
```

For each Released PV:
1. Verify the owning application no longer needs the data
2. On Synology DSM: delete the iSCSI target/LUN matching `k8s-csi-pvc-<uuid>`
3. `kubectl delete pv <pv-name>`

**Known causes of Released PVs:**
- PVC deleted manually
- ArgoCD `prune: true` + SSA recreating PVCs during chart upgrades (see [argocd-pvc-protection.md](argocd-pvc-protection.md))
- Application namespace deleted (e.g. pihole removed)

---

## Node iSCSI Initiator Names

All 5 nodes share the same IQN (cloned from the same Ubuntu image):

```
iqn.2004-10.com.ubuntu:01:65feca77e5f9
```

This is expected and does not cause issues because the Synology CSI driver tracks node identities via Kubernetes node names, not initiator IQNs.

| Node | IP |
|------|----|
| control-plane | 10.0.10.214 |
| node01 | 10.0.10.235 |
| node02 | 10.0.10.211 |
| node03 | 10.0.10.244 |
| node04 | 10.0.10.220 |

CSI node pod to node mapping:
```bash
kubectl get pods -n synology-csi -l app=synology-csi-node -o wide
```
