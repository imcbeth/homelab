---
name: renovate-apply
description: Applies merged Renovate dependency PRs to the cluster in sync-wave order. Use after Renovate PRs that change manifests/applications/ are merged, because Argo CD does not deploy Application specs itself - run kubectl apply per app and confirm Synced+Healthy at the new chart version. Triggers on "apply Renovate updates", "deploy the Renovate PRs", "go through the dependency PRs".
---

# Renovate Apply Skill

## Purpose

Safely review and apply merged Renovate dependency update PRs to the cluster in the correct order, with pre-flight compatibility checks, per-app verification, and full post-apply cluster validation.

## When to Use

- User has merged one or more Renovate PRs and asks to apply them
- Triggered by: "apply Renovate updates", "deploy the Renovate PRs", "apply the merged Renovate PRs"

## Skill Instructions

### Phase 1: Discover What Was Merged

1. Pull the latest main branch to see what Renovate PRs changed:
   ```bash
   git fetch origin && git log origin/main --oneline -20
   ```

2. For each relevant commit, identify:
   - Which apps changed (`manifests/applications/<app>.yaml`)
   - Whether it's a **patch**, **minor**, or **major** version bump
   - Whether it's a Helm chart version bump or image-only bump

3. Group apps into two tiers:
   - **Tier 1 (safe):** patch/minor bumps, image-only changes, apps with no stateful side effects
   - **Tier 2 (review required):** major version bumps, chart changes with potential API/schema changes

### Phase 2: Pre-Flight for Major Version Bumps

For any **major** Helm chart version bump (e.g., Loki 6.x→7.x, uptime-kuma 2.x→4.x):

1. Inspect our current values to identify key chart API paths we depend on:
   ```bash
   cat manifests/base/<app>/values.yaml
   ```

2. Check the new chart's values schema:
   ```bash
   helm show values <repo>/<chart> --version <new-version> | head -200
   ```

3. Verify critical keys are still present (e.g., `deploymentMode`, `useDeploy`, `volume:`, `strategy:`).

4. Read the release notes / CHANGELOG for breaking changes.

5. **Do NOT apply if breaking changes require values migration.** File a follow-up task.

**Known major version gotchas:**
- Loki 7.x: default deployment mode changed to `SimpleScalable`, but explicit `deploymentMode: SingleBinary` in values overrides it safely
- uptime-kuma 4.x: `useDeploy`, `volume:`, `strategy:`, `ingress:` all preserved — compatible
- Always verify with `helm show values` rather than trusting release notes alone

### Phase 3: Apply in Correct Order

**Ordering rules:**
1. Apply infrastructure apps (ArgoCD, argo-workflows, monitoring) before dependent apps
2. Apply apps with lower sync-waves before higher sync-waves
3. Apply Tier 1 apps first; wait for each to be Synced+Healthy before proceeding
4. Apply Tier 2 (major) apps last, one at a time

**Apply pattern (CRITICAL — ArgoCD self-management does NOT auto-detect Application manifest changes):**
```bash
kubectl apply -f manifests/applications/<app>.yaml
```

Then wait for the app to sync. Monitor with MCP:
- `mcp__argocd__get_application` to check `.status.sync.status` and `.status.health.status`
- Or: `kubectl get application <app> -n argocd -o custom-columns='SYNC:.status.sync.status,HEALTH:.status.health.status,OP:.status.operationState.phase'`

**Expected progression:** OutOfSync/Healthy/Running → Synced/Healthy/Succeeded

### Phase 4: Handle Common Failures

#### Strategy Type Conflict (RollingUpdate → Recreate)
**Symptom:** `spec.strategy.rollingUpdate: Forbidden: may not be specified when strategy 'type' is 'Recreate'`

**Cause:** Chart changed `strategy.type` to Recreate, but the existing Deployment has Kubernetes-defaulted `rollingUpdate` fields that SSA can't remove (not owned by argocd-controller).

**Fix:**
```bash
kubectl delete deployment <deployment-name> -n <namespace>
```
ArgoCD recreates it immediately with the clean strategy.

#### ArgoCD PreSync Hook Stuck
**Symptom:** `waiting for completion of hook batch/Job/<hook-job-name>` for >5 minutes

**Cause:** kube-prometheus-stack (and other charts with admission webhook cert jobs) runs a PreSync job. This is normal — it must complete before the main sync proceeds.

