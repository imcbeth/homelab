#!/usr/bin/env python3
"""Report container restarts across the cluster, and refuse to under-report.

WHY THIS EXISTS
---------------
On 2026-10-07 a cluster health check reported "0 container restarts cluster-wide"
three times in one session. The real figure was 517 restarts across 43 pods,
including external-dns-unifi at 219 and unipoller at 130.

The check was an ad-hoc one-liner over `kubectl get pods -A --no-headers`:

    p = line.split()
    try:
        n = int(p[3])          # intended: the RESTARTS column
    except ValueError:
        continue               # <-- swallowed every single pod
    if n > 0:
        ...

With `-A`, kubectl prepends a NAMESPACE column, so `p[3]` is STATUS, not
RESTARTS. `int("Running")` raised, the bare `continue` ate it, and the loop
finished having examined nothing. **The script could not have returned a
nonzero count for any cluster.** It was not inaccurate; it was incapable.

Two separate faults, and the second is the dangerous one:

  1. Parsing column positions out of human-readable output. The RESTARTS
     column also renders as "14 (6d11h ago)", which splits into two fields and
     shifts everything after it.
  2. Treating a parse failure as "nothing to see here". An exception while
     reading a pod's status means the reading is WRONG, not that the pod is
     fine.

HOW THIS SCRIPT CANNOT MAKE THE SAME MISTAKE
--------------------------------------------
  * It reads `-o json`. No column positions, ever.
  * A pod whose status cannot be interpreted is a hard error that exits
    non-zero. There is no code path that skips a pod quietly.
  * `--self-test` runs fixtures that include a pod with restarts and asserts a
    NONZERO total. A regression to "always reports 0" fails the self-test
    rather than shipping. This is the whole point: the previous script's bug
    was invisible precisely because zero is a plausible-looking answer.

USAGE
-----
    scripts/cluster-restarts.py                  # report everything
    scripts/cluster-restarts.py --since 24h      # only restarts in the window
    scripts/cluster-restarts.py --fail-on-recent 24h   # exit 1 if any are recent
    scripts/cluster-restarts.py --self-test      # no cluster needed

Totals count every container a pod has: regular, init, and ephemeral. An init
container that crashloops is a real restart and was invisible in the old check.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

CONTAINER_STATUS_FIELDS = (
    "containerStatuses",
    "initContainerStatuses",
    "ephemeralContainerStatuses",
)

DURATION_RE = re.compile(r"^(\d+)([smhd])$")
_UNITS = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}


class PodStatusError(RuntimeError):
    """A pod's status could not be interpreted. Never swallow this."""


def parse_duration(text: str) -> timedelta:
    match = DURATION_RE.match(text.strip())
    if not match:
        raise ValueError(f"bad duration {text!r}; use forms like 30m, 24h, 7d")
    return timedelta(**{_UNITS[match.group(2)]: int(match.group(1))})


def parse_k8s_time(text: str) -> datetime:
    """Parse a Kubernetes RFC3339 timestamp into an aware datetime."""
    cleaned = text.replace("Z", "+00:00")
    return datetime.fromisoformat(cleaned)


def container_restarts(status: dict, pod_ref: str) -> tuple[int, datetime | None]:
    """Restart count and last-termination time for one container status."""
    if "restartCount" not in status:
        raise PodStatusError(
            f"{pod_ref}: container {status.get('name', '<unnamed>')!r} has no "
            f"restartCount. Refusing to assume zero."
        )
    count = status["restartCount"]
    if not isinstance(count, int) or isinstance(count, bool):
        raise PodStatusError(
            f"{pod_ref}: restartCount is {count!r} ({type(count).__name__}), "
            f"not an int."
        )

    last: datetime | None = None
    terminated = (status.get("lastState") or {}).get("terminated") or {}
    finished = terminated.get("finishedAt")
    if finished:
        try:
            last = parse_k8s_time(finished)
        except ValueError as exc:
            raise PodStatusError(f"{pod_ref}: unparseable finishedAt {finished!r}") from exc
    return count, last


