# Homelab TODO & Improvements

## ✅ **Recently Completed** (December 2025 - January 2026)

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
- **Log Aggregation** - Loki + Promtail deployed, 7-day retention, collecting logs from all pods on all nodes (including control-plane)
- **Prometheus Stack Fixes** - Fixed node-exporter scraping, Grafana PVC issues, cleaned up control plane monitoring
- **Control Plane Monitoring** - Re-enabled kube-scheduler and kube-controller-manager monitoring
- **ServiceMonitor Enablement** - Enabled metrics collection for Loki and Promtail

### DNS & Service Discovery
- **External-DNS Deployment** - Dual provider setup (Cloudflare + UniFi webhook) for split-horizon DNS (2025-12-27)
  - Cloudflare provider for public DNS records
  - kashalls/external-dns-unifi-webhook v0.7.0 for internal DNS
  - Automatic DNS record creation for Ingresses (argocd.k8s.n37.ca, grafana.k8s.n37.ca, localstack.k8s.n37.ca)
  - TXT registry for ownership tracking

### Documentation
- **Comprehensive Docs Site** - k8s-docs-n37 Docusaurus site with application guides
- **External-DNS Guide** - Complete documentation with dual provider setup and troubleshooting
- **Loki Application Guide** - Complete documentation for Loki + Promtail deployment
- **SNMP Exporter Guide** - Synology monitoring documentation
- **Troubleshooting Guides** - Monitoring stack and common issues documented

---

## 🎯 **High Priority**

### 1. **Blackbox Exporter**
- [x] **Blackbox Exporter** - Fully operational (deployed 2025-12-27, verified 2025-12-28)
- [x] Deploy blackbox exporter for endpoint monitoring (v0.25.0, 2 replicas)
- [x] Monitor external services availability (DNS, HTTP/HTTPS probes configured)
- [x] SSL certificate expiry monitoring for k8s.n37.ca domain (https_cert_expiry module)
- [x] Network latency and response time tracking (ICMP ping monitoring)
- [x] Add alerts for service downtime (12 PrometheusRule alerts configured)
- [x] Monitor Synology NAS web interface availability (10.0.1.204 monitored)

### 2. **Enhanced Alerting**
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

### 3. **Backup Strategy** ⭐ Critical
- [x] **Velero** - Deployed for Kubernetes cluster backup (2025-12-27)
- [x] **CSI Snapshots** - Configured Velero to use CSI snapshots exclusively (2026-01-05)
- [x] **snapshot-controller** - Deployed v6.3.1 for VolumeSnapshot processing (2026-01-05)
- [x] Backup critical PVCs (Prometheus 50Gi, Grafana 5Gi, Loki 20Gi, Pi-hole 5Gi)
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

### 4. **Custom Dashboards**
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
- [ ] Network utilization by VLAN/segment
- [ ] Storage performance metrics (iSCSI latency, IOPS, throughput)
- [ ] Application performance monitoring (APM) dashboard

### 5. **Metrics Server Deployment**
- [x] **Metrics Server** - Deployed for kubectl top and HPA (2025-12-28)
- [x] Deploy metrics-server for kubectl top commands
- [x] Enable Horizontal Pod Autoscaler (HPA) capabilities
- [x] Configure for resource-constrained Pi environment (50m CPU / 100Mi RAM)
- [x] Prometheus ServiceMonitor integration

### 6. **Log-Based Alerting**
- [~] **Loki Ruler Alerting** - Temporarily disabled due to singleBinary mode compatibility (2026-01-05)
- [~] Set up Loki alerting rules for error patterns (HighErrorLogRate, CriticalErrorLogs)
- [~] Alert on CrashLoopBackOff events (CrashLoopBackOffDetected)
- [~] Alert on OOMKilled events (OOMKilledDetected)
- [~] Alert on persistent pod failures (PersistentPodRestarts)
- [~] Create log-based SLO monitoring (Error rate tracking via HighErrorLogRate)
- [~] Additional alerts: HTTP 5xx errors, DB connection errors, auth failures, security events

**Status:** Rules created but disabled (loki-alerts.yaml.disabled). Can be re-enabled with proper singleBinary ruler configuration.

---

## 🛡️ **Security & Compliance**

### 7. **Security Scanning & Runtime Protection**
- [x] **Trivy Operator** - Container vulnerability scanning (deployed 2026-01-05, chart 0.31.0)
  - [x] ServiceMonitor configured for Prometheus metrics
  - [x] VulnerabilityReports available via kubectl
  - [x] Scanning all cluster images automatically
