# 2026-04-18: lifeonabike.ca DNS + TLS, Velero v1.18.0 Validation, cert-manager Fix

## Completed Work

**Velero v1.18.0 Validated:**
- Forced ArgoCD re-poll via `kubectl annotate app velero -n argocd argocd.argoproj.io/refresh=hard --overwrite`
- End-to-end validated: test backup Queued → InProgress → Completed

**lifeonabike.ca Infrastructure (PR #553):**
- Added `lifeonabike.ca` domain-filter to both external-dns deployments
- Created `manifests/base/lifeonabike/`: namespace.yaml, certificate.yaml, kustomization.yaml
- Created `manifests/applications/lifeonabike.yaml` (sync-wave 5)
- Certificate: uses `lets-encrypt-k8s-n37-ca-prod` ClusterIssuer, DNS-01 challenge

**cert-manager Nameserver Fix (PR #555):**
- Root cause: `10.0.10.1:53` (UniFi) had local authoritative zone for `lifeonabike.ca` returning NXDOMAIN for TXT challenge
- Fix: removed `10.0.10.1:53` from `--dns01-recursive-nameservers`; now uses `1.1.1.1:53,8.8.8.8:53`
- `lifeonabike-ca-tls` READY=True (valid Apr 18 – Jul 17 2026, SANs: lifeonabike.ca + www)

## Key Learnings
- `--dns01-recursive-nameservers-only` means cert-manager queries ONLY configured resolvers. Split-horizon local DNS returning NXDOMAIN causes permanent propagation failure.
- ArgoCD git cache lag: use `kubectl annotate app ... argocd.argoproj.io/refresh=hard --overwrite` after fast PR merges.

**PRs:** #553 [Merged], #555 [Merged]