def collect(pods: list[dict]) -> list[dict]:
    """One record per pod that has restarts. Raises on anything ambiguous."""
    records = []
    for pod in pods:
        meta = pod.get("metadata")
        if not isinstance(meta, dict) or "name" not in meta:
            raise PodStatusError(f"pod object without metadata.name: {str(pod)[:120]}")
        ref = f"{meta.get('namespace', '<none>')}/{meta['name']}"

        status = pod.get("status")
        if not isinstance(status, dict):
            raise PodStatusError(f"{ref}: no status object")

        # A Pending pod legitimately has no container statuses yet. That is the
        # ONE case where absence is not suspicious -- and it is still not a
        # silent skip, because zero containers means zero restarts, which is a
        # real answer rather than a dropped row.
        total = 0
        last: datetime | None = None
        per_container = []
        for field in CONTAINER_STATUS_FIELDS:
            for cstatus in status.get(field) or []:
                count, when = container_restarts(cstatus, ref)
                total += count
                if count:
                    per_container.append((cstatus.get("name", "<unnamed>"), count, when))
                if when and (last is None or when > last):
                    last = when

        if total:
            records.append(
                {
                    "ref": ref,
                    "namespace": meta.get("namespace", "<none>"),
                    "name": meta["name"],
                    "node": (pod.get("spec") or {}).get("nodeName", "<unscheduled>"),
                    "total": total,
                    "last": last,
                    "containers": per_container,
                }
            )
    return records


