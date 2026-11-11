## Summary

<!-- What changes and why. -->

## Checklist

- [ ] `pre-commit` passes
- [ ] **Changed a file in `manifests/applications/`?** Argo CD does not deploy
      Application specs itself. After merging, run `kubectl diff -f` and then
      `kubectl apply -f manifests/applications/<app>.yaml`, and confirm the app
      is Synced and Healthy **at the new chart version**. "Synced" alone can
      mean the old version.
- [ ] Changes under `manifests/base/` sync on their own within ~3 minutes;
      confirm the app is Synced and Healthy

## Test plan

<!-- How the change was verified, and what to check after merge. -->
