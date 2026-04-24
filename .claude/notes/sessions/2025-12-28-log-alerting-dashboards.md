# 2025-12-28 (Afternoon/Evening): Log-Based Alerting + Dashboard Migration Audit

**Completed Work:**
- Dashboard Migration Audit - Verified all Grafana dashboards in GitOps
- Migrated 13 Uncommitted Dashboards - Exported and created ConfigMaps
- Log-Based Alerting - Deployed Loki ruler with 11 alerting rules

**Pull Requests:**
- PR #173: Migrate 13 uncommitted Grafana dashboards to ConfigMaps (MERGED)
- PR #174: Implement log-based alerting with Loki ruler (MERGED)

**Dashboard Migration:**
Migrated 13 manually imported dashboards to GitOps:
- **Loki folder (4):** Logging Dashboard via Loki, Loki Dashboard, Stack Monitoring, Global Metrics
- **Synology folder (2):** Synology Dashboard, Synology Dashboard2
- **UniFi folder (7):** Access Points, Clients, DPI, Gateway, PDU, Sites, Switches

Total dashboard count: **43 dashboards** (17 custom + 26 kube-prometheus-stack)

**Log-Based Alerting (11 rules across 4 categories):**

1. **Error Pattern Detection:**
   - HighErrorLogRate: Errors >1/sec for 5m (warning)
   - CriticalErrorLogs: Critical/fatal logs >0.1/sec for 2m (critical)

2. **Pod Failure Detection:**
   - CrashLoopBackOffDetected (critical)
   - OOMKilledDetected (critical)
   - PersistentPodRestarts: >5 restarts in 15m (warning)

3. **Application Error Detection:**
   - HighHTTP5xxErrorRate (warning)
   - DatabaseConnectionErrors (warning)

4. **Security Event Detection:**
   - AuthenticationFailures (warning)
   - SuspiciousActivity (critical)

**Issue Resolved: Grafana API Authentication Failed**
Used `grafana cli admin reset-admin-password` to temporarily access API for dashboard export.

**Files Modified:**
- `manifests/base/grafana/dashboards/` - 13 new dashboard ConfigMaps
- `manifests/base/loki/values.yaml` - Enabled ruler, AlertManager integration
- `manifests/base/loki/loki-alerts.yaml` - Created 11 PrometheusRule alerts
- `.pre-commit-config.yaml` - Excluded Grafana dashboards from yamllint
