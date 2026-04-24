# 2026-04-17 Sessions 2 & 3: tigera-operator, iSCSI PVC Protection, Always-On Monitoring

## Session 2: tigera-operator, iSCSI Root Cause, PVC Protection

**Completed Work:**

**tigera-operator Gatekeeper exclusion removed (PR #543):**
- Created `manifests/base/tigera-operator/kustomization.yaml`: Kustomize overlay fetching upstream + strategic merge patch adding resource limits (100m/128Mi requests, 500m/256Mi limits)
- Consolidated ArgoCD Application from 2 sources to single Kustomize source
- Removed `tigera-operator` from Gatekeeper `require-resource-limits` excludedNamespaces → 0 violations
- Also included `IstioXDSPushRejections` alert from previous session

**iSCSI "Portal doesn't exist" — Root Cause Investigation:**
- Warning source: Released PV `pvc-ad5666f9` (old Grafana LUN, orphaned during chart upgrade)
- Stale `/etc/iscsi/nodes/` entries on node02 and node03 for dead target
- All 5 nodes share SAME initiator IQN `iqn.2004-10.com.ubuntu:01:65feca77e5f9` (cloned images)

**Systemic iSCSI PVC Recreation Bug Found + Fixed (PR #544):**
- Root cause: ArgoCD `prune: true` + `ServerSideApply=true` deletes+reprovisioned PVCs during chart upgrades
- Confirmed victims: Grafana, Trivy (×2), Loki
- Fix 1 — Grafana standalone PVC: `argocd.argoproj.io/sync-options: Prune=false` annotation
- Fix 2 — Trivy StatefulSet VCT: `ignoreDifferences` for `.spec.volumeClaimTemplates`
- Fix 3 — Loki StatefulSet VCT: extended existing `ignoreDifferences` to full VCT

**PRs:** #543 [Merged], #544 [Merged]

---

## Session 3: Always-On Monitoring, VPN, Renovate Batch

**Completed Work:**

**VPN Decision:** Section 15 closed — UniFi gateway VPN handles it, no cluster-side VPN needed.

**Renovate Deferred Batch (5 PRs merged):**
- #546: cert-manager v1.20.1→v1.20.2
- #547: Istio 1.29.1→1.29.2
- #548: kube-prometheus-stack AlertManager v0.31.1→v0.32.0
- #549: external-dns v0.20.0→v0.21.0
- #550: kube-prometheus-stack 82.18.0→83.6.0

**Always-On Monitoring — Layer 1 (Mac LaunchAgent):**
- `~/.claude/scripts/k8s-daily-check.sh` — daily health check via `claude --print`, macOS notifications, 30-day log rotation
- Runs at 08:00 local time via `~/Library/LaunchAgents/dev.n37.k8s-healthcheck.plist`

**Always-On Monitoring — Layer 2 (Argo Workflows CronWorkflow, PR #551):**
- `cluster-healthcheck-rbac.yaml` — SA + Role (emissary) + ClusterRole (read-only cluster)
- `cluster-healthcheck-workflow.yaml` — CronWorkflow `0 6 * * *`; 5 parallel checks; POST `ClusterHealthDegraded` to AlertManager on failure

**k8s-docs-n37 Sync (PR #75):** Updated velero.md, new iscsi-troubleshooting.md, new argocd-pvc-protection.md

**PRs:** #545-551 [Merged]
