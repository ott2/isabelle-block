#!/usr/bin/env python3
"""Sort a session's zero-caller roots by why they might not be dead.

Usage: bin/classify-unused.py SESSION_DIR

Runs `query -R SESSION_DIR unused --roots` and prints each root under one
of three headings:

  ATTR      declared with an attribute, or named in a `declare` / `lemmas`
            command (unused_lib.implicit_use) -- possibly used implicitly,
            so zero callers proves nothing; the build decides
  THEOREM   a `theorem` / `corollary` -- by convention an intended endpoint
  LEMMA     everything else -- the candidates for deletion

with the exclusive-subtree entry and line counts from the forest summary.
Read-only.
"""
import re
import subprocess
import sys
from pathlib import Path

from unused_lib import implicit_use

ROOT = Path(__file__).resolve().parent.parent
ROW = re.compile(r"^\s+(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\S+)\s*$")
HEAD = re.compile(r"^--- (\S+) \((\w+)\) — (\S+\.thy) \[src (\d+)\.\.(\d+)")


def run(args):
    return subprocess.run(args, capture_output=True, text=True, cwd=ROOT).stdout


def main(argv):
    if len(argv) != 1:
        print(__doc__)
        return 2
    sdir = argv[0]
    roots = []
    for line in run(["query", "-R", sdir, "unused", "--roots"]).splitlines():
        m = ROW.match(line)
        if m and m.group(1) != "Root":
            roots.append((m.group(1), int(m.group(2)), int(m.group(3)), m.group(6)))
    groups = {"ATTR": [], "THEOREM": [], "LEMMA": []}
    for name, excl, lines, thy in roots:
        shown = run(["query", "-R", sdir, "show", name])
        m = next((HEAD.match(l) for l in shown.splitlines() if HEAD.match(l)), None)
        tag = m.group(2) if m else "?"
        if implicit_use(sdir, name):
            groups["ATTR"].append((name, excl, lines, thy, tag))
        elif tag in ("THEOREM", "COROLLARY"):
            groups["THEOREM"].append((name, excl, lines, thy, tag))
        else:
            groups["LEMMA"].append((name, excl, lines, thy, tag))
    for g in ("ATTR", "THEOREM", "LEMMA"):
        rows = sorted(groups[g], key=lambda r: -r[2])
        total = sum(r[2] for r in rows)
        print(f"== {g}: {len(rows)} roots, {total} exclusive lines")
        for name, excl, lines, thy, tag in rows:
            print(f"  {name:45s} {excl:4d} {lines:6d}  {thy} ({tag})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
