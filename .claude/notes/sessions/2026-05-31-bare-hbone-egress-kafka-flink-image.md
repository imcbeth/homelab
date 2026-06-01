# 2026-05-31: Bare HBONE Egress Fix — Kafka READY, Flink Image Build

## Completed Work (continuation of 2026-05-30 session)

### Root Cause: ztunnel HBONE NetworkPolicy (PR #635)

After PR #634 enrolled 4 new namespaces in Istio Ambient, kafka topic-operator started crashing with "Connection to kafka-bootstrap:9091 terminated during authentication". Kafka broker logs showed NO incoming connections — traffic dropped before reaching the broker.

ztunnel access log revealed: `error="connection timed out, maybe a NetworkPolicy is blocking HBONE port 15008"` from entity-operator pod IP to broker pod IP:15008.

Root cause: ztunnel sends HBONE **from within the pod's network namespace** (using the pod's source IP), so pod NetworkPolicies DO apply. But the HBONE destination is the broker pod's IP on port 15008 — NOT an `istio-system` pod IP. The old namespace-scoped rule `to: istio-system, port: 15008` never matched.

Fix: Split Istio egress into two rules in all 4 namespace NetworkPolicies:
- Port 15008: bare rule (no `to` selector) — allows ztunnel HBONE to any destination
- Ports 15012/15017: namespace-scoped to istio-system — istiod xDS/webhook

Also fixed for strimzi-system, flink-operator, flink-demo (same pattern). PR #635 created and merged.

### ArgoCD selfHeal Revert

First `kubectl apply` was reverted by ArgoCD within ~30s (selfHeal: true). Had to push the fix to git and trigger ArgoCD refresh with:
```bash
kubectl annotate app network-policies argocd.argoproj.io/refresh=hard -n argocd
```

### Kafka Fully Healthy

- `kubectl get kafka -n kafka` → `READY: True` ✅
- `kafka-cluster-entity-operator`: 1/1 Running, 0 restarts ✅
- Kafka ArgoCD app: Synced+Healthy ✅

### localstack-flink-setup Job Fixed

The same HBONE issue was blocking the flink-demo PreSync job from reaching LocalStack (cross-node traffic on port 15008 blocked). After PR #635, job completed: `s3://flink-output` bucket created ✅

### Flink Docker Image Build

Started colima (`colima start --arch aarch64`), built `registry.k8s.n37.ca/flink-demo:1.0.0` for linux/arm64 via:
```bash
DOCKER_HOST=unix://$HOME/.colima/default/docker.sock bash build-and-push.sh
```

## Key Gotchas

- **ztunnel HBONE uses pod network namespace**: ztunnel sends HBONE connections with the SOURCE POD'S IP (not ztunnel's hostNetwork IP). Therefore Calico NetworkPolicies DO apply to HBONE traffic. Bare egress rule for port 15008 is needed because the DESTINATION is the target pod's IP on port 15008, not an istio-system pod.
- **ArgoCD selfHeal reverts kubectl apply in ~30s**: For NetworkPolicy fixes in ambient mesh clusters, `kubectl apply` is only useful for testing. Must commit and push to git for permanent effect.
- **HTTPS push workaround**: `gh auth setup-git` + `git remote set-url origin https://github.com/...` allows push when SSH key isn't loaded.

## Pull Requests

- **PR #635:** [Merged] fix: use bare egress rule for ztunnel HBONE port 15008 in all 4 new namespaces
