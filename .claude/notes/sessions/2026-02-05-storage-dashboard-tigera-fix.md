### 2026-02-05 (Evening): Storage Dashboard, Tigera Fix, Network Dashboard & Cleanup

**Completed Work:**
- Created storage performance Grafana dashboard (5 sections: PVC overview/trends, iSCSI LUN performance, node disk I/O, Synology RAID health)
- Diagnosed and fixed tigera-operator IPPool ownership error (root cause: `RestoreV3Metadata()` wiped `managed-by` label from in-memory IPPool via `projectcalico.org/metadata` annotation)
- Deployed Calico APIServer CR to enable v3 API for operator IPPool reconciliation
- Created network utilization Grafana dashboard (5 sections: WAN, switch ports, node network, Synology NAS, WiFi clients)
- Enabled SealedSecrets key rotation (30-day period)
- Validated all dashboard panels have live Prometheus data
- Updated TODO.md with completed items

**Pull Requests:**
- **PR #383:** [Merged] feat: add storage performance Grafana dashboard
- **PR #385:** [Merged] fix: deploy Calico APIServer and fix IPPool ownership error
- **PR (pending):** feat: add network utilization dashboard, enable SealedSecrets key rotation

**Issues Resolved:**

1. **tigera-operator "Cannot update an IP pool not owned by the operator"**
   - Root cause: `RestoreV3Metadata()` in the operator reads `projectcalico.org/metadata` annotation and calls `SetLabels()` with stored labels. The annotation had no labels stored, so it wiped the `managed-by: tigera-operator` label from the in-memory object before the ownership check ran.
   - Fix: Patched annotation to include the `managed-by` label; deployed Calico APIServer for v3 API access.
   - **Key Learning:** The `projectcalico.org/metadata` annotation on Calico CRDs stores v3 metadata including labels. If this annotation lacks labels, `RestoreV3Metadata()` will wipe all labels from the object in-memory.

2. **tigera-operator "Unable to modify IP pools while Calico API server is unavailable"**
   - Root cause: No Calico APIServer CR deployed; operator can't use v3 API for pool reconciliation.
   - Fix: Created `apiserver.yaml` with `APIServer` CR (`spec: {}`)

**Files Created/Modified:**
- `manifests/base/grafana/dashboards/storage-performance-dashboard.yaml` (new)
- `manifests/base/grafana/dashboards/network-utilization-dashboard.yaml` (new)
- `manifests/base/grafana/dashboards/kustomization.yaml` (added both dashboards)
- `manifests/base/tigera-operator/apiserver.yaml` (new)
- `manifests/applications/tigera-operator.yaml` (APIServer ignoreDifferences)
- `manifests/base/sealed-secrets/values.yaml` (key rotation enabled)
- `TODO.md` (marked completed items)
