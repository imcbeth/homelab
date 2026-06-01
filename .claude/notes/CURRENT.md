# Claude Code - Homelab Current Context

**Last Updated:** 2026-06-01 (Afternoon)
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
- **✅ Velero v1.18.1 running** — Plugin pinned to v1.13.2 (PR #681, 2026-06-01): v1.14.x sends `x-amz-tagging` on every PutObject; Backblaze B2 rejects it. v1.13.2 predates object tagging. Backup verified working end-to-end ✅.

**Monitoring:** Operational — Retention bumped to 30 days (PR #661, 2026-05-31)
- Prometheus: 30d retention (was 10d), AlertManager: 720h (was 120h)
- Loki: 720h retention (was 168h), Tempo: 720h (was 168h)
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

**Zot OCI Registry:** ✅ Deployed 2026-04-23, extended 2026-04-25 (PR #595), credentials rotated 2026-06-01 (PR #675)
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

**Grafana Tempo:** ✅ Deployed 2026-04-23 (PR #574), restored 2026-06-01
- Distributed tracing (monolithic mode), chart v1.24.4 (app v2.9.0), 10Gi iSCSI PVC, 30d retention
- OTLP via Alloy (loki namespace) as single collector → Tempo; apps send to Alloy :4317
- Grafana datasource auto-discovered; trace↔logs (Loki uid: loki) + trace↔metrics (Prometheus) correlation
- Loki datasource given fixed `uid: loki` so cross-datasource links resolve
- **Gotcha:** chart v1.24.4 requires `resources:` under `tempo:` key — top-level `resources:` is silently ignored. Gatekeeper `require-resource-limits` blocked pod until fixed (PR #682).

**Argo Events:** ✅ Deployed + CI pipeline live 2026-05-31 (PRs #662, #664–#678)
- v1.9.10 (Helm chart 2.4.21), JetStream EventBus (NATS 2.10.10, 1 replica, replicas=1 explicit), sync-wave -8
- Controller metrics port 7777 (ServiceMonitor → kube-prometheus-stack in `default` namespace)
- Webhook server enabled (port 12000), Istio Ambient enrolled
- NetworkPolicy: HBONE bare port 15008, Prometheus scrape from `default`, ingress from ingress-nginx+lifeonabike:12000, egress to argo-workflows:2746 and kafka:9092
- **EventSource** `lifeonabike-github`: listens for push to `imcbeth/lifeonabike.ca` main branch, HMAC-verified (SealedSecret), exposed at `https://build-webhook.n37.ca` via Cloudflare Tunnel
- **Sensor** `lifeonabike-build`: submits `lifeonabike-build` WorkflowTemplate in `argo-workflows` on push event
- Workflow artifacts stored in LocalStack S3 bucket `argo-workflows`

**LocalStack:** ✅ Fixed 2026-05-31 (PRs #659, #660)
- CORS: `EXTRA_CORS_ALLOWED_ORIGINS=https://localstack.k8s.n37.ca`
- Persistence: `PERSISTENCE=1` + 2Gi iSCSI PVC (`synology-iscsi-retain`) at `/var/lib/localstack`
- S3 state survives pod restarts; `aws login` no longer triggers NoSuchBucket on startup

**Network Policies:** Complete (23 namespaces — argo-events added 2026-05-31)
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

**ArgoCD:** 40 apps — all Synced+Healthy ✅ (as of 2026-05-31 night). Exception: flink-operator CRD drift (pre-existing, not blocking).
- flink-demo: both FlinkDeployments running. file-to-kafka FINISHED/STABLE (batch), kafka-to-s3 RUNNING/STABLE (streaming).
- **Renovate batch 1 (10 PRs, 2026-05-31):** argo-cd 9.5.11, kube-prometheus-stack 86.1.0, istio 1.29.3, sealed-secrets, velero 12.0.1, busybox all upgraded. ArgoCD self-upgraded during batch (repo-server cycled briefly, auto-recovered).
- **Renovate batch 2 (8+3 PRs, 2026-05-31):** Istio 1.30.0, Alloy 1.8.2, oauth2-proxy chart 10.6.0, Prometheus 3.12.0, synology-csi 1.3.0, csi-attacher 4.12.0, csi-node-driver-registrar 2.17.0, external-snapshotter 8.6.0. Plus flink-operator 1.15.0 (image + chart URL together, PR #656), Flink Dockerfile 2.2 base image.
- **Zot:** chart 0.1.116, app v2.1.17 ✅. StatefulSet recreated (chart removed immutable `serviceName` field; `RespectIgnoreDifferences` didn't prevent SSA managed-field release from triggering admission check — fix was StatefulSet delete → recreate). PVC `zot-pvc-zot-0` (50Gi iSCSI) survived.
- **MetalLB:** 0.16.1 with `frrk8s.enabled: false` ✅. Chart 0.16 enabled frr-k8s BGP backend by default; DaemonSet init containers have no chart-level resource config → blocked by Gatekeeper. Cluster uses L2 mode only, so frr-k8s disabled cleanly.
- ingress-nginx migrated from Kustomize to Helm chart (v4.14.3) via ArgoCD
- ServerSideApply drift fully resolved for istio-ztunnel and tigera-operator
- Server-Side Apply enabled on ArgoCD itself (#376)

**External-DNS:** Fixed (2026-01-25), expanded 2026-04-18
- Root cause: domain-filter=k8s.n37.ca rejected the n37.ca zone
- Fix: Changed to domain-filter=n37.ca (PRs #295-296)
- All 4 A records + TXT ownership records now auto-managed
- Both Cloudflare + UniFi deployments now also manage `lifeonabike.ca` (PR #553)

**lifeonabike.ca:** ✅ Full CI/CD pipeline live 2026-05-31 (PRs #664–#678)
- ArgoCD app `lifeonabike` Synced+Healthy (sync-wave 5)
- TLS cert `lifeonabike-ca-tls` READY=True (LE R12 prod, valid Apr 18 – Jul 17 2026)
- Covers both `www.lifeonabike.ca` + `lifeonabike.ca` (apex SAN)
- **Cloudflare Tunnel** (2 replicas, `cloudflare/cloudflared:2024.10.0`): routes lifeonabike.ca → web:80, build-webhook.n37.ca → argo-events:12000
- Tunnel credentials: SealedSecret `tunnel-credentials` in `lifeonabike` namespace
- Registry creds: SealedSecret `lifeonabike-registry-creds` (in both `lifeonabike` and `argo-workflows` namespaces)
- **Build pipeline**: GitHub push → Argo Events → Sensor → WorkflowTemplate `lifeonabike-build` (clone → Kaniko → rollout-restart)
- Kaniko pushes to `zot.zot.svc.cluster.local:5000` (HTTP, in-cluster) — pod-to-MetalLB HTTPS broken in-cluster
- Workflow pods have `ambient.istio.io/redirection: disabled` (Kaniko + kubectl reach non-mesh endpoints)

**Istio Ambient Mesh:** Updated 2026-05-31 → **1.30.0** (PR #645)
- Path: 1.28.4 → 1.29.0 → 1.29.3 → 1.30.0
- 29+ pods across 10 namespaces with mTLS (HBONE protocol, Ambient mode)
- Namespaces: default, loki, argo-workflows, localstack, unipoller, trivy-system, kafka, strimzi-system, flink-operator, flink-demo
- Waypoint proxies: Skipped (L4 mTLS sufficient, add later if L7 needed)
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

### 2026-06-01 (Afternoon): Cluster Health Check, Tempo Fix, Velero B2 Fix

**Completed Work:**

**Deep cluster health check (fanned-out subagents):**
- All 5 nodes Ready, all DaemonSets at expected counts, metrics API healthy
- Discovered: Tempo pod 0 ready replicas (ArgoCD Application CRD not applied + Gatekeeper blocking pod)
- Discovered: external-dns-unifi 1,598 restarts + unifi-poller 670 restarts — both currently stable; historical accumulation from periodic UniFi controller unavailability. unifi-poller has nil-pointer panic bug in v5.25.0 (`GetPortAnomaliesSite`). No immediate action needed.

**Tempo restored (PR merged inline):**
- Root cause 1: `tempo` ArgoCD Application CRD existed in repo but was never applied → namespace was empty. Fixed: `kubectl apply -f manifests/applications/tempo.yaml`
- Root cause 2: Gatekeeper `require-resource-limits` blocked pod because `resources:` in values.yaml was at top-level — chart v1.24.4 requires it under `tempo:` key
- Fix: moved `resources:`, `extraEnv:`, `podLabels:` under the `tempo:` block in `manifests/base/tempo/values.yaml`
- Result: `tempo-0 1/1 Running` ✅

**Documentation update (PRs #679, #83):**
- Updated `homelab/.claude/notes/CURRENT.md` (PR #679, merged)
- Added `k8s-docs-n37/docs/applications/argo-events.md` — EventBus/EventSource/Sensor architecture, CI pipeline, NetworkPolicy table, Cloudflare Tunnel webhook routing
- Added `k8s-docs-n37/docs/applications/lifeonabike.md` — Cloudflare Tunnel routing, CI/CD pipeline steps, in-cluster Zot HTTP push gotcha, ztunnel ambient bypass
- Updated `k8s-docs-n37/docs/applications/argo-workflows.md` — lifeonabike-build WorkflowTemplate + Artifact Storage sections
- Addressed Copilot review comment: port 80 vs 8080 discrepancy — added callout explaining ingress-nginx connects to pod endpoint (8080) while Cloudflare Tunnel uses Service (80). Components table updated.
- PR #83 merged (k8s-docs-n37, branch `docs/april-2026-updates`)

**Velero B2 backup fix (PR #680, PR #681):**
- PR #680 (merged): added `tagging: ""` to BSL config — **INEFFECTIVE**. AWS SDK sends `x-amz-tagging` header regardless of empty string value.
- PR #681 (merged): pinned `velero-plugin-for-aws` from `v1.14.1` → `v1.13.2`. v1.14.x introduced object tagging and unconditionally sends `x-amz-tagging` on every PutObject. B2 rejects it. v1.13.2 predates tagging entirely.
- Removed ineffective `tagging: ""` line from BSL config.
- Verified: `velero backup create test-b2-pin-fix --wait` → `Phase: Completed` ✅

**Makeup backups (post-fix):**
- `manual-argocd-makeup` → Completed ✅
- `manual-critical-pvcs-makeup` (CSI snapshots: default, loki, trivy-system, falco) → Completed ✅
- Deleted 3 failed/test backups: `test-b2-tagging-fix`, `velero-daily-argocd-20260601013011`, `velero-daily-critical-pvcs-20260601020011`

**Pull Requests:**
- **PR #679:** [Merged] docs: update session notes for lifeonabike CI pipeline + Argo Events
- **PR #680:** [Merged] fix(velero): attempt tagging="" BSL config for B2 — ineffective, superseded by #681
- **PR #681:** [Merged] fix: pin velero-plugin-for-aws to v1.13.2 to restore B2 backups

**Key Gotchas Discovered:**
- **tempo chart v1.24.4: `resources:` must be under `tempo:` key** — top-level is silently ignored by the chart, causing Gatekeeper `require-resource-limits` to block pod creation.
- **velero-plugin-for-aws v1.14.x incompatible with Backblaze B2**: Sends `x-amz-tagging` header on every PutObject. The `tagging: ""` BSL config does NOT suppress it. Only solution is to pin back to v1.13.x until B2 adds support or plugin adds a `disableTagging` option.

---

### 2026-06-01 (Morning): EventSource Filter Fix, Zot Credential Rotation

**Completed Work:**

**EventSource filter fix (PR included in #676–#678 branch):**
- Fixed EventSource expression: `body.ref == 'refs/heads/main'` (was `body.ref` referenced incorrectly — Argo Events body accessor requires the full dot-path)
- Verified push events from GitHub now correctly match main-branch pushes only

**Zot registry credential rotation (PR #675):**
- Rotated admin credentials for Zot OCI registry
- Fixed bcrypt hash encoding in `zot-htpasswd` SealedSecret (incorrect encoding was causing auth failures)
- SealedSecret re-sealed and merged

**HMAC webhook SealedSecret rename (PR #678):**
- Renamed `github-lifeonabike-webhook-secret` SealedSecret file to `lifeonabike-webhook-hmac-sealed.yaml`
- Required because git-crypt catches `*secret*` filenames; sealed files must use `*-sealed.yaml` naming convention

**Pull Requests:**
- **PR #675:** [Merged] chore: rotate Zot registry credentials + fix bcrypt encoding
- **PR #678:** [Merged] fix: rename webhook HMAC SealedSecret to avoid git-crypt encryption

---

### 2026-05-31 (Late Night): lifeonabike Build Pipeline, Cloudflare Tunnel, Workflow Fixes

**Completed Work:**

**lifeonabike build pipeline — WorkflowTemplate + EventSource + Sensor (PRs #664, #667):**
- **WorkflowTemplate** `lifeonabike-build` in `argo-workflows` namespace: 3-step pipeline (clone → kaniko → rollout-restart)
  - Step 1: `alpine/git:2.43.0` shallow-clones `imcbeth/lifeonabike.ca` using github-clone-token PAT, captures git SHA
  - Step 2: Kaniko builds image, pushes `sha` + `latest` tags to `zot.zot.svc.cluster.local:5000/lifeonabike/lifeonabike.ca`
  - Step 3: `alpine/k8s:1.31.0` runs `kubectl rollout restart deployment/web -n lifeonabike`
- **EventSource** `lifeonabike-github`: GitHub push events, HMAC-verified, main-branch only (`body.ref == 'refs/heads/main'`), exposed at `https://build-webhook.n37.ca`
- **Sensor** `lifeonabike-build`: submits WorkflowTemplate with `revision: main` on each push
- **RBAC**: `lifeonabike-workflow-submitter` Role (sensor SA can submit workflows in argo-workflows), `lifeonabike-deployer` Role (argo-workflow SA can `patch deployment` in lifeonabike)

**Argo Workflows fixes:**
- **PR #669 (ztunnel bypass):** Added `ambient.istio.io/redirection: disabled` to workflow pod metadata — Kaniko pushes to Zot HTTP endpoint; kubectl in rollout-restart step talks to K8s API; both are outside the mesh
- **PR #670 (in-cluster Zot push):** Kaniko destination changed to `zot.zot.svc.cluster.local:5000` with `--insecure` flag. Pod-to-MetalLB HTTPS is broken in-cluster (kubelet pulls at node-level are unaffected and still use `registry.k8s.n37.ca`)
- **PR #671 (ingress-nginx egress):** Added egress from ingress-nginx to lifeonabike:8080 for web traffic routing
- **PR #672 (EventBus + artifacts):** Set EventBus JetStream stream replicas=1 (single-node NATS); switched Argo Workflows artifact storage from Backblaze B2 to LocalStack S3 bucket `argo-workflows`; added `localstack-argo-workflows-setup` PreSync Job to ensure bucket exists
- **PR #673 (sealed secrets):** Converted `lifeonabike-registry-creds` and `github-clone-token` to SealedSecrets; also sealed `lifeonabike-registry-creds` in `lifeonabike` namespace

**Cloudflare Tunnel (PRs #676, #677):**
- Deployed `cloudflare/cloudflared:2024.10.0` Deployment (2 replicas) in `lifeonabike` namespace
- ConfigMap routes: `lifeonabike.ca` → `web.lifeonabike.svc.cluster.local:80`, `www.lifeonabike.ca` → same, `build-webhook.n37.ca` → `lifeonabike-github-eventsource-svc.argo-events.svc.cluster.local:12000`
- Removed old webhook Ingress (no longer needed — Cloudflare Tunnel handles external→internal routing)
- SealedSecret `tunnel-credentials` stores tunnel credentials JSON

**Key Gotchas Discovered:**
- **Pod-to-MetalLB HTTPS broken in-cluster**: Kaniko and other in-cluster clients cannot reach `registry.k8s.n37.ca` (MetalLB LoadBalancer IP) via HTTPS from inside the cluster. Use `zot.zot.svc.cluster.local:5000` (HTTP) for in-cluster pushes. Kubelet image pulls (node-level, not pod-level) still use the external hostname fine.
- **ztunnel resets connections to non-mesh destinations**: Workflow pods that push to Zot HTTP or run kubectl need `ambient.istio.io/redirection: disabled` on the pod to bypass ztunnel interception entirely.
- **EventBus replicas must match NATS cluster size**: With a 1-replica EventBus, set `nats.containerTemplate.resources.replicas: 1` explicitly or NATS will try to form a cluster and hang.
- **Cloudflare Tunnel replaces ingress for external webhook**: No public IP or ingress-nginx rule needed — tunnel connects outbound from the cluster to Cloudflare's edge and routes `build-webhook.n37.ca` inward.
- **git-crypt filename rule catches `*secret*`**: Any file with "secret" in the name is git-crypt encrypted. SealedSecret files must use `*-sealed.yaml` suffix to avoid encryption and yamllint failures.

**Pull Requests:**
- **PR #664:** [Merged] feat(lifeonabike): add in-cluster build pipeline + consolidate k8s manifests
- **PR #666:** [Merged] docs: update CLAUDE.md — argo-events sync wave + registry description
- **PR #667:** [Merged] fix(lifeonabike): satisfy Gatekeeper require-labels + private repo auth
- **PR #668:** [Merged] docs: update CURRENT.md
- **PR #669:** [Merged] fix(lifeonabike): bypass Istio ambient ztunnel for build workflow pods
- **PR #670:** [Merged] fix(lifeonabike): push to Zot in-cluster directly, bypass ingress-nginx
- **PR #671:** [Merged] fix: allow ingress-nginx egress to lifeonabike namespace on port 8080
- **PR #672:** [Merged] fix: set eventbus stream replicas=1 and switch artifacts to LocalStack
- **PR #673:** [Merged] chore: seal lifeonabike-registry-creds and github-clone-token secrets
- **PR #676:** [Merged] chore(argo-events): remove webhook ingress, use Cloudflare Tunnel
- **PR #677:** [Merged] fix: use build-webhook.n37.ca for Cloudflare Tunnel + add deploy step

---

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

---

### 2026-05-31 (Evening): Renovate Batch, Zot StatefulSet Fix, MetalLB frr-k8s Disable

**Context:** Resumed from previous context mid-session (session archiving + Renovate batch were already complete). Picked up at the MetalLB frr-k8s Gatekeeper blocking issue.

**Completed Work:**

**MetalLB 0.16 frr-k8s Gatekeeper fix (PR #652, merged):**
- MetalLB 0.16 enabled the `frr-k8s` BGP backend by default, deploying `metallb-frr-k8s` DaemonSet (5 nodes) + `metallb-frr-k8s-statuscleaner` Deployment. Both blocked by OPA Gatekeeper `require-resource-limits` — DaemonSet has 4 init containers (`cp-frr-files`, `cp-reloader`, `cp-metrics`, `cp-frr-status`) with NO chart-level resource configuration.
- Cluster uses L2 mode exclusively (`L2Advertisement`, no `BGPAdvertisement`). Set `frrk8s.enabled: false` in `manifests/base/metal-lb/metallb-metrics-yaml` — cleanly removes both components without any Gatekeeper namespace exclusions.
- After merge: `kubectl apply -f manifests/applications/metal-lb.yaml` → `metal-lb Synced Healthy` ✅

**Zot StatefulSet serviceName fix (PR #651, merged):**
- zot chart 0.1.116 removed `spec.serviceName` from the StatefulSet template. ArgoCD (as SSA field manager `argocd-controller`) previously owned this field. Releasing SSA field ownership triggers Kubernetes StatefulSet admission controller ("spec: Forbidden: updates to statefulset spec for fields other than 'replicas'...")
- Added `ignoreDifferences` for `.spec.serviceName` + `RespectIgnoreDifferences=true` to zot ArgoCD Application — but this did NOT fix the issue. SSA managed-field release still triggers the admission check regardless.
- **Real fix:** Deleted the StatefulSet (`kubectl delete statefulset zot -n zot --wait=false`). ArgoCD immediately recreated it from chart 0.1.116 (without `serviceName`). PVC `zot-pvc-zot-0` (50Gi iSCSI, `synology-iscsi-delete`) survived — VCT PVCs are not tracked by ArgoCD and not deleted when StatefulSet is removed. New pod came up `1/1 Running` within ~7 minutes.
- After merge: `kubectl apply -f manifests/applications/zot.yaml` → StatefulSet delete → `zot Synced Healthy` ✅

**Key Gotchas Discovered:**
- **`RespectIgnoreDifferences` doesn't prevent SSA managed-field release errors**: When a chart REMOVES an immutable field, ArgoCD releases SSA field manager ownership. Even with `RespectIgnoreDifferences=true`, Kubernetes StatefulSet admission controller validates the managed-fields change and rejects it. The only fix for this pattern is StatefulSet delete + recreate.
- **frr-k8s subchart init containers have no resource config**: `frr-k8s` chart init containers (`cp-frr-files`, `cp-reloader`, `cp-metrics`, `cp-frr-status`) copy binaries at startup and cannot have resources configured via Helm values. Gatekeeper `require-resource-limits` blocks the DaemonSet pods. If BGP mode is not needed, `frrk8s.enabled: false` is the cleanest solution.
- **StatefulSet VCT PVCs survive StatefulSet deletion**: Kubernetes does not auto-delete VCT-created PVCs when a StatefulSet is deleted. The new StatefulSet picks up the existing PVC by name (`<vctName>-<stsName>-<ordinal>`). ArgoCD with `prune: true` does not delete them either (VCT PVCs are not in ArgoCD's tracked resources).

**Pull Requests:**
- **PR #651:** [Merged] fix: ignore zot StatefulSet serviceName removed in chart 0.1.116
- **PR #652:** [Merged] fix(metallb): disable frr-k8s backend (L2-only cluster)

**Second Renovate batch (8 PRs, merged same evening):**
- Merged: #641 (alloy 1.8.2), #643 (external-snapshotter 8.6.0), #644 (oauth2-proxy chart 10.6.0), #645 (istio 1.30.0), #646 (prometheus 3.12.0), #647 (csi-attacher 4.12.0), #648 (csi-node-driver-registrar 2.17.0), #649 (synology-csi 1.3.0)
- Applied: `kubectl apply` for istio-base/cni/istiod, alloy, oauth2-proxy (all changed Application manifests); synology-csi auto-synced via base/
- Skipped then fixed #642 + #650 (see below)
- All apps Synced+Healthy post-batch (flink-operator CRD drift pre-existing, not related)

**Third pass — flink-operator 1.15.0 + Flink Dockerfile 2.2 (PRs #642, #650, #656):**
- **#642** (flink-operator image 1.15.0) + **#656** (chart URL `1.14.0` → `1.15.0` archive): merged together so chart CRDs and operator binary stay in sync. Applied `kubectl apply -f manifests/applications/flink-operator.yaml`. Pod immediately rolled to `apache/flink-kubernetes-operator:1.15.0` ✅
- **#650** (Flink Dockerfile `1.20-java17` → `2.2-java17`): merged. No immediate cluster impact — running FlinkDeployments use pre-built `registry.k8s.n37.ca/flink-demo:1.0.0`. Next image rebuild will use Flink 2.2 and will need PyFlink pipeline testing against Flink 2.x APIs.
- **All Renovate PRs closed.** No open Renovate PRs remain.

**Also completed earlier in this context window (session archiving + first Renovate batch):**
- Archived 5 oldest sessions from CURRENT.md into `sessions/` files
- Created kafka.md and flink.md guides in k8s-docs-n37 (PRs #640 and #81, merged)
- Merged 10 Renovate PRs (#619–#628) with `--admin` bypass; applied all Application manifests
- ArgoCD self-upgrade completed during batch (repo-server cycled, auto-recovered)
- Zot 0.1.116 Renovate PR triggered the serviceName issue investigated above

---

## Session Archive Index

| Date | Title | Key Topics |
|------|-------|------------|
| 2026-05-31 | [Flink Demo Pipeline — End-to-End Working (file→Kafka→S3)](sessions/2026-05-31-flink-demo-pipeline-e2e.md) | flink-webhook OOMKill 256Mi, Flink memory 1Gi, PyFlink type_info=Types.STRING() |
| 2026-05-31 | [Bare HBONE Egress Fix — Kafka READY, Flink Image Build](sessions/2026-05-31-bare-hbone-egress-kafka-flink-image.md) | ztunnel HBONE pod network namespace, ArgoCD selfHeal revert, bare port 15008 rule |
| 2026-05-30 | [Kafka + Flink Demo Infrastructure](sessions/2026-05-30-kafka-flink-infrastructure.md) | Strimzi 1.0.0 port 9091, KRaft CONTROLPLANE 9090, user-operator ARM64 liveness, Flink CRD drift |
| 2026-05-02 | [ArgoCD SSO Fix, chaos-mesh Recovery, Argo Workflows v4, oauth2-proxy Login Fix](sessions/2026-05-02-argocd-sso-chaos-mesh-argo-workflows-v4.md) | preferred_username scopes, containerd corruption fix, schedules array, $uri allowlist |
| 2026-04-23 | [oauth2-proxy GitHub Authentication](sessions/2026-04-23-oauth2-proxy-github-auth.md) | GitHub OAuth, static://202 validate-only, auth-url ClusterIP, $uri not $escaped_request_uri |
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
