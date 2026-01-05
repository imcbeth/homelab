# Technical Resume

## Professional Summary

DevOps Engineer and Infrastructure Architect with hands-on expertise in Kubernetes, cloud-native technologies, and infrastructure automation. Proven ability to design, implement, and maintain production-grade infrastructure using GitOps principles, comprehensive monitoring, and enterprise-grade tools. Specializes in building scalable, resilient systems with strong emphasis on automation, observability, and infrastructure-as-code practices.

## Technical Skills

### Container Orchestration & Cloud Native
- **Kubernetes:** Production cluster management, resource optimization, multi-node deployments
- **Container Technologies:** containerd runtime, Docker, ARM64 container builds
- **Service Mesh & Networking:** Calico CNI, VLAN segmentation, network policies
- **Storage Orchestration:** CSI drivers, iSCSI integration, persistent volume management

### GitOps & CI/CD
- **GitOps Tools:** ArgoCD for automated application deployment and synchronization
- **Infrastructure as Code:** Terraform for network infrastructure automation
- **Version Control:** Git workflows, branch strategies, code review processes
- **Secrets Management:** git-crypt, Kubernetes secrets, secure credential handling

### Monitoring & Observability
- **Metrics & Monitoring:** Prometheus, Grafana, AlertManager, PromQL
- **Logging:** Loki, Promtail, centralized log aggregation
- **Specialized Exporters:** Blackbox Exporter, SNMP Exporter, UniFi Poller
- **Dashboard Design:** Custom Grafana dashboards, data visualization
- **Network Monitoring:** UniFi device monitoring, bandwidth tracking, client metrics

### Networking & Infrastructure
- **Network Engineering:** VLAN configuration, DNS, DHCP, network segmentation
- **Enterprise Networking:** UniFi ecosystem (UDM Pro, USW-Pro-24-POE)
- **DNS Management:** External-DNS with Cloudflare and UniFi providers
- **Load Balancing:** MetalLB for bare-metal Kubernetes
- **Certificate Management:** Cert-Manager, TLS automation

### Backup & Disaster Recovery
- **Backup Solutions:** Velero, Kopia integration
- **Data Protection:** PVC backup strategies, retention policies
- **High Availability:** Multi-node cluster design, persistent storage strategies

### Scripting & Automation
- **Bash Scripting:** Advanced automation, API integration, data transformation
- **YAML/JSON Processing:** jq, configuration management
- **API Integration:** RESTful APIs, authentication, error handling
- **Validation Tools:** Pre-commit hooks, manifest validation

### Development Tools & Practices
- **Documentation:** Docusaurus, technical writing, comprehensive guides
- **Code Quality:** Pre-commit hooks, linting, build validation
- **Project Management:** TODO tracking, issue management, code ownership

## Major Projects

### Production Kubernetes Homelab Cluster
*Enterprise-Grade Infrastructure on Raspberry Pi 5 Hardware*

**Technologies:** Kubernetes 1.35, ArgoCD, Prometheus, Grafana, Loki, Calico, Synology NAS

**Key Achievements:**
- Designed and deployed production-ready 5-node Kubernetes cluster on ARM64 architecture
- Implemented complete GitOps workflow managing 25+ applications with ArgoCD
- Built comprehensive monitoring stack with Prometheus, Grafana, and custom dashboards
- Integrated enterprise storage solution using Synology NAS with iSCSI CSI driver
- Established centralized logging with Loki/Promtail with 7-day retention
- Configured multi-VLAN network architecture for security and isolation
- Implemented automated backup strategy using Velero and Kopia

**Infrastructure Highlights:**
- **High Availability:** Multi-node design with persistent storage and data retention
- **Security:** VLAN segmentation, network policies, encrypted secrets management
- **Automation:** Fully GitOps-managed with self-healing capabilities
- **Observability:** 20+ Grafana dashboards, comprehensive metrics, and alerting
- **Documentation:** Complete technical documentation site with 50+ guides

**Hardware Configuration:**
- 5x Raspberry Pi 5 (16GB RAM each)
- 5x 256GB NVMe SSDs with PoE+ power
- Synology NAS for persistent storage
- UniFi networking equipment (UDM Pro, USW-Pro-24-POE)

### UniFi Terraform Configuration Generator
*Automated Infrastructure-as-Code Generation for Network Infrastructure*

**Technologies:** Terraform, Bash, UniFi API, jq, JSON processing