- [ ] **Falco** - Runtime security monitoring and threat detection
- [ ] **OPA Gatekeeper** - Policy enforcement and admission control
- [ ] Security policy definitions for workloads
- [ ] Compliance reporting and alerting
- [ ] Create Grafana dashboard for vulnerability trends

### 8. **Secrets Management** ✅ Complete
- [x] **Evaluation Complete** - Sealed Secrets recommended for homelab (2026-01-13)
  - Sealed Secrets: 1 pod, 9Mi RAM, simple, GitOps-native
  - External Secrets: 3 pods, 69Mi RAM, complex, requires backend
- [x] **Sealed Secrets Deployed** - bitnami-labs/sealed-secrets v2.16.2 (2026-01-13)
- [x] **Secrets Migrated to SealedSecrets** (2026-01-14)
  - unipoller-secret, external-dns (cloudflare + unifi), alertmanager-smtp-credentials
  - snmp-exporter-credentials, cert-manager cloudflare token, synology-csi client-info
  - pihole-web-password (8 secrets total)
- [x] **External Secrets Operator Removed** - Evaluation complete, not needed (2026-01-14)
- [x] **Secrets Directory Cleaned** - Only bootstrap secret (ArgoCD SSH key) remains (2026-01-14)
- [x] **Documentation Updated** - CLAUDE_NOTES.md and secrets/README.md updated
- [ ] Set up secret rotation automation for certificates
- [ ] Create runbook for adding new SealedSecrets

### 9. **Network Policies** ✅ PARTIALLY COMPLETED (2026-01-24)
- [x] Define NetworkPolicies for namespace isolation (5 namespaces)
- [x] Implement ingress/egress rules for sensitive workloads
  - [x] localstack: Allow velero, ingress-nginx, prometheus; egress DNS only
  - [x] unipoller: Allow prometheus; egress DNS + UniFi controller
  - [x] loki: Allow promtail, prometheus, grafana; egress DNS + alertmanager
  - [x] trivy-system: Allow prometheus; egress DNS + K8s API + registries
  - [x] velero: Allow prometheus; egress DNS + localstack + B2 + K8s API
- [x] Test policy enforcement (all tests passed)
- [ ] Document network segmentation strategy in k8s-docs-n37
- [ ] Expand to remaining namespaces (cert-manager, external-dns, metallb-system)

**Configuration:** See `manifests/base/network-policies/` for all policy definitions.

---

## 🚀 **Platform Enhancements**

### 10. **Service Mesh Evaluation**
- [ ] Research lightweight service mesh options for Pi cluster
- [ ] Evaluate **Linkerd** (lightweight, Pi-friendly)
- [ ] Evaluate **Istio** (full-featured but resource-intensive)
- [ ] Proof-of-concept deployment in test namespace
- [ ] Performance impact analysis on Pi 5 cluster
- [ ] Document decision and implementation plan

### 11. **Ingress Enhancements**
- [ ] Document current nginx-ingress configuration
- [ ] Implement rate limiting for public endpoints
- [ ] Add ModSecurity WAF rules
- [ ] Configure geo-blocking if needed
- [ ] Monitor ingress performance and errors

---

## 🏗️ **Infrastructure & DevOps**

### 12. **GitOps Enhancements**
- [x] **Renovate** - Automated dependency updates for Helm charts (deployed 2026-01-23)
  - [x] GitHub App installed and configured
  - [x] ArgoCD Application manifest scanning (Helm charts)
  - [x] Docker image tag updates in Kubernetes manifests
  - [x] Grouped updates (ArgoCD, monitoring, networking, security, backup)
  - [x] Weekend schedule (Sat/Sun 6am-9pm) to minimize disruption
- [ ] Pre-commit hooks for Kubernetes manifest validation (kubeval, kustomize)
- [ ] Automated testing pipeline for infrastructure changes
- [ ] Expand GitOps workflow documentation
- [ ] Consider multi-cluster ArgoCD setup for dev/staging

**Configuration:** See `renovate.json` in repository root.

### 13. **Development & CI/CD Tools - Argo Workflows** ✅ DEPLOYED (2026-01-24)

**Phase 1: Argo Workflows Deployment** ✅ Complete
- [x] Deploy Argo Workflows v3.7.8 (Helm chart 0.47.1)
- [x] Configure sync-wave: -8 (after LocalStack, before Velero)
- [x] Set up artifact repository (Backblaze B2 - pending bucket permissions fix)
- [x] Configure resource limits for Pi cluster constraints:
  - Controller: 50m CPU / 128Mi RAM (request), 100m / 256Mi (limit)
  - Server: 25m CPU / 64Mi RAM (request), 50m / 128Mi (limit)
