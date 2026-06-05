# Homelab TODO & Improvements

## ✅ **Recently Completed** (December 2025 - March 2026)

### Infrastructure Fixes (January 2026)
- **Tigera Operator Migration** - Migrated Calico CNI to GitOps-managed Tigera operator (PRs #346-352, 2026-01-30)
  - Calico now managed by Tigera operator in calico-system namespace
  - ArgoCD Application with multi-source (operator from GitHub, Installation CR from homelab)
  - Typha topology spread constraints for node distribution
  - Established ignoreDifferences patterns for operator-managed resources
  - ArgoCD repo-server memory increased to 512Mi for large manifest generation
- **External-DNS Domain Filter Fix** - Fixed subdomain zone filtering (PRs #295-296, 2026-01-25)
  - Root cause: `--domain-filter=k8s.n37.ca` rejected the `n37.ca` Cloudflare zone
  - Solution: Use parent zone as domain-filter; ingresses specify exact hostnames
- **Grafana fsGroup Race Condition** - Fixed mount failure with Synology CSI (PR #298, 2026-01-25)
  - Root cause: SQLite journal file deleted during fsGroup recursive application
  - Solution: Added `fsGroupChangePolicy: OnRootMismatch` to podSecurityContext

### Secrets Management (January 2026)
- **Sealed Secrets Migration** - Migrated 8 secrets from git-crypt to SealedSecrets (2026-01-14)
- **External Secrets Removed** - Evaluation complete, Sealed Secrets chosen for simplicity (2026-01-14)
- **Secrets Directory Cleanup** - Removed 15 obsolete files, only ArgoCD bootstrap secret remains

### Backup & Disaster Recovery (January 2026)
- **Velero Backblaze B2 Migration** - Migrated from LocalStack to Backblaze B2 for production backups (2026-01-14, PR #239)
- **Velero CSI Snapshots** - Configured Velero to use CSI snapshots exclusively (2026-01-05)
- **snapshot-controller Fix** - Downgraded from v8.2.0 → v6.3.1 to resolve VolumeSnapshot failures (2026-01-05)
- **Loki Memory Optimization** - Implemented GOMEMLIMIT, ingestion rate limits, reduced memory usage from 474Mi → 232Mi (2026-01-05)

### Monitoring & Observability (December 2025)
- **SNMP Monitoring for Synology** - Deployed SNMP exporter, scraping NAS metrics (disk health, temperature, RAID status)
- **Node Exporter for Pi Cluster** - DaemonSet running on all 5 nodes, monitoring CPU, memory, disk, network
- **Log Aggregation** - Loki + Alloy deployed, 7-day retention, collecting logs from all pods on all nodes (including control-plane)
- **Prometheus Stack Fixes** - Fixed node-exporter scraping, Grafana PVC issues, cleaned up control plane monitoring
- **Control Plane Monitoring** - Re-enabled kube-scheduler and kube-controller-manager monitoring
- **ServiceMonitor Enablement** - Enabled metrics collection for Loki and Alloy

### DNS & Service Discovery
- **External-DNS Deployment** - Dual provider setup (Cloudflare + UniFi webhook) for split-horizon DNS (2025-12-27)
  - Cloudflare provider for public DNS records
  - kashalls/external-dns-unifi-webhook v0.7.0 for internal DNS
  - Automatic DNS record creation for Ingresses (argocd.k8s.n37.ca, grafana.k8s.n37.ca, localstack.k8s.n37.ca, workflows.k8s.n37.ca)
  - TXT registry for ownership tracking
  - **Fixed domain-filter for subdomain zones** (PRs #295-296, 2026-01-25) - Use parent zone (n37.ca) as domain-filter

### Documentation
- **Comprehensive Docs Site** - k8s-docs-n37 Docusaurus site with application guides
- **External-DNS Guide** - Complete documentation with dual provider setup and troubleshooting
- **Loki Application Guide** - Complete documentation for Loki + Alloy deployment
- **SNMP Exporter Guide** - Synology monitoring documentation
- **Troubleshooting Guides** - Monitoring stack and common issues documented

---

## 🎯 **High Priority**

### 1. **Blackbox Exporter** ✅ Complete
- [x] **Blackbox Exporter** - Fully operational (deployed 2025-12-27, verified 2025-12-28)
- [x] Deploy blackbox exporter for endpoint monitoring (v0.25.0, 2 replicas)
- [x] Monitor external services availability (DNS, HTTP/HTTPS probes configured)
- [x] SSL certificate expiry monitoring for k8s.n37.ca domain (https_cert_expiry module)
- [x] Network latency and response time tracking (ICMP ping monitoring)
- [x] Add alerts for service downtime (12 PrometheusRule alerts configured)
- [x] Monitor Synology NAS web interface availability (10.0.1.204 monitored)

### 2. **Enhanced Alerting** ✅ Complete
- [x] **AlertManager SMTP Email** - Configured Gmail SMTP for critical alerts (2025-12-27)
- [x] **Alert Routing** - Critical → email, warning/info → null (reduce noise)
- [x] **Velero Backup Alerts** - 7 PrometheusRule alerts for backup monitoring
- [x] **HTML Email Templates** - Custom-formatted critical alert emails
- [~] ~~Configure AlertManager webhook to Discord/Slack/Telegram~~ - Not used (email preferred)
- [x] Implement tiered alerting (warning → suppress, critical → email)
- [x] **Predictive Disk Space Alerts** - Node filesystem, PVC, and Synology volume alerts with predict_linear() (2026-01-12)
- [x] **NAS Health Alerts** - Disk failures, RAID degradation, temperature, bad sectors, power status (2026-01-12)
- [x] **Alert runbooks** - Documented in secrets/SEALED-SECRETS.md and k8s-docs-n37 (2026-01-14)
- [x] **Test alert routing** - Verified email delivery (121 sent, 0 failed) (2026-01-14)

### 3. **Backup Strategy** ✅ Complete
- [x] **Velero** - Deployed for Kubernetes cluster backup (2025-12-27)
- [x] **CSI Snapshots** - Configured Velero to use CSI snapshots exclusively (2026-01-05)
- [x] **snapshot-controller** - Deployed v6.3.1 for VolumeSnapshot processing (2026-01-05)
- [x] Backup critical PVCs (Prometheus 50Gi, Grafana 5Gi, Loki 20Gi)
- [x] Daily PVC backups (2 AM, 30-day retention) - CSI snapshots operational
- [x] Weekly cluster resource backups (3 AM Sunday, 90-day retention)
- [x] Velero backup monitoring alerts (7 PrometheusRule alerts)
- [x] **Fixed VolumeSnapshot failures** - Upgraded snapshot-controller to v8.2.1, csi-snapshotter to v8.4.0 (2026-01-11)
- [x] **LocalStack Sync Wave Fix** - LocalStack at wave -7, before Velero (-5) ✓
- [x] **Schedule regular backup testing** - Velero B2 restore tested and validated (2026-01-14)
- [x] **Migrate from LocalStack to Backblaze B2** - Production backup storage (2026-01-14, PR #239)
- [x] **Test disaster recovery scenarios** - Namespace restore with SealedSecrets validated (2026-01-14)
- [x] **ArgoCD configuration backup automation** - Daily backup schedule at 1:30 AM (2026-01-14)

**Note:** Kopia file-level backups disabled in favor of CSI snapshots (more efficient for block storage)

---

## 🔍 **Monitoring & Observability Enhancements**

### 4. **Custom Dashboards** ✅ Complete
- [x] **Custom Grafana Dashboards** - 4 dashboards deployed via ConfigMap provisioning (2025-12-28)
- [x] Pi cluster temperature monitoring dashboard (per-node CPU temps with Raspberry Pi 5 specifics)
- [x] Node resource utilization dashboard (CPU, memory, disk per node)
- [x] Loki log volume and ingestion rate dashboard (log analytics and error tracking)
- [x] Create unified "cluster health" dashboard (Pi Cluster Overview with 12 panels)
- [x] **Migrate Uncommitted Dashboards to Code** - Completed audit, no migration needed (2025-12-28)
  - [x] Audit Grafana UI for any manually created or modified dashboards (30 total, all in ConfigMaps)
  - [x] Export uncommitted dashboards as JSON (N/A - no uncommitted dashboards found)
  - [x] Create ConfigMap manifests for exported dashboards (N/A - all 30 already in code)
  - [x] Add to kustomization and deploy via GitOps (N/A - all already deployed)
  - [x] Verify dashboards load correctly after migration (All 30 dashboards confirmed via sidecar)
  - [x] Document dashboard creation and modification workflow (Added comprehensive audit section)
- [x] Network utilization dashboard - Deployed initial cluster-wide network utilization view (2026-02-05)
- [x] Storage performance metrics (iSCSI latency, IOPS, throughput) - Dashboard deployed (PR #383, 2026-02-05)
- [x] Application performance monitoring (APM) dashboard - 8-row overview with service health, CPU/memory, blackbox endpoints, API server, network I/O, saturation (2026-02-13)

### 5. **Metrics Server Deployment** ✅ Complete
- [x] **Metrics Server** - Deployed for kubectl top and HPA (2025-12-28)
- [x] Deploy metrics-server for kubectl top commands
- [x] Enable Horizontal Pod Autoscaler (HPA) capabilities
- [x] Configure for resource-constrained Pi environment (50m CPU / 100Mi RAM)
- [x] Prometheus ServiceMonitor integration

### 6. **Log-Based Alerting** ✅ ENABLED (2026-03-01)
- [x] **Loki Ruler Alerting** - Enabled via structuredConfig (rulerConfig ignored when ruler.enabled=false)
- [x] Set up Loki alerting rules for error patterns (HighErrorLogRate, CriticalErrorLogs)
- [x] Alert on CrashLoopBackOff events (CrashLoopBackOffDetected)
- [x] Alert on OOMKilled events (OOMKilledDetected)
- [x] Alert on persistent pod failures (PersistentPodRestarts)
- [x] Create log-based SLO monitoring (Error rate tracking via HighErrorLogRate)
- [x] Additional alerts: HTTP 5xx errors, DB connection errors, auth failures, security events

**Status:** 9 LogQL rules in 4 groups deployed as ConfigMap with loki_rule label. k8s-sidecar loads rules to /rules/fake/ for embedded ruler in singleBinary mode. Alerts route to AlertManager (PR #489, 2026-03-01).

---

## 🛡️ **Security & Compliance**

### 7. **Security Scanning & Runtime Protection** ✅ Complete
- [x] **Trivy Operator** - Container vulnerability scanning (deployed 2026-01-05, chart 0.31.0)
  - [x] ServiceMonitor configured for Prometheus metrics
  - [x] VulnerabilityReports available via kubectl
  - [x] Scanning all cluster images automatically
  - [x] Node-collector tolerations for control-plane scanning (PR #345, 2026-01-30)
- [x] **Falco** - Runtime security monitoring (deployed 2026-01-29, chart 8.0.1)
  - [x] Modern eBPF driver for ARM64 efficiency
  - [x] DaemonSet running on all nodes including control-plane
  - [x] Falcosidekick with AlertManager and Loki integration
  - [x] Web UI at falco.k8s.n37.ca (PR #340)
  - [x] Custom rules for homelab (cryptocurrency mining, reverse shell detection)
  - [x] PrometheusRules for security alerts
  - [x] NetworkPolicy configured (PR #339, #344)
- [x] **OPA Gatekeeper** - Policy enforcement and admission control (deployed 2026-02-06, chart 3.21.1)
  - [x] 5 ConstraintTemplates: resource limits, allowed repos, required labels, block NodePort, container limits
  - [x] All constraints switched to deny mode (0 violations, 2026-02-07)
  - [x] Pi-optimized: 1 replica, 100m/256Mi requests, 500m/512Mi limits
  - [x] Prometheus metrics with ServiceMonitor
  - [x] NetworkPolicy configured
  - [x] System namespaces exempted (kube-system, argocd, gatekeeper-system)
- [x] Security policy definitions for workloads
- [x] Compliance reporting and alerting (PSS Baseline + Restricted alerts, weekly CronJob summary to AlertManager)
- [x] Create Grafana dashboard for vulnerability trends (completed 2026-02-08, PRs #410-412: fixed NetworkPolicy HBONE, Gatekeeper exemption, SBOM bug)

### 8. **Secrets Management** ✅ Complete
- [x] **Evaluation Complete** - Sealed Secrets recommended for homelab (2026-01-13)
  - Sealed Secrets: 1 pod, 9Mi RAM, simple, GitOps-native
  - External Secrets: 3 pods, 69Mi RAM, complex, requires backend
- [x] **Sealed Secrets Deployed** - bitnami-labs/sealed-secrets v2.16.2 (2026-01-13)
- [x] **Secrets Migrated to SealedSecrets** (2026-01-14)
  - unipoller-secret, external-dns (cloudflare + unifi), alertmanager-smtp-credentials
  - snmp-exporter-credentials, cert-manager cloudflare token, synology-csi client-info
  - (7 secrets total; pihole-web-password removed when Pi-hole was decommissioned Feb 2026)
- [x] **External Secrets Operator Removed** - Evaluation complete, not needed (2026-01-14)
- [x] **Secrets Directory Cleaned** - Only bootstrap secret (ArgoCD SSH key) remains (2026-01-14)
- [x] **Documentation Updated** - CLAUDE_NOTES.md and secrets/README.md updated
- [x] Set up SealedSecrets sealing key rotation automation - SealedSecrets controller key rotation enabled (30d, 2026-02-05); cert-manager separately handles TLS cert renewal automatically
- [x] Create runbook for adding new SealedSecrets (added to SEALED-SECRETS.md, PR #489, 2026-03-01)

### 9. **Network Policies** ✅ Complete (2026-01-25)
- [x] Define NetworkPolicies for namespace isolation (18 namespaces)
- [x] Implement ingress/egress rules for sensitive workloads
  - [x] localstack: Allow velero, ingress-nginx, prometheus; egress DNS only
  - [x] unipoller: Allow prometheus; egress DNS + UniFi controller
  - [x] loki: Allow alloy, prometheus, grafana; egress DNS + alertmanager + K8s API
  - [x] trivy-system: Allow prometheus; egress DNS + K8s API + registries
  - [x] velero: Allow prometheus; egress DNS + localstack + B2 + K8s API
  - [x] argo-workflows: Allow ingress-nginx, prometheus; egress DNS + K8s API + B2 (2026-01-24)
  - [x] cert-manager: Allow webhook validation, prometheus; egress DNS + K8s API + Let's Encrypt + Cloudflare (2026-01-25)
  - [x] external-dns: Allow prometheus, internal webhook; egress DNS + K8s API + Cloudflare + UniFi (2026-01-25)
  - [x] metallb-system: Allow prometheus, memberlist, webhook; egress DNS + K8s API (2026-01-25)
  - [x] ingress-nginx: Allow external traffic, prometheus; egress DNS + K8s API
  - [x] istio-system: Allow prometheus, webhook; egress DNS + K8s API + HBONE port 15008
  - [x] gatekeeper-system: Allow prometheus, webhook; egress DNS + K8s API
  - [x] falco: Allow prometheus, alertmanager, loki; egress DNS + K8s API
  - [x] default: Allow ingress-nginx, prometheus; egress DNS + K8s API
  - [x] argocd: Allow ingress-nginx, prometheus; egress DNS + K8s API + GitHub
  - [x] synology-csi: Allow K8s API; egress DNS + NAS iSCSI
  - [x] kube-system: Allow prometheus; egress DNS + K8s API (metrics-server port 10250)
  - [x] tigera-operator: Allow prometheus; egress DNS + K8s API
- [x] Test policy enforcement (all tests passed)
- [x] Document network segmentation strategy in k8s-docs-n37 (PR #60, 2026-01-29)

**Configuration:** See `manifests/base/network-policies/` for all policy definitions.

---

## 🚀 **Platform Enhancements**

### 10. **Service Mesh** ✅ DEPLOYED (2026-01-28)
- [x] Research lightweight service mesh options for Pi cluster
- [x] Evaluate **Linkerd** (lightweight, Pi-friendly) - Considered but Istio Ambient selected
- [x] Evaluate **Istio** (full-featured but resource-intensive) - Istio Ambient mode chosen
- [x] Proof-of-concept deployment in test namespace
- [x] Performance impact analysis on Pi 5 cluster (~38m CPU, ~145Mi memory)
- [x] Document decision and implementation plan
- **Status:** Istio Ambient Mesh deployed with mTLS on 29 pods across 6 namespaces
- **Note:** All 25 ArgoCD apps Synced and Healthy (OutOfSync resolved 2026-02-05, PRs #379-381)

### 11. **Ingress Enhancements** ✅ Complete
- [x] Document current nginx-ingress configuration *(Updated network-info.md with all 5 Ingresses, rate limits, hardening config)*
- [x] Implement rate limiting for public endpoints *(Already configured: 50-100 RPS + 20 conn limits on all Ingresses)*
- [ ] ~~Add ModSecurity WAF rules~~ *Deferred: 256Mi memory limit insufficient for OWASP CRS (~512-768Mi needed); not justified for private 10.0.10.0/24 network*
- [ ] ~~Configure geo-blocking if needed~~ *N/A: All services on private network (MetalLB IP 10.0.10.10 is RFC 1918), no public ingress*
- [x] Monitor ingress performance and errors *(Created 7 PrometheusRule alerts + Grafana dashboard with 20 panels)*

---

## 🏗️ **Infrastructure & DevOps**

### 12. **GitOps Enhancements**
- [x] **Renovate** - Automated dependency updates for Helm charts (deployed 2026-01-23)
  - [x] GitHub App installed and configured
  - [x] ArgoCD Application manifest scanning (Helm charts)
  - [x] Docker image tag updates in Kubernetes manifests
  - [x] Grouped updates (ArgoCD, monitoring, networking, security, backup)
  - [x] Weekend schedule (Sat/Sun 6am-9pm) to minimize disruption
- [x] **Pre-commit hooks for Kubernetes manifest validation** (PR #702, 2026-06-02) — kubeconform per-file + kustomize-build with kubeconform on rendered output; git-crypt paths excluded from text-mutating hooks
- [x] **Automated CI validation pipeline** (PR #702, 2026-06-02) — `.github/workflows/validate.yml` runs the full pre-commit suite on every PR + push to main (installs kustomize v5.4.3 + kubeconform v0.6.7)
- [ ] Expand GitOps workflow documentation
- [ ] Consider multi-cluster ArgoCD setup for dev/staging

**Configuration:** See `renovate.json` in repository root.

### 13. **Development & CI/CD Tools - Argo Workflows** ✅ DEPLOYED (2026-01-24)

**Phase 1: Argo Workflows Deployment** ✅ Complete
- [x] Deploy Argo Workflows v3.7.8 (Helm chart 0.47.1)
- [x] Configure sync-wave: -8 (after LocalStack, before Velero)
- [x] Set up artifact repository (Backblaze B2) ✅ Fixed (PRs #287-289, 2026-01-24)
- [x] Configure resource limits for Pi cluster constraints:
  - Controller: 50m CPU / 128Mi RAM (request), 100m / 256Mi (limit)
  - Server: 25m CPU / 64Mi RAM (request), 50m / 128Mi (limit)
- [x] Enable Prometheus ServiceMonitor for workflow metrics
- [x] NetworkPolicy enabled ✅ Fixed K8s API egress (PR #291, 2026-01-24)
- [x] Ingress configured at https://workflows.k8s.n37.ca (PR #293, 2026-01-24)
- [x] Create Grafana dashboards for workflow monitoring (2026-01-29)
- [x] Set up AlertManager rules for workflow failures (2026-01-30, PR #354)

**Phase 2: Workflow Integration**
- [ ] ARM64 container image build workflows
- [ ] Automated testing pipelines for infrastructure changes
- [ ] Monthly backup validation workflows (Velero restore tests)
- [ ] Security vulnerability scanning workflows (Trivy integration)
- [ ] Infrastructure compliance scan workflows

**Phase 3: Advanced Features**
- [ ] SSO integration via oauth2-proxy
- [ ] Workflow templates library
- [ ] Automated dependency updates (Renovate integration)
- [ ] Multi-cluster workflow support (if dev/staging clusters added)

**Dependencies & Considerations:**
- Requires: Synology CSI (wave -30) for PVC storage ✓
- Requires: kube-prometheus-stack (wave -15) for monitoring ✓
- Optional: LocalStack (wave 0 → -7) for S3 artifact storage
- Resource Impact: ~600m CPU, ~768Mi RAM total (acceptable for 20-core cluster)

**Alternative Tools Considered:**
- [ ] Evaluate **Tekton** (more complex, higher resource usage)
- [ ] Evaluate **Gitea** vs **GitLab** for self-hosted git
- [x] **Zot** - CNCF OCI registry with pull-through proxy + Trivy CVE scanning (PR #571, 2026-04-23). Harbor skipped — no ARM64 images for Pi 5 cluster.
- [ ] Build and deployment automation for ARM64 custom containers

---

## 🌐 **Network & Access Management**

### 14. **CoreDNS Customization**
- [x] **Document current CoreDNS configuration** (k8s-docs-n37 PR #86, 2026-06-02) — `docs/networking/coredns.md`: live Corefile, plugin-by-plugin reference, split-horizon DNS walkthrough, troubleshooting, Prometheus metrics
- [ ] Custom DNS records for internal services
- [ ] DNS-based service discovery patterns
- [ ] DNS monitoring and troubleshooting tools (covered in the new guide)
- [ ] Consider DNS caching optimizations

### 15. **VPN & Remote Access** ✅ Complete (2026-04-17)
- [x] Remote access to cluster — handled by UniFi gateway VPN server (WireGuard/L2TP built-in)
- [x] Full home network access (NAS 10.0.1.x, cluster 10.0.10.x, MetalLB 10.0.10.10) via UniFi
- [x] ~~Deploy Tailscale/WireGuard on cluster~~ — closed as redundant; UniFi VPN is a superset
- [x] **oauth2-proxy** — deployed 2026-04-23 (PR #576). GitHub OAuth, restricted to user `imcbeth`, cookie domain `.k8s.n37.ca`. Protects Uptime Kuma, Argo Workflows; add 3 annotations to any ingress to extend coverage.
- [x] Public site hosting — Cloudflare Tunnel deployed for `lifeonabike.ca` (PRs #664–#678, 2026-05-31). No port-forward needed; outbound-only tunnel from cluster to Cloudflare edge.

**Decision:** UniFi gateway VPN server provides full network access. Cluster-side VPN adds complexity for zero gain. Tailscale Kubernetes Operator remains an option if per-service sharing with others is needed in the future.

---

## 🔧 **Operational Improvements**

### 16. **Documentation Enhancements**
- [x] **Operational runbooks** (k8s-docs-n37 PR #91, 2026-06-03) — `docs/operations/runbooks.md`: ArgoCD stuck syncs, pod restarts, rollbacks, PVC Terminating, cert renewal, Falco WebUI silent, Renovate force-rebase
- [x] **Disaster recovery procedures** (k8s-docs-n37 PR #92, 2026-06-03) — `docs/operations/disaster-recovery.md`: single node failure, control plane failure + etcd restore, PVC recovery, full cluster rebuild, NAS failure. Includes RTO/RPO targets table.
- [x] **Capacity planning documentation with growth projections** (k8s-docs-n37 PR #94, 2026-06-03) — `docs/operations/capacity-planning.md`: current baseline (CPU 13-32%, mem requests 24-34%, mem limits up to 80% on node01), per-resource detail, "when to add hardware" threshold table, predict_linear forecasting recipe, quarterly review checklist
- [x] **Cluster-internal network topology diagrams** (k8s-docs-n37 PR #93, 2026-06-03) — `docs/networking/cluster-topology.md`: Mermaid sequence diagrams for external client → backend, pod-to-pod HBONE, MetalLB VIP hairpin, DNS/egress paths
- [x] **Performance baseline documentation** (k8s-docs-n37 PR #95, 2026-06-03) — `docs/operations/performance-baseline.md`: measured P99/P95/avg values for apiserver (49ms read / 462ms write), etcd (24ms), CoreDNS (36ms), ingress (5-9ms), SLO probes (5-38ms), node load1 (0.6-2.2), container restarts (\<1/day), storage I/O, Prometheus self-metrics, Velero, image pulls. Mermaid diagnostic flowchart + quarterly refresh checklist.
- [ ] Document on-call procedures and escalation paths
- [x] Create k8s-docs-n37 guides for: cert-manager, metallb, ingress-nginx, localstack (completed in earlier sessions)

### 17. **Testing & Validation**
- [x] Chaos engineering with **Chaos Mesh** 2.8.2 — 4 scheduled experiments: pod-kill, network-delay, CPU-stress, node-failure simulation (PR #563, 2026-04-21). Note: Litmus has no ARM64 images; Chaos Mesh is the CNCF alternative with official ARM64 support.
- [ ] Load testing framework for applications
- [x] Backup and restore testing automation (monthly Velero DR validation CronWorkflow, deployed 2026-03-25)
- [x] Network failure simulation and recovery testing (network-delay-loki experiment via Chaos Mesh, weekly)
- [ ] Performance regression testing
- [x] Test node drain and pod eviction scenarios (pod-failure-node04 experiment via Chaos Mesh, monthly)

### 18. **Resource Optimization**
- [x] Audit resource requests/limits across all workloads (7 workloads adjusted, 2026-02-11)
- [x] Identify over-provisioned pods (resource right-sizing audit complete, net +928Mi requests)
- [x] Implement Vertical Pod Autoscaler (VPA) — fairwinds/vpa v4.11.0, recommender only, 7 VPA objects in Off mode (PR #522, 2026-03-25)
- [x] **Object-count ResourceQuotas for 14 stable namespaces** (PR #703, 2026-06-02) — count/pods, count/persistentvolumeclaims, count/services, count/configmaps, count/secrets. Object counts only (no CPU/memory quotas yet — too easy to mis-size). Excludes dynamic-workload + system namespaces.
- [x] **Storage capacity planning and alerting** — covered by `manifests/base/kube-prometheus-stack/storage-alerts.yaml`: NodeFilesystemSpaceLow/Critical/Predicted (predict_linear over 4h), NodeFilesystemInodesLow, PersistentVolumeSpaceLow/Critical/Predicted, plus Synology SNMP alerts (disk/RAID/volume/system temperature, bad sectors, power)
- [x] **Network bandwidth monitoring and alerting** (PR #710, 2026-06-03) — `network-alerts.yaml`: NodeNetworkReceiveErrors / NodeNetworkTransmitErrors, NodeNetworkReceiveDrops, NodeNetwork{Receive,Transmit}Saturation (>85% gigabit), NodeNetworkInterfaceDown, NodeConntrackTableNearFull/Full. Dashboard already deployed (network-utilization-dashboard.yaml, PR ~#383)

---

## 🌟 **Nice to Have**

### 19. **Pi Cluster Specific Monitoring**
- [x] **Power consumption tracking** (PR #726, 2026-06-04) — PoE per-port wattage already exposed via `unpoller_device_port_poe_watts`; per-node aligns to per-port. UPS integration deferred (no UPS deployed).
- [x] **PoE power draw per node** (PR #726, 2026-06-04) — alert `PiNodePoEPortHighDraw` fires on >15W sustained 15m; dashboard could follow if needed (data exists).
- [x] **NVMe thermal throttling detection** (PR #726, 2026-06-04) — `node_hwmon_temp_celsius{chip="nvme_nvme0"}` already exposed; alerts `PiNodeNVMeTempHigh` (>65°C 15m warning) + `PiNodeNVMeTempCritical` (>72°C 5m critical, past typical 70°C throttle).
- [x] **Track undervoltage events** (PR #726, 2026-06-04) — `node_hwmon_in_lcrit_alarm_volts` on `soc:firmware_raspberrypi_hwmon`; alert `PiNodeUndervoltage` fires immediately at 2m for lcrit_alarm > 0 (silent corruption risk if ignored).
- [ ] ARM64-specific performance optimizations — workload-level tuning concern, not monitoring; address as bottlenecks surface

### 20. **Application Deployments**
- [ ] Home Assistant integration
- [x] Private container registry — Zot v2.1.16 at registry.k8s.n37.ca (PR #571, 2026-04-23)
- [ ] Internal wiki or knowledge base
- [ ] Status page (Uptime Kuma or similar)
- [ ] Internal chat/collaboration tool

### 21. **Observability Maturity Enhancements**
- [x] **Distributed Tracing** — Tempo deployed 2026-04-23 (PR #574); OTLP via Alloy, trace↔logs (Loki) + trace↔metrics correlation in Grafana
- [~] **Continuous Profiling** — deferred 2026-06-04. Pyroscope singleBinary deployment is feasible (chart 2.0.3, ARM64 images verified) but adds non-trivial complexity: ~1Gi RAM, 10Gi PVC, Alloy scrape config, Grafana datasource, NetworkPolicy + ingress + cert. **Value at current scale is low** — most workloads are Helm-chart deployments not actively being optimized; the existing tracing + metrics stack covers the perf-investigation use cases we encounter. Revisit when a real production-perf problem can't be diagnosed with metrics + traces alone.
- [x] **Service Level Objectives (SLOs)** (PRs #704, #705, #707, #708, 2026-06-02) — multi-window multi-burn-rate alerts (Google SRE Workbook pattern) on 5 critical services. 99.5%/30d target. Fast burn (14.4x, 1h+5m), slow burn (6x, 6h+30m), budget-exhausted alerts. Two probe jobs: `blackbox-availability` (HTTPS via ingress, argocd + grafana) and `blackbox-availability-internal` (HTTP via ClusterIP, workflows + registry + lifeonabike). All 5 probes green.
- [x] **Error Budget Tracking** (PR #704, 2026-06-02) — `slo:error_budget_consumed:ratio_30d` recording rule (0-1 clamped). Future: Grafana dashboard.
- [~] **Anomaly Detection** — deferred 2026-06-04. ML-based anomaly detection is overkill at homelab scale: existing infrastructure (~70 PrometheusRule alerts across 8 rule files, SLO burn-rate alerts, predict_linear forecasting for storage/network) already covers the practical detection use cases. ML would add an entire pipeline (training data, model lifecycle, label noise) for marginal lift over threshold alerts that are tuned to actual cluster patterns. Revisit if alert fatigue becomes a problem or if a complex regression keeps slipping past the current rules.
- [x] **Synthetic Monitoring** — covered by Uptime Kuma (PR #573, status.k8s.n37.ca, 15 monitors across 3 groups via internal ClusterIP DNS) + blackbox SLO probes. True user-journey testing (form fills, multi-step) deferred until needed.

### 22. **Disaster Recovery Testing**
- [x] **Monthly DR Drills** - Automated DR validation CronWorkflow (1st of month 6am MT), 8-step backup/restore cycle, validated 2026-03-25 in 3m45s (PR #522-524)
- [x] **Velero Restore Testing** - Monthly Argo Workflows CronWorkflow: check-bsl → create-backup → verify-backup → test-restore → verify-restore → cleanup. ✅ 9/9 steps green.
- [x] **Chaos Engineering** — Chaos Mesh 2.8.2 deployed (PR #563, 2026-04-21). Litmus has no ARM64 images. 4 scheduled experiments: pod-kill, network-delay, CPU-stress, node-failure simulation.
- [x] **Network Partition Testing** — Chaos Mesh `network-delay-loki` experiment running weekly (validates monitoring stack resilience to network jitter)
- [x] **Node Failure Scenarios** — Chaos Mesh `pod-failure-node04` experiment monthly + ad-hoc node drain validated during cluster maintenance
- [ ] **Control Plane Failure** — Test etcd backup/restore procedures (single control-plane node; manual procedure documented in k8s-docs-n37 disaster-recovery guide)

### 23. **Cost Optimization & Efficiency**
- [ ] **Resource Right-Sizing** - Analyze actual vs requested resources
- [ ] **Spot/Preemptible Instances** - Not applicable for bare metal, document for future cloud consideration
- [ ] **Storage Optimization** - Compress old logs, optimize retention policies
- [ ] **Network Egress Optimization** - Monitor and optimize outbound traffic
- [ ] **Power Consumption Tracking** - PoE monitoring and efficiency analysis
- [ ] **Carbon Footprint** - Calculate and optimize cluster carbon footprint

### 24. **LLM Hosting & AI Infrastructure** (Planning)
- [ ] **GPU Hardware** - Add GPU-capable unit to cluster (planned)
- [ ] **Evaluate inference frameworks** - vLLM, Ollama, LocalAI, llama.cpp for ARM64/GPU
- [ ] **Kubernetes GPU scheduling** - NVIDIA device plugin or equivalent
- [ ] **Model storage** - Plan NFS/iSCSI storage for large model weights (7B-70B+ parameter models)
- [ ] **Resource isolation** - Dedicated node pool or taints/tolerations for GPU workloads
- [ ] **API gateway** - OpenAI-compatible API endpoint for model serving
- [ ] **Monitoring** - GPU utilization, inference latency, token throughput dashboards
- [ ] **Model management** - Version control and deployment pipeline for models
- [ ] **Network considerations** - High-bandwidth model loading, inference API exposure

---

## 📅 **Implementation Priorities**

Items are organized by priority, not by timeline. Focus on:

### **Phase 1: Foundation & Reliability** ✅ Complete
1. ✅ Backup strategy (Velero + critical PVC backups)
2. ✅ Enhanced alerting (AlertManager notifications)
3. ✅ Metrics server deployment
4. ✅ Blackbox exporter for endpoint monitoring

### **Phase 2: Security & Observability** ✅ Complete
1. ✅ Security scanning (Trivy Operator)
2. ✅ Secrets management migration (SealedSecrets)
3. ✅ Blackbox exporter for endpoint monitoring
4. ✅ Custom Grafana dashboards

### **Phase 3: Advanced Features** ✅ Complete
1. ✅ GitOps enhancements (Renovate deployed 2026-01-23)
2. ✅ Network policies implementation (18 namespaces isolated)
3. ✅ Development tools and CI/CD (Argo Workflows deployed 2026-01-24)
4. ✅ Service mesh (Istio Ambient deployed 2026-01-28)

### **Phase 4: Optimization & Expansion** (In Progress)
1. ✅ Resource optimization and VPA (deployed 2026-03-25)
2. ✅ Monthly DR validation workflow (deployed 2026-03-25)
3. ✅ Chaos engineering with Chaos Mesh 2.8.2 (PR #563, 2026-04-21)
4. Advanced networking and VPN (Tailscale/WireGuard)
5. Additional application deployments — ✅ Zot registry (PR #571, 2026-04-23), Home Assistant (pending)

---

## 🔄 **ArgoCD Sync Wave Optimization**

### Current Sync Wave Order (Updated 2026-04-17)

```
Wave -100: tigera-operator (CNI foundation - ArgoCD-managed)
Wave  -50: argocd (self-management)
Wave  -40: network-policies (namespace isolation)
Wave  -35: metallb (networking foundation)
Wave  -30: synology-csi (storage driver)
Wave  -25: sealed-secrets (secrets management)
Wave  -20: unipoller (UniFi metrics collection)
Wave  -15: kube-prometheus-stack (monitoring stack)
Wave  -12: loki (log aggregation)
Wave  -11: alloy (log collection, replaced Promtail 2026-03-01)
Wave  -10: cert-manager, external-dns, metrics-server (certificates & DNS & metrics)
Wave   -8: argo-workflows (CI/CD)
Wave   -7: localstack (S3 mock for Velero)
Wave   -6: gatekeeper (admission control + ConstraintTemplates)
Wave   -5: gatekeeper-policies, velero, falco (Constraints, backup, runtime security)
Wave   -4: vpa (Vertical Pod Autoscaler)
```

### ✅ Resolved Issues

**1. LocalStack Dependency Conflict** ✅ FIXED
- **Problem**: Velero (wave -5) depended on LocalStack (wave 0)
- **Solution**: LocalStack moved to wave -7, now deploys before Velero
- **Status**: Resolved - Velero BackupStorageLocation is available on startup

**2. UniFi Poller Timing**
- **Current**: Wave -20 (before monitoring stack)
- **Analysis**: Could move to -10 or -5 (no critical dependencies)
- **Decision**: Keep at -20 (metrics available when Prometheus starts)

### Validated Dependencies

- **Tigera Operator** (-100) → CNI available before all other workloads
- **ArgoCD** (-50) → Deploys itself after CNI is ready
- **MetalLB** (-35) → Provides LoadBalancer IPs before services need them
- **Synology CSI** (-30) → Storage driver available before PVCs
- **kube-prometheus-stack** (-15) → Uses CSI for 50Gi Prometheus PVC
- **Loki** (-12) → Uses CSI for 20Gi log storage PVC
- **Alloy** (-11) → Log collector DaemonSet, depends on Loki being available
- **cert-manager** (-10) → Independent, issues certs on-demand
- **external-dns** (-10) → Works with TLS Ingresses (safe timing)
- **LocalStack** (-7) → S3 mock available before Velero
- **Gatekeeper** (-6) → Admission control after monitoring, before app workloads
- **Velero** (-5) → Uses CSI and LocalStack S3
- **Falco** (-5) → Runtime security after monitoring is ready

### 🎯 Recommended Actions

1. **Optional Optimizations**:
   - Move UniFi Poller to -10 (aligns with other non-critical monitoring)

### 📊 Sync Wave Best Practices

**Critical Infrastructure** (Wave -50 to -30):
- Self-managed components (ArgoCD)
- Networking foundation (MetalLB, CNI)
- Storage drivers (Synology CSI)

**Monitoring & Logging** (Wave -20 to -10):
- Metrics collection (UniFi Poller)
- Monitoring stack (Prometheus, Grafana, AlertManager)
- Log aggregation (Loki, Alloy)
- Certificates and DNS (cert-manager, external-dns)

**Operational Tools** (Wave -10 to 0):
- CI/CD (Argo Workflows)
- Testing infrastructure (LocalStack)
- Backup solutions (Velero)

**Applications** (Wave 0+):
- User-facing services
- Development tools
- Internal applications

---

## 📋 **Notes**

- **Resource Constraints:** All implementations must consider the Pi 5 cluster constraints (80GB RAM total, 20 ARM cores)
- **Testing Strategy:** Test all implementations in a development namespace before production deployment
- **Documentation First:** Document all configurations and procedures for maintainability
- **GitOps Workflow:** All changes must go through PR workflow, never direct kubectl apply to production
- **Regular Reviews:** Review and update this TODO list monthly based on cluster evolution
- **Monitoring First:** Ensure monitoring is in place before deploying new workloads

---

## 🔗 **References**

- **CLAUDE_NOTES.md** - Detailed session notes and troubleshooting history
- **k8s-docs-n37/** - Comprehensive documentation site
- **Hardware.md** - Cluster hardware specifications
- **network-info.md** - Network configuration (to be expanded)
