# Troubleshooting: ArgoCD PVC Recreation During Chart Upgrades

## Problem

ArgoCD with `prune: true` + `ServerSideApply=true` can **delete and reprovision PVCs** during chart upgrades. With the Synology CSI `Retain` reclaim policy:

- A new iSCSI LUN is provisioned on the NAS (empty, data lost from application's perspective)
- The old LUN is left as a **Released PV** — orphaned, consuming NAS storage indefinitely
- The application starts fresh with an empty volume

This has affected the following PVCs at least once each:

| PVC | Namespace | Date | Old PV |
|-----|-----------|------|--------|
| `kube-prometheus-stack-grafana` | default | 2026-04-17 | pvc-ad5666f9 |
| `data-trivy-server-0` | trivy-system | 2026-01-06, 2026-04-17 | pvc-72cd5620 |
| `storage-loki-0` | loki | 2026-01-25 | pvc-1f408dc1 |

Prometheus (`prometheus-db-...`) has **not** been affected despite being a StatefulSet on the same storage class.

---

## Root Cause

### Standalone PVCs (Grafana)

Grafana uses a Deployment + standalone PVC rendered directly by the Helm chart. When ArgoCD syncs a chart upgrade:

1. The chart renders the PVC with updated labels (e.g., `helm.sh/chart: grafana-11.3.7`)
2. ArgoCD applies via SSA — normally this is a no-op label update
3. Under certain SSA field-ownership conditions, ArgoCD's diff engine marks the live PVC as diverged
4. With `prune: true`, ArgoCD deletes the old PVC and creates a new one

### StatefulSet VolumeClaimTemplates (Loki, Trivy)

StatefulSets have immutable `spec.volumeClaimTemplates`. When a chart upgrade changes any VCT field (storageClass, size, labels, annotations):

1. ArgoCD detects the VCT diff (SSA sees the live StatefulSet spec differs from rendered)
2. Since VCT is immutable, ArgoCD cannot patch it — it deletes and recreates the StatefulSet
3. The StatefulSet controller creates a new PVC from the new VCT template
4. The old PVC is orphaned (Retain policy keeps the LUN)

---

## Detecting the Problem

```bash
# Check for Released PVs (orphaned LUNs)
kubectl get pv | grep Released

# Check PVC creation timestamps — sudden "recent" PVC for a long-running app is suspicious
kubectl get pvc -A --sort-by='.metadata.creationTimestamp' | tail -10

# Check if a StatefulSet was recently recreated
kubectl get statefulset -A -o custom-columns=\
'NS:.metadata.namespace,NAME:.metadata.name,CREATED:.metadata.creationTimestamp' | sort -k3
```

---

## Fixes Applied (as of 2026-04-17)

### Grafana — `Prune=false` annotation

In `manifests/base/kube-prometheus-stack/values.yaml`:

```yaml
grafana:
  persistence:
    enabled: true
    storageClassName: synology-iscsi-retain
    annotations:
      argocd.argoproj.io/sync-options: "Prune=false"
```

The `Prune=false` sync option tells ArgoCD: **never delete this resource during automated sync**, even if it appears orphaned or diverged. The PVC persists across all future chart upgrades.

### Trivy — `ignoreDifferences` for StatefulSet VCT

In `manifests/applications/trivy-operator.yaml`:

```yaml
ignoreDifferences:
  - group: apps
    kind: StatefulSet
    jqPathExpressions:
      - .spec.volumeClaimTemplates
```

ArgoCD will no longer detect VCT changes as requiring action. If the chart changes the VCT spec in a future upgrade, it will be silently ignored — the existing StatefulSet and PVC are preserved.

### Loki — `ignoreDifferences` extended to full VCT spec

In `manifests/applications/loki.yaml`:

```yaml
ignoreDifferences:
  - group: "apps"
    kind: "StatefulSet"
    jqPathExpressions:
      - .spec.volumeClaimTemplates   # Full VCT spec (previously only status/creationTimestamp)
      - .status
```

---

## Pattern: Protecting Any PVC from ArgoCD Prune

### Option A — `Prune=false` annotation (standalone PVCs / Helm charts with `persistence.annotations`)

Add to the chart values wherever the PVC is rendered:

```yaml
persistence:
  annotations:
    argocd.argoproj.io/sync-options: "Prune=false"
```

Or if managing the PVC directly as a manifest:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  annotations:
    argocd.argoproj.io/sync-options: "Prune=false"
```

### Option B — `ignoreDifferences` for StatefulSet VCT (StatefulSet-managed PVCs)

Add to the ArgoCD Application spec:

```yaml
ignoreDifferences:
  - group: apps
    kind: StatefulSet
    jqPathExpressions:
      - .spec.volumeClaimTemplates
```

### Option C — `existingClaim` (decouple PVC from chart lifecycle entirely)

For Helm charts that support it, use an existing PVC name:

```yaml
persistence:
  existingClaim: my-app-data
```

Then manage the PVC as a separate GitOps resource with `Prune=false`. The chart will not render a PVC — ArgoCD cannot delete what it doesn't render.

---

## When a PVC Has Already Been Recreated

If data was lost due to a recreation event:

1. **Check the Released PV** — the old LUN is still on the NAS (Retain policy):
   ```bash
   kubectl get pv | grep Released
   kubectl get pv <old-pv-name> -o jsonpath='{.spec.csi.volumeHandle}'
   ```

2. **Recover data if needed** — the old LUN is accessible. Mount it on a node for manual recovery:
   - On Synology DSM: temporarily create a snapshot clone of the old LUN
   - Or: recreate a PV/PVC pointing to the old `volumeHandle` and mount it to a debug pod

3. **Clean up the orphan** (after data verified or not needed):
   - Delete the LUN on Synology DSM: Storage Manager → iSCSI Manager → Target
   - `kubectl delete pv <old-pv-name>`

---

## Applications Currently Protected (as of 2026-04-17)

| Application | PVC | Protection Method |
|-------------|-----|-------------------|
| kube-prometheus-stack / Grafana | `kube-prometheus-stack-grafana` | `Prune=false` annotation |
| trivy-operator / trivy-server | `data-trivy-server-0` (VCT) | `ignoreDifferences: .spec.volumeClaimTemplates` |
| loki / loki | `storage-loki-0` (VCT) | `ignoreDifferences: .spec.volumeClaimTemplates` |
| kube-prometheus-stack / Prometheus | `prometheus-db-...` (VCT) | Unaffected so far; monitor |
| falco / redis | `falco-falcosidekick-ui-redis-data-...` (VCT) | Unaffected so far; monitor |
