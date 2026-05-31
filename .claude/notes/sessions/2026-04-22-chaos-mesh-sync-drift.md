# 2026-04-22: Chaos Mesh 2.8.2 — Final Sync Drift Resolution

## Completed Work

**Chaos Mesh ArgoCD Sync Drift — 6 PRs to reach Synced+Healthy (64 resources, 0 OutOfSync):**

All drift sources resolved across PRs #562–#570:
- **PR #563:** Initial chaos-mesh deployment (Helm 2.8.2, 4 scheduled experiments, NetworkPolicy, Gatekeeper exclusions)
- **PR #564:** NetworkPolicy webhook fix — bare port rule (no `from`) for port 10250. Calico IPIP rewrites source IP on cross-node traffic, making `ipBlock` rules ineffective for API server → webhook calls
- **PR #565:** `ignoreDifferences` for 4 TLS cert Secrets (`/data`) auto-populated by chaos-mesh controller
- **PR #566:** `startingDeadlineSeconds: null` in all 4 Schedule YAMLs (mutation webhook adds this field); DaemonSet/Deployment switched from `jsonPointers` to `jqPathExpressions`
- **PR #567:** Webhook configs — switch from `jsonPointers: [/webhooks]` to `jqPathExpressions: [.webhooks[].clientConfig.caBundle]` (jsonPointers not honored with SSA)
- **PR #568:** Add `group: admissionregistration.k8s.io` to webhook ignoreDifferences — **cluster-scoped resources require `group` field** for ArgoCD to match them
- **PR #569:** Remove `gracePeriod: 0` from pod-kill experiment (mutation webhook strips it); rollme `jqPathExpressions` added but didn't work (ArgoCD bug/limitation with annotation map traversal)
- **PR #570:** Pin `podAnnotations.rollme: "pinned"` in values.yaml for controllerManager + chaosDaemon — chart uses `randAlphaNum 5` per render, causing perpetual drift + rolling restarts on every commit

**Final state:** 64 resources Synced+Healthy. chaos-mesh stable.

## Key Gotchas Learned
1. `jsonPointers: [/webhooks]` silently ignored with `ServerSideApply=true` — must use `jqPathExpressions`
2. Cluster-scoped resources (MutatingWebhookConfiguration, ValidatingWebhookConfiguration) require `group: admissionregistration.k8s.io` in `ignoreDifferences` or entries are silently skipped
3. Namespace-scoped resources (DaemonSet, Deployment) match WITHOUT `group` field — but jq annotation map traversal (`.spec.template.metadata.annotations.rollme`) didn't work with ArgoCD v3.3.8
4. chaos-mesh uses `randAlphaNum` for `rollme` annotation — pin it in values.yaml to prevent perpetual drift
5. Mutation webhook strips `gracePeriod: 0` from pod-kill Schedules (0 is the K8s default)

## Pull Requests
- **PRs #562–570:** chaos-mesh deployment and drift resolution (all merged)
