### 2026-06-01 (Morning): EventSource Filter Fix, Zot Credential Rotation

**Completed Work:**

**EventSource filter fix (PR included in #676–#678 branch):**
- Fixed EventSource expression: `body.ref == 'refs/heads/main'` (was `body.ref` referenced incorrectly — Argo Events body accessor requires the full dot-path)
- Verified push events from GitHub now correctly match main-branch pushes only

**Zot registry credential rotation (PR #675):**
- Rotated admin credentials for Zot OCI registry
- Fixed bcrypt hash encoding in `zot-htpasswd` SealedSecret (incorrect encoding was causing auth failures)
- SealedSecret re-sealed and merged

**HMAC webhook SealedSecret rename (PR #678):**
- Renamed `github-lifeonabike-webhook-secret` SealedSecret file to `lifeonabike-webhook-hmac-sealed.yaml`
- Required because git-crypt catches `*secret*` filenames; sealed files must use `*-sealed.yaml` naming convention

**Pull Requests:**
- **PR #675:** [Merged] chore: rotate Zot registry credentials + fix bcrypt encoding
- **PR #678:** [Merged] fix: rename webhook HMAC SealedSecret to avoid git-crypt encryption
