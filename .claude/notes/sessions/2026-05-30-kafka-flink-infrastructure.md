# 2026-05-30: Kafka + Flink Demo Infrastructure — PR Reviews, Deployment, Post-Merge Fixes

## Completed Work

### PR Reviews + Fixes (#617, #618)

Resolved all 15 Copilot review comments across both PRs with code fixes and reply comments.

Key fixes: CLAUDE.md sealed-secret filename (`*-sealed.yaml` required to avoid git-crypt and yamllint), ValidatingWebhookConfiguration ignoreDifferences for flink-operator, webhook name corrected to `flink-operator-flink-operator-webhook-configuration`, removed `path:` from ref-only ArgoCD sources, LocalStack hook `exit 1` on failure, Dockerfile script duplication removed.

PR #617 merged by user; PR #618 rebased onto updated main (CLAUDE.md + kustomization.yaml conflicts resolved). PR #618 merged; all 4 ArgoCD Application manifests applied via `kubectl apply`.

### Post-Merge Infrastructure Fixes (PRs #629–#635)

- **PR #629:** `kafka version: 3.9.0 → 4.1.2` (Strimzi 1.0.0 only supports Kafka 4.x); added `ignoreDifferences` for Flink CRD `spec.conversion.strategy=None` drift (Kubernetes adds this after SSA apply)
- **PR #630:** Added strimzi-system → kafka ingress on 9091/9092 (NetworkPolicy was blocking Strimzi AdminClient)
- **PR #631:** Added port 9090 (KRaft CONTROLPLANE) to kafka NP and strimzi-system NP. Root cause: Strimzi's `describeMetadataQuorum` AdminClient connects to bootstrap (9092), discovers controller at `CONTROLPLANE-9090://...` from metadata, then tries port 9090
- **PR #632:** Attempted startup probe for user-operator via `spec.entityOperator.template.userOperatorContainer.startupProbe` — rejected by ArgoCD SSA: "field not declared in schema". Only `env`, `securityContext`, `volumeMounts` are available in that template.
- **PR #633:** Removed `spec.entityOperator.userOperator` — Strimzi 1.0.0's user-operator liveness probe (`initialDelaySeconds=10`, `failureThreshold=3`) kills the container at ~35s before ARM64 JVM + AdminClient init completes. No KafkaUser CRDs needed for demo.
- **PR #634:** Added `istio.io/dataplane-mode: ambient` to all 4 new namespace manifests (kafka, strimzi-system, flink-operator, flink-demo)
- **PR #635:** Use bare egress rule for ztunnel HBONE port 15008 in all 4 new namespaces (see HBONE Egress Fix session)

## Key Gotchas

- Strimzi 1.0.0 entity-operator bootstrap uses port 9091 (REPLICATION/internal TLS), not 9092. NetworkPolicy intra-kafka rules must include 9091.
- Strimzi `describeMetadataQuorum` AdminClient connects to bootstrap (9092) then follows controller endpoint to CONTROLPLANE-9090. Both ports need NetworkPolicy egress from strimzi-system.
- Strimzi 1.0.0 Kafka CRD only exposes `env`, `securityContext`, `volumeMounts` in `spec.entityOperator.template.userOperatorContainer` — no probe fields. Cannot configure startupProbe via CR.
- User-operator tini `-e 143` maps SIGTERM (exit 143) to exit 0, so CrashLoopBackOff shows `exitCode: 0, reason: Completed` — looks like clean exit but is actually liveness probe kill.
- Flink CRD drift: `spec.conversion.strategy=None` added by Kubernetes after SSA apply; not in chart. Add `apiextensions.k8s.io/CustomResourceDefinition` ignoreDifferences with `.spec.conversion` jqPathExpression.

## Pull Requests

- **PR #617:** [Merged by user] feat: Strimzi + Flink operator infrastructure
- **PR #618:** [Merged] feat: Kafka cluster + Flink demo pipeline (file→Kafka→S3)
- **PR #629:** [Merged] fix: Kafka 4.1.2 for Strimzi 1.0.0 + Flink CRD conversion drift
- **PR #630:** [Merged] fix: allow strimzi-system ingress to kafka on 9091/9092
- **PR #631:** [Merged] fix: add KRaft CONTROLPLANE port 9090 to kafka and strimzi-system NPs
- **PR #632:** [Merged] fix: attempted startup probe (field not in schema — superseded by #633)
- **PR #633:** [Merged] fix: remove user-operator from entity operator
- **PR #634:** [Merged] fix: add Istio ambient mesh labels to all 4 new namespaces
- **PR #635:** [Merged] fix: use bare egress rule for ztunnel HBONE port 15008 in all 4 new namespaces
