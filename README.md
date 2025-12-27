## Homelab

Outline of setup / repo framework / bits of helpful code for my k8s cluster

### Storage Infrastructure
- **Synology CSI Driver Integration**: Deployed Synology CSI driver for persistent storage support
  - Added iSCSI storage class configuration: `synology-iscsi-retain`
  - Integrated with Synology NAS at `10.0.1.204` for block storage
  - Configured retention policies for persistent volume claims
  - Storage now used for Pi-hole data persistence and Prometheus monitoring stack

### Network Migration to UniFi
- **UniFi Network Migration**: Migrated infrastructure monitoring to UniFi network stack
  - Deployed UniFi Poller for network metrics collection
  - Configured UniFi controller integration at `10.0.1.1`
  - Added Prometheus scraping configuration for UniFi metrics (20s interval)
  - Site configuration: `n37-gw`
  - Monitoring includes network performance, device status, and traffic analytics

### Monitoring Stack Enhancements
- **Prometheus Stack Updates**: Enhanced monitoring capabilities
  - Updated kube-prometheus-stack configuration
  - Added UniFi network monitoring integration
  - Improved storage configuration with Synology iSCSI backend
  - Enhanced Grafana dashboards for network visibility

## `/apps`

Containerized applications:

* `/DockerFiles` - Containers I have created for my kubernetes cluster (arm64)


## `/manifests`

* `/applications` - contains ArgoCD applications deploying all other manifests
* `/base` - contains kustomizations + charts to deploy the applications

### Storage Configuration
- **Synology CSI**: Provides persistent storage via iSCSI from Synology NAS
- **Pi-hole**: Now uses persistent volume claims for data retention
- **Prometheus**: Configured with 50Gi persistent storage for metrics retention

### Network Monitoring
- **UniFi Poller**: Collects metrics from UniFi network infrastructure
- **Prometheus Integration**: Scrapes UniFi metrics for network observability