- [x] Enable Prometheus ServiceMonitor for workflow metrics
- [ ] Create Grafana dashboards for workflow monitoring
- [ ] Set up AlertManager rules for workflow failures

**Known Issues:**
- B2 artifact storage returns "not entitled" - archiveLogs disabled temporarily
- NetworkPolicy disabled temporarily while debugging API egress rules

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
- [ ] **Harbor** - Container registry with vulnerability scanning
- [ ] Build and deployment automation for ARM64 custom containers

---

## 🌐 **Network & Access Management**

### 14. **CoreDNS Customization**
- [ ] Document current CoreDNS configuration
- [ ] Custom DNS records for internal services
- [ ] DNS-based service discovery patterns
- [ ] DNS monitoring and troubleshooting tools
- [ ] Consider DNS caching optimizations

### 15. **VPN & Remote Access**
- [ ] Evaluate **Tailscale** vs **WireGuard** for cluster access
- [ ] Deploy chosen VPN solution
- [ ] **oauth2-proxy** - Single Sign-On (SSO) integration
- [ ] Multi-factor authentication for critical services
- [ ] Document remote access policies and procedures
- [ ] VPN performance monitoring

---

## 🔧 **Operational Improvements**

### 16. **Documentation Enhancements**
- [ ] Create operational runbooks for common tasks (pod restarts, rollbacks, etc.)
- [ ] Document disaster recovery procedures (node failure, control plane failure)
- [ ] Capacity planning documentation with growth projections
- [ ] Create network topology diagrams to complement the existing network-info.md documentation
- [ ] Performance baseline documentation
- [ ] Document on-call procedures and escalation paths
- [ ] Create k8s-docs-n37 guides for: cert-manager, metallb, ingress-nginx, localstack

### 17. **Testing & Validation**
- [ ] Chaos engineering with **Litmus** (lighter than Chaos Monkey)
- [ ] Load testing framework for applications
- [ ] Backup and restore testing automation (monthly validation)
- [ ] Network failure simulation and recovery testing
- [ ] Performance regression testing
- [ ] Test node drain and pod eviction scenarios

### 18. **Resource Optimization**
- [ ] Audit resource requests/limits across all workloads
- [ ] Identify over-provisioned pods
- [ ] Implement pod resource quotas per namespace
- [ ] Storage capacity planning and alerting
- [ ] Network bandwidth monitoring and optimization
- [ ] Consider implementing Vertical Pod Autoscaler (VPA)

---

## 🌟 **Nice to Have**

### 19. **Pi Cluster Specific Monitoring**
- [ ] Power consumption tracking (requires PoE monitoring or UPS integration)
- [ ] Track PoE power draw per node
- [ ] NVMe thermal throttling detection
- [ ] Track undervoltage events
- [ ] ARM64-specific performance optimizations

### 20. **Application Deployments**
- [ ] Home Assistant integration
- [ ] Private container registry (Harbor or similar)
- [ ] Internal wiki or knowledge base
- [ ] Status page (Uptime Kuma or similar)
- [ ] Internal chat/collaboration tool

### 21. **Observability Maturity Enhancements**
- [ ] **Distributed Tracing** - Evaluate Jaeger or Tempo for trace collection
- [ ] **Continuous Profiling** - Pyroscope for application performance profiling
- [ ] **Service Level Objectives (SLOs)** - Define and monitor SLOs for critical services
- [ ] **Error Budget Tracking** - Automated SLO/error budget reporting
- [ ] **Anomaly Detection** - ML-based anomaly detection for metrics (Prometheus AI/ML)
- [ ] **Synthetic Monitoring** - Automated user journey testing

### 22. **Disaster Recovery Testing**
- [ ] **Monthly DR Drills** - Automated disaster recovery validation
- [ ] **Chaos Engineering** - Controlled failure injection (Litmus)
- [ ] **Velero Restore Testing** - Automated monthly PVC restore validation
- [ ] **Network Partition Testing** - Simulate network failures
- [ ] **Node Failure Scenarios** - Test cluster resilience to node loss
- [ ] **Control Plane Failure** - Test etcd backup/restore procedures
- [ ] **DR Runbook Automation** - Convert manual runbooks to Argo Workflows

### 23. **Cost Optimization & Efficiency**
- [ ] **Resource Right-Sizing** - Analyze actual vs requested resources
- [ ] **Spot/Preemptible Instances** - Not applicable for bare metal, document for future cloud consideration
- [ ] **Storage Optimization** - Compress old logs, optimize retention policies
- [ ] **Network Egress Optimization** - Monitor and optimize outbound traffic
- [ ] **Power Consumption Tracking** - PoE monitoring and efficiency analysis
- [ ] **Carbon Footprint** - Calculate and optimize cluster carbon footprint

