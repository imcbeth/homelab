# 2025-12-28 (Late Morning/Afternoon): Custom Grafana Dashboards Deployment

**Completed Work:**
- Created 4 custom Grafana dashboards (38 total panels)
- Deployed dashboards via ConfigMap sidecar provisioning pattern
- Fixed datasource format (structured with type/uid)
- Fixed temperature dashboard chip label (thermal_thermal_zone0)

**Pull Requests:**
- **PR #164:** [Merged] feat: Add custom Grafana dashboards for Pi cluster monitoring
- **PR #167:** [Merged] fix: Use kustomization base for Grafana dashboards
- **PR #168:** [Open] fix: Update temperature dashboard to use correct chip label

**Dashboards Deployed:**

1. **Pi Cluster Overview (7 panels)** - Cluster stats, per-node CPU/memory, temperature
2. **Node Resource Monitoring (13 panels)** - CPU, memory, disk I/O, network, filesystem
3. **Temperature Monitoring (8 panels)** - 24h timeline, statistics, heatmap, cooling efficiency
4. **Loki Log Analytics (10 panels)** - Ingestion rate, ingester metrics, query performance

**Issue: Kustomize Security Error**
Kustomize doesn't allow referencing files outside base directory using `../`. Solution: Use kustomize `bases:` to include resources from another directory.

**Issue: Temperature Metrics Not Displaying**
Dashboard queried wrong hwmon chip label (`cpu_thermal` vs actual `thermal_thermal_zone0`).

**Dashboard Configuration Standards:**
- Datasource format: `{"type": "prometheus", "uid": "prometheus"}`
- Thresholds: Green < 70%, Yellow 70-90%, Red > 90%
- Temperature: Green < 70°C, Yellow 70-85°C, Red > 85°C

**Files Modified:**
- `manifests/base/grafana/dashboards/pi-cluster-overview.yaml`
- `manifests/base/grafana/dashboards/node-resource-monitoring.yaml`
- `manifests/base/grafana/dashboards/temperature-monitoring.yaml`
- `manifests/base/grafana/dashboards/loki-log-analytics.yaml`
- `manifests/base/grafana/dashboards/kustomization.yaml`
- `manifests/base/kube-prometheus-stack/kustomization.yaml` (updated to use bases)