def fetch_pods() -> list[dict]:
    result = subprocess.run(
        ["kubectl", "get", "pods", "--all-namespaces", "-o", "json"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"kubectl failed: {result.stderr.strip()[:300]}")
    payload = json.loads(result.stdout)
    items = payload.get("items")
    if items is None:
        raise RuntimeError("kubectl returned no 'items' key")
    return items


def report(records: list[dict], total_pods: int, since: timedelta | None) -> None:
    now = datetime.now(timezone.utc)
    shown = records
    if since is not None:
        cutoff = now - since
        shown = [r for r in records if r["last"] and r["last"] >= cutoff]

    grand = sum(r["total"] for r in records)
    print(f"pods scanned:        {total_pods}")
    print(f"pods with restarts:  {len(records)}  ({grand} restarts total)")
    if since is not None:
        print(f"restarting within {since}: {len(shown)} pods")
    print()

    if not shown:
        print("  none" if since is None else f"  none in the last {since}")
        return

    for rec in sorted(shown, key=lambda r: (-r["total"], r["ref"])):
        when = rec["last"].isoformat(timespec="seconds") if rec["last"] else "unknown"
        age = f"{(now - rec['last']).days}d ago" if rec["last"] else ""
        print(f"  {rec['total']:5}  {rec['ref']:52} node={rec['node']:14} last={when} {age}")
        for cname, count, cwhen in rec["containers"]:
            stamp = cwhen.isoformat(timespec="seconds") if cwhen else "unknown"
            print(f"         {cname}: {count} ({stamp})")


# --------------------------------------------------------------------------
# Self-test. The fixtures exist to make "always reports 0" unshippable.
# --------------------------------------------------------------------------

def _pod(ns, name, statuses, node="node01", field="containerStatuses"):
    return {
        "metadata": {"namespace": ns, "name": name},
        "spec": {"nodeName": node},
        "status": {field: statuses},
    }


def self_test() -> int:
    failures: list[str] = []

    def check(label, condition, detail=""):
        """`condition` may be a bool or a zero-arg callable.

        Callables are used where evaluating the condition could itself raise --
        e.g. indexing into a records list that a regression has left empty. A
        check that explodes must report FAIL and let the remaining checks run,
        not abort the suite with a traceback.
        """
        try:
            ok = condition() if callable(condition) else condition
        except Exception as exc:  # noqa: BLE001 - any failure here is a FAIL
            print(f"  FAIL  {label} (raised {type(exc).__name__}: {exc})")
            failures.append(label)
            return
        if ok:
            print(f"  PASS  {label}")
        else:
            print(f"  FAIL  {label} {detail}")
            failures.append(label)

    # The regression that motivated this script: a pod WITH restarts must be
    # found and must produce a nonzero total.
    pods = [
        _pod("external-dns", "external-dns-unifi-x", [
            {"name": "external-dns", "restartCount": 219,
             "lastState": {"terminated": {"finishedAt": "2026-10-06T06:58:52Z"}}},
        ]),
        _pod("default", "quiet-pod", [{"name": "app", "restartCount": 0}]),
    ]
    records = collect(pods)
    total = sum(r["total"] for r in records)
    check("a pod with restarts is reported", len(records) == 1, f"got {len(records)}")
    check("total is nonzero (the old bug was always-zero)", total == 219, f"got {total}")
    check("a pod with zero restarts is excluded",
          all(r["name"] != "quiet-pod" for r in records))

    # Init and ephemeral containers count too; the old check saw neither.
    records = collect([
        _pod("ns", "init-crasher", [{"name": "setup", "restartCount": 5}],
             field="initContainerStatuses"),
    ])
    check("init container restarts are counted",
          lambda: len(records) == 1 and records[0]["total"] == 5)

    # Multiple containers in one pod sum, rather than taking the first.
    records = collect([
        _pod("loki", "alloy-x", [
            {"name": "alloy", "restartCount": 7},
            {"name": "config-reloader", "restartCount": 7},
        ]),
    ])
    check("multi-container restarts sum",
          lambda: len(records) == 1 and records[0]["total"] == 14)

    # Pending pod: no container statuses is legitimate, not an error.
    try:
        collect([{"metadata": {"namespace": "ns", "name": "pending"},
                  "spec": {}, "status": {"phase": "Pending"}}])
        check("Pending pod with no statuses is tolerated", True)
    except PodStatusError as exc:
        check("Pending pod with no statuses is tolerated", False, str(exc))

    # A container status missing restartCount must RAISE, never read as zero.
    try:
        collect([_pod("ns", "weird", [{"name": "app"}])])
        check("missing restartCount raises", False, "it was silently accepted")
    except PodStatusError:
        check("missing restartCount raises", True)

    # A non-integer restartCount must raise.
    try:
        collect([_pod("ns", "weird2", [{"name": "app", "restartCount": "Running"}])])
        check("non-int restartCount raises", False, "it was silently accepted")
    except PodStatusError:
        check("non-int restartCount raises", True)

    # Malformed pod object must raise rather than be skipped.
    try:
        collect([{"status": {}}])
        check("pod without metadata.name raises", False, "it was skipped")
    except PodStatusError:
        check("pod without metadata.name raises", True)

    print()
    if failures:
        print(f"SELF-TEST FAILED: {len(failures)} check(s): {', '.join(failures)}")
        return 1
    print("SELF-TEST PASSED")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--since", metavar="DURATION",
                        help="only show pods whose last restart is within this window (e.g. 24h)")
    parser.add_argument("--fail-on-recent", metavar="DURATION",
                        help="exit 1 if any pod restarted within this window")
    parser.add_argument("--self-test", action="store_true",
                        help="run fixtures; needs no cluster")
    args = parser.parse_args(argv[1:])

    if args.self_test:
        return self_test()

    try:
        pods = fetch_pods()
        records = collect(pods)
    except (PodStatusError, RuntimeError, json.JSONDecodeError) as exc:
        # Loud, non-zero. The whole point: a broken reading is not "no restarts".
        print(f"ERROR: could not count restarts reliably: {exc}", file=sys.stderr)
        return 2

    since = parse_duration(args.since) if args.since else None
    report(records, len(pods), since)

    if args.fail_on_recent:
        window = parse_duration(args.fail_on_recent)
        cutoff = datetime.now(timezone.utc) - window
        recent = [r for r in records if r["last"] and r["last"] >= cutoff]
        if recent:
            print(f"\nFAIL: {len(recent)} pod(s) restarted within {window}", file=sys.stderr)
            return 1
        print(f"\nOK: no restarts within {window}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
