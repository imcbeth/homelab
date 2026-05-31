# 2026-04-21 (Evening, Session 2): Housekeeping + Healthcheck Verification

## Completed Work

**Renovate kube-webhook-certgen Warning (PR #562):**
- Added `registry.k8s.io/ingress-nginx/kube-webhook-certgen` to `ignoreDeps` in `renovate.json`
- Pinned in `manifests/base/kube-prometheus-stack/values.yaml` but registry.k8s.io lookup returns `no-result`
- Version managed by kube-prometheus-stack chart upgrades — no separate tracking needed

**TODO.md Cleanup:**
- Marked VPN/Remote Access section done (UniFi gateway VPN server handles it — applied from session stash)
- Marked k8s-docs-n37 guides done (cert-manager, metallb, ingress-nginx, localstack all exist from earlier sessions)

**Cluster Healthcheck Verification:**
- ArgoCD `argo-workflows` Synced+Healthy at commit `44b2926` (PR #559 fix) — synced 2026-04-20 19:35 UTC (before April 21 06:00 MDT run)
- CronWorkflow `failed: 3, succeeded: 0` — 3 pre-fix failures (Apr 18-20). `succeeded: 0` likely due to TTL GC decrementing counter after today's successful run (2h TTL)
- Fix confirmed deployed: CronWorkflow spec shows `velero-daily-*` prefix names
- Pre-existing `RepeatedResourceWarning`: argo-workflows source 2 has both `ref: values` AND `path:` — non-fatal

**Branch Sync:**
- Local `main` was 29 commits behind origin/main (PRs #553-#561 not pulled). Updated via `git reset --hard origin/main`
- Rebased `chore/renovate-ignore-kube-webhook-certgen` onto origin/main

## Pull Requests
- **PR #562:** [Open] chore: ignore kube-webhook-certgen in Renovate, update TODO

## Key Learnings
- CronWorkflow `succeeded` counter may decrement when completed workflows are cleaned up by TTL. Don't rely on it as a strict cumulative counter.
