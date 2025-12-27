# Homelab TODO & Improvements

## ✅ **Recently Completed** (December 2025)

### Monitoring & Observability
- **SNMP Monitoring for Synology** - Deployed SNMP exporter, scraping NAS metrics (disk health, temperature, RAID status)
- **Node Exporter for Pi Cluster** - DaemonSet running on all 5 nodes, monitoring CPU, memory, disk, network
- **Log Aggregation** - Loki + Promtail deployed, 7-day retention, collecting logs from all pods on all nodes (including control-plane)
- **Prometheus Stack Fixes** - Fixed node-exporter scraping, Grafana PVC issues, cleaned up control plane monitoring
- **Control Plane Monitoring** - Re-enabled kube-scheduler and kube-controller-manager monitoring
- **ServiceMonitor Enablement** - Enabled metrics collection for Loki and Promtail

### Documentation
- **Comprehensive Docs Site** - k8s-docs-n37 Docusaurus site with application guides
- **Loki Application Guide** - Complete documentation for Loki + Promtail deployment
- **SNMP Exporter Guide** - Synology monitoring documentation
- **Troubleshooting Guides** - Monitoring stack and common issues documented

---

## 🎯 **High Priority**

### 1. **External-DNS Deployment**
> **Status:** Manifest exists but not deployed to cluster
> **Blocker:** Needs UniFi RFC2136 configuration

- [ ] Complete UniFi UDR7 RFC2136 setup (TSIG key generation)
- [ ] Apply external-dns ArgoCD Application to cluster
- [ ] Verify Cloudflare provider creating DNS records
- [ ] Verify UniFi RFC2136 provider creating internal DNS
- [ ] Test automatic DNS creation for new Ingresses

**Note:** See CLAUDE_NOTES.md 2025-12-26 Afternoon session for deployment details.

### 2. **Blackbox Exporter**
- [ ] Deploy blackbox exporter for endpoint monitoring
- [ ] Monitor external services availability (DNS, HTTP/HTTPS)
- [ ] SSL certificate expiry monitoring for k8s.n37.ca domain
- [ ] Network latency and response time tracking
- [ ] Add alerts for service downtime
- [ ] Monitor Synology NAS web interface availability

### 3. **Enhanced Alerting**
- [ ] Configure AlertManager webhook to Discord/Slack/Telegram
- [ ] Implement tiered alerting (warning → critical)
- [ ] Set up predictive alerts for disk space (Prometheus, Loki, Synology)
- [ ] Create alerts for NAS disk failures and high temperature
- [ ] Create runbooks for common alert scenarios
- [ ] Test alert routing and escalation

### 4. **Backup Strategy** ⭐ Critical
- [ ] **Velero** - Deploy for Kubernetes cluster backup to Synology
- [ ] **Restic** or **Kopia** - Application data backup
- [ ] Backup critical PVCs (Prometheus 50Gi, Grafana 5Gi, Loki 20Gi)
- [ ] ArgoCD configuration backup automation
- [ ] Schedule regular backup testing and restore procedures
- [ ] Document backup and restore processes
- [ ] Test disaster recovery scenarios

---

## 🔍 **Monitoring & Observability Enhancements**

### 5. **Custom Dashboards**
- [ ] Pi cluster temperature monitoring dashboard (per-node CPU temps)
- [ ] Node resource utilization dashboard (CPU, memory, disk per node)
- [ ] Network utilization by VLAN/segment
- [ ] Storage performance metrics (iSCSI latency, IOPS, throughput)
- [ ] Loki log volume and ingestion rate dashboard
- [ ] Application performance monitoring (APM) dashboard
- [ ] Create unified "cluster health" dashboard

### 6. **Metrics Server Deployment**
- [ ] Deploy metrics-server for kubectl top commands
- [ ] Enable Horizontal Pod Autoscaling (HPA) capabilities
- [ ] Configure for resource-constrained Pi environment

### 7. **Log-Based Alerting**
- [ ] Set up Loki alerting rules for error patterns
- [ ] Alert on CrashLoopBackOff events
- [ ] Alert on OOMKilled events
- [ ] Alert on persistent pod failures
- [ ] Create log-based SLO monitoring

---

## 🛡️ **Security & Compliance**

### 8. **Security Scanning & Runtime Protection**
- [ ] **Trivy Operator** - Container vulnerability scanning
- [ ] **Falco** - Runtime security monitoring and threat detection
- [ ] **OPA Gatekeeper** - Policy enforcement and admission control
- [ ] Security policy definitions for workloads
- [ ] Compliance reporting and alerting
- [ ] Scan existing images for vulnerabilities

### 9. **Secrets Management**
- [ ] Evaluate **External Secrets Operator** vs **Sealed Secrets**
- [ ] Deploy chosen secrets management solution
- [ ] Migrate existing git-crypt secrets to managed solution
- [ ] Set up secret rotation automation for certificates
- [ ] Document secrets management procedures
- [ ] Integrate with ArgoCD for automated secret sync

### 10. **Network Policies**
- [ ] Define NetworkPolicies for namespace isolation
- [ ] Implement ingress/egress rules for sensitive workloads
- [ ] Document network segmentation strategy
- [ ] Test policy enforcement

