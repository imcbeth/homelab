### 2026-02-14: Ingress-nginx Helm Migration, Linkerd Cleanup, NetworkPolicies & Gatekeeper Audit

Archived from CURRENT.md. See full details in conversation history.

**Key Work:** Migrated ingress-nginx to Helm chart (v4.14.3), cleaned up Linkerd manifests, added NetworkPolicies for ingress-nginx and istio-system, fixed DNS egress AND semantics across 9 policies, audited Gatekeeper exclusions (10 → 2).

**PRs:** #441, #442, #443, #448, #449, #450, #451, #452
**Issues:** #444 (closed), #446 (closed), #447 (open)
