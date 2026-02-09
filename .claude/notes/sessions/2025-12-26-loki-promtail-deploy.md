# 2025-12-26 (Post-Midnight): Deploy Loki + Promtail Log Aggregation Stack

**Completed Work:**
- Deployed Grafana Loki in SingleBinary mode for centralized log aggregation
- Deployed Promtail DaemonSet (5 pods, one per node) for log collection
- Fixed initial deployment issue (Promtail not included in Loki chart v6.x)
- Configured Grafana datasource auto-discovery

**Pull Requests:**
- **PR #83:** [Merged] Deploy Loki + Promtail logging stack
- **PR #84:** [Ready] Fix: Add Promtail deployment for log collection

**Architecture:**
- Promtail DaemonSet (5 pods): 50m/100m CPU, 64Mi/128Mi memory each
- Loki SingleBinary (1 pod): 200m/500m CPU, 384Mi/768Mi memory
- Storage: 20Gi PVC on Synology
- Retention: 7 days

**Issue: Promtail Not Included in Loki Chart v6.x**

Root Cause: `grafana/loki` chart version 6.49.0 split Loki and Promtail into separate Helm charts. The `promtail.enabled: true` setting was ignored.

Solution: Deploy Promtail using separate `grafana/promtail` chart with sync-wave -11.

**Configuration:**
- Loki: Namespace `loki`, Schema v13 (TSDB store)
- Promtail: hostNetwork false, hostPID true
- Client URL: `http://loki.loki.svc.cluster.local:3100/loki/api/v1/push`

**Query Examples:**
```logql
{namespace="default"}                  # All default namespace logs
{namespace="default"} |= "error"       # Filter for errors
{pod=~"prometheus.*"}                  # Prometheus pod logs
{node="node04"}                        # All logs from node04
```

**Files Created:**
- `manifests/applications/loki.yaml`
- `manifests/base/loki/values.yaml`
- `manifests/base/loki/loki-datasource.yaml`
- `manifests/applications/promtail.yaml`
- `manifests/base/promtail/values.yaml`