---

## 📅 **Implementation Priorities**

Items are organized by priority, not by timeline. Focus on:

### **Phase 1: Foundation & Reliability**
1. Backup strategy (Velero + critical PVC backups)
2. Enhanced alerting (AlertManager notifications)
3. Metrics server deployment
4. Blackbox exporter for endpoint monitoring

### **Phase 2: Security & Observability** ✅ Complete
1. ✅ Security scanning (Trivy Operator)
2. ✅ Secrets management migration (SealedSecrets)
3. ✅ Blackbox exporter for endpoint monitoring
4. ✅ Custom Grafana dashboards

### **Phase 3: Advanced Features** ✅ Complete
1. ✅ GitOps enhancements (Renovate deployed 2026-01-23)
2. ✅ Network policies implementation (5 namespaces isolated 2026-01-24)
3. ✅ Development tools and CI/CD (Argo Workflows deployed 2026-01-24)
4. Service mesh evaluation and potential deployment

### **Phase 4: Optimization & Expansion**
1. Resource optimization and VPA
2. Chaos engineering and resilience testing
3. Advanced networking and VPN
4. Additional application deployments

---

## 🔄 **ArgoCD Sync Wave Optimization**

### Current Sync Wave Order (Validated 2026-01-11)

```
Wave -50: argocd (self-management)
Wave -35: metal-lb, pi-hole (networking foundation)
Wave -30: synology-csi (storage driver)
Wave -25: sealed-secrets (secrets management)
Wave -20: unipoller (UniFi metrics collection)
Wave -15: kube-prometheus-stack (monitoring stack)
Wave -12: loki (log aggregation)
Wave -11: promtail (log collection)
Wave -10: cert-manager, external-dns, metrics-server (certificates & DNS & metrics)
Wave  -8: argo-workflows (CI/CD) ✅
Wave  -7: localstack (S3 mock for Velero)
Wave  -5: velero (backup solution)
```

### ✅ Resolved Issues

**1. LocalStack Dependency Conflict** ✅ FIXED
- **Problem**: Velero (wave -5) depended on LocalStack (wave 0)
- **Solution**: LocalStack moved to wave -7, now deploys before Velero
- **Status**: Resolved - Velero BackupStorageLocation is available on startup

**2. Pi-hole Early Deployment**
- **Current**: Wave -35 (same as MetalLB)
- **Analysis**: Could move to -30 or -25 (only needs MetalLB for LoadBalancer IP)
- **Decision**: Keep at -35 for early DNS availability (acceptable)

**3. UniFi Poller Timing**
- **Current**: Wave -20 (before monitoring stack)
- **Analysis**: Could move to -10 or -5 (no critical dependencies)
- **Decision**: Keep at -20 (metrics available when Prometheus starts)

### ✅ Validated Dependencies

- ✅ **ArgoCD** (-50) → Deploys itself first (correct)
- ✅ **MetalLB** (-35) → Provides LoadBalancer IPs before services need them
- ✅ **Synology CSI** (-30) → Storage driver available before PVCs
- ✅ **kube-prometheus-stack** (-15) → Uses CSI for 50Gi Prometheus PVC
- ✅ **Loki** (-12) → Uses CSI for 20Gi log storage PVC
- ✅ **Promtail** (-11) → Depends on Loki being available
- ✅ **cert-manager** (-10) → Independent, issues certs on-demand
- ✅ **external-dns** (-10) → Works with TLS Ingresses (safe timing)
- ✅ **LocalStack** (-7) → S3 mock available before Velero
- ✅ **Velero** (-5) → Uses CSI and LocalStack S3

### 🎯 Recommended Actions

1. **Future**: Consider sync wave for Argo Workflows at `-8`

2. **Optional Optimizations**:
   - Move UniFi Poller to -10 (aligns with other non-critical monitoring)
   - Move Pi-hole to -30 (after MetalLB, with CSI)

### 📊 Sync Wave Best Practices

**Critical Infrastructure** (Wave -50 to -30):
- Self-managed components (ArgoCD)
- Networking foundation (MetalLB, CNI)
- Storage drivers (Synology CSI)

**Monitoring & Logging** (Wave -20 to -10):
- Metrics collection (UniFi Poller)
- Monitoring stack (Prometheus, Grafana, AlertManager)
- Log aggregation (Loki, Promtail)
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