**Key Achievements:**
- Developed comprehensive bash toolkit for automatic Terraform configuration generation
- Built API integration for extracting complete UniFi controller configurations
- Implemented cross-platform compatibility (Linux, macOS, containers)
- Created automatic import generation for existing infrastructure
- Designed data transformation pipeline for complex network configurations
- Integrated with CI/CD workflows using GitHub Actions

**Capabilities:**
- **Complete Resource Coverage:** Devices, networks, firewall rules, port forwarding, VLANs, wireless networks
- **Automation:** Automatic terraform import command generation
- **Disaster Recovery:** Code-based infrastructure reconstruction
- **Version Control:** Network configuration history and change tracking

### Kubernetes Documentation Portal
*Comprehensive Technical Documentation Site*

**Technologies:** Docusaurus, TypeScript, React, Markdown, GitHub Pages

**Key Achievements:**
- Created professional documentation site with 50+ comprehensive guides
- Organized content into structured sections (installation, monitoring, networking, troubleshooting)
- Implemented automated build and deployment pipeline
- Designed user-friendly navigation with role-based learning paths
- Integrated pre-commit validation for content quality

## Application Deployments

**Successfully deployed and manage:**
- **Core Infrastructure:** ArgoCD, MetalLB, Cert-Manager, External-DNS, Metrics-Server
- **Monitoring Stack:** Prometheus, Grafana, AlertManager, Blackbox Exporter, SNMP Exporter
- **Logging:** Loki, Promtail
- **Network Services:** Pi-hole, UniFi Poller
- **Storage:** Synology CSI Driver
- **Backup:** Velero with Kopia
- **Development:** LocalStack

## Technical Accomplishments

### Infrastructure Engineering
- Architected and implemented multi-VLAN network design with proper segmentation
- Integrated enterprise NAS storage with Kubernetes using iSCSI CSI driver
- Established GitOps workflow enabling declarative infrastructure management
- Designed and deployed production-grade monitoring and alerting infrastructure

### Automation & Efficiency
- Automated network configuration management through custom Terraform generator
- Implemented comprehensive validation scripts for manifest quality assurance
- Created self-documenting infrastructure with extensive technical guides
- Developed disaster recovery procedures and backup automation

### DevOps Practices
- Implemented GitOps methodology for 25+ applications
- Established monitoring best practices with custom dashboards and alerting
- Created comprehensive documentation covering all aspects of infrastructure
- Applied infrastructure-as-code principles across networking and Kubernetes layers

### Problem Solving
- Resolved ARM64 compatibility issues through custom container builds
- Optimized resource allocation for Raspberry Pi cluster constraints
- Implemented effective log management with retention policies
- Designed efficient storage strategies balancing performance and cost

## Documentation & Knowledge Sharing

- **Technical Writing:** Authored 50+ comprehensive guides covering installation, configuration, and troubleshooting
- **Architecture Documentation:** Detailed system design, network topology, and component relationships
- **Runbooks:** Step-by-step procedures for common operations and maintenance
- **Best Practices:** Documented lessons learned and recommended approaches
- **Skills Development:** Created learning paths for different experience levels

## Tools & Technologies

**Container & Orchestration:** Kubernetes, Docker, containerd, Helm, Kustomize, ArgoCD

**Monitoring & Observability:** Prometheus, Grafana, Loki, Promtail, AlertManager, various exporters

**Networking:** Calico, MetalLB, External-DNS, UniFi ecosystem, VLANs

**Infrastructure as Code:** Terraform, Bash scripting, YAML/JSON configuration

**Storage:** Synology CSI, iSCSI, Velero, Kopia

**Development:** Git, GitHub Actions, Docusaurus, TypeScript, Markdown

**Operating Systems:** Linux (Raspberry Pi OS), ARM64 architecture

**Hardware:** Raspberry Pi 5, NVMe storage, PoE networking, Synology NAS, UniFi equipment

## Project Links

- **Homelab Repository:** [github.com/imcbeth/homelab](https://github.com/imcbeth/homelab)
- **Documentation Site:** [imcbeth.github.io/k8s-docs-n37](https://imcbeth.github.io/k8s-docs-n37/)
- **Terraform Generator:** [github.com/imcbeth/unifi-tf-generator](https://github.com/imcbeth/unifi-tf-generator)

---

*This resume showcases practical, hands-on experience building and maintaining production-grade infrastructure using modern DevOps practices and enterprise tools, all demonstrated through comprehensive, documented homelab projects.*
