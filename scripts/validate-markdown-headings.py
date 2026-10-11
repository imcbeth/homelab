#!/usr/bin/env python3
"""Stop `markdownlint --fix` from turning prose into H1 headings.

WHY THIS EXISTS
---------------
Session notes in this repo reference pull requests constantly, and line
wrapping regularly pushes one to the start of a line:

    ... the grouped "argocd ecosystem" PR
    #955 still proposed 10.8.4.

In CommonMark that is prose: an ATX heading needs a space after the `#`, so
`#955` is literal text and renders correctly.

**The problem is our own pre-commit hook.** `markdownlint` runs with `--fix`,
and MD018 (no-missing-space-atx) "helpfully" rewrites the line:

    #955 still proposed 10.8.4.      ->      # 955 still proposed 10.8.4.

which IS a heading. The hook does not fail; it silently edits the file and
passes. The sentence then appears in the rendered notes as an H1 reading
"955 still proposed 10.8.4."

This happened on 2026-09-29, 2026-10-03 and again on 2026-10-11 before the
mechanism was understood. Each time it was read as "I accidentally wrote a
heading", and each time the fix was to prefix the line with "PR " — treating
the symptom. The hook was the cause.

THE TWO-PART FIX
----------------
1. `.pre-commit-config.yaml` adds MD018 to markdownlint's `--disable` list, so
   `--fix` stops rewriting these lines.
2. This script, which:
     a. flags line-initial `#` followed by a non-space, so the pattern is
        surfaced loudly rather than silently rewritten; and
     b. asserts MD018 is still disabled in the hook config, so the protection
        cannot be removed without failing the check.

(b) is the part that matters. Without it, anyone tidying the hook args
reintroduces a silent file-mangler, and the next person spends an afternoon
wondering why their notes grew a heading.

NOT A STYLE RULE. Real headings (`# Heading`, `## Heading`) are untouched;
only `#` immediately followed by a non-space, outside code fences, is flagged.
The fix is to rewrap the sentence so the reference is not line-initial —
"PR #955 ..." or moving the word before it onto the same line.
"""

from __future__ import annotations

import re
import sys

PRECOMMIT_CONFIG = ".pre-commit-config.yaml"
REQUIRED_DISABLED = "MD018"

# A line that begins with one or more '#' followed immediately by something
# that is neither whitespace nor another '#'. `# Heading` and `## Heading`
# are fine; `#955` and `#1026` are not.
SUSPECT = re.compile(r"^#+[^#\s]")

FENCE = re.compile(r"^\s*(```|~~~)")


def check_markdown(path: str) -> list[str]:
    try:
        text = open(path, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError):
        return []  # binary or unreadable; not ours to judge

    failures = []
    in_fence = False
    for num, line in enumerate(text.split("\n"), 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if SUSPECT.match(line):
            # Tailor the advice. A bare "#123" is almost always a PR or issue
            # reference pushed to the line start by wrapping; anything else
            # (a run of social hashtags, say) needs escaping instead, and
            # suggesting "PR #Kubernetes" would be nonsense.
            if re.match(r"^#\d", line):
                advice = "Rewrap so the reference is not line-initial, or write 'PR #<n>'."
            else:
                advice = "Rewrap, or escape the leading hash as '\\#'."
            failures.append(
                f"{path}:{num}: line starts with '#' and no space\n"
                f"    {line[:88]}\n"
                f"    markdownlint --fix would rewrite this into a heading.\n"
                f"    {advice}"
            )
    return failures


def check_hook_config() -> list[str]:
    """MD018 must stay disabled, or --fix silently mangles prose again."""
    try:
        import yaml
    except ImportError:
        return [f"{PRECOMMIT_CONFIG}: PyYAML not installed; cannot verify MD018 is disabled"]

    try:
        config = yaml.safe_load(open(PRECOMMIT_CONFIG, encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [f"{PRECOMMIT_CONFIG}: cannot read ({exc})"]

    for repo in (config or {}).get("repos", []):
        for hook in repo.get("hooks", []):
            if hook.get("id") != "markdownlint":
                continue
            args = hook.get("args") or []
            if "--fix" in args and REQUIRED_DISABLED not in args:
                return [
                    f"{PRECOMMIT_CONFIG}: the markdownlint hook runs --fix without "
                    f"disabling {REQUIRED_DISABLED}.\n"
                    f"    MD018's autofix rewrites '#955 text' into '# 955 text', turning a\n"
                    f"    sentence into an H1. It edits the file and still passes.\n"
                    f"    Add {REQUIRED_DISABLED} to the hook's --disable list."
                ]
            return []  # hook found and correctly configured
    return [f"{PRECOMMIT_CONFIG}: no markdownlint hook found; this guard is now dead code"]


# --------------------------------------------------------------------------
# Self-test. Fixtures assert the check CAN fail, so a regression to
# "always passes" is caught here rather than in a rendered page.
# --------------------------------------------------------------------------

def self_test() -> int:
    import os
    import tempfile

    failures: list[str] = []

    def check(label, cond, detail=""):
        try:
            ok = cond() if callable(cond) else cond
        except Exception as exc:  # noqa: BLE001
            print(f"  FAIL  {label} (raised {type(exc).__name__}: {exc})")
            failures.append(label)
            return
        print(("  PASS  " if ok else "  FAIL  ") + label + ("" if ok else f"  {detail}"))
        if not ok:
            failures.append(label)

    def run(content):
        fd, path = tempfile.mkstemp(suffix=".md")
        os.write(fd, content.encode())
        os.close(fd)
        try:
            return check_markdown(path)
        finally:
            os.unlink(path)

    # The real-world case, and the regression that must fail.
    check("flags a line-initial PR reference",
          lambda: len(run("text wrapping to\n#955 still proposed 10.8.4.\n")) == 1)
    check("flags a multi-hash case",
          lambda: len(run("##1026 was merged\n")) == 1)

    # Real headings must NOT be flagged.
    check("a real H1 is not flagged", lambda: run("# Heading\n") == [])
    check("a real H3 is not flagged", lambda: run("### Heading\n") == [])
    check("a setext-ish line is not flagged", lambda: run("Heading\n=======\n") == [])

    # Code fences are prose-exempt: shell comments legitimately start with '#'.
    check("'#!/bin/bash' inside a fence is not flagged",
          lambda: run("```bash\n#!/bin/bash\n#comment\n```\n") == [])
    check("tilde fences are honoured",
          lambda: run("~~~\n#1026\n~~~\n") == [])
    check("a violation AFTER a closed fence is still caught",
          lambda: len(run("```\n#ok\n```\n#1026 bad\n")) == 1)

    # Config guard.
    cfg = check_hook_config()
    check("hook config guard passes on this repo", cfg == [], f"got {cfg}")

    print()
    if failures:
        print(f"SELF-TEST FAILED: {len(failures)}: {', '.join(failures)}")
        return 1
    print("SELF-TEST PASSED")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()

    paths = [a for a in argv[1:] if not a.startswith("-")]
    failures: list[str] = []
    for path in paths:
        failures.extend(check_markdown(path))
    failures.extend(check_hook_config())

    if failures:
        print("Markdown heading hazards:\n", file=sys.stderr)
        for f in failures:
            print(f"  {f}\n", file=sys.stderr)
        print(
            "  A '#' at the start of a line with no space is prose in CommonMark, but\n"
            "  markdownlint --fix rewrites it into a heading WITHOUT failing. That is why\n"
            "  MD018 is disabled in .pre-commit-config.yaml.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
