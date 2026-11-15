#!/usr/bin/env python3
"""Audit NetworkPolicy ports against the ports pods actually listen on.

WHY THIS EXISTS
---------------
NetworkPolicy is evaluated AFTER kube-proxy DNAT, so a rule has to name the
container port, not the Service port. A rule that names the Service port looks
right next to the Service definition and matches nothing.

On 2026-11-15 that turned out to have been true of the prometheus-operator
webhook rule in the `default` policy since it was written: it allowed 443 (the
Service port) while the operator listens on 10250. The webhook fails open, so
every PrometheusRule apply still succeeded -- 20 s late, two 10 s timeouts at a
time -- and nobody noticed until Argo CD 3.6 began dry-running every resource on
each compare and the kube-prometheus-stack comparison took 16 minutes (#1147).
REFERENCE.md had recorded this exact gotcha two weeks earlier (2026-10-29, the
lifeonabike `web` 80/8080 case); nobody went back to check the existing
policies against it. This script is that check.

WHAT IT REPORTS
---------------
  * DEAD-PORT: an ingress rule admits, or an egress rule (to in-cluster
    namespaces) allows, a port that no selected pod declares and no
    EndpointSlice in the namespace serves. Either the rule is stale, or it is
    the Service-port mistake -- flagged SERVICE-PORT when the number matches a
    Service port in that namespace.
  * BLOCKED-WEBHOOK: an admission webhook or APIService whose backing pod port
    is not admitted by any ingress rule that accepts traffic from outside the
    namespace (no `from`, or an ipBlock). The API server is a hostNetwork pod,
    so a rule scoped to a namespaceSelector never matches it. This is the
    dangerous direction: something that needs to be reached is not.
  * MISSING-NAMESPACE: a rule's namespaceSelector names a namespace
    (`kubernetes.io/metadata.name`) that does not exist, so it admits nothing.
    On 2026-11-15 three policies admitted Prometheus from `monitoring`; it runs
    in `default`. The scrapes worked only because every ambient namespace
    admitted HBONE (15008) from anywhere, which hid the typo too.

Findings listed in EXPECTED are known and explained; they are reported
separately and do not fail the run.

LIMITS
------
"No pod declares the port" is a strong hint, not proof: a container can listen
on a port it never declares (EXPECTED covers the known cases). Ingress to
hostNetwork pods is not governed by pod NetworkPolicy, so those pods are left
out. Calico-native policies are not read.

USAGE
-----
    scripts/networkpolicy-port-audit.py              # needs kubectl access
    scripts/networkpolicy-port-audit.py --self-test  # no cluster needed

Exits 1 when there is any unexpected finding.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict

# (kind, namespace, policy, port) -> why it is fine.
EXPECTED = {
    ("DEAD-PORT", "external-dns", "external-dns-network-policy", 7979):
        "external-dns-cloudflare serves metrics on 7979 without declaring it",
    ("DEAD-PORT", "flink-operator", "flink-operator-network-policy", 8081):
        "flink-demo JobManager REST; flink-demo has no pods while the job is stopped",
    ("DEAD-PORT", "ingress-nginx", "ingress-nginx-network-policy", 8081):
        "flink-demo JobManager UI backend; same as above",
    ("DEAD-PORT", "synology-csi", "synology-csi-network-policy", 9808):
        "CSI liveness-probe sidecar; kubelet probes are allowed regardless",
}

# HBONE (ztunnel rewrites the destination port) and DNS are always fine.
ALWAYS_OK = {15008, 53}


def matches(selector: dict | None, labels: dict) -> bool:
    if selector is None:
        return True
    for key, value in (selector.get("matchLabels") or {}).items():
        if labels.get(key) != value:
            return False
    for expr in selector.get("matchExpressions") or []:
        key, op, values = expr["key"], expr["operator"], expr.get("values", [])
        if op == "In" and labels.get(key) not in values:
            return False
        if op == "NotIn" and labels.get(key) in values:
            return False
        if op == "Exists" and key not in labels:
            return False
        if op == "DoesNotExist" and key in labels:
            return False
    return True


def index(objs: dict) -> dict:
    """Group the raw object lists into lookups keyed by namespace."""
    ns_labels = {n["metadata"]["name"]: n["metadata"].get("labels", {}) for n in objs["namespaces"]}
    pods = defaultdict(list)
    for p in objs["pods"]:
        if p["status"].get("phase") not in ("Running", "Pending") or p["spec"].get("hostNetwork"):
            continue
        ports = {
            (cp["containerPort"], cp.get("protocol", "TCP"))
            for c in p["spec"].get("containers", []) + p["spec"].get("initContainers", [])
            for cp in c.get("ports", [])
        }
        pods[p["metadata"]["namespace"]].append((p["metadata"].get("labels", {}), ports))
    eps = defaultdict(set)
    for e in objs["endpointslices"]:
        for pt in e.get("ports") or []:
            if pt.get("port"):
                eps[e["metadata"]["namespace"]].add((pt["port"], pt.get("protocol", "TCP")))
    svc_ports = defaultdict(set)
    for s in objs["services"]:
        for sp in s["spec"].get("ports", []):
            svc_ports[s["metadata"]["namespace"]].add((sp["port"], sp.get("protocol", "TCP")))
    return {"ns_labels": ns_labels, "pods": pods, "eps": eps, "svc_ports": svc_ports}


def served(idx: dict, ns: str, selector: dict | None) -> set:
    ports = set(idx["eps"][ns])
    for labels, declared in idx["pods"][ns]:
        if matches(selector, labels):
            ports |= declared
    return ports


def rule_ports(rule: dict):
    for pt in rule.get("ports") or []:
        port = pt.get("port")
        if isinstance(port, int) and not pt.get("endPort") and port not in ALWAYS_OK:
            yield port, pt.get("protocol", "TCP")


def dead_ports(policies: list[dict], idx: dict) -> list[tuple]:
    findings = []
    for pol in policies:
        ns, name, spec = pol["metadata"]["namespace"], pol["metadata"]["name"], pol["spec"]
        selector = spec.get("podSelector") or {}
        if not any(matches(selector, labels) for labels, _ in idx["pods"][ns]):
            continue
        own = served(idx, ns, selector)
        for rule in spec.get("ingress") or []:
            for key in rule_ports(rule):
                if key not in own:
                    kind = "SERVICE-PORT" if key in idx["svc_ports"][ns] else "DEAD-PORT"
                    findings.append((kind, ns, name, key[0], "ingress"))
        for rule in spec.get("egress") or []:
            peers = rule.get("to") or []
            if not peers or any("ipBlock" in p for p in peers):
                continue  # egress to anywhere / outside the cluster: not checkable here
            targets = []
            for p in peers:
                dest = ([n for n, labels in idx["ns_labels"].items() if matches(p["namespaceSelector"], labels)]
                        if "namespaceSelector" in p else [ns])
                targets += [(d, p.get("podSelector")) for d in dest]
            for key in rule_ports(rule):
                if not any(key in served(idx, d, sel) for d, sel in targets):
                    findings.append(("DEAD-PORT", ns, name, key[0], "egress"))
    return findings


def admits_from_outside(policies: list[dict], ns: str, port: int) -> bool:
    """True if `ns` has no policy, or one admits `port` from outside the namespace."""
    in_ns = [p for p in policies if p["metadata"]["namespace"] == ns]
    if not in_ns:
        return True
    for pol in in_ns:
        if "Ingress" not in (pol["spec"].get("policyTypes") or ["Ingress"]):
            continue
        for rule in pol["spec"].get("ingress") or []:
            peers = rule.get("from") or []
            if peers and not any("ipBlock" in p for p in peers):
                continue
            ports = rule.get("ports")
            if not ports or any(pt.get("port") == port for pt in ports):
                return True
    return False


def blocked_webhooks(objs: dict, policies: list[dict]) -> list[tuple]:
    refs = set()
    for cfg in objs["webhookconfigurations"]:
        for wh in cfg.get("webhooks") or []:
            svc = (wh.get("clientConfig") or {}).get("service")
            if svc:
                refs.add((svc["namespace"], svc["name"], svc.get("port", 443), cfg["metadata"]["name"]))
    for api in objs["apiservices"]:
        svc = api["spec"].get("service")
        if svc:
            refs.add((svc["namespace"], svc["name"], svc.get("port", 443), api["metadata"]["name"]))
    services = {(s["metadata"]["namespace"], s["metadata"]["name"]): s for s in objs["services"]}
    findings = []
    for ns, name, port, owner in sorted(refs):
        svc = services.get((ns, name))
        if not svc:
            findings.append(("BLOCKED-WEBHOOK", ns, name, port, f"{owner}: service missing"))
            continue
        port_name = next((sp.get("name", "") for sp in svc["spec"]["ports"] if sp["port"] == port), None)
        pod_ports = {
            pt["port"]
            for e in objs["endpointslices"]
            if e["metadata"]["namespace"] == ns
            and e["metadata"].get("labels", {}).get("kubernetes.io/service-name") == name
            for pt in e.get("ports") or []
            if pt.get("port") and pt.get("name", "") == (port_name or "")
        }
        for pod_port in sorted(pod_ports):
            if not admits_from_outside(policies, ns, pod_port):
                findings.append(("BLOCKED-WEBHOOK", ns, name, pod_port, owner))
    return findings


def missing_namespaces(objs: dict, policies: list[dict]) -> list[tuple]:
    live = {o["metadata"]["name"] for o in objs["namespaces"]}
    findings = []
    for pol in policies:
        ns, name = pol["metadata"]["namespace"], pol["metadata"]["name"]
        for direction, peer_key in (("ingress", "from"), ("egress", "to")):
            for rule in pol["spec"].get(direction, []):
                for peer in rule.get(peer_key) or []:
                    labels = (peer.get("namespaceSelector") or {}).get("matchLabels", {})
                    target = labels.get("kubernetes.io/metadata.name")
                    if target and target not in live:
                        findings.append(("MISSING-NAMESPACE", ns, name, target, direction))
    return findings


def audit(objs: dict) -> tuple[list, list]:
    policies = objs["networkpolicies"]
    findings = (dead_ports(policies, index(objs)) + blocked_webhooks(objs, policies)
                + missing_namespaces(objs, policies))
    unexpected = [f for f in findings if f[:4] not in EXPECTED]
    expected = [f for f in findings if f[:4] in EXPECTED]
    return unexpected, expected


def kubectl_items(*resource: str) -> list[dict]:
    args = ["kubectl", "get", *resource, "-o", "json"]
    if resource[0] not in ("namespaces", "validatingwebhookconfigurations",
                           "mutatingwebhookconfigurations", "apiservices"):
        args.insert(3, "-A")
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise SystemExit(f"kubectl get {' '.join(resource)} failed: {result.stderr.strip()}")
    return json.loads(result.stdout)["items"]


def fetch() -> dict:
    return {
        "networkpolicies": kubectl_items("networkpolicies"),
        "pods": kubectl_items("pods"),
        "services": kubectl_items("services"),
        "endpointslices": kubectl_items("endpointslices"),
        "namespaces": kubectl_items("namespaces"),
        "webhookconfigurations": kubectl_items("validatingwebhookconfigurations")
        + kubectl_items("mutatingwebhookconfigurations"),
        "apiservices": kubectl_items("apiservices"),
    }


def report(unexpected: list, expected: list, policy_count: int) -> None:
    for kind, ns, name, port, where in sorted(unexpected):
        print(f"{kind:16} {ns}/{name} {port} ({where})")
    if expected:
        print("\nExpected (see EXPECTED in this script):")
        for kind, ns, name, port, _ in sorted(expected):
            print(f"  {kind:16} {ns}/{name} {port}: {EXPECTED[(kind, ns, name, port)]}")
    print(f"\n{len(unexpected)} unexpected finding(s) across {policy_count} NetworkPolicies")


# --------------------------------------------------------------------------
# Self-test: the fixture reproduces the 2026-11-15 bug. It must be flagged.
# --------------------------------------------------------------------------

def _fixture(webhook_rule_port: int) -> dict:
    labels = {"app": "operator"}
    return {
        "namespaces": [{"metadata": {"name": "mon", "labels": {"kubernetes.io/metadata.name": "mon"}}}],
        "pods": [{
            "metadata": {"namespace": "mon", "name": "operator-0", "labels": labels},
            "spec": {"containers": [{"ports": [{"containerPort": 10250, "name": "https"},
                                               {"containerPort": 8080, "name": "metrics"}]}]},
            "status": {"phase": "Running"},
        }],
        "services": [{"metadata": {"namespace": "mon", "name": "operator"},
                      "spec": {"ports": [{"port": 443, "name": "https", "targetPort": "https"}]}}],
        "endpointslices": [{"metadata": {"namespace": "mon", "name": "operator-x",
                                         "labels": {"kubernetes.io/service-name": "operator"}},
                            "ports": [{"port": 10250, "name": "https"}]}],
        "networkpolicies": [{
            "metadata": {"namespace": "mon", "name": "mon-policy"},
            "spec": {"podSelector": {}, "policyTypes": ["Ingress"], "ingress": [
                {"ports": [{"port": webhook_rule_port}]},
                {"from": [{"namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": "mon"}}}],
                 "ports": [{"port": 8080}]},
            ]},
        }],
        "webhookconfigurations": [{"metadata": {"name": "operator-admission"}, "webhooks": [
            {"clientConfig": {"service": {"namespace": "mon", "name": "operator", "port": 443}}}]}],
        "apiservices": [],
    }


def self_test() -> int:
    failures = 0

    def check(label: str, condition: bool, detail: object = "") -> None:
        nonlocal failures
        print(f"{'PASS' if condition else 'FAIL'}  {label}" + (f"  {detail}" if not condition else ""))
        failures += not condition

    broken, _ = audit(_fixture(webhook_rule_port=443))
    kinds = {(f[0], f[3]) for f in broken}
    check("Service port 443 in the rule is flagged SERVICE-PORT", ("SERVICE-PORT", 443) in kinds, broken)
    check("the webhook on pod port 10250 is flagged BLOCKED-WEBHOOK", ("BLOCKED-WEBHOOK", 10250) in kinds, broken)
    check("the broken fixture fails the run (nonzero findings)", len(broken) > 0)

    fixed, _ = audit(_fixture(webhook_rule_port=10250))
    check("the fixed policy (pod port 10250) is clean", fixed == [], fixed)

    namespaced = _fixture(webhook_rule_port=10250)
    namespaced["networkpolicies"][0]["spec"]["ingress"][0]["from"] = [
        {"namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": "mon"}}}]
    scoped, _ = audit(namespaced)
    check("a namespace-scoped webhook rule is BLOCKED (apiserver is hostNetwork)",
          ("BLOCKED-WEBHOOK", 10250) in {(f[0], f[3]) for f in scoped}, scoped)

    typo = _fixture(webhook_rule_port=10250)
    typo["networkpolicies"][0]["spec"]["ingress"][1]["from"] = [
        {"namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": "monitoring"}}}]
    missing, _ = audit(typo)
    check("a rule naming a nonexistent namespace is flagged MISSING-NAMESPACE",
          ("MISSING-NAMESPACE", "monitoring") in {(f[0], f[3]) for f in missing}, missing)

    print(f"\n{'OK' if failures == 0 else f'{failures} FAILED'}")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--self-test", action="store_true", help="run fixtures; no cluster needed")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    objs = fetch()
    unexpected, expected = audit(objs)
    report(unexpected, expected, len(objs["networkpolicies"]))
    return 1 if unexpected else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
