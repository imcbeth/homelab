# Homelab TODO & Improvements

## 🔍 **Monitoring & Observability Enhancements**

### 1. **SNMP Monitoring for Synology** ⭐ Priority
- [ ] Deploy SNMP exporter for Synology NAS monitoring
- [ ] Configure Prometheus scrape config for SNMP metrics
- [ ] Add Grafana dashboards for NAS performance, disk health, temperature
- [ ] Set up alerts for disk failures, high temperature, storage capacity

```yaml
# Add to prometheus scrape configs
- job_name: 'synology-snmp'
  static_configs:
    - targets: ['10.0.1.204']
  metrics_path: /snmp
  params:
    module: [synology]
  relabel_configs:
    - source_labels: [__address__]
      target_label: __param_target
    - source_labels: [__param_target]
      target_label: instance
    - target_label: __address__
      replacement: snmp-exporter:9116
```

### 2. **Node Exporter for Pi Cluster**
- [ ] Deploy node-exporter on all 5x Pi 5 nodes
- [ ] Monitor CPU temperature and throttling
- [ ] Track NVMe SSD health and performance metrics
- [ ] Memory usage and available capacity monitoring
- [ ] Network interface statistics

### 3. **Blackbox Exporter**
- [ ] Deploy blackbox exporter for endpoint monitoring
- [ ] Monitor external services availability (DNS, HTTP/HTTPS)
- [ ] SSL certificate expiry monitoring
- [ ] Network latency and response time tracking
- [ ] Add alerts for service downtime

## 🛡️ **Security & Backup**

### 4. **Backup Strategy**
- [ ] **Velero** - Deploy for Kubernetes cluster backup
- [ ] **Restic** - Set up application data backup to Synology NAS
- [ ] **ArgoCD backup** - Automate app-of-apps configuration backup
- [ ] Schedule regular backup testing and restore procedures
- [ ] Document backup and restore processes

### 5. **Security Scanning & Runtime Protection**
- [ ] **Trivy Operator** - Container vulnerability scanning
- [ ] **Falco** - Runtime security monitoring and threat detection
- [ ] **OPA Gatekeeper** - Policy enforcement and admission control
- [ ] Security policy definitions for workloads
- [ ] Compliance reporting and alerting

## 🚀 **Platform Enhancements**

### 6. **Service Mesh**
- [ ] Evaluate **Istio** vs **Linkerd** for the Pi cluster
- [ ] Implement traffic management and load balancing
- [ ] Add observability for service-to-service communication
- [ ] Implement security policies and mTLS
- [ ] Circuit breaker and retry policies

### 7. **Log Aggregation**
- [ ] Deploy **Loki + Promtail** stack for centralized logging
- [ ] Integrate with existing Grafana instance
- [ ] Configure log retention policies
- [ ] Set up log-based alerting for errors and anomalies
- [ ] Create log dashboards for application troubleshooting

### 8. **Secrets Management**
- [ ] **External Secrets Operator** - Use Synology as secrets backend
- [ ] **Sealed Secrets** - GitOps-friendly encrypted secrets
- [ ] Migrate existing secrets to managed solution
- [ ] Set up secret rotation automation
- [ ] Document secrets management procedures

## 📊 **Advanced Monitoring & Dashboards**

### 9. **Custom Dashboards**
- [ ] Pi cluster temperature monitoring dashboard
- [ ] Power consumption tracking (if UPS available)
- [ ] Network utilization by VLAN/segment
- [ ] Storage performance metrics (iSCSI latency, IOPS)
- [ ] Application performance monitoring (APM)

### 10. **Alerting Improvements**
- [ ] Configure **AlertManager** webhook to Discord/Slack
- [ ] Implement tiered alerting (warning → critical → page)
- [ ] Set up predictive alerts for disk space and temperature
- [ ] Create runbooks for common alert scenarios
- [ ] Test alert routing and escalation

## 🏗️ **Infrastructure & DevOps**

### 11. **GitOps Enhancements**
- [ ] **Renovate** - Automated dependency updates for manifests
- [ ] Evaluate **Flux** as ArgoCD complement for specific workflows
- [ ] Pre-commit hooks for Kubernetes manifest validation
- [ ] Automated testing pipeline for infrastructure changes
- [ ] GitOps workflow documentation

### 12. **Development & CI/CD Tools**
- [ ] **Gitea** or **GitLab** - Self-hosted git repository
- [ ] **Harbor** - Container registry with vulnerability scanning
- [ ] **Tekton** or **Argo Workflows** - CI/CD pipeline automation
- [ ] Build and deployment automation for custom containers
- [ ] Integration with existing ArgoCD setup

## 🌐 **Network & Access Management**

### 13. **DNS & Service Discovery**
- [ ] **CoreDNS** customization for internal service discovery
- [ ] **External-DNS** - Automatic DNS record creation
- [ ] Internal domain setup (.k8s.local or similar)
- [ ] DNS-based load balancing configuration
- [ ] DNS monitoring and troubleshooting tools

### 14. **VPN & Remote Access**
- [ ] **Tailscale** or **WireGuard** - Secure remote access to cluster
- [ ] **oauth2-proxy** - Single Sign-On (SSO) integration
- [ ] Multi-factor authentication setup
- [ ] Remote access policies and user management
- [ ] VPN performance monitoring

## 🔧 **Operational Improvements**

### 15. **Documentation & Knowledge Management**
- [ ] Create operational runbooks for common tasks
- [ ] Document disaster recovery procedures
- [ ] Capacity planning documentation
- [ ] Update network topology diagrams
- [ ] Performance baseline documentation

### 16. **Testing & Validation**
- [ ] Chaos engineering with **Chaos Monkey** or **Litmus**
- [ ] Load testing framework for applications
- [ ] Backup and restore testing automation
- [ ] Network failure simulation and recovery testing
- [ ] Performance regression testing

### 17. **Capacity Planning & Optimization**
- [ ] Resource utilization analysis and optimization
- [ ] Storage capacity planning and alerting
- [ ] Network bandwidth monitoring and optimization
- [ ] Power consumption analysis
- [ ] Cost tracking and optimization (if applicable)

---

## 📅 **Implementation Priority**

### **Phase 1 (Immediate - Next 2 weeks)**
1. SNMP Monitoring for Synology
2. Node Exporter deployment
3. Backup strategy implementation (Velero)

### **Phase 2 (Short term - Next month)**
1. Security scanning (Trivy Operator)
2. Log aggregation (Loki stack)
3. Blackbox exporter for endpoint monitoring

### **Phase 3 (Medium term - Next quarter)**
1. Service mesh evaluation and deployment
2. Secrets management implementation
3. Advanced alerting and dashboards

### **Phase 4 (Long term - Next 6 months)**
1. Development tools and CI/CD
2. Chaos engineering and testing
3. Advanced networking and access management

---

## 📋 **Notes**
- Consider resource constraints on Pi 5 cluster when implementing resource-intensive solutions
- Test all implementations in development namespace before production deployment
- Document all configurations and procedures for maintainability
- Regular review and updates of this TODO list based on cluster evolution