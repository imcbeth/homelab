### 2026-05-31 (Night): LocalStack Fix, Retention 30d, Flink Verify, Argo Events

**Completed Work:**

**LocalStack CORS + Persistence (PRs #659, #660):**
- Added `EXTRA_CORS_ALLOWED_ORIGINS` env var to fix CORS errors from `https://localstack.k8s.n37.ca`
- Added `PERSISTENCE=1` + 2Gi iSCSI PVC (`synology-iscsi-retain`) → S3 state survives pod restarts
- Root cause of NoSuchBucket on `aws login`: internal auth service uses S3 as state backend; ephemeral LocalStack wiped it on every restart

**Retention bumped to 30 days (PR #661):**
- Prometheus: `10d → 30d`, AlertManager: `120h → 720h`, Loki: `168h → 720h`, Tempo: `168h → 720h`

**Flink job re-verified after retention PR:**
- Deleted file-to-kafka JobManager pod → replayed 15 records
- Confirmed: `s3://flink-output/events/2026/05/31/18/*.json` — 15 files in LocalStack S3 ✅

**Argo Events deployment (PR #662):**
- Deployed v1.9.10 (Helm chart 2.4.21) with JetStream EventBus (NATS 2.10.10)
- NetworkPolicies for argo-events namespace + complementary rules in default, ingress-nginx, argo-workflows NPs
- Fixed all 5 Copilot review comments: wrong Prometheus namespace, missing port 7777 egress, ingress-nginx→argo-events:12000 egress, argo-workflows ingress from argo-events, kustomization.yaml to exclude values.yaml from directory source
- Applied: `kubectl apply -f manifests/applications/argo-events.yaml`
- Pods healthy: controller-manager 1/1, eventbus-default-js-0 3/3, events-webhook 1/1, sensor 1/1, eventsource starting

**Key Gotchas:**
- **ArgoCD directory source applies ALL YAML**: Any directory source will try to apply `values.yaml` as a K8s manifest. Add `kustomization.yaml` to switch to Kustomize mode and enumerate only real resources.
- **kube-prometheus-stack namespace is `default`**: ServiceMonitor `namespace:` field and NetworkPolicy scrape rules must use `default`, not `monitoring`.

**Pull Requests:**
- **PR #659:** [Merged] fix(localstack): add CORS allowed origin for localstack.k8s.n37.ca
- **PR #660:** [Merged] fix(localstack): add persistence PVC and PERSISTENCE env var
- **PR #661:** [Merged] chore: increase log and metric retention to 30 days
- **PR #662:** [Merged] feat(argo-events): deploy Argo Events v1.9.10 with JetStream EventBus
