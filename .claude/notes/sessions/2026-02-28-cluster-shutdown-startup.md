# 2026-02-28: NAS Maintenance — Full Cluster Shutdown/Startup & Health Check

**Completed Work:**
- Executed graceful full cluster shutdown for NAS maintenance
- Disabled ArgoCD auto-sync on all 25 apps before shutdown
- Scaled down 6 NAS-dependent workloads (Prometheus operator first, then StatefulSets/Deployments)
- Verified all 5 iSCSI VolumeAttachments cleanly released before node shutdown
- Cordoned, drained, and SSH shutdown all 5 nodes (workers first, control-plane last)
- Post-maintenance: verified all nodes Ready, uncordoned, re-enabled ArgoCD auto-sync
- Fixed kube-prometheus-stack stuck sync (174+ PreSync hooks — cleared operationState, manually scaled workloads)
- Fixed metrics-server unreachable (kube-system NetworkPolicy had port 4443, should be 10250)
- Fixed falco-sidekick-ui Init:Error (wait-redis init container, deleted pod to reschedule near Redis)
- All 24/25 apps restored to Synced+Healthy (network-policies OutOfSync pre-existing)
- Documented cluster maintenance procedures in k8s-docs-n37 Docusaurus site
- Created `/cluster-shutdown` and `/cluster-healthcheck` Claude Code slash commands

**Pull Requests:**
- **PR #485 (homelab):** [Merged] fix: correct kube-system NetworkPolicy port for metrics-server (4443 → 10250)
- **PR #69 (k8s-docs-n37):** [Merged] docs: add cluster maintenance guide

**Issues Resolved:**
1. **metrics-server aggregated API unreachable** — kube-system NetworkPolicy bare ingress rule used port 4443, but metrics-server serves on 10250. hostNetwork API server can't match namespaceSelector rules, so bare port rule is required. Latent bug exposed by full cluster reboot.
2. **kube-prometheus-stack sync stuck on hooks** — 174+ PreSync resources for admission webhook cert generation. Cleared `/status/operationState` and `/operation`, manually scaled operator+grafana+prometheus.
3. **Gatekeeper PDB blocks drain** — Deleted PDB during shutdown. ArgoCD auto-restored it on startup.
4. **Falco sidekick-ui Init:Error** — wait-redis init container fails when Redis pod is on different node. Deleting pod allows rescheduling near Redis.

**Key Learning:**
- Prometheus Operator MUST be scaled to 0 before Prometheus StatefulSet, or operator reconciles it back immediately
- kube-prometheus-stack ArgoCD sync with 174+ hooks hangs after restart — need to clear operation and manually scale
- hostNetwork pods (kube-apiserver) don't match namespaceSelector NetworkPolicy rules — always use bare port rules for aggregated API access
- Node kernel updates happen during reboot via unattended-upgrades (6.8.0-1043 → 6.8.0-1048)
- SSH key for nodes: `~/.ssh/id_ed25519_k8s` (not default)

**Files Modified:**
- `manifests/base/network-policies/kube-system/network-policy.yaml` (port 4443 → 10250)
- `~/.claude/commands/cluster-shutdown.md` (new skill)
- `~/.claude/commands/cluster-healthcheck.md` (new skill)