**Action:** Wait. Typical completion time is 30s–3min. Check the hook job with:
```bash
kubectl get job -n <namespace>
kubectl logs -n <namespace> job/<hook-job-name>
```

If stuck >10min, check if the job pod is Pending (resource constraint or node issue).

#### OOMKilled Controller
**Symptom:** ArgoCD application-controller pods restarting, `reason: OOMKilled`, `exitCode: 137`

**Cause:** Controller memory limit insufficient for cache warm-up with current app count.

**Fix:**
1. Bump limit in `manifests/base/argocd/argocd-config.yaml` (Gatekeeper max: 2Gi)
2. For immediate relief: `kubectl patch statefulset argocd-application-controller -n argocd --type='json' -p='[{"op":"replace","path":"/spec/template/spec/containers/0/resources/limits/memory","value":"2Gi"}]'`

#### App Stuck in Running/OutOfSync After Apply
**Symptom:** App stays OutOfSync/Running >5 minutes with no progress

**Check for stuck operation:**
```bash
kubectl get application <app> -n argocd -o jsonpath='{.status.operationState.message}'
kubectl get application <app> -n argocd -o jsonpath='{.status.conditions}'
```

**If stale sync annotation:**
```bash
kubectl annotate app <app> -n argocd argocd.argoproj.io/sync- argocd.argoproj.io/sync-options- 2>/dev/null; true
```

**If stuck operation:**
```bash
kubectl patch app <app> -n argocd --type json -p '[{"op":"remove","path":"/status/operationState"}]'
```

### Phase 5: Post-Apply Cluster Validation

After all apps have been applied:

1. **Full cluster health check** using `mcp__argocd__list_applications` — parse results to confirm all apps show `sync: Synced` and `health: Healthy`.

2. **Spot-check updated apps** specifically — confirm they are running the new image versions.

3. **Check for OOMKills or restarts:**
   ```bash
   kubectl get pods -A --field-selector=status.phase!=Running | grep -v Completed
   ```

4. **Validate key services** are accessible (if applicable):
   - ArgoCD: `https://argocd.k8s.n37.ca`
   - Grafana: `https://grafana.k8s.n37.ca`
   - Status page: `https://status.k8s.n37.ca`

5. Report final count: `N/N apps Synced + Healthy`.

---

## Session Notes Template

After completing a Renovate apply session, document it in `.claude/notes/CURRENT.md`:

```markdown
### YYYY-MM-DD: Renovate Batch — <short description>

**PRs Applied:**
- **PR #NNN:** [Merged] <description> (<old-version>→<new-version>)

**Applications Updated:**
| App | Old Version | New Version | Status |
|-----|-------------|-------------|--------|
| argocd | 9.5.3 | 9.5.4 | ✅ Synced+Healthy |

**Issues Encountered:**
- <app>: <problem> → <root cause> → <fix applied>

**Final State:** 31/31 apps Synced+Healthy
```

---

## Quick Reference: Apps Requiring Manual Apply

ALL apps in `manifests/applications/` require `kubectl apply` after PR merge.
ArgoCD self-management only monitors `manifests/base/argocd/` for its own config.

Common targets:
```bash
kubectl apply -f manifests/applications/argocd.yaml
kubectl apply -f manifests/applications/argo-workflows.yaml
kubectl apply -f manifests/applications/alloy.yaml
kubectl apply -f manifests/applications/kube-prometheus-stack.yaml
kubectl apply -f manifests/applications/loki.yaml
kubectl apply -f manifests/applications/uptime-kuma.yaml
kubectl apply -f manifests/applications/velero.yaml
kubectl apply -f manifests/applications/cert-manager.yaml
```

## Known Safe Batch Pattern

For patch/minor bumps with no breaking changes, multiple apps can be applied simultaneously:
```bash
kubectl apply -f manifests/applications/argocd.yaml \
              -f manifests/applications/argo-workflows.yaml \
              -f manifests/applications/alloy.yaml
```

Then watch all together:
```bash
kubectl get application argocd argo-workflows alloy -n argocd \
  -o custom-columns='NAME:.metadata.name,SYNC:.status.sync.status,HEALTH:.status.health.status,OP:.status.operationState.phase' \
  --watch
```

For **major** version bumps: apply one at a time and wait for Synced+Healthy before proceeding.
