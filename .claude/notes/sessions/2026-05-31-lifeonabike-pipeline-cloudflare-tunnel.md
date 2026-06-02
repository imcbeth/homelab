### 2026-05-31 (Late Night): lifeonabike Build Pipeline, Cloudflare Tunnel, Workflow Fixes

**Completed Work:**

**lifeonabike build pipeline — WorkflowTemplate + EventSource + Sensor (PRs #664, #667):**
- **WorkflowTemplate** `lifeonabike-build` in `argo-workflows` namespace: 3-step pipeline (clone → kaniko → rollout-restart)
  - Step 1: `alpine/git:2.43.0` shallow-clones `imcbeth/lifeonabike.ca` using github-clone-token PAT, captures git SHA
  - Step 2: Kaniko builds image, pushes `sha` + `latest` tags to `zot.zot.svc.cluster.local:5000/lifeonabike/lifeonabike.ca`
  - Step 3: `alpine/k8s:1.31.0` runs `kubectl rollout restart deployment/web -n lifeonabike`
- **EventSource** `lifeonabike-github`: GitHub push events, HMAC-verified, main-branch only (`body.ref == 'refs/heads/main'`), exposed at `https://build-webhook.n37.ca`
- **Sensor** `lifeonabike-build`: submits WorkflowTemplate with `revision: main` on each push
- **RBAC**: `lifeonabike-workflow-submitter` Role (sensor SA can submit workflows in argo-workflows), `lifeonabike-deployer` Role (argo-workflow SA can `patch deployment` in lifeonabike)

**Argo Workflows fixes:**
- **PR #669 (ztunnel bypass):** Added `ambient.istio.io/redirection: disabled` to workflow pod metadata — Kaniko pushes to Zot HTTP endpoint; kubectl in rollout-restart step talks to K8s API; both are outside the mesh
- **PR #670 (in-cluster Zot push):** Kaniko destination changed to `zot.zot.svc.cluster.local:5000` with `--insecure` flag. Pod-to-MetalLB HTTPS is broken in-cluster (kubelet pulls at node-level are unaffected and still use `registry.k8s.n37.ca`)
- **PR #671 (ingress-nginx egress):** Added egress from ingress-nginx to lifeonabike:8080 for web traffic routing
- **PR #672 (EventBus + artifacts):** Set EventBus JetStream stream replicas=1 (single-node NATS); switched Argo Workflows artifact storage from Backblaze B2 to LocalStack S3 bucket `argo-workflows`; added `localstack-argo-workflows-setup` PreSync Job to ensure bucket exists
- **PR #673 (sealed secrets):** Converted `lifeonabike-registry-creds` and `github-clone-token` to SealedSecrets; also sealed `lifeonabike-registry-creds` in `lifeonabike` namespace

**Cloudflare Tunnel (PRs #676, #677):**
- Deployed `cloudflare/cloudflared:2024.10.0` Deployment (2 replicas) in `lifeonabike` namespace
- ConfigMap routes: `lifeonabike.ca` → `web.lifeonabike.svc.cluster.local:80`, `www.lifeonabike.ca` → same, `build-webhook.n37.ca` → `lifeonabike-github-eventsource-svc.argo-events.svc.cluster.local:12000`
- Removed old webhook Ingress (no longer needed — Cloudflare Tunnel handles external→internal routing)
- SealedSecret `tunnel-credentials` stores tunnel credentials JSON

**Key Gotchas Discovered:**
- **Pod-to-MetalLB HTTPS broken in-cluster**: Kaniko and other in-cluster clients cannot reach `registry.k8s.n37.ca` (MetalLB LoadBalancer IP) via HTTPS from inside the cluster. Use `zot.zot.svc.cluster.local:5000` (HTTP) for in-cluster pushes. Kubelet image pulls (node-level, not pod-level) still use the external hostname fine.
- **ztunnel resets connections to non-mesh destinations**: Workflow pods that push to Zot HTTP or run kubectl need `ambient.istio.io/redirection: disabled` on the pod to bypass ztunnel interception entirely.
- **EventBus replicas must match NATS cluster size**: With a 1-replica EventBus, set `nats.containerTemplate.resources.replicas: 1` explicitly or NATS will try to form a cluster and hang.
- **Cloudflare Tunnel replaces ingress for external webhook**: No public IP or ingress-nginx rule needed — tunnel connects outbound from the cluster to Cloudflare's edge and routes `build-webhook.n37.ca` inward.
- **git-crypt filename rule catches `*secret*`**: Any file with "secret" in the name is git-crypt encrypted. SealedSecret files must use `*-sealed.yaml` suffix to avoid encryption and yamllint failures.

**Pull Requests:**
- **PR #664:** [Merged] feat(lifeonabike): add in-cluster build pipeline + consolidate k8s manifests
- **PR #666:** [Merged] docs: update CLAUDE.md — argo-events sync wave + registry description
- **PR #667:** [Merged] fix(lifeonabike): satisfy Gatekeeper require-labels + private repo auth
- **PR #668:** [Merged] docs: update CURRENT.md
- **PR #669:** [Merged] fix(lifeonabike): bypass Istio ambient ztunnel for build workflow pods
- **PR #670:** [Merged] fix(lifeonabike): push to Zot in-cluster directly, bypass ingress-nginx
- **PR #671:** [Merged] fix: allow ingress-nginx egress to lifeonabike namespace on port 8080
- **PR #672:** [Merged] fix: set eventbus stream replicas=1 and switch artifacts to LocalStack
- **PR #673:** [Merged] chore: seal lifeonabike-registry-creds and github-clone-token secrets
- **PR #676:** [Merged] chore(argo-events): remove webhook ingress, use Cloudflare Tunnel
- **PR #677:** [Merged] fix: use build-webhook.n37.ca for Cloudflare Tunnel + add deploy step
