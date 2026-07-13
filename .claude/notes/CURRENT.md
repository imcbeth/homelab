# Claude Code - Homelab Current Context

**Last Updated:** 2026-07-13 (Chaos-mesh un-suspend + verify script + Falco Redis OOM fix)
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
- Trivy scanning: 96 VulnerabilityReports, 244 ConfigAuditReports, 190 ExposedSecretReports — metrics in Prometheus, Grafana dashboard healthy. Local registry scan fix: added `/32` egress rule for MetalLB IP `10.0.10.10` in trivy-system NetworkPolicy (PR #684, 2026-06-01) — scans of `registry.k8s.n37.ca` images were timing out because that IP fell in the excluded `10.0.0.0/8` private range.
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

**Uptime Kuma:** ✅ Deployed 2026-04-23 (PR #573), monitors seeded + fixed 2026-06-01 (PR #690)
- Status page at https://status.k8s.n37.ca — 15 monitors across 3 groups
- Helm chart v2.25.0 (app v1.23.17), 5Gi iSCSI PVC (synology-iscsi-delete), Recreate strategy
- WebSocket via native ingress-nginx support (proxy-read/send-timeout: 3600)
- **Monitors use internal cluster DNS** — pod-to-MetalLB VIP (10.0.10.10) is broken for non-meshed pods (kube-proxy KUBE-EXT chain only routes `--src-type LOCAL` traffic). All monitors point to ClusterIP service DNS, not `*.k8s.n37.ca` URLs.
- **Gotcha:** kube-proxy LoadBalancer VIP handling: KUBE-EXT chain only fires for `--src-type LOCAL` (node-generated traffic). Pod traffic to MetalLB VIP silently drops after the check fails — no DNAT, packet goes to node network and times out. Meshed pods (via ztunnel HBONE) are unaffected. Non-meshed pods must use ClusterIP DNS.

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

**PVC Read-Only Mount Auto-Remediation:** ✅ End-to-end live as of 2026-06-07
- **Detection**: `pvc-mount-monitor` DaemonSet in `synology-csi` ns reads `/host/proc/1/mounts` and exports `pvc_mount_readonly{node,pvc,...}` gauge for every CSI-backed mount (PR #734 + procfs fix #737). 5 pods, 9 series at steady state.
- **Alerting**: `PVCMountReadOnly` PrometheusRule (critical, 2m sustained `== 1`).
- **Remediation**: `pvc-ro-remediator` CronJob in `synology-csi` ns (every 2m) queries Prometheus for firing alerts, extracts pod UID from mountpoint path, `kubectl delete pod` (PR #735). Protected namespace allowlist for safety.
- **Per-app livenessProbe (defense-in-depth)**: Uptime Kuma (PR #731) + LocalStack (PR #732) do a write-test in their existing probe. Other stateful apps couldn't take this approach (distroless or chart-hardcoded).
- **Total detection-to-recovery**: ~4 min worst case. Beats the hours it took to notice the 2026-06-04 incident manually.
- **NetworkPolicy network path**: required 4 PRs total to wire end-to-end — #736 (syn-csi ingress 9300 for monitor scrape), #738 (default egress 9300), #739/#746 (syn-csi egress 9090 for remediator), #747 (default ingress 9090). The cross-namespace path needs ingress on dest + egress on src EVERY time.

**Argo Workflows:** Deployed (2026-01-24)
- Argo Workflows v3.7.8 (Helm chart 0.47.3) at sync-wave -8
- B2 artifact storage working (PRs #287-289 fixed credentials)
- NetworkPolicy enabled (PR #291 fixed K8s API egress)
- UI accessible at https://workflows.k8s.n37.ca (PR #293)
- **Workspace storage:** `synology-iscsi-delete-ssd` (changed 2026-06-01, PR #685) — Delete policy auto-cleans PVCs on workflow completion; SSD for faster build I/O. Previously defaulted to `synology-iscsi-retain` (HDD) which left orphaned PVs after every build.

**ArgoCD:** 38 apps — all Synced+Healthy ✅ (as of 2026-06-04 — flink-operator CRD drift resolved by PR #722, adding `.spec.versions[].additionalPrinterColumns[].priority` to ignoreDifferences).
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
- **Cloudflare Tunnel** (2 replicas, `cloudflare/cloudflared:2026.5.2`): routes lifeonabike.ca → web:80, build-webhook.n37.ca → argo-events:12000
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

### 2026-07-13: Chaos-Mesh Schedules Un-Suspended with Safety Fixes

Completed the un-suspend of the 4 chaos-mesh Schedules that were disabled 2026-07-12 pending safety review. Applied minimal fixes to prevent recurrence of the self-lockup pattern.

**Universal fix (all 4 Schedules):**
- `startingDeadlineSeconds: 60` — if the cron slot is missed by more than 60s (e.g. controller down), do NOT fire a catch-up run. Prevents the "backlog cascade" that fired network-delay-loki and pod-kill-prometheus immediately when chaos-mesh recovered on 2026-07-12.

**Per-spec fix:**
- **pod-failure-node04** — added `namespaces:` allowlist limiting the target set to user-workload namespaces (`falco, loki, lifeonabike, unipoller, argo-workflows, argo-events`). Chaos-mesh's own components (in the chaos-mesh namespace) are now excluded by omission from the allowlist. Also excludes all critical infrastructure — kube-system, calico-system, istio-system, argocd, metallb-system, cert-manager, gatekeeper-system, and default (Prometheus + Grafana). No other Schedule needed a target-scope fix.

**Chaos-mesh selector gotcha discovered:** the first attempt used `expressionSelectors: [{key: app.kubernetes.io/name, operator: NotIn, values: [chaos-mesh]}]`. Reproducibly returned `"no pod is selected"` even though the semantics are correct per the K8s label-selector spec. Chaos-mesh's implementation apparently doesn't combine `nodeSelectors` with `expressionSelectors` the way I expected. Verified with both plain `NotIn` and `Exists + NotIn` combined — both broken. Working pattern: **positive `namespaces:` allowlist**. Validated with a 15s dry-run — 11 target pods across 6 allowed namespaces, all 3 chaos-mesh pods on node04 kept their real image.

**Pull Requests:**
- **PR #788:** [Merged] Un-suspend Schedules with initial safety fixes (used broken expressionSelectors — fix in #789)
- **PR #789:** [Merged] Fix pod-failure-node04 selector — switch to `namespaces` allowlist

**Next scheduled fires (things to watch):**

| Time (UTC) | Schedule | Expected outcome |
|---|---|---|
| Wed 09:00 | `pod-kill-prometheus` | Prometheus StatefulSet recovers within ~1 min; no iSCSI RO cascade |
| Wed 10:00 | `network-delay-loki` | ip-set application succeeds (chaos-daemon healthy this time) |
| Wed 11:00 | `cpu-stress-unipoller` | Gatekeeper CPU limit holds; unipoller recovers |
| Aug 1 12:00 | `pod-failure-node04` | Only user workloads pause; all 3 chaos-mesh pods on node04 stay Running |

**Verification tooling shipped (PR #791):** `scripts/verify-chaos-week.sh` runs on-demand any time after Wednesday 11:15 UTC and prints per-fire verdicts (✅/⚠️/❌/⏭️) for the 3 weekly schedules plus 4 global cluster health checks (ArgoCD sync, chaos-mesh pod images, ArgoCDApp* alert state, PVC RO count). Uses `AllInjected` + `AllRecovered` conditions + "Failed" injection events on the most recent child experiment as the verdict inputs. On-demand only — no automation depends on it. Dry-run today confirmed 4 globals ✅ and all 3 schedules ⏭️ pre-Wednesday.

**Follow-up (later same day) — Falco Redis OOM fix (PR #793):**

Healthcheck picked up that Falco Redis had been OOMKilling every ~24 min for 21 days (876 restarts). Not new — a longstanding chronic issue, just first noticed today because I was scanning restart counts.

**Root cause:** the falcosidekick chart's key for Redis config overrides is `webui.redis.customConfig` (a LIST of strings), not `webui.redis.config` (a map). Our values file had used `config:` for months; the chart silently ignored it. Live Redis showed `maxmemory: 0`, `maxmemory-policy: noeviction` → grew unbounded until it hit the 2Gi container limit → OOMKill → repeat.

**Fix:** switch to `customConfig: ["maxmemory 1500mb", "maxmemory-policy allkeys-lru"]`. The chart renders this into a ConfigMap with a `redis-stack.conf` file, mounts it at `/redis-stack.conf`, and the redis-stack image auto-loads it. Verified live: `redis-cli CONFIG GET maxmemory` returns `1572864000` (1500 MiB), policy is `allkeys-lru`, restarts back to 0.

**Also cleaned up:** 5 orphaned `PodNetworkChaos` records in the loki namespace, leftover from yesterday's chaos-mesh recovery. Parent NetworkChaos was gone but the per-pod records persisted, generating "unable to flush ip sets" warning events every ~20s for 25 hours.

**Additional gotcha captured:**
- **Helm charts silently drop unknown values keys.** No error, no warning — the chart renders whatever it knows about, extra keys go into `.Values` but are never referenced. When a config change appears to have no runtime effect, verify with `helm template <chart> -f values.yaml` and grep for the expected rendered output before assuming the app is misbehaving. The 21-day Falco Redis chronic OOM was invisible because ArgoCD reported Synced + Healthy the whole time (fresh pod after each OOMKill is still Ready).

**Key Gotchas Captured:**
- **Chaos-mesh selectors don't combine `nodeSelectors + expressionSelectors` cleanly** — silently returns "no pod is selected" instead of an error. Test any complex selector with a short-duration one-shot before scheduling it. Positive allowlists (`namespaces`, `labelSelectors`) are the reliable pattern.
- **`startingDeadlineSeconds` on chaos-mesh Schedules** — same concept as batch CronJob's `startingDeadlineSeconds`. Set to 60s (or similar short value) on every Schedule so cron slots missed during downtime don't fire catch-up runs. `null` (default) means "catch up ALL missed slots on recovery" which is almost never what you want.
- **Falco Redis pod is on node01, not node04** — the original `pod-failure-node04` manifest comment claimed node04 had the Falco Redis PVC. It moved during the 2026-06-21 recovery when we drained node04 for the iSCSI RO cascade. The premise of the experiment changed but the manifest wasn't updated. Reminder: chaos experiment comments/rationale should be reviewed periodically for accuracy against current cluster state.

---

### 2026-07-12: Cluster Healthcheck — chaos-mesh chaos-tested itself for 11 days

**Healthcheck found chaos-mesh in a self-inflicted lockup.** Three chaos-mesh pods (controller-manager, dashboard, chaos-daemon-s8bwr) had accumulated **3130 restarts each** in `RunContainerError`. All had their container image swapped to `gcr.io/google-containers/pause:latest` (chaos-mesh's marker for pod-failure simulation), while the annotation `chaos-mesh-normal` preserved the original `ghcr.io/chaos-mesh/chaos-mesh:v2.8.3`.

**Root cause — `pod-failure-node04` Schedule fired 2026-07-01 with mode: all**:
- cron `0 12 1 * *` (noon on 1st of month)
- selector: `{nodeSelectors: {kubernetes.io/hostname: node04}}`, `mode: all`
- Targeted EVERY pod on node04 including `chaos-daemon-s8bwr` (chaos-mesh's own reconciler)
- With its own daemon paused, chaos-mesh couldn't restore the pause-swap when duration expired → deadlock for 11 days
- ArgoCD showed `chaos-mesh` app `Synced + Progressing` the entire time (not `Healthy`, but not surfaced anywhere obvious)

**Recovery + cascade during recovery:**
1. Force-deleted 3 stuck pods → Deployment/ReplicaSet recreated with correct images
2. When controller came back up, it caught up on missed cron slots and immediately fired:
   - `network-delay-loki` catch-up → PodNetworkChaos records failing with `unable to flush ip sets`. Storm of Warning events. Deleted manually.
   - `pod-kill-prometheus` catch-up → **actually killed Prometheus 7 min into recovery**. Prometheus recovered cleanly this time, no iSCSI RO cascade. Lucky.
3. Investigation revealed 4 active Schedules dating back 81 days, unattended.

**Pull Requests:**
- **PR #769:** [Merged] chore(chaos-mesh): suspend all 4 Schedules pending safety review — removed them from kustomization; ArgoCD pruned. Un-suspending = uncomment.

**The 4 suspended Schedules:**

| Schedule | Cron | Action | Risk |
|---|---|---|---|
| `cpu-stress-unipoller` | Wed 11am UTC | 3m CPU stress on unipoller | Low |
| `network-delay-loki` | Wed 10am UTC | 5m 200ms delay on Loki | Medium (ip-set failures) |
| `pod-failure-node04` | 1st monthly noon UTC | 5m pause-swap all pods on node04 | **HIGH — caused this lockup** |
| `pod-kill-prometheus` | Wed 9am UTC | pod-kill Prometheus | **HIGH — Prometheus PVC = iSCSI RO cascade risk** |

**Fixes required before un-suspending:**
- `pod-failure-node04`: exclude `chaos-mesh` namespace from selector, or switch to `mode: fixed-percent` with small percentage
- `pod-kill-prometheus`: reconsider whether weekly forced-kill of Prometheus is proportional value vs risk (Prometheus's iSCSI PVC has been the source of multiple silent outages this year)
- `network-delay-loki` + `cpu-stress-unipoller`: investigate why ip-set application fails on some nodes before re-enabling

**Key Gotchas Captured:**
- **`Synced + Progressing` is a real state that survives.** ArgoCD's app-level status showed chaos-mesh Progressing for 11 days because 3 pods weren't Ready. No alert rule caught it — the `ArgoCDAppNotHealthy` rules typically only fire on `Degraded` transitions, not sustained `Progressing`. Worth an alert for "app in Progressing state > 1h."
- **Chaos-mesh Schedule CRDs have no `spec.suspend` field** (unlike batch/CronJob). To suspend, you must delete the Schedule resource or edit the cron. GitOps-safe way: comment out of kustomization + PR + let ArgoCD prune.
- **PodChaos `mode: all` on a node selector is self-destructive.** If chaos-mesh's own components are on that node, the experiment kills its own reconciler mid-experiment. Always exclude chaos-mesh's namespace from selectors, or use `mode: fixed-percent` / `mode: one` with a limit.
- **Chaos-mesh Schedules catch up on missed cron slots when the controller recovers.** No `startingDeadlineSeconds` = every missed slot fires when recovered. Explains why fixing chaos-mesh triggered a pod-kill-prometheus AND a network-delay-loki immediately. Set `startingDeadlineSeconds: 0` or a short value on Schedules to prevent this.
- **`foregroundDeletion` finalizer on chaos-mesh resources** can stick when parent Schedule is already gone. Manual `kubectl patch --type=merge -p '{"metadata":{"finalizers":null}}'` clears it.

**Follow-up (same day) — closed the alerting gaps + sealed-secrets URL fix:**

- **PR #771:** ArgoCDAppProgressing alert (`health_status="Progressing"` for 1h). Directly motivated by today's finding — would have caught the chaos-mesh lockup ~1h after July 1.
- **PR #772:** ArgoCDAppDegraded (15m) + ArgoCDAppUnknown (30m). Unknown uses `health_status="Unknown" OR sync_status="Unknown"` — the OR is important because today's sealed-secrets case is `health=Healthy, sync=Unknown` (chart fetch fails while runtime is fine). Metric distinguishes health vs sync; obvious in hindsight, worth writing down.
- **PR #773:** Fix sealed-secrets chart URL `bitnami-labs.github.io/sealed-secrets` → `bitnami.github.io/sealed-secrets` (the `-labs` GitHub org apparently stopped serving chart repos at some point). Confirmed via sealed-secrets README + verified our pinned chart version 2.18.6 exists at the new URL. Runtime was healthy the whole time; this just unblocks the ArgoCD reconcile.

**Result:** 38/38 apps Synced+Healthy — first fully-clean cluster state in ~3 weeks. New ArgoCDApp* alerts loaded in Prometheus.

**Alert verified end-to-end (no false positive):**
- `ArgoCDAppUnknown` entered `pending` state for ~1 minute (4 eval samples for `sealed-secrets` at 15s scrape interval) as soon as the rule loaded
- PR #773 merged + applied ~15 min later → `sync_status` transitioned to `Synced` → alert returned to `inactive`
- Never crossed the 30m `for:` duration → never transitioned to `firing` → no email sent
- Confirms the 30m threshold is well-tuned: same-day fixes don't page, but sustained Unknown will fire within an actionable window
- Range query for the record: `count_over_time(ALERTS{alertname="ArgoCDAppUnknown",alertstate="pending"}[2h])` returned 4 samples; `alertstate="firing"` returned 0

**Follow-up (same day) — Renovate batches A/B/D/C applied:**

10 open Renovate PRs reviewed and applied across 4 batches:

| Batch | PRs | Change |
|---|---|---|
| **A — patches** | #755, #756, #757, #762, #766 | velero 12.0.3, strimzi 1.0.1, trivy-operator 0.33.2, falco 9.1.0, vpa 4.12.3 |
| **B — image bumps** | #758, #759, #761 | alpine/git v2.54.0, alpine/k8s 1.36.2, cloudflared 2026.7.1 |
| **D — oauth2-proxy minor** | #765 | 10.6.2 → 10.7.0 |
| **C — argocd chart** | #760 | **9.5.22 → 9.7.1 (2-minor jump, appVersion unchanged v3.4.4)** |

**Notable during the apply:**
- argo-workflows briefly OutOfSync on a `waiting for deletion of hook batch/Job/localstack-argo-workflows-setup` — self-cleared within 45s
- **argocd chart bump showed transient chart-label drift** — sync `Succeeded` reported before `selfHeal` picked up `helm.sh/chart: 9.5.22 → 9.7.1` on 13 resources. I ran a manual sync patch out of habit, but a follow-up empirical test (below) shows this was unnecessary — `selfHeal` handles chart-label drift within ~30-60s natively.
- **All 3 ArgoCDApp* alerts stayed `inactive` throughout** — transient OutOfSync/Progressing states were well under the `for:` thresholds (15m/30m/1h). No noise, as tuned.

**Final state:** 38/38 apps Synced+Healthy. 4 open Renovate PRs from earlier this session (chaos-mesh, docs) — all closed as merged or superseded.

**Correction (later same day) — "chart bumps need manual sync" was misdiagnosis.**

When the user asked to automate the manual-sync-after-chart-bump pattern, I ran a controlled test first to check whether ArgoCD's built-in `selfHeal` should already handle it:

1. **Test 1** — added an untracked label to argocd-dex-server: sync stayed `Synced` (correctly ignored — labels I add aren't in git)
2. **Test 2** — deleted `servicemonitor argocd-server`: recovered by selfHeal in 60s
3. **Test 3** — corrupted the `helm.sh/chart` label to `argo-cd-STALE` (mimics exactly the chart-bump failure mode): recovered by selfHeal in 30s

The pattern I documented as needing manual intervention was actually just impatience — I was force-syncing during the transient window before selfHeal ran. Both istio 1.30.1 (last session) and argocd 9.7.1 (today) would have selfHealed within ~60s if I'd waited.

**No CronJob built.** The right corrections are docs-only. `syncPolicy.automated.selfHeal: true` (already on every app) plus the existing `ArgoCDAppProgressing` alert (1h threshold — catches the actual failure case where selfHeal gets stuck) is the correct stack.

**Updated gotcha in REFERENCE.md** to reflect the correction: wait 60s before intervening.

**Additional gotcha captured today:**
- **argocd_app_info has separate `health_status` and `sync_status` labels.** Sealed-secrets case shows `health=Healthy` (runtime is fine) but `sync=Unknown` (ArgoCD can't render manifests to compare against because the chart repo returns 404). Alerts should check either label depending on the concern — for "app in a state I should investigate," use `or` across both.

---

### 2026-06-21: Cluster Healthcheck — 16-day silent outage discovered + remediator architectural fix

**Healthcheck found 5 pods crashlooping for 16 days straight** — Loki (144 restarts), Uptime Kuma (144), Grafana, Falco-Redis, **and Prometheus itself**. All EROFS on iSCSI PVCs. The auto-remediation pipeline that was verified working on 2026-06-07 had been silently no-op'ing the whole time.

**Root cause:** the remediator's hot path was:

```
curl http://prometheus:9090/api/v1/alerts → parse firing PVCMountReadOnly → act
```

When Prometheus's own PVC went RO, Prometheus crashed → curl failed → Job `BackoffLimitExceeded` → silent no-op forever. Textbook "monitor the system from the system" anti-pattern: the remediator depended on the workload it was supposed to remediate.

**Recovery (manual, step-by-step):**
1. Deleted Prometheus, Loki, Grafana pods on node03 (RW globalmount) → recovered with fresh pod mounts
2. Discovered 3 of 4 globalmounts on node04 were RO at the **kernel level** (not just pod bind-mount). Pod delete alone insufficient — need to detach + reattach iSCSI device.
3. Cordoned node04, deleted the 3 affected pods (Grafana, Falco-Redis, Uptime Kuma) — they rescheduled to other nodes with fresh CSI attaches
4. Uncordoned node04 — its RO globalmounts will clean up when the next pod requests a volume there

**Fix shipped:**
- **PR #753:** Remediator now queries the `pvc-mount-monitor` DaemonSet pods directly via the headless Service endpoints — no Prometheus dependency. Keeps working even if the entire monitoring stack is broken.
  - New path: `kubectl get endpoints` → curl each monitor pod's `/metrics` → parse `pvc_mount_readonly{...} 1` lines → kubectl delete pod
  - RBAC added: `endpoints get/list`
  - Distinct error log when 0 monitors are reachable (vs "no RO mounts detected") — true detection-coverage gap is now visible

**Pull Requests:**
- **PR #753:** [Merged] fix(pvc-ro-remediator): query monitor pods directly, drop Prom dependency

**Key Gotchas Captured:**
- **Don't build an auto-remediation system that depends on the system it's monitoring.** Even when each component "works", a partial failure of the dependency creates silent no-op behavior that's worse than no automation at all (people stop watching).
- **The auto-remediation can fail in ways that ArgoCD doesn't surface.** ArgoCD reported `Synced + Healthy` for synology-csi the whole 16 days. The CronJob was `Failed` for 16 days but jobs roll out of history quickly (3-job retention). Need a separate alert for "remediator job hasn't completed successfully in N hours".
- **iSCSI RO can be at globalmount level**, not just per-pod. When pod-delete doesn't fix it, the underlying device itself is RO and requires a cross-node detach+reattach (drain the node).
- **AlertManager survived (17d uptime) but had no alerts to deliver** — Prometheus crashing means rule evaluation stopped entirely. AlertManager is healthy but useless without upstream alerts. Argues for an external heartbeat / dead-man-switch alert.

---

### 2026-06-07: Cluster Healthcheck + PVC RO Automation Verified End-to-End

**Full /cluster-healthcheck pass.** All 38 ArgoCD apps Synced+Healthy, 9/9 PVCs Bound + attached, all DaemonSets at expected count, no non-Running pods, all NAS workloads (Prometheus, Grafana, Loki, Trivy, Falco-Redis, Tempo, Zot, Uptime Kuma, LocalStack) showing 1/1.

**During the healthcheck, found two latent bugs in the PVC RO automation pipeline (deployed 2026-06-05/06):**

1. **PR #739 had a YAML editing mistake** — when adding the synology-csi → prometheus:9090 egress rule, port 3260 (iSCSI) got accidentally moved out of the Synology NAS rule into the new Prometheus rule. ArgoCD's SSA field-ownership quirk silently prevented the bad state from applying to the cluster (Synced status, but the new rule didn't actually exist). iSCSI kept working because the live policy was preserved. Net effect: the pvc-ro-remediator's curl to Prometheus kept timing out and the CronJob hit `BackoffLimitExceeded` every cycle.
   - Fix: **PR #746** restored port 3260 to the NAS rule.

2. **Default ns INGRESS NetworkPolicy didn't allow port 9090 from synology-csi**. Only same-ns + uptime-kuma were on the list. THIRD instance today of "NetworkPolicy fixes need both ingress AND egress sides" (already documented in k8s-docs-n37 PR #90).
   - Fix: **PR #747** added the missing ingress rule.

**Verification:** Force-applied the corrected manifests with `kubectl apply --force-conflicts --server-side`, then triggered a manual remediator job. Completed in 5 seconds with the expected `no firing PVCMountReadOnly alerts` log line. **The PVC RO automation is now end-to-end functional and verified.**

**Pull Requests:**
- **PR #746:** [Merged] fix(network-policies): restore iSCSI port 3260 to Synology NAS egress
- **PR #747:** [Merged] fix(network-policies): allow synology-csi → default:9090 ingress

**Key Gotchas Captured:**
- **ArgoCD "Synced" doesn't mean "applied":** SSA field-ownership disagreements can leave the cluster in the pre-change state even when ArgoCD reports the app as Synced. When making NetworkPolicy changes, always verify with `kubectl get networkpolicy ... -o yaml` after sync, don't trust the ArgoCD status alone.
- **Always re-survey egress + ingress on BOTH sides** of a new cross-namespace path. The "both directions" reminder applies to every namespace pair, not just the destination service's NetPol. We hit this three times today between syn→default and the prometheus egress rules.

---

### 2026-06-05/06: PVC RO-Mount Automation — Layered Strategy Shipped

**Strategy (per TODO #17a, principle: automate by default):**

1. **Primary** (per-app livenessProbe with write test) — covers apps where shell + chart customization both work
2. **Detection** (cluster-wide writability monitor) — covers the rest
3. **Backstop** (auto-remount controller) — closes the loop on detection

**Coverage matrix:**

| App | Livenessprobe | Reason |
|---|---|---|
| Uptime Kuma | ✅ PR #731 | Shell + chart support |
| LocalStack | ✅ PR #732 | Shell + plain manifests |
| Falco-Redis | ⏭️ Controller path | Chart hardcodes TCP probe |
| Loki, Tempo, Zot | ⏭️ Controller path | Distroless containers |

**PRs:**
- **PR #731:** [Merged] feat(uptime-kuma): write-test livenessProbe
- **PR #732:** [Merged] feat(localstack): write-test livenessProbe
- **PR #733:** [Merged] chore(todo): document PVC livenessProbe survey results
- **PR #734:** [Merged] feat(synology-csi): pvc-mount-monitor DaemonSet for RO detection
- **PR #735:** [Merged] feat(synology-csi): pvc-ro-remediator CronJob — auto-remount on RO
- **PR #736:** [Merged] fix(network-policies): allow Prometheus scrape of pvc-mount-monitor :9300
- **PR #737:** [Merged] fix(pvc-mount-monitor): read /host/proc/1/mounts not /host/proc/mounts
- **PR #738:** [Merged] fix(network-policies): allow default→pvc-mount-monitor:9300 egress
- **PR #739:** [Merged] fix(network-policies): allow synology-csi → prometheus:9090 egress (had latent bug, fixed by #746)

**End-to-end pipeline:**

```
pvc-mount-monitor DaemonSet → pvc_mount_readonly gauge (every node)
PrometheusRule PVCMountReadOnly → fires after 2m sustained RO
pvc-ro-remediator CronJob (every 2m) → kubectl delete pod → fresh iSCSI session → RW
```

**Total detection-to-recovery: ~4 min worst case.** Beats the hours it took to notice manually on 2026-06-04.

**Key Gotchas Captured:**
- **`/host/proc/mounts` is per-container, not host:** symlinks to `/proc/self/mounts` which the container's Python process resolves to ITS OWN mount namespace (no CSI mounts there). PID 1 in `/host/proc` is the host's init regardless of PID namespace, so `/host/proc/1/mounts` gives the actual host mount table.
- **NetworkPolicy fixes need both directions, EVERY time.** Caught a fresh instance for every new cross-namespace metric path: ingress on dest, egress on src (#736 + #738 for monitor scrape; #739 + #747 for remediator curl).
- **Two of six stateful apps support livenessProbe override** — Loki/Tempo/Zot are distroless (no shell), Falco-Redis chart hardcodes TCP probe. Per-app strategy alone wouldn't have closed the loop; needed the controller as backstop.

---

### 2026-06-04 (afternoon): Cluster Shutdown/Restart + NAS CPU Triage + VSC Janitor

**Cluster shutdown via /cluster-shutdown skill:**
- All 38 ArgoCD apps auto-sync disabled; NAS-dependent workloads scaled to 0.
- **Skill gap discovered:** tempo, zot, uptime-kuma, localstack not in the skill's scale-down list (they were deployed after the skill was written). Added them manually before the volume detach gate.
- All 9 synology-csi VAs cleanly released → workers shut down in parallel → control-plane last.

**Cluster restart recovery:**
- All 5 nodes still `SchedulingDisabled` from the drain — uncordoned first.
- Re-enabled auto-sync on all 38 apps.
- **Skill gap #2:** ArgoCD's `selfHeal` did NOT restore `.spec.replicas` after the manual `kubectl scale`. Field ownership in SSA isn't held by argocd-controller. **Had to manually scale all 10 workloads back up** to mirror the shutdown.
- Once Zot was back, force re-pulled the ImagePullBackOff pods (external-dns × 3, lifeonabike-web × 2).
- iSCSI PVCs (Prometheus, Grafana, Loki, Tempo, Zot, Uptime Kuma, Falco-Redis) all mounted RW cleanly. **No btrfs RO-remount this cycle** — the planned scale-down → VA release → drain sequence avoided the April UDR-reset failure mode.

**NAS CPU triage (separate but immediate post-restart issue):**
- NAS CPU pegged at 80-94% for 30+ min after restart, with `ssCpuUser=79%`. iSCSI itself was idle (`iSCSILUNIopsRead/Write=0`).
- SSH'd into NAS (sshpass + password from user) → `top` showed `synoscgi_SYNO.Core.ISCSI.LUN_1_get` at 100% CPU. **DSM REST API was being hammered.**
- 11 active connections to DSM from node04 (10.0.10.220). Traced to `synology-csi-snapshotter-0`.
- **Root cause: 283 orphan VolumeSnapshotContent objects** dating to 2026-02-20, each pointing at long-gone Synology snapshots. Snapshotter retried each one against DSM REST API on every reconcile pass.
- Manual fix: patched finalizers off + deleted all 283 orphans → NAS CPU dropped to **95.2% idle, load avg 11.19→6.79 in 5 min**.

**Pull Requests:**
- **PR #724:** [Merged] feat(synology-csi): add daily orphan VolumeSnapshotContent janitor — CronJob in synology-csi ns at 03:00 MT. Prunes VSCs matching `readyToUse=false` + "can not find snapshot" + >7d old. Patches finalizers off before delete. Hardened pod (non-root, readOnly fs, all caps dropped, RBAC limited to VSC CRUD only).
- Copilot review caught a BSD-specific `date -r ${epoch}` fallback that would fail on Linux/busybox under `set -e`. Fixed before merge by extracting the human-readable cutoff into its own variable with an `echo`-based fallback that can't fail.

**Key Gotchas Captured:**
- **ArgoCD selfHeal doesn't restore `.spec.replicas`** after manual scale — field ownership in SSA. Cluster shutdown skill must include re-scale on restart.
- **Orphan VSCs hammer DSM** — the snapshotter retries every error VSC on every reconcile. The synology-csi-snapshotter has no built-in backoff for orphans. The new janitor catches the accumulation source.
- **`/cluster-shutdown` skill is 4 months old** and missing tempo, zot, uptime-kuma, localstack scale-downs + the post-restart recovery procedure. Follow-up needed.
- **DSM REST API is the bottleneck**, not iSCSI. Heavy NAS CPU with idle `iSCSILUNIops*` means the CSI driver (or snapshotter) is calling the management API.
- **NAS SSH key is separate from cluster nodes** — `~/.ssh/id_ed25519_k8s` is cluster-only. NAS uses password auth (user provided via /tmp/nas_pass).

---

### 2026-06-04 (later): Fix flink-operator CRD drift — 38/38 clean

**Completed Work:**
- **PR #722:** [Merged] fix(flink-operator): ignore priority=0 default on CRD printer columns
- **Root cause:** apiextensions/v1 API server defaults `priority: 0` on every `additionalPrinterColumns` entry the chart leaves unspecified. ArgoCD's stored-vs-rendered diff showed only the `> priority: 0` line on each of the 4 flink CRDs.
- **Fix:** Added `.spec.versions[].additionalPrinterColumns[].priority` to the existing CRD `ignoreDifferences` block (which already covered `.spec.conversion` for the same defaulting reason).
- **Result:** flink-operator → Synced+Healthy. **38/38 ArgoCD apps Synced+Healthy** — first clean state across the entire cluster in months.

**Key Gotcha Captured:**
- **apiextensions/v1 CRD field defaulting:** server-side defaults `additionalPrinterColumns[].priority=0` and `spec.conversion.strategy=None` on storage. Both need to be in ArgoCD `ignoreDifferences` for any Helm chart that doesn't specify them explicitly. The pattern: any CRD-shipping chart that goes OutOfSync indefinitely is probably hitting one of these.

---

### 2026-06-04: Renovate Batch — kube-prometheus-stack 86.1.1, trivy-operator 0.33.1, CI action bumps

**PRs Applied:**
- **PR #715:** [Merged] chore(deps): update monitoring stack to v86.1.1 (kube-prometheus-stack chart 86.1.0 → 86.1.1)
- **PR #717:** [Merged] chore(deps): update security tools to v0.33.1 (trivy-operator chart 0.32.1 → 0.33.1)
- **PR #720:** [Merged] chore(deps): bump CI workflow actions and Python — combined supersede of Renovate #716, #718, #719 (all touched `.github/workflows/validate.yml`):
  - `actions/checkout` v4 → v6
  - `actions/setup-python` v5 → v6
  - Python 3.12 → 3.14
- **PRs #716, #718, #719:** [Closed] superseded by #720

**Applications Updated:**

| App | Old Version | New Version | Status |
|-----|-------------|-------------|--------|
| kube-prometheus-stack | 86.1.0 | 86.1.1 | ✅ Synced+Healthy |
| trivy-operator | 0.32.1 | 0.33.1 | ✅ Synced+Healthy |

**Issues Encountered:**
- kube-prometheus-stack briefly OutOfSync after `kubectl apply` — operation phase Running while PreSync hook `kube-prometheus-stack-admission-create` (Helm webhook cert job) completed. Standard pattern documented in `/renovate-apply` skill. Resolved on its own in ~90 seconds.

**Final State:** 37/38 apps Synced+Healthy. The remaining `flink-operator` OutOfSync is the pre-existing CRD drift documented in Current State above — not blocking. No new pod restarts in the hour following the apply.

---

### 2026-06-03 (Cleanup Sprint): Network Alerts, TODO Sweep, 3 Docs PRs

**Completed Work:** Finished the small open TODO items as 2 homelab PRs + 3 k8s-docs-n37 PRs.

**PR #710 (merged): Network bandwidth/error PrometheusRule.**
- New `network-alerts.yaml`: 8 rules across two groups
- `node_network`: NodeNetworkReceiveErrors (>0.1/s 10m), NodeNetworkTransmitErrors, NodeNetworkReceiveDrops (>10/s 15m), NodeNetwork{Receive,Transmit}Saturation (>85% gigabit 15m), NodeNetworkInterfaceDown (critical, 2m)
- `node_conntrack`: NodeConntrackTableNearFull (>80% 10m), NodeConntrackTableFull (>95% 2m critical)
- Selector excludes `lo`, `cali*`, `tunl*`, `vxlan*`, `veth*`, `docker*` to focus on physical NICs
- Validated with in-cluster promtool: 8/8 rules

**PR #711 (merged): TODO sweep marking items completed by deployed work.**
- Storage capacity planning + alerting → covered by existing storage-alerts.yaml
- Distributed Tracing → Tempo (PR #574)
- Synthetic Monitoring → Uptime Kuma + blackbox SLO probes
- Chaos Engineering / Network Partition Testing / Node Failure Scenarios → Chaos Mesh (PR #563)
- VPN & Remote Access → UniFi VPN + oauth2-proxy + Cloudflare Tunnel

**k8s-docs-n37 PRs #91, #92, #93 (all merged):**
- **#91 Operational runbooks** — `docs/operations/runbooks.md`: ArgoCD stuck syncs, pod restarts, rollbacks, PVC Terminating, cert renewal, Falco WebUI silent, Renovate force-rebase, application manifest gotcha
- **#92 Disaster recovery** — `docs/operations/disaster-recovery.md`: RTO/RPO targets table; single worker node failure, control plane failure (incl. etcd restore), PVC recovery, full cluster rebuild, Synology NAS failure
- **#93 Cluster topology diagrams** — `docs/networking/cluster-topology.md`: Mermaid sequence diagrams for external client → backend, pod-to-pod HBONE, MetalLB VIP hairpin (with workaround table), DNS/egress paths

**Pull Requests:**
- **PR #710:** [Merged] feat(monitoring): add network bandwidth + error + saturation alerts
- **PR #711:** [Merged] chore(todo): mark items completed by recent work + supersede VPN
- **k8s-docs-n37 PR #91:** [Merged] docs(operations): operational runbooks for common tasks
- **k8s-docs-n37 PR #92:** [Merged] docs(operations): disaster recovery procedures
- **k8s-docs-n37 PR #93:** [Merged] docs(networking): cluster-internal topology diagrams

**Key Gotcha Discovered:**
- **Docusaurus pre-commit blocks on broken cross-doc links:** Forward-references to docs not yet committed cause `pre-commit run docusaurus-build` to fail. Fix is to add docs in dependency order — DR doc shipped after runbooks doc with a follow-up edit to cross-link them.

---

### 2026-06-02 (SLO Probe Tuning): Internal Service Probes, NetworkPolicy Fixes

**Completed Work:** Resolved the 4 failing SLO probes from the morning's PR #705 fallback. Now 5 of 5 probe targets green.

**PR #707 (merged): Probe internal Services for non-passthrough ingresses.**
- Diagnosed: external HTTPS probes for workflows / registry / lifeonabike all timeout because the redirect chain crosses MetalLB VIP 10.0.10.10 from a non-mesh-meshed pod, hitting the kube-proxy `KUBE-EXT` hairpin (`src-type LOCAL` only). argocd works via TLS-passthrough (no L7 redirect); grafana works because nginx returns 200 directly on `/`.
- New `blackbox-availability-internal` job probes ClusterIP Services directly (HTTP, not HTTPS):
  - `http://argo-workflows-server.argo-workflows:2746/` — HBONE bypass works (both ns ambient-meshed)
  - `http://zot.zot:5000/v2/` — needed ingress NetPol rule (zot not meshed)
  - `http://web.lifeonabike:80/` — no NetPol on lifeonabike, just works
- SLI recording-rule selector broadened from `job="blackbox-availability"` to `slo_target!=""` so future targets roll in automatically.
- New `slo_path` label (`ingress` vs `backend`) — dashboards can split end-to-end from backend-only signals.

**PR #708 (merged): Allow default ns egress to zot:5000.**
- After PR #707 zot probe still timed out. Diagnosed: default ns egress to `10.0.0.0/8` only allowed ports 80/443/8443/161. Port 5000 missing. HBONE bypass on port 15008 didn't apply because zot ns is not ambient-meshed.
- Added focused egress rule: `default → zot` on TCP/5000.

**Final state — all 5 SLO probes green:**
```
✅ ingress  https://argocd.k8s.n37.ca
✅ ingress  https://grafana.k8s.n37.ca
✅ backend  http://argo-workflows-server.argo-workflows:2746/
✅ backend  http://zot.zot:5000/v2/
✅ backend  http://web.lifeonabike:80/
```

**Pull Requests:**
- **PR #707:** [Merged] fix(slo): probe internal Services for non-passthrough ingresses
- **PR #708:** [Merged] fix(slo): allow default ns egress to zot:5000 for blackbox SLO probe

**Key Gotchas Discovered:**
- **HBONE bypass requires BOTH ends ambient-meshed:** Traffic from a meshed pod to a non-meshed pod is direct TCP (no HBONE), so a port-15008 bare ingress rule on the destination doesn't help — the destination must allow the source pod IP explicitly on the actual application port.
- **NetworkPolicy fixes need both directions:** Adding an ingress allow on the destination namespace's NetPol is half the work — the source namespace's egress NetPol must also permit the destination port. PR #707 only fixed ingress on zot; PR #708 was the egress half on default. Both required for a 2-policy path.
- **Hard refresh sometimes needed for Helm-sourced ArgoCD apps:** After updating `values.yaml`, a normal `kubectl annotate ... argocd.argoproj.io/refresh=normal` didn't pick up the new probe job in the additionalScrapeConfigs Secret. Forcing `refresh=hard` did.

---

### 2026-06-02 (Quick Wins Sprint): Pre-commit CI, Resource Quotas, SLO Framework, CoreDNS Docs

**Completed Work:** Four small/focused PRs landed in sequence to close TODO items #12 / #18 / #21 / #14.

**Pre-commit CI workflow (PR #702, merged):**
- New `.github/workflows/validate.yml` runs full pre-commit suite on every PR + push to main. Installs kustomize v5.4.3 + kubeconform v0.6.7, then `pre-commit/action@v3.0.1`.
- New `scripts/validate-kustomizations.sh` runs `kustomize build` on every `kustomization.yaml` under `manifests/` and pipes the rendered output through kubeconform. Catches errors the per-file check misses (missing resources, bad patch targets). Skips kustomizations with remote git refs locally; CI sets `VALIDATE_REMOTE=1` to include them.
- Required two iterations of fixing exclude regex for git-crypt'd paths: yamllint, kubeconform, trailing-whitespace, end-of-file-fixer, mixed-line-ending, markdownlint all needed `(^secrets/|.*secret.*|.*\.key$|.*-sealed\.ya?ml$)` exclude. In CI those files are binary blobs; without exclude they fail UnicodeDecodeError / yaml parse / get auto-"fixed" producing dirty tree.
- **Required `gh auth refresh -h github.com -s workflow`** — OAuth token without workflow scope cannot push `.github/workflows/*.yml`.

**ResourceQuotas for 14 namespaces (PR #703, merged):**
- New ArgoCD app `resource-quotas` at sync-wave -38. One ResourceQuota per namespace: argocd, cert-manager, external-dns, ingress-nginx, lifeonabike, localstack, metallb-system, oauth2-proxy, synology-csi, tempo, unipoller, uptime-kuma, velero, zot.
- Object counts only (`count/pods`, `count/persistentvolumeclaims`, `count/services`, `count/configmaps`, `count/secrets`). No CPU/memory quotas — admission rejection on count is recoverable; too-low memory quota would block valid scale-up.
- Sized 3-5x current count. Worst pre-apply utilization is argocd at 11/100 configmaps and 8/40 pods.
- Excluded (dynamic / system / operator-managed): argo-workflows, argo-events, flink-demo, flink-operator, kafka, strimzi-system, trivy-system, falco, loki, chaos-mesh, istio-system, default, kube-system, calico-system, tigera-operator, gatekeeper-system (already quota'd by Helm chart).
- Required `kubectl apply -f manifests/applications/resource-quotas.yaml` post-merge (Application manifests not auto-synced).

**SLO framework (PR #704, merged; fix PR #705, merged):**
- New `blackbox-availability` probe job in kube-prometheus-stack values.yaml using `https_2xx` module (separate from existing `blackbox-https` which uses `https_cert_expiry` — that conflates connectivity + cert validity).
- New `manifests/base/kube-prometheus-stack/slo-alerts.yaml` PrometheusRule. Multi-window multi-burn-rate pattern (Google SRE Workbook): 5 SLI recording rules (5m/30m/1h/6h/30d), 1 budget-consumed recording rule, fast burn alert (14.4x rate, 1h+5m AND'd), slow burn alert (6x rate, 6h+30m AND'd), budget-exhausted alert. SLO target 99.5%/30d (3h 36m budget). All severities at `warning` for now — promote to `critical` after observation.
- Validated in-cluster: `kubectl cp` rules to prometheus pod, `promtool check rules` → SUCCESS 9/9.
- **Post-merge gotcha (fix PR #705):** 4 of 6 probe targets returned HTTP status 0:
  - `workflows.k8s.n37.ca` — oauth2-proxy 302 redirect, `https_2xx` rejects non-2xx
  - `registry.k8s.n37.ca/v2/` — timeout (L7 routing under investigation)
  - `lifeonabike.ca` / `www.lifeonabike.ca` — public Cloudflare anycast IP blocked by default-ns egress NetworkPolicy (only allows `10.0.0.0/8`)
  - Reduced to argocd + grafana only (both 200) to prevent false-positive burn alerts within 1-6h. Each failing target needs its own follow-up tuning.

**CoreDNS docs (k8s-docs-n37 PR #86, merged):**
- New `docs/networking/coredns.md` (slotted into sidebar between Cloudflare Tunnel and Terraform).
- Live Corefile from `kubectl get cm coredns -n kube-system`: kubeadm default + Pi-friendly `disable success/denial cluster.local` cache override (in-cluster Service IPs always refetched).
- Architecture Mermaid diagram: pod → CoreDNS → node `/etc/resolv.conf` → UniFi gateway → Cloudflare.
- Plugin-by-plugin reference, resolution walkthrough for `cluster.local` / external / split-horizon `*.k8s.n37.ca`, pod-to-MetalLB VIP hairpin warning callout, Prometheus metrics reference, troubleshooting (NetworkPolicy egress, ndots:5 expansion, stale Service IPs, P99 latency).

**Pull Requests:**
- **PR #702:** [Merged] chore: add kustomize-build pre-commit hook and CI validation workflow
- **PR #703:** [Merged] feat(quotas): add object-count ResourceQuotas to 14 stable namespaces
- **PR #704:** [Merged] feat(slo): add SLO recording rules and multi-window burn alerts
- **PR #705:** [Merged] fix(slo): reduce blackbox-availability targets to known-working set
- **k8s-docs-n37 PR #86:** [Merged] docs(networking): add CoreDNS configuration guide

**Key Gotchas Discovered:**
- **gh OAuth + workflow scope:** Adding `.github/workflows/*.yml` requires `gh auth refresh -h github.com -s workflow`. Default repo scope (`repo`) is insufficient; push gets "refusing to allow an OAuth App to create or update workflow `.github/workflows/...` without `workflow` scope".
- **git-crypt + CI:** In CI, git-crypt'd files are encrypted binary blobs (no key). Every text-mutating pre-commit hook MUST exclude `(^secrets/|.*secret.*|.*\.key$|.*-sealed\.ya?ml$)` or it'll either fail (yamllint UnicodeDecodeError, kubeconform "control characters not allowed") or auto-"fix" the blob and exit dirty.
- **blackbox `https_2xx` strictness:** Module accepts 2xx only by default. Endpoints behind oauth2-proxy (302 redirect) and Zot OCI registry (200 but with quirks) need either redirect-following config or `valid_status_codes: [200,302]`. NetworkPolicy can also break public-IP probes — default-ns egress restricts to `10.0.0.0/8`.
- **Promtool validates rule files, not PrometheusRule CRDs:** `promtool check rules` chokes on `apiVersion/kind/metadata/spec` — extract just `spec.groups` and wrap in `{groups: ...}` before validating.

---

### 2026-06-02 (After Midnight): ArgoCD Monitor URL Fix + Renovate Batch Apply

**Completed Work:**

**ArgoCD Uptime Kuma monitor fix (SQLite, no PR):**
- Monitor #1 (ArgoCD): ETIMEDOUT on port 8080 even after NetworkPolicy fix — root cause: Uptime Kuma had old in-memory config from before SQLite DB edit; pod must be restarted to reload SQLite.
- After pod restart with `http://argocd-server.argocd:80/healthz`: got "self-signed certificate" error — argocd-server ALWAYS serves HTTPS on pod port 8080, even when accessed via svc port 80 (DNAT: svc:80 → pod:8080 → TLS handshake). HTTP client received TLS response → cert error.
- Fix: changed URL to `https://argocd-server.argocd:443/healthz` with `ignore_tls=1` in SQLite, then restarted pod. Monitor green ✅.

**lifeonabike.ca / www.lifeonabike.ca monitor fix (SQLite, no PR):**
- Both monitors showing ETIMEDOUT to MetalLB VIP — split-horizon DNS resolves `lifeonabike.ca` to 10.0.10.10; pods can't reach MetalLB VIP (kube-proxy hairpin, same issue as cluster monitors).
- Fix: changed both to `http://web.lifeonabike:80` (internal ClusterIP service). Monitors green ✅.

**Renovate batch apply (PRs #694, #696, #700, via /renovate-apply skill):**
Reviewed Dependency Dashboard issue #251. Action on all awaiting-schedule items:

Merged (safe patches):
- **PR #694:** [Merged] chore: bump alpine/k8s 1.31.0 → 1.31.13 in lifeonabike-build-workflow.yaml
- **PR #696:** [Merged] chore: bump velero chart 12.0.1 → 12.0.2
- **PR #700:** [Merged] chore: bump cloudflared 2024.10.0 → 2026.5.2

Closed (dangerous / superseded):
- **PR #699:** Closed — velero-plugin-for-aws v1.14.1: sends `x-amz-tagging`, breaks B2 (pinned to v1.13.2, PR #681)
- **PR #697:** Closed — alpine/k8s 1.36.1: cluster is k8s 1.31.x; kubectl 1.36.1 could break API compatibility
- **PR #695, #698:** Closed — cloudflared 2024.10.1 / 2024.12.2: superseded by #700 (2026.5.2)

**Post-apply validation:**
- `kubectl apply -f manifests/applications/velero.yaml` — required because ArgoCD does not auto-detect Application manifest changes
- ArgoCD refresh triggered for velero, lifeonabike, argo-workflows
- All three apps Synced+Healthy: velero (chart 12.0.2, plugin v1.13.2 ✅), lifeonabike (cloudflared 2026.5.2 ✅), argo-workflows (alpine/k8s 1.31.13 in WorkflowTemplate ✅)

**Key Gotchas Discovered:**
- **ArgoCD server HTTPS on pod port 8080**: argocd-server always serves HTTPS on pod port 8080. HTTP monitor on svc:80 gets DNAT → pod:8080 → TLS response → "self-signed certificate". Must use `https://argocd-server.argocd:443/healthz` with `ignore_tls=1`.
- **Uptime Kuma SQLite hot-reload**: Uptime Kuma does NOT hot-reload from SQLite while running. After any SQLite edit via `kubectl exec`, the pod must be restarted to pick up the new monitor URLs.

---

### 2026-06-02 (Late Night): Flink UI 503 Fix + Operator Health Check

**Completed Work:**

**Flink UI 503 fix (PR #692, merged):**
- User reported 503 on `https://flink.k8s.n37.ca/`
- Root cause: ingress pointed at `file-to-kafka-rest:8081`, but `file-to-kafka` is a bounded job (reads static CSV → publishes to Kafka → exits). Once it finishes, the Flink operator tears down the jobmanager pod and REST Service. nginx had no backends → 503.
- Fix: Changed ingress backend to `kafka-to-s3-rest:8081` (long-running streaming job, always available). ArgoCD auto-synced within ~60s of merge.

**Flink operator health check:**
- Operator pod: 2/2 Running, 32h, 0 restarts — healthy
- ArgoCD: `OutOfSync` on 4 CRDs (pre-existing drift — `ignoreDifferences` covers `.spec.conversion` but status still oscillates). Not blocking.
- Logs: `kafka-to-s3` fully reconciled; `file-to-kafka` observes `MISSING` jobmanager (expected — FINISHED + STABLE lifecycle). Repeated INFO warnings about memory fractions (`jvm overhead 102mb < min 192mb`, `network 57mb < min 64mb`) — operator auto-corrects to minimums, non-blocking.

**Pull Requests:**
- **PR #692:** [Merged] fix(flink-demo): point ingress at kafka-to-s3-rest instead of file-to-kafka-rest

**Key Gotchas Discovered:**
- **Flink bounded job removes its own REST service**: When a FlinkDeployment reaches FINISHED state, the operator deletes the jobmanager pod AND the `<name>-rest` Service. Any ingress pointing at that service gets 503. Always point ingress at an unbounded streaming job for a stable REST target.

---

### 2026-06-02 (Night): Uptime Kuma Monitor Fix — MetalLB VIP Hairpin + NetworkPolicy

**Completed Work:**

**Root cause: pod-to-MetalLB VIP connection failure:**
- All Uptime Kuma monitors using `*.k8s.n37.ca` URLs showed DOWN (TCP SYN timeout)
- Root cause: kube-proxy's `KUBE-EXT` chain for LoadBalancer IPs only processes `--src-type LOCAL` traffic (node-originated). Pod traffic fails the LOCAL check → no DNAT → raw packet routed to node network → times out.
- Confirmed: Direct pod IP (192.168.x.x) → works ✅; ClusterIP (port 443) → works ✅; MetalLB VIP (10.0.10.10) → 100% packet loss ❌
- Meshed pods (default namespace, ztunnel HBONE) can reach the VIP because ztunnel intercepts and routes via HBONE, bypassing kube-proxy's broken path.
- Also discovered Tempo NetworkPolicy had wrong port (3100 instead of 3200 for Tempo's HTTP API).

**NetworkPolicy fix (PR #690, merged):**
- **uptime-kuma egress**: added ports 3100 (Loki), 3200 (Tempo), 2746 (Argo Workflows), 2802 (Falco UI), 4566 (LocalStack), 5000 (Zot), 8081 (Flink) + self-ingress (port 3001)
- **9 destination namespace ingress policies**: added `from: uptime-kuma` rule in argocd, default, loki, tempo, argo-workflows, zot, localstack, falco, flink-demo
- **Tempo NetworkPolicy bug fixed**: ingress port 3100 → 3200 (Tempo HTTP API is on 3200, not Loki's 3100)
- ArgoCD auto-sync restores policies from Git; direct `kubectl apply` is overridden immediately by selfHeal. Must merge PR first, then trigger ArgoCD refresh.

**Monitor URLs updated (SQLite, not Git):**
- All 11 cluster service monitors switched from `https://service.k8s.n37.ca` to internal ClusterIP DNS
- ArgoCD: `http://argocd-server.argocd:80/healthz`; Grafana: `http://kube-prometheus-stack-grafana.default:80/api/health`; Tempo: `http://tempo.tempo:3200/ready`; Argo Workflows: `http://argo-workflows-server.argo-workflows:2746`; Uptime Kuma self: `http://uptime-kuma.uptime-kuma:3001`; Zot: `http://zot.zot:5000/v2/`; LocalStack: `http://localstack.localstack:4566/_localstack/health`; Falco UI: `http://falco-falcosidekick-ui.falco:2802`; Flink: `http://kafka-to-s3-rest.flink-demo:8081`
- Monitors 12-15 (lifeonabike.ca, www.lifeonabike.ca, UniFi 10.0.1.1, UNVR 10.0.20.130) unchanged

**Result:** All 11 internal monitors pass curl tests from the uptime-kuma pod (connect: 0.001-0.036s).

**Pull Requests:**
- **PR #690:** [Merged] fix(network-policies): allow uptime-kuma to monitor internal cluster services

**Key Gotchas Discovered:**
- **kube-proxy MetalLB VIP hairpin**: KUBE-EXT chain only routes `--src-type LOCAL`. Pods are NOT local. Packet goes to node network without DNAT and is never delivered. Non-meshed pods must use ClusterIP DNS, not LoadBalancer hostname.
- **ArgoCD selfHeal reverts direct kubectl apply within seconds**: Always merge PR first, then trigger ArgoCD refresh (`kubectl annotate application ... argocd.argoproj.io/app-refresh=$(date) --overwrite`).
- **Tempo HTTP API port is 3200, not 3100**: Loki uses 3100. Tempo's HTTP server is on 3200.

---

### 2026-06-01 (Night): k8s-docs App Audit, Tempo Guide, UniFi tf-generator API Key Auth, Grafana Bridge Support

**Completed Work:**

**k8s-docs-n37 app doc audit + version updates (k8s-docs-n37 PR #85, merged):**
- Version bumps across 11 docs to match live cluster: ArgoCD (9.5.17/v3.4.3), Falco (chart 9.0.0/app 0.44.0), kube-prometheus-stack (86.1.0, Prometheus v3.12.0, Grafana 13.0.1-security-01), Zot (chart v0.1.116/image v2.1.17), Argo Workflows (1.0.14), Gatekeeper (3.22.2), ingress-nginx (v4.15.1), Istio (1.30.0 + upgrade callout), oauth2-proxy (v10.6.0), Uptime Kuma (v4.1.0), Velero (12.0.1/v1.18.1)
- **New doc: `docs/applications/tempo.md`** — Tempo v2.9.0 / chart 1.24.4; architecture diagram, OTLP receivers, Grafana datasource wiring, `resources: must be under tempo: key` gotcha, iSCSI PVC troubleshooting
- **Velero gotcha added:** `velero-plugin-for-aws` pinned to v1.13.2; v1.14.x sends `x-amz-tagging` header rejected by Backblaze B2
- **Falco gotcha added:** WebUI goes silent after Redis restarts independently (RediSearch index lost; fix: restart WebUI pod)
- sidebars.ts: Tempo added after Loki

**UniFi tf-generator API key auth (unifi-tf-generator PR #6, merged):**
- `get_token.sh`: when `-t`/`SECRET_UNIFI_TOKEN` provided, sets `AUTH_TYPE=apikey` and skips login; also accepts `SECRET_UNIFI_USERNAME` alongside existing `SECRET_UNIFI_USER`
- `json_utils.sh`: `fetch_raw_json` sends `X-API-KEY: <token>` when `AUTH_TYPE=apikey`, `cookie: TOKEN=` otherwise
- Re-ran `./scripts/all.sh` — live controller had drifted: +1 network (Video, VLAN 20, 10.0.20.1/24), +3 devices (U7 Pro AP, SunRoom Bridge, Garage Bridge), +15 users (33→48). Committed refreshed Terraform.

**Grafana UniFi switches dashboard — bridge device support (homelab PR #688, merged):**
- New UDBA69F bridges report `type=udb` to unipoller — not captured by any existing dashboard filter
- Updated `unifi-switches.yaml`: added `udb` to Controller + Site `label_values` filters and `$Devices` custom variable (+ `udm,usw,uap` → `udm,usw,uap,udb` query string)
- SunRoom and Garage bridges now appear in the Switches dashboard device picker

**Pull Requests:**
- **k8s-docs-n37 PR #85:** [Merged] docs: update application versions and add Tempo guide (June 2026)
- **unifi-tf-generator PR #6:** [Merged] feat: add X-API-KEY header auth + refresh Terraform from live controller
- **homelab PR #688:** [Merged] feat(grafana): add udb (network bridge) type to UniFi switches dashboard

---

### 2026-06-01 (Late Evening): k8s-docs-n37 Network Diagrams + Cloudflare Tunnel How-To

**Completed Work:**

**k8s-docs-n37 network diagrams (PR #84, merged):**
- Added `@docusaurus/theme-mermaid` 3.9.2 to enable Mermaid diagram rendering in Docusaurus
- **Networking overview** — added VLAN topology diagram (UDR7 → USW-Pro-24-PoE → all 6 VLANs with subnets/SSIDs/descriptions) and K8s cluster layout diagram (5 RPi5 nodes, Calico/Istio, MetalLB, Synology iSCSI with volume2/volume4 distinction)
- **New page: `docs/networking/cloudflare-tunnel.md`** — architecture diagram (Mermaid graph LR), key properties table, ingress routing table, full 7-step provisioning how-to (install cloudflared, login, create tunnel, DNS routes, K8s secret, kubeseal, commit + apply), troubleshooting section. Added to sidebar.
- **ArgoCD docs** — added GitOps flow diagram (graph LR) and application sync-wave structure diagram (graph TB)
- **Argo Workflows docs** — added lifeonabike CI/CD pipeline sequence diagram (14 numbered steps: Developer → GitHub → Cloudflare Edge → cloudflared → Argo Events EventSource → Sensor → Argo Workflows → git clone → Kaniko → Zot → kubectl rollout restart → K8s pull)

**Note:** `docs/architecture.md` was written locally to the homelab repo but could not be committed — `docs/` is gitignored in homelab (prevents accidental Docusaurus commands). All diagrams live in k8s-docs-n37.

**Pull Requests:**
- **k8s-docs-n37 PR #84:** [Merged] docs: add network diagrams and Cloudflare Tunnel how-to guide

---

### 2026-06-01 (Evening): Falco v9 + WebUI Fix, Trivy Network Policy, Argo Workflows SSD

**Completed Work:**

**GitHub MCP server configured:**
- Added `@modelcontextprotocol/server-github` via `claude mcp add --scope user`; stored in `~/.claude.json` (not settings.json — schema validation rejects `mcpServers` there)

**Renovate PRs reviewed and merged:**
- Closed **#663** (alpine/git v2.49.0 — superseded by #664 which targets the same line with a higher version)
- Merged **#664** (alpine/git v2.43.0 → v2.52.0 in `lifeonabike-build-workflow.yaml`)
- Merged **#665** (kaniko v1.23.2 → v1.24.0)
- Merged **#654** (Falco chart 8.0.5 → 9.0.0) after deep values.yaml compatibility check — all override keys present and unchanged in v9 (falcoctl 0.12.2→0.13.0, containerEngine.pluginRef 0.6.3→0.7.1, Falco engine 0.43.1→0.44.0)

**Falco v9 rollout confirmed:**
- All 5 DaemonSet pods Running 2/2 with modern eBPF driver; `kubectl apply -f manifests/applications/falco.yaml` required after merge (Application manifests not auto-synced)
- Deprecated `evt.dir` warnings in logs come from upstream `falco-rules:3` (not our custom rules); TOCTOU warnings are harmless on ARM64
- Falco IS generating events (confirmed in logs + Loki receiving POST 204 OK)

**Falco WebUI fix (in-cluster, no manifest change):**
- Root cause: `falcosidekick-ui` pod was 92 days old; Redis pod had restarted 44 days ago, wiping the RediSearch `eventIndex`. Every POST to `/events` returned HTTP 500 → falcosidekick logged as "exceeding post rate limit (500)"
- Fix: `kubectl rollout restart deployment/falco-falcosidekick-ui -n falco` — on startup the WebUI logs "Index does not exist → Create Index" and rebuilds it. Events immediately flowing (`WebUI - POST OK (200)`)
- **Gotcha:** If Redis restarts while the WebUI pod stays up, the index is lost silently. Next WebUI restart recreates it — watch for this pattern if events disappear from the UI again.

**Trivy review + network policy fix (PR #684):**
- Operator healthy: 96 VulnerabilityReports, 244 ConfigAuditReports, 190 ExposedSecretReports, compliance CronJob running on schedule
- Grafana dashboard (`grafana-dashboard-trivy-security`) loaded and querying correct metric names
- Scan jobs for `registry.k8s.n37.ca` images were failing: `TLS handshake timeout` — root cause: egress rule for port 443 excludes `10.0.0.0/8`, but MetalLB IP `10.0.10.10` for the nginx ingress is in that range. Added explicit `/32` rule before the exclusion block.
- Operator 4 restarts in 146min were caused by scan job failures (now fixed) + transient reconciler errors from our WebUI rollout (self-resolving)

**Argo Workflows PV cleanup + storage class (PR #685):**
- Deleted 24 orphaned Released PVs (48Gi total) left behind by `synology-iscsi-retain` Retain policy from previous builds
- Added `storageClassName: synology-iscsi-delete-ssd` to `volumeClaimTemplates` in `lifeonabike-build-workflow.yaml` — Delete policy auto-cleans on workflow completion, SSD for faster build I/O

**Pull Requests:**
- **PR #654:** [Merged] chore(falco): upgrade chart 8.0.5 → 9.0.0 (Falco engine 0.44.0)
- **PR #664:** [Merged] chore: bump alpine/git v2.43.0 → v2.52.0
- **PR #665:** [Merged] chore: bump kaniko v1.23.2 → v1.24.0
- **PR #684:** [Merged] fix: allow trivy scan pods to reach internal Zot registry (MetalLB IP egress)
- **PR #685:** [Merged] chore: switch lifeonabike build workspace to synology-iscsi-delete-ssd

**Key Gotchas Discovered:**
- **Falco WebUI Redis index loss:** The WebUI only creates the RediSearch index on startup. If Redis restarts independently the UI goes silent (HTTP 500 on every event POST). Fix is always a WebUI pod restart — it self-heals.
- **Trivy egress to internal registry:** The `0.0.0.0/0 except 10.0.0.0/8` egress rule that protects against private-range access also blocks `registry.k8s.n37.ca` (MetalLB IP). Must add an explicit `/32` rule for the ingress LoadBalancer IP before the exclusion block.
- **Branch protection requires `--admin` for merges:** All PR merges in this repo need `gh pr merge --admin` to bypass the branch protection policy.

---

## Session Archive Index

| Date | Title | Key Topics |
|------|-------|------------|
| 2026-06-01 | [Cluster Health Check, Tempo Fix, Velero B2 Fix](sessions/2026-06-01-cluster-health-tempo-velero-b2.md) | Tempo resources: under tempo: key, velero-plugin v1.13.2 B2 pin, makeup backups |
| 2026-06-01 | [EventSource Filter Fix, Zot Credential Rotation](sessions/2026-06-01-eventsource-filter-zot-credentials.md) | body.ref dot-path fix, bcrypt htpasswd encoding, *-sealed.yaml naming |
| 2026-05-31 | [lifeonabike Build Pipeline, Cloudflare Tunnel, Workflow Fixes](sessions/2026-05-31-lifeonabike-pipeline-cloudflare-tunnel.md) | 3-step Kaniko pipeline, Cloudflare Tunnel routing, ztunnel bypass, EventBus replicas=1 |
| 2026-05-31 | [LocalStack Fix, Retention 30d, Flink Verify, Argo Events](sessions/2026-05-31-localstack-retention-flink-argo-events.md) | CORS+persistence fix, 30d retention, Flink e2e verified, Argo Events v1.9.10 |
| 2026-05-31 | [Renovate Batch, Zot StatefulSet Fix, MetalLB frr-k8s Disable](sessions/2026-05-31-renovate-batch-zot-metallb.md) | RespectIgnoreDifferences+SSA release, frrk8s.enabled=false, VCT PVCs survive STS delete |
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