---

## 🚀 **Platform Enhancements**

### 11. **Service Mesh Evaluation**
- [ ] Research lightweight service mesh options for Pi cluster
- [ ] Evaluate **Linkerd** (lightweight, Pi-friendly)
- [ ] Evaluate **Istio** (full-featured but resource-intensive)
- [ ] Proof-of-concept deployment in test namespace
- [ ] Performance impact analysis on Pi 5 cluster
- [ ] Document decision and implementation plan

### 12. **Ingress Enhancements**
- [ ] Document current nginx-ingress configuration
- [ ] Implement rate limiting for public endpoints
- [ ] Add ModSecurity WAF rules
- [ ] Configure geo-blocking if needed
- [ ] Monitor ingress performance and errors

---

## 🏗️ **Infrastructure & DevOps**

### 13. **GitOps Enhancements**
- [ ] **Renovate** - Automated dependency updates for Helm charts
- [ ] Pre-commit hooks for Kubernetes manifest validation (kubeval, kustomize)
- [ ] Automated testing pipeline for infrastructure changes
- [ ] Expand GitOps workflow documentation
- [ ] Consider multi-cluster ArgoCD setup for dev/staging

### 14. **Development & CI/CD Tools**
- [ ] Evaluate **Gitea** vs **GitLab** for self-hosted git
- [ ] **Harbor** - Container registry with vulnerability scanning
- [ ] **Tekton** or **Argo Workflows** - CI/CD pipeline automation
- [ ] Build and deployment automation for ARM64 custom containers
- [ ] Integration with existing ArgoCD setup
- [ ] Consider resource requirements on Pi cluster

---

## 🌐 **Network & Access Management**

### 15. **CoreDNS Customization**
- [ ] Document current CoreDNS configuration
- [ ] Custom DNS records for internal services
- [ ] DNS-based service discovery patterns
- [ ] DNS monitoring and troubleshooting tools
- [ ] Consider DNS caching optimizations

### 16. **VPN & Remote Access**
- [ ] Evaluate **Tailscale** vs **WireGuard** for cluster access
- [ ] Deploy chosen VPN solution
- [ ] **oauth2-proxy** - Single Sign-On (SSO) integration
- [ ] Multi-factor authentication for critical services
- [ ] Document remote access policies and procedures
- [ ] VPN performance monitoring

---

## 🔧 **Operational Improvements**

### 17. **Documentation Enhancements**
- [ ] Create operational runbooks for common tasks (pod restarts, rollbacks, etc.)
- [ ] Document disaster recovery procedures (node failure, control plane failure)
- [ ] Capacity planning documentation with growth projections
- [ ] Create network topology diagrams to complement the existing network-info.md documentation
- [ ] Performance baseline documentation
- [ ] Document on-call procedures and escalation paths
- [ ] Create k8s-docs-n37 guides for: cert-manager, metallb, ingress-nginx, localstack

### 18. **Testing & Validation**
- [ ] Chaos engineering with **Litmus** (lighter than Chaos Monkey)
- [ ] Load testing framework for applications
- [ ] Backup and restore testing automation (monthly validation)
- [ ] Network failure simulation and recovery testing
- [ ] Performance regression testing
- [ ] Test node drain and pod eviction scenarios

### 19. **Resource Optimization**
- [ ] Audit resource requests/limits across all workloads
- [ ] Identify over-provisioned pods
- [ ] Implement pod resource quotas per namespace
- [ ] Storage capacity planning and alerting
- [ ] Network bandwidth monitoring and optimization
- [ ] Consider implementing Vertical Pod Autoscaler (VPA)

---

## 🌟 **Nice to Have**

### 20. **Pi Cluster Specific Monitoring**
- [ ] Power consumption tracking (requires PoE monitoring or UPS integration)
- [ ] Track PoE power draw per node
- [ ] NVMe thermal throttling detection
- [ ] Track undervoltage events
- [ ] ARM64-specific performance optimizations

### 21. **Application Deployments**
- [ ] Home Assistant integration
- [ ] Private container registry (Harbor or similar)
- [ ] Internal wiki or knowledge base
- [ ] Status page (Uptime Kuma or similar)
- [ ] Internal chat/collaboration tool

---

## 📅 **Implementation Priorities**

Items are organized by priority, not by timeline. Focus on:

### **Phase 1: Foundation & Reliability**
1. External-DNS deployment (unblock pending work)
2. Backup strategy (Velero + critical PVC backups)
3. Enhanced alerting (AlertManager notifications)
4. Metrics server deployment

### **Phase 2: Security & Observability**
1. Security scanning (Trivy Operator)
2. Secrets management migration
3. Blackbox exporter for endpoint monitoring
4. Custom Grafana dashboards

### **Phase 3: Advanced Features**
1. Service mesh evaluation and potential deployment
2. GitOps enhancements (Renovate)
3. Network policies implementation
4. Development tools and CI/CD

### **Phase 4: Optimization & Expansion**
1. Resource optimization and VPA
2. Chaos engineering and resilience testing
3. Advanced networking and VPN
4. Additional application deployments

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
