#!/usr/bin/env python3
"""Validate YAML/JSON embedded inside ConfigMap `data:` keys.

WHY THIS EXISTS
---------------
yamllint and kubeconform validate the OUTER Kubernetes document. Inside it, a
ConfigMap `data:` value is just an opaque scalar string — neither tool ever
parses it. So a ConfigMap carrying syntactically broken YAML passes every check
in this repo and fails only in the consuming component, at runtime.

That happened on 2026-09-19. A comment inserted at the wrong indentation left
`loki-alerting-rules.yaml` unparseable:

    error parsing /rules/fake/log-alerts.yaml: yaml: line 58:
    did not find expected key

Loki's ruler ran with ZERO rules loaded until someone checked its API. The full
pre-commit suite — yamllint, kubeconform, kustomize build — passed on that
commit.

This repo ships two whole classes of config this way: Loki alerting rules and
every Grafana dashboard. Both are load-bearing and both fail silently.

WHAT IT CHECKS
--------------
For each ConfigMap in the given files, every `data:` key is parsed according to
its extension:

    *.yaml / *.yml  ->  yaml.safe_load
    *.json          ->  json.loads

Keys with any other extension (.sh, .py, .txt, .csv, and extensionless ones) are
left alone — they are not structured data and parsing them would be noise.

NOT A LINTER. This only asks "does it parse". It deliberately says nothing about
whether the content is a valid Loki rule or Grafana dashboard; that is the
component's job. Catching the unparseable case is what was missing.

NOTE: `{{ ... }}` is fine. Grafana legend formats (`{{pod}}`) and Loki alert
annotations (`{{ $labels.namespace }}`) live inside quoted strings and parse
normally. Do not add a skip for them — it would blind the check to exactly the
files it exists to protect.
"""

from __future__ import annotations

import json
import os
import sys

try:
    import yaml
except ImportError:  # pragma: no cover
    print("validate-configmap-embedded: PyYAML not installed", file=sys.stderr)
    sys.exit(1)

# git-crypt encrypts some paths; in CI those are binary and must be skipped.
GITCRYPT_MAGIC = b"\x00GITCRYPT"

PARSERS = {
    ".yaml": ("YAML", yaml.safe_load),
    ".yml": ("YAML", yaml.safe_load),
    ".json": ("JSON", json.loads),
}


def check_file(path: str) -> list[str]:
    """Return a list of human-readable failures for one file."""
    failures: list[str] = []

    try:
        raw = open(path, "rb").read()
    except OSError as exc:
        return [f"{path}: cannot read ({exc})"]

    if raw.startswith(GITCRYPT_MAGIC):
        return []  # encrypted blob — nothing to parse

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return []  # binary; not ours to judge

    try:
        docs = list(yaml.safe_load_all(text))
    except yaml.YAMLError:
        # The OUTER document is broken. yamllint owns that error, and reporting
        # it here too would just duplicate its output.
        return []

    for doc in docs:
        if not isinstance(doc, dict) or doc.get("kind") != "ConfigMap":
            continue
        name = (doc.get("metadata") or {}).get("name", "<unnamed>")
        for key, value in (doc.get("data") or {}).items():
            if not isinstance(value, str):
                continue
            ext = os.path.splitext(key)[1].lower()
            if ext not in PARSERS:
                continue
            label, parse = PARSERS[ext]
            try:
                parse(value)
            except Exception as exc:
                first = str(exc).split("\n")[0]
                failures.append(
                    f"{path}\n"
                    f"    ConfigMap/{name} -> data['{key}'] is not valid {label}\n"
                    f"    {first}\n"
                    f"    (line numbers above are relative to the EMBEDDED "
                    f"document, not to {os.path.basename(path)})"
                )
    return failures


def main(argv: list[str]) -> int:
    paths = argv[1:]
    if not paths:
        return 0

    failures: list[str] = []
    checked = 0
    for path in paths:
        result = check_file(path)
        checked += 1
        failures.extend(result)

    if failures:
        print("Embedded ConfigMap data failed to parse:\n", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}\n", file=sys.stderr)
        print(
            "  These blobs are opaque to yamllint and kubeconform, so nothing "
            "else catches this.\n"
            "  The consuming component (Loki ruler, Grafana) would load zero "
            "config and stay silent about it.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
