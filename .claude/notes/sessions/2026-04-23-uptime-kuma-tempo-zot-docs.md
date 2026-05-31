# 2026-04-23 (Session 2): Uptime Kuma, Grafana Tempo, Zot Docs

## Completed Work

**Zot k8s-docs-n37 Guide (PR #76 — k8s-docs-n37 repo, merged):**
- Full Zot tutorial: purpose, pull-through cache usage, quick start, Web UI, CVE scanning, configuration, troubleshooting
- Fixed Copilot review: sidebars.ts entries, broken relative links (.md extensions), label selectors, StorageClass wording, imagePullSecret example, docs URL
- Resolved merge conflict via `git rebase origin/main --force-with-lease`

**Uptime Kuma (PR #573, merged):**
- `manifests/applications/uptime-kuma.yaml` — ArgoCD Application (sync-wave 0, multi-source Helm)
- `manifests/base/uptime-kuma/values.yaml` — image docker.io/louislam/uptime-kuma:1.23.17-debian, Recreate strategy, 5Gi iSCSI PVC (synology-iscsi-delete), ingress status.k8s.n37.ca
- `manifests/base/network-policies/uptime-kuma/network-policy.yaml` — ingress from ingress-nginx + Prometheus; egress DNS + external HTTP/HTTPS
- Updated ingress-nginx NetworkPolicy with egress to uptime-kuma :3001
- **Copilot fix:** replaced `server-snippets` (creates duplicate `location /` block, requires disabled `allow-snippet-annotations`) with native ingress-nginx WebSocket support via timeout annotations only

**Grafana Tempo (PR #574, merged):**
- `manifests/applications/tempo.yaml` — ArgoCD Application (sync-wave -11, three-source: Helm + values ref + manifest path)
- `manifests/base/tempo/values.yaml` — OTLP receivers (4317/4318), 10Gi iSCSI PVC, 7-day retention, GOMEMLIMIT=900MiB
- `manifests/base/tempo/tempo-datasource.yaml` — Grafana datasource ConfigMap with `tracesToLogs` (not `derivedFields`), `tracesToMetrics`, `serviceMap`, `lokiSearch`
- `manifests/base/network-policies/tempo/namespace.yaml` + `network-policy.yaml` — Istio ambient mesh rules, OTLP ingress from loki, HTTP API from default, istio-system egress
- Updated loki NetworkPolicy: bare OTLP ingress (4317/4318), egress to tempo :4317
- Updated Alloy values: `otelcol.receiver.otlp` + `otelcol.exporter.otlp` for Tempo; `extraPorts` for Service exposure
- Added `uid: loki` to loki-datasource ConfigMap for cross-datasource correlation

## Key Gotchas
- `server-snippets` creates duplicate `location /` block AND requires `allow-snippet-annotations: true` (disabled by default since ingress-nginx v1.9, CVE-2021-25742). Use timeout annotations for WebSocket instead.
- `derivedFields` is a Loki datasource key (log→trace). Tempo datasource uses `tracesToLogs` for trace→log direction.
- Cross-datasource `datasourceUid` references require a fixed `uid:` in the target datasource ConfigMap — Grafana auto-generated UIDs won't match.
- Three-source ArgoCD pattern for Tempo: source 1 = Helm chart, source 2 = `ref: values` only (no path), source 3 = `path:` only (no ref) for extra manifests. Combining ref+path is ambiguous.
- Tempo NetworkPolicy needs Istio ambient mesh rules (bare 15008 ingress, ztunnel link-local, istio-system egress) like all other namespaced policies.

## Pull Requests
- **PR #76 (k8s-docs-n37):** [Merged] docs: add Zot OCI registry guide with pull-through tutorial
- **PR #573:** [Merged] feat: deploy Uptime Kuma status page
- **PR #574:** [Merged] feat: add Grafana Tempo distributed tracing
