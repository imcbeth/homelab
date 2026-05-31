# Claude Code - Homelab Current Context

**Last Updated:** 2026-05-31
**Repository:** imcbeth/homelab
**Cluster:** 5x Raspberry Pi 5 (16GB each) Kubernetes Homelab

---

## Quick Start

1. Read this file for recent session context
2. Check `TODO.md` for current priorities
3. Reference `.claude/notes/REFERENCE.md` for patterns and gotchas
4. Grep `.claude/notes/sessions/` for historical lookups

---

## Current State

**Secrets Management:** Complete
- 8 SealedSecrets deployed, git-crypt migration finished
- Sealing key backed up to Synology NAS
- Bootstrap secret: `secrets/argocd-git-access.yaml` (manual apply)
- Grafana password: Helm-managed (do NOT create SealedSecret)

**Prometheus + Grafana + Loki:** ✅ All Healthy — Recovered 2026-04-20/21. UDR factory reset (2026-04-19) dropped iSCSI sessions; btrfs remounted Grafana (5Gi), Prometheus (50Gi), and Loki (20Gi) PVCs read-only. All three fixed by pod delete → fresh volume remount → RW restored. 0 restarts post-fix. Falco Redis (2Gi) unaffected.

**Backup Strategy:** Complete + DR Validation
- Daily ArgoCD config backup (1:30 AM)
- Daily critical PVC backup (2:00 AM)
- Weekly full cluster backup (3:00 AM Sunday)
- Backblaze B2 restore tested and validated
- Monthly DR validation CronWorkflow (1st of month 6am MT) — full backup/restore cycle, ✅ validated 2026-03-25
- **✅ Velero v1.18.0 running** — Upgraded to v1.18.0 binary + chart v12.0.0 (PRs #531/#532/#552). "Queued" phase now in CRD enum. Validated end-to-end: Queued → InProgress → Completed 2026-04-18.

**Monitoring:** Operational
- AlertManager email: 121 sent, 0 failed
- Trivy scanning: 58+ VulnerabilityReports, metrics in Prometheus (Critical: 44, High: 479, Medium: 1058)
- Trivy dashboard enhanced with vulnerability panels, alerts, and trends
- Trivy compliance reporting: Weekly CronJob → AlertManager summary (PRs #494-496)
- All Prometheus targets healthy (metrics-server HTTPS scraping fixed)
- Argo Workflows: Grafana dashboard deployed with ServiceMonitor
- Alloy: Replaced Promtail (EOL March 2026), using loki.source.kubernetes + selective labelmap for Loki's 15 label limit
- Blackbox-exporter: Uses hostAliases for internal HTTPS probes (hairpin NAT fix)
- Istio: ServiceMonitor (istiod/15014) + PodMonitor (ztunnel/15020) scraping via kube-prometheus-stack
- Ingress NGINX: 7 PrometheusRule alerts + Grafana dashboard (23 panels, PR #498)
- Loki log-based alerting: 9 LogQL rules in 4 groups via embedded ruler (PR #489)
- All targets healthy, zero down (metrics-server 403 fixed with bearer token auth)
- Custom PrometheusRules: ~70 alerts across 8 rule files

**Dependency Management:** Complete
- Renovate GitHub App deployed
- Weekend schedule (Sat/Sun 6am-9pm)
- Grouped updates: ArgoCD, monitoring, networking, security, backup

**Zot OCI Registry:** ✅ Deployed 2026-04-23, extended 2026-04-25 (PR #595)
- Pull-through cache: Docker Hub, GHCR, quay.io, registry.k8s.io
- ARM64-only sync (`platforms: [{os: linux, arch: arm64}]`) — fast first-pulls (~seconds vs ~41s for multi-platform)
- CVE scanning (built-in Trivy, 2h update interval), Prometheus ServiceMonitor, 50Gi iSCSI PVC
- URL: https://registry.k8s.n37.ca — auth: `admin` + SealedSecret htpasswd
- **Anonymous read enabled:** `accessControl.repositories["**"].anonymousPolicy: ["read"]` — pods pull without imagePullSecrets; admin write remains restricted
- Workloads routing through Zot: both argo-workflow CronWorkflows, trivy compliance-reporter, all 3 external-dns deployments (19 image refs)
- **Gotcha:** First pull blocks until on-demand sync completes. ARM64 filter is critical — without it, all 12+ platform variants are downloaded (~41s for nginx:latest)
- **Gotcha:** Path format is flat (no upstream prefix). `registry.k8s.n37.ca/registry.k8s.io/image` would require Zot `destination` field in sync config — without it, that path fails. Use `registry.k8s.n37.ca/image` directly.
- **PRs:** #571 (deployment), #572 (ingress-nginx egress fix + arm64 filter), #595 (anonymous read + workload routing)

**oauth2-proxy:** ✅ Deployed 2026-04-23 (PR #576)
- GitHub OAuth provider, restricted to user `imcbeth`, cookie domain `.k8s.n37.ca`
- Uptime Kuma (status.k8s.n37.ca) protected immediately
- Add 3 annotations to any ingress to protect additional services
- `auth-url` uses internal ClusterIP to avoid hairpin NAT

**Uptime Kuma:** ✅ Deployed 2026-04-23 (PR #573)
- Status page at https://status.k8s.n37.ca — monitors all cluster services
- Helm chart v2.25.0 (app v1.23.17), 5Gi iSCSI PVC (synology-iscsi-delete), Recreate strategy
- WebSocket via native ingress-nginx support (proxy-read/send-timeout: 3600)

**Grafana Tempo:** ✅ Deployed 2026-04-23 (PR #574)
- Distributed tracing (monolithic mode), chart v1.24.4 (app v2.9.0), 10Gi iSCSI PVC, 7-day retention
- OTLP via Alloy (loki namespace) as single collector → Tempo; apps send to Alloy :4317
- Grafana datasource auto-discovered; trace↔logs (Loki uid: loki) + trace↔metrics (Prometheus) correlation
- Loki datasource given fixed `uid: loki` so cross-datasource links resolve

**Network Policies:** Complete (22 namespaces, oauth2-proxy added)
- Covered: localstack, unipoller, loki, trivy-system, velero, argo-workflows, cert-manager, external-dns, metallb-system, ingress-nginx, istio-system, gatekeeper-system, falco, default, argocd, synology-csi, kube-system, tigera-operator
- Remaining uncovered: calico-system (Gatekeeper-exempted), kube-node-lease, kube-public, secrets-source, velero-test (all empty or system-managed)
- DNS egress rules fixed across all policies (AND semantics, not OR)
- ArgoCD Application at sync-wave -40
- **Gotcha:** K8s API egress requires both ClusterIP (10.96.0.1:443) AND control plane network (10.0.10.0/24:6443)
- **Gotcha:** Ambient mesh namespaces need bare port 15008 ingress/egress rules + link-local 169.254.7.127/32 health probe
- **Gotcha:** DNS egress must use AND semantics (namespaceSelector + podSelector in same list item), not OR (separate items)
- **Gotcha:** Calico IPIP encapsulation rewrites source IP for cross-node traffic; `ipBlock` rules unreliable for matching node IPs. Use bare port rules for API server → webhook traffic.

**Argo Workflows:** Deployed (2026-01-24)
- Argo Workflows v3.7.8 (Helm chart 0.47.3) at sync-wave -8
- B2 artifact storage working (PRs #287-289 fixed credentials)
- NetworkPolicy enabled (PR #291 fixed K8s API egress)
- UI accessible at https://workflows.k8s.n37.ca (PR #293)

**ArgoCD:** 39 apps — all Synced+Healthy ✅ including strimzi-operator, flink-operator, kafka, flink-demo (as of 2026-05-31).
- flink-demo: both FlinkDeployments running. file-to-kafka FINISHED/STABLE (batch), kafka-to-s3 RUNNING/STABLE (streaming).
- argo-cd chart 9.5.3, kube-prometheus-stack 83.7.0, external-dns v0.21.0, unipoller v2.39.0 (all updated 2026-04-21)
- ingress-nginx migrated from Kustomize to Helm chart (v4.14.3) via ArgoCD
- ServerSideApply drift fully resolved for istio-ztunnel and tigera-operator
- Server-Side Apply enabled on ArgoCD itself (#376)

**External-DNS:** Fixed (2026-01-25), expanded 2026-04-18
- Root cause: domain-filter=k8s.n37.ca rejected the n37.ca zone
- Fix: Changed to domain-filter=n37.ca (PRs #295-296)
- All 4 A records + TXT ownership records now auto-managed
- Both Cloudflare + UniFi deployments now also manage `lifeonabike.ca` (PR #553)

**lifeonabike.ca:** Deployed 2026-04-18
- ArgoCD app `lifeonabike` Synced+Healthy (sync-wave 5)
- TLS cert `lifeonabike-ca-tls` READY=True (LE R12 prod, valid Apr 18 – Jul 17 2026)
- Covers both `www.lifeonabike.ca` + `lifeonabike.ca` (apex SAN)
- External-DNS (Cloudflare + UniFi) will manage A records from Ingress annotations
- **Next step**: Add Ingress to `lifeonabike` namespace when web backend is ready

**Istio Ambient Mesh:** Updated (2026-03-01)
- Upgraded from 1.28.4 → 1.29.0 (Renovate PR #469)
- 29 pods across 6 namespaces with mTLS (HBONE protocol)
- Namespaces: default, loki, argo-workflows, localstack, unipoller, trivy-system
- Resource usage: ~38m CPU, ~145Mi memory (istiod + cni + ztunnel)
- Waypoint proxies: Skipped (L4 mTLS sufficient, add later if L7 needed)
- 1.29.0 changes: DNS capture default on, iptables reconciliation auto-enabled, GOMEMLIMIT auto-set
- **Gotcha:** ztunnel tunnels ALL inter-pod traffic through port 15008, rewriting dest port. NetworkPolicies need bare port 15008 ingress/egress rules (not namespace-scoped). Also need link-local 169.254.7.127/32 for ztunnel health probes.

**Argo Workflows Alerting:** Complete (2026-01-30)
- 8 PrometheusRule alerts deployed (PR #354)
- Alerts: Failed, Error, ControllerErrors, Stuck, QueueBacklog, NotLeader, Down, HighFailureRate
- All alerts active in Prometheus, currently inactive (healthy state)

**Calico APIServer:** Deployed (2026-02-05, updated 2026-02-15)
- APIServer CR enables v3 API for operator IPPool management
- Fixed IPPool ownership error (RestoreV3Metadata annotation fix)
- CPU limit bumped from 100m to 250m to prevent burst handler timeouts

**OPA Gatekeeper:** Enforcing (2026-02-15)
- Helm chart 3.21.1, sync-wave -6
- 2 ArgoCD apps: `gatekeeper` (Helm + ConstraintTemplates) and `gatekeeper-policies` (Constraints)
- 5 ConstraintTemplates, 5 Constraints (deny mode, 0 violations)
- PodMonitor + Grafana dashboard for metrics
- NetworkPolicy configured for gatekeeper-system
- require-resource-limits exclusions: kube-system, calico-system (tigera-operator removed 2026-04-17 — resource limits added via Kustomize patch, PR #543)

**Phase 4 Status:** In Progress
- Storage performance + network utilization dashboards deployed
- SealedSecrets key rotation enabled (30d)
- OPA Gatekeeper in deny mode (0 violations)
- OOM fixes: Grafana sidecars (256Mi), Loki sidecar/canary, Falco redis (1536Mi/2Gi + 30d TTL + 1000mb maxmemory)
- Resource right-sizing audit complete (7 workloads adjusted, net +928Mi requests)
- ArgoCD MCP RBAC configured (readonly for MCP service account)
- k8s-docs-n37 documentation synced (PR #64, #66 merged)
- Trivy vulnerability dashboard complete (scanning, alerts, Grafana panels)
- Renovate dependency updates deployed (kube-prometheus-stack 82.4.3, trivy-operator 0.32.0)
- Force=true/SSA incompatibility fixed (PR #426)
- Istio Prometheus monitors deployed (PR #428)
- metrics-server 403 Forbidden scraping fixed (PR #434)
- APM dashboard updated with Istio service mesh section (PR #435)
- Ingress-nginx hardened: security headers, rate limiting (PR #436), Helm migration (PR #441)
- NetworkPolicies expanded to 11 namespaces (ingress-nginx + istio-system added, DNS fix across all 11)
- Gatekeeper exclusions audited: 10 → 2 remaining (resource limits added to 8 namespaces)
- Linkerd dead code removed (never deployed, Istio Ambient is production mesh)
- Falco Redis PV expanded 1Gi → 2Gi (was 99% full, PR #473)
- Blackbox-exporter ICMP egress Calico NetworkPolicy added (PR #462)
- Renovate safe batch merged: Velero, cert-manager, MetalLB, ingress-nginx, Loki, external-dns
- synology-csi Kustomize patch namespace fixed (kube-system, not synology-csi)
- Falco Redis OOMKill resolved (memory 1536Mi/2Gi, 30d TTL, PRs #478, #481)

---

## Recent Sessions

### 2026-05-31: Flink Demo Pipeline — End-to-End Working (file→Kafka→S3)

**Completed Work:**

**Three bugs fixed across three PRs to get the pipeline end-to-end:**

**PR #637: flink-webhook OOMKill (128Mi → 256Mi)**
- The flink-webhook JVM was OOMKilling at 128Mi during TLS crypto ops, causing EOF on every API server webhook call → FlinkDeployments couldn't be created.
- Fix: `webhook.resources.limits.memory: 256Mi` in `manifests/base/flink-operator/values.yaml`

**PR #638: FlinkDeployment memory 512m → 1Gi**
- With `resource.memory: "512m"`, JVM overhead (192mb) + JVM Metaspace (256mb) = 448mb, leaving only 64mb for Total Flink Memory vs 128mb off-heap default.
- Error: `Total Flink Memory (64mb) < Off-heap Memory (128mb)`
- Fix: Changed jobManager and taskManager memory to `"1Gi"` in both FlinkDeployment YAMLs.

**PR #639: `env.from_collection()` type_info=Types.STRING()**
- Without explicit type info, PyFlink uses Kryo to serialize elements. Kryo serializes Python strings as Java byte arrays (`[B`). KafkaSink's `SimpleStringSchema.serialize()` then fails casting `[B` → `String`.
- Error: `ClassCastException: class [B cannot be cast to class java.lang.String`
- Fix: `env.from_collection(records, type_info=Types.STRING())` in `pipeline-file-to-kafka-configmap.yaml`

**Also fixed: Dockerfile pemja build issue (previous session, image build)**
- `pemja==0.4.1` requires JDK headers, GCC, Python headers to compile C extension.
- Added `openjdk-17-jdk-headless`, `build-essential`, `python3-dev` + header symlink.

**Final verified state:**
- `flink-events:0:15` — 15 JSON records in Kafka ✅
- `s3://flink-output/events/2026/05/31/14/*.json` — 15 individual JSON files in LocalStack S3 ✅
- `file-to-kafka` FlinkDeployment: FINISHED/STABLE ✅ (batch job, replays on restart)
- `kafka-to-s3` FlinkDeployment: RUNNING/STABLE ✅ (streaming, consuming new messages)
- colima stopped ✅

**Key Gotchas Discovered:**
- **flink-webhook JVM needs ≥256Mi**: TLS crypto is memory-intensive. 128Mi causes OOMKill → EOF on all webhook calls.
- **Flink memory model minimum**: With 1Gi, breakdown is: JVM Overhead 192mb + JVM Metaspace 256mb + JVM Heap 448mb + Off-heap 128mb = 1024mb. 512mb leaves only 64mb for Flink which is below the 128mb off-heap default.
- **PyFlink from_collection() type safety**: Always pass `type_info=Types.STRING()` (or appropriate type) to `env.from_collection()`. Without it, Kryo serialization converts Python strings to `[B` byte arrays, breaking any Java-side String sink.
- **FAILED FlinkDeployment restart**: The operator doesn't restart a FAILED job on ConfigMap change — it requires a spec change. Delete the old JobManager pod to force the Deployment controller to recreate it; the new pod picks up the updated ConfigMap.

**Pull Requests:**
- **PR #637:** [Merged] fix: increase flink-webhook memory limit to 256Mi (OOMKill)
- **PR #638:** [Merged] fix: bump FlinkDeployment memory from 512m to 1Gi
- **PR #639:** [Merged] fix: add type_info=Types.STRING() to from_collection in file-to-kafka

---

### 2026-05-30: Kafka + Flink Demo Infrastructure — PR Reviews, Deployment, Post-Merge Fixes

**Completed Work:**

**PR Reviews + Fixes (#617, #618):**
- Resolved all 15 Copilot review comments across both PRs with code fixes and reply comments
- Key fixes: CLAUDE.md sealed-secret filename (`*-sealed.yaml` required to avoid git-crypt and yamllint), ValidatingWebhookConfiguration ignoreDifferences for flink-operator, webhook name corrected to `flink-operator-flink-operator-webhook-configuration`, removed `path:` from ref-only ArgoCD sources, LocalStack hook `exit 1` on failure, Dockerfile script duplication removed
- PR #617 merged by user; PR #618 rebased onto updated main (CLAUDE.md + kustomization.yaml conflicts resolved)
- PR #618 merged; all 4 ArgoCD Application manifests applied via `kubectl apply`

**Post-Merge Infrastructure Fixes (PRs #629–#634):**
- **PR #629:** `kafka version: 3.9.0 → 4.1.2` (Strimzi 1.0.0 only supports Kafka 4.x); added `ignoreDifferences` for Flink CRD `spec.conversion.strategy=None` drift (Kubernetes adds this after SSA apply)
- **PR #630:** Added strimzi-system → kafka ingress on 9091/9092 (NetworkPolicy was blocking Strimzi AdminClient)
- **PR #631:** Added port 9090 (KRaft CONTROLPLANE) to kafka NP and strimzi-system NP. Root cause: Strimzi's `describeMetadataQuorum` AdminClient connects to bootstrap (9092), discovers controller at `CONTROLPLANE-9090://...` from metadata, then tries port 9090
- **PR #632:** Attempted startup probe for user-operator via `spec.entityOperator.template.userOperatorContainer.startupProbe` — rejected by ArgoCD SSA: "field not declared in schema". Only `env`, `securityContext`, `volumeMounts` are available in that template.
- **PR #633:** Removed `spec.entityOperator.userOperator` — Strimzi 1.0.0's user-operator liveness probe (`initialDelaySeconds=10`, `failureThreshold=3`) kills the container at ~30s before ARM64 JVM + AdminClient init completes (~35s). No KafkaUser CRDs needed for demo, so omitting it is clean.
- **PR #634:** Added `istio.io/dataplane-mode: ambient` to all 4 new namespace manifests (kafka, strimzi-system, flink-operator, flink-demo)

**Key Gotchas Discovered:**
- Strimzi 1.0.0 entity-operator bootstrap uses port 9091 (REPLICATION/internal TLS), not 9092. NetworkPolicy intra-kafka rules must include 9091.
- Strimzi `describeMetadataQuorum` AdminClient connects to bootstrap (9092) then follows controller endpoint to CONTROLPLANE-9090. Both ports need NetworkPolicy egress from strimzi-system.
- Strimzi 1.0.0 Kafka CRD only exposes `env`, `securityContext`, `volumeMounts` in `spec.entityOperator.template.userOperatorContainer` — no probe fields. Cannot configure startupProbe via CR.
- User-operator tini `-e 143` maps SIGTERM (exit 143) to exit 0, so CrashLoopBackOff shows `exitCode: 0, reason: Completed` — looks like clean exit but is actually liveness probe kill.
- Flink CRD drift: `spec.conversion.strategy=None` added by Kubernetes after SSA apply; not in chart. Add `apiextensions.k8s.io/CustomResourceDefinition` ignoreDifferences with `.spec.conversion` jqPathExpression.

**Current Cluster State (end of 2026-05-31 continued session):**
- kafka-cluster-combined-0: Running 1/1 ✅ (Kafka 4.1.2, KRaft mode)
- kafka-cluster-entity-operator: 1/1 Running ✅ (topic-operator only, user-operator removed)
- kafka CRD: `READY: True` ✅
- strimzi-operator: Synced+Healthy ✅
- flink-operator: Synced+Healthy ✅
- network-policies: Synced+Healthy ✅ (with all 4 new namespaces, bare HBONE rules)
- kafka: Synced+Healthy ✅
- flink-demo: OutOfSync (FlinkDeployments Missing — Docker image `registry.k8s.n37.ca/flink-demo:1.0.0` build in progress via colima)

**Pending (next session):**
- Verify flink-demo FlinkDeployments deploy once image is pushed
- Check `kubectl get flinkdeployment -n flink-demo` shows READY
- Verify file-to-kafka and kafka-to-s3 pipelines are running
- Stop colima when done: `colima stop`

**Pull Requests (all sessions):**
- **PR #617:** [Merged by user] feat: Strimzi + Flink operator infrastructure
- **PR #618:** [Merged] feat: Kafka cluster + Flink demo pipeline (file→Kafka→S3)
- **PR #629:** [Merged] fix: Kafka 4.1.2 for Strimzi 1.0.0 + Flink CRD conversion drift
- **PR #630:** [Merged] fix: allow strimzi-system ingress to kafka on 9091/9092
- **PR #631:** [Merged] fix: add KRaft CONTROLPLANE port 9090 to kafka and strimzi-system NPs
- **PR #632:** [Merged] fix: attempted startup probe (field not in schema — superseded by #633)
- **PR #633:** [Merged] fix: remove user-operator from entity operator
- **PR #634:** [Merged] fix: add Istio ambient mesh labels to all 4 new namespaces
- **PR #635:** [Merged] fix: use bare egress rule for ztunnel HBONE port 15008 in all 4 new namespaces

---

### 2026-05-31: Bare HBONE Egress Fix — Kafka READY, Flink Image Build

**Completed Work (continuation of 2026-05-30 session):**

**Root Cause: ztunnel HBONE NetworkPolicy (PR #635):**
- After PR #634 enrolled 4 new namespaces in Istio Ambient, kafka topic-operator started crashing with "Connection to kafka-bootstrap:9091 terminated during authentication"
- Kafka broker logs showed NO incoming connections — traffic dropped before reaching the broker
- ztunnel access log revealed: `error="connection timed out, maybe a NetworkPolicy is blocking HBONE port 15008"` from entity-operator pod IP to broker pod IP:15008
- Root cause: ztunnel sends HBONE **from within the pod's network namespace** (using the pod's source IP), so pod NetworkPolicies DO apply. But the HBONE destination is the broker pod's IP on port 15008 — NOT an `istio-system` pod IP. The old namespace-scoped rule `to: istio-system, port: 15008` never matched.
- Fix: Split Istio egress into two rules in all 4 namespace NetworkPolicies:
  - Port 15008: bare rule (no `to` selector) — allows ztunnel HBONE to any destination
  - Ports 15012/15017: namespace-scoped to istio-system — istiod xDS/webhook
- Also fixed for strimzi-system, flink-operator, flink-demo (same pattern)
- Pushed via HTTPS (gh auth setup-git + remote URL change). PR #635 created and merged.

**ArgoCD selfHeal revert issue:**
- First `kubectl apply` was reverted by ArgoCD within ~30s (selfHeal: true). Had to push the fix to git and trigger ArgoCD refresh with `kubectl annotate app network-policies argocd.argoproj.io/refresh=hard`.

**Kafka is fully healthy:**
- `kubectl get kafka -n kafka` → `READY: True` ✅
- `kafka-cluster-entity-operator-dcf64c79-dhq2z`: 1/1 Running, 0 restarts ✅
- Kafka ArgoCD app: Synced+Healthy ✅

**localstack-flink-setup job also fixed:**
- The same HBONE issue was blocking the flink-demo PreSync job from reaching LocalStack (cross-node traffic on port 15008 blocked)
- After PR #635, job completed successfully: `s3://flink-output` bucket created ✅

**Flink Docker image build:**
- Docker Desktop not running; started colima (`colima start --arch aarch64`)
- Build in progress: `DOCKER_HOST=unix://$HOME/.colima/default/docker.sock bash build-and-push.sh`
- Building `registry.k8s.n37.ca/flink-demo:1.0.0` for linux/arm64

**Key Gotchas Discovered:**
- **ztunnel HBONE uses pod network namespace**: ztunnel sends HBONE connections with the SOURCE POD'S IP (not ztunnel's hostNetwork IP). Therefore Calico NetworkPolicies DO apply to HBONE traffic. Bare egress rule for port 15008 is needed because the DESTINATION is the target pod's IP on port 15008, not an istio-system pod.
- **ArgoCD selfHeal reverts kubectl apply in ~30s**: For NetworkPolicy fixes in ambient mesh clusters, `kubectl apply` is only useful for testing. Must commit and push to git for permanent effect. Use `kubectl annotate app <name> -n argocd argocd.argoproj.io/refresh=hard` to force immediate re-poll.
- **HTTPS push workaround**: `gh auth setup-git` + `git remote set-url origin https://github.com/...` allows push when SSH key isn't loaded.

**Pull Requests:**
- **PR #635:** [Merged] fix: use bare egress rule for ztunnel HBONE port 15008 in all 4 new namespaces

---

### 2026-05-02/03: ArgoCD SSO Fix, chaos-mesh Recovery, Argo Workflows v4, oauth2-proxy Login Fix

**Completed Work:**

**ArgoCD GitHub SSO — users saw no apps after login (PR #609, merged):**
- Root cause: default `scopes: '[groups]'` + empty GitHub `groups` claim = `g, imcbeth, role:admin` never fired
- Fix: added `scopes: '[preferred_username]'` to `manifests/base/argocd/argocd-config.yaml`

**chaos-mesh — all pods on node04 crashing (node04 image corruption):**
- Root cause: containerd content store corruption on node04; chaos-mesh images resolved to `pause:latest`
- Fix: tainted node04 → deleted Deployment pods → `crictl rmi` all chaos-mesh images via debug pod → untainted → fresh pull

**Argo Workflows v4 CronWorkflow fix (PR #610, open):**
- Root cause: v4.0 renamed `schedule:` (string) → `schedules:` (array); both CronWorkflows used old format → silently never fired
- Fix: updated both `cluster-healthcheck-workflow.yaml` and `backup-validation-workflow.yaml`
- Also fixed: removed `path:` from ref-only source in `manifests/applications/argo-workflows.yaml` to stop duplicate resource warnings
- **Pending merge + `kubectl apply -f manifests/applications/argo-workflows.yaml`**

**oauth2-proxy login redirect — all 3 protected ingresses returned blank 401 (PR #611, merged):**
- Root cause: `$escaped_request_uri` not in ingress-nginx v1.14.3 nginx variable allowlist → auth-signin annotation silently rejected → no `error_page 401` redirect generated in nginx.conf
- Fix: changed `$scheme%3A%2F%2F$host$escaped_request_uri` → `$scheme://$host$uri` in all 3 ingresses
- Used `$uri` (not `$request_uri`) to avoid `&` in query strings breaking the `rd=` parameter
- Affected: `argo-workflows/argo-workflows-ingress`, `falco/falco-ui-ingress`, `uptime-kuma/values.yaml`

**Key Gotchas:**
- ingress-nginx v1.14.x has a strict nginx variable allowlist for `auth-signin`; `$escaped_request_uri` is NOT on it → annotation silently rejected, no redirect generated
- Use `$scheme://$host$uri` (not `$request_uri`) in `auth-signin` `rd=` param to avoid `&` in query strings breaking redirect

**Pull Requests:**
- **PR #609:** [Merged] fix: set argocd rbac scopes to preferred_username for GitHub SSO
- **PR #610:** [Open] fix: update CronWorkflows to v4 schedules array, fix duplicate resources — needs merge + kubectl apply
- **PR #611:** [Merged] fix: replace $escaped_request_uri with $uri in oauth2-proxy auth-signin

---

### 2026-04-23 (Session 3): oauth2-proxy GitHub Authentication

**Completed Work:**

**oauth2-proxy (PR #576, merged):**
- `manifests/applications/oauth2-proxy.yaml` — ArgoCD Application, sync-wave -3, three-source pattern
- `manifests/base/oauth2-proxy/values.yaml` — GitHub provider, `github-user: imcbeth`, cookie domain `.k8s.n37.ca`, `upstream: static://202` (validate-only), `skip-provider-button: true`
- `manifests/base/oauth2-proxy/oauth2-proxy-secret-sealed.yaml` — client-id, client-secret, cookie-secret sealed for `oauth2-proxy` namespace
- `manifests/base/network-policies/oauth2-proxy/namespace.yaml` + `network-policy.yaml` — namespace pre-created for network-policies app (wave -40); ingress from ingress-nginx :4180; egress to GitHub API (0.0.0.0/0:443 excluding RFC1918)
- Updated ingress-nginx NetworkPolicy: egress to oauth2-proxy :4180 for auth_request subrequests
- Updated Uptime Kuma ingress: `auth-url` (internal ClusterIP), `auth-signin` (external), `auth-response-headers`

**Key Gotchas:**
- `auth-url` must use internal ClusterIP (`oauth2-proxy.oauth2-proxy.svc.cluster.local:4180`) not the external hostname — external URL causes hairpin NAT issues (same pattern as blackbox-exporter)
- Always add `namespace.yaml` to `network-policies/` when adding a new namespace NetworkPolicy — the network-policies app runs at wave -40 before any app creates the namespace

**Adding auth to future services:** Add these 3 annotations to any ingress:
```
nginx.ingress.kubernetes.io/auth-url: "http://oauth2-proxy.oauth2-proxy.svc.cluster.local:4180/oauth2/auth"
nginx.ingress.kubernetes.io/auth-signin: "https://oauth.k8s.n37.ca/oauth2/start?rd=$scheme://$host$uri"
nginx.ingress.kubernetes.io/auth-response-headers: "X-Auth-Request-User,X-Auth-Request-Email"
```
Note: `$escaped_request_uri` is NOT in ingress-nginx v1.14.x's allowlist — use `$uri` (path only). `$request_uri` works but breaks if the URL has `&` in query params.

**Pull Requests:**
- **PR #576:** [Merged] feat: deploy oauth2-proxy with GitHub authentication

---

## Session Archive Index

| Date | Title | Key Topics |
|------|-------|------------|
| 2026-04-23 | [Uptime Kuma, Grafana Tempo, Zot Docs](sessions/2026-04-23-uptime-kuma-tempo-zot-docs.md) | WebSocket via timeout annotations, tracesToLogs, cross-datasource uid, three-source ArgoCD pattern |
| 2026-04-23 | [Zot OCI Registry Deployment + Pull-Through Fix](sessions/2026-04-23-zot-registry-deployment.md) | ARM64 platform filter, ingress-nginx egress per-backend, *-sealed.yaml naming |
| 2026-04-22 | [Chaos Mesh 2.8.2 Sync Drift Resolution](sessions/2026-04-22-chaos-mesh-sync-drift.md) | jqPathExpressions vs jsonPointers+SSA, cluster-scoped group field, randAlphaNum pin |
| 2026-04-21 | [Housekeeping + Healthcheck Verification](sessions/2026-04-21-housekeeping-healthcheck.md) | CronWorkflow TTL counter decrement, Renovate ignoreDeps, branch sync |
| 2026-04-21 | [Renovate Batch, Loki btrfs Fix](sessions/2026-04-21-renovate-batch-loki-btrfs-fix.md) | unipoller v2.39.0 safe after UDR recovery, loki btrfs RO, Application manifest apply pattern |
| 2026-04-19 | [Alert False Positives, UDR Recovery, Healthcheck Fix](sessions/2026-04-19-alert-false-positives-udr-recovery.md) | Loki ruler self-scan, LocalStack Trivy false positive, btrfs RO recovery, velero schedule name fix |
| 2026-04-18 | [lifeonabike.ca DNS + TLS, Velero Validation, cert-manager Fix](sessions/2026-04-18-lifeonabike-velero-cert-manager.md) | DNS-01 split-horizon fix, lifeonabike.ca cert issued, velero v1.18.0 validated |
| 2026-04-17 | [tigera-operator, iSCSI PVC Protection, Always-On Monitoring](sessions/2026-04-17-tigera-iscsI-pvc-protection-monitoring.md) | Prune+SSA PVC orphan bug fixed, cluster-healthcheck CronWorkflow, Mac LaunchAgent |
| 2026-04-17 | [Cluster Health + Renovate Batch](sessions/2026-04-17-cluster-health-renovate-batch.md) | iSCSI recovery x3, 8 Renovate PRs, velero v1.18.0 blocked |
| 2026-03-25 | [Prometheus Recovery, VPA, DR Workflow, Velero Fix](sessions/2026-03-25-prometheus-recovery-vpa-velero-fix.md) | VolumeAttachment mismatch fix, VPA deployed, velero binary/CRD root cause |
| 2026-03-12 | [TODO Cleanup, Renovate Batch, Monitoring Stack Upgrade](sessions/2026-03-12-todo-cleanup-renovate-monitoring-upgrade.md) | HookSucceeded race fix, kube-prometheus-stack 82.10.3, 25 apps Synced |
| 2026-02-27 | [Renovate Batch, Health Review, Critical Fixes](sessions/2026-02-27-renovate-health-review-critical-fixes.md) | Falco Redis OOM, synology-csi Kustomize namespace fix, Pi-hole removal |
| 2026-02-28 | [Cluster Shutdown/Startup, NAS Maintenance](sessions/2026-02-28-cluster-shutdown-startup.md) | metrics-server port 4443→10250, stuck hooks, /cluster-shutdown skill |
| 2026-03-01 | [Istio 1.29.0 Upgrade, Webhook & Blackbox Fix](sessions/2026-03-01-istio-upgrade-webhook-blackbox.md) | istiod bare port rule, redundant probe removal |
| 2026-03-01p | [Promtail → Grafana Alloy Migration](sessions/2026-03-01-promtail-to-alloy-migration.md) | EOL migration, loki.source.kubernetes, port 3101→12345 |
| 2026-02-15e | Gatekeeper Violations, Renovate & Hook Fix | 96 violations resolved, MetalLB limits, BeforeHookCreation |
| 2026-02-15p | Istio/APM Alerting & NetworkPolicy Expansion | 13 Istio + 8 APM alerts, 5 new NetworkPolicies |
| 2026-02-15 | Webhook Timeout Fix, Calico CPU & Alert Fix | IPIP/ipBlock bare port, calico-apiserver 250m, PromQL or fix |
| 2026-02-14 | Ingress Helm, Linkerd Cleanup, Gatekeeper Audit | Helm migration, DNS AND fix, 10→2 exclusions |
| 2026-02-13e | Istio Prometheus ServiceMonitors | istiod/ztunnel monitors, metrics-server 403 fix, APM dashboard |
| 2026-02-13 | Documentation Sync, Renovate Deploy & Force/SSA Fix | k8s-docs-n37 sync, Force=true/SSA incompatibility, Renovate deploys |
| 2026-02-11 | Resource Right-Sizing Audit | 7 workloads adjusted, trivy value path bug, StatefulSet VCT |
| 2026-02-08 | Trivy Scanning & Ambient Mesh NetworkPolicy | HBONE port 15008 fix, scan job labels, 5 namespace policies |
| 2026-02-07e | ArgoCD MCP RBAC Fix | MCP readonly policy, redis-secret-init stuck sync |
| 2026-02-07 | OOM Fixes, Gatekeeper Deny Mode & Docs Sync | 12 violations fixed, deny mode, OOMKill fixes |
| 2026-02-06 | OPA Gatekeeper Deployment | 5 policies, dryrun mode, CRD ordering split |
| 2026-02-05e | Storage Dashboard, Tigera Fix & Cleanup | Grafana dashboards, Calico APIServer, key rotation |
| 2026-02-05 | ArgoCD ServerSideApply OutOfSync Fixes | ignoreDifferences, ztunnel+tigera defaults, 22/22 Synced |
| 2026-01-30 | Dependency Updates, Docs & Argo Alerts | Renovate PRs, Istio 1.28.3, 8 workflow alerts |
| 2026-01-29 | Monitoring Fixes & Docs | Metrics-server, Trivy, hairpin NAT, learned skills |
| 2026-01-28 | Istio ArgoCD Sync & Labels | ignoreDifferences, Promtail labelmap, HBONE NetworkPolicies |
| 2026-01-25 | External-DNS, Grafana & Promtail | Domain-filter fix, fsGroup race, K8s API egress |
| 2026-01-24 | Argo Workflows & Network Policies | Deployment, B2 artifacts, ingress, 5 namespace policies |
| 2026-01-23 | Renovate PR Merge & Velero Fix | 20 PRs merged, Velero v1.17 breaking change |
| 2026-01-21 | Restructure CLAUDE_NOTES.md | Modular notes system, 93% reduction |
| 2026-01-14 | Sealed Secrets Ops & Backups | Key backup, B2 restore test, ArgoCD backup |
| 2026-01-14 | Documentation Update - Sealed Secrets | k8s-docs-n37, Security section |
| 2026-01-14 | Secrets Migration Completion | ESO removal, 8 SealedSecrets final |
| 2026-01-14 | Secrets Migration Git-crypt to Sealed | 8 secrets migrated, encryption fixes |
| 2026-01-13 | Secrets Management Evaluation | Sealed Secrets vs ESO, memory comparison |
| 2026-01-12 | Predictive Disk Space & NAS Health Alerts | storage-alerts, predict_linear(), SNMP |
| 2026-01-11 | Major Vulnerability Remediation Day | ArgoCD, MetalLB, CSI upgrades |
| 2026-01-07 | Promtail & Synology CSI Upgrades | Promtail 6.17.1, CSI rollback |
| 2026-01-05 | Trivy Operator Deployment | Security scanning, alerts, dashboard |
| 2026-01-05 | Snapshot-Controller Downgrade | CSI snapshots, v8.x issues |
| 2026-01-05 | Loki Memory Optimization | singleBinary, GOMEMLIMIT, Velero CSI |
| 2025-12-28 | Log-Based Alerting + Dashboards | 43 dashboards, 11 Loki alerts |
| 2025-12-28 | Custom Grafana Dashboards | 4 dashboards, 38 panels |
| 2025-12-27 | Velero + AlertManager SMTP | Backup schedules, email alerts |
| 2025-12-27 | External-DNS Deployment | Cloudflare, UniFi, split-horizon |
| 2025-12-27 | Loki + Promtail Hardening | jqPathExpressions, tolerations |
| 2025-12-26 | Loki + Promtail Deploy | Log aggregation stack |
| 2025-12-26 | Calico hostNetwork Issues | CNI routing limitation |
| 2025-12-26 | Monitoring Stack Fixes | node-exporter, Grafana PVC |

See `.claude/notes/sessions/` for full session details.

---

## Session Documentation Workflow

When documenting a new session:

1. **Add to this file** (CURRENT.md) at the top of "Recent Sessions"
2. **If CURRENT.md has >5 sessions**, move the oldest to a new file in `sessions/`:
   - Name format: `YYYY-MM-DD-slugified-title.md`
   - Add one-line entry to "Session Archive Index"
3. **If new gotchas discovered**, update `.claude/notes/REFERENCE.md`
4. **Update "Current State"** section if project state changed

### Session Template
```markdown
### YYYY-MM-DD (Time of Day): Brief Session Title

**Completed Work:**
- Item 1
- Item 2

**Pull Requests:**
- **PR #XXX:** [Status] Description

**Issues Resolved:**
- Problem → Root Cause → Solution

**Files Modified:**
- `path/to/file.yaml` (description)
```
