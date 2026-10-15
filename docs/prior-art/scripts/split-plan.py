#!/usr/bin/env python3
"""Report the cross-group reference edges of a proposed theory split.

Splitting one large theory into several means choosing a *layering*: each
new theory imports the ones below it, so every reference must point down.
This reads the entry-level citation graph (`query callees`) and classifies
each in-theory edge by the groups its endpoints fall in, so a proposed cut
can be checked before a line is moved.

It also reads the *prose* references — `\\<^const>`, `\\<^term>` and friends
in `text` blocks and `\\<comment>`s.  Those are real elaboration
dependencies (a forward `\\<^const>` fails the build, and across a cut every
reference to a group above becomes forward), but they are invisible to a
citation graph built from proof bodies, so a cut can pass on the proofs and
then fail on the documentation.  Prose edges are marked `(text)` in the
per-pair listing; a prose-only edge is often better removed by demoting the
antiquotation to a plain cartouche than by adding an import.

Usage:

    bin/split-plan.py Machine_Relabelling \\
        EXTRAS=584-677,1396-1652 \\
        EMBED=1653-2805 \\
        REL=5-583,678-1395,2806-99999

Groups are named line-span sets over the theory's own source.  Any entry
whose start line falls in a span belongs to that group; entries in no span
are reported separately (an incomplete cut).

Output is the group-to-group edge matrix plus, for every ordered pair, the
individual edges — so a cycle can be broken by looking at the handful of
lemmas causing it rather than at the whole theory.  A layering exists iff
the matrix is triangular under some ordering; the script reports one if it
finds one, and names the cycle if it does not.
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections import defaultdict

OUTLINE_ENTRY = re.compile(
    r"^\s+(?P<tag>[A-Z]+)\s+(?P<name>\S+)\s+\((?P<start>\d+)\.\.(?P<end>\d+),")
CALLEE_HEADER = re.compile(r"^\d+ callee\(s\) of (?P<name>\S+):")
CALLEE_ROW = re.compile(
    r"^\s+(?P<name>\S+)\s+\((?P<tag>[A-Z]+)\)\s+—\s+(?P<theory>\S+)\s+\[L(?P<line>\d+)\]")

# `query grep --with-comments` prints a locus line then the matched source
# line.  Only comment/text hits are of interest here: a live-source reference
# is already an edge in the callee graph.
GREP_LOC = re.compile(
    r"^\s+(?P<file>\S+\.thy):(?P<line>\d+)\s.*\[in comment/text\]\s*$")
ANTIQ = re.compile(r"\\<\^(?:const|term|prop|typ)>\\<open>(?P<body>.*?)\\<close>"
                   r"|@\{(?:const|term|prop|typ)\s+(?P<brace>[^}]*)\}")
IDENT = re.compile(r"[A-Za-z][A-Za-z0-9_']*")


def run_query(args: list[str]) -> str:
    proc = subprocess.run(["query", *args], capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        sys.exit(f"FAIL: query {' '.join(args)} exited {proc.returncode}")
    return proc.stdout


def parse_groups(specs: list[str]) -> dict[str, list[tuple[int, int]]]:
    groups: dict[str, list[tuple[int, int]]] = {}
    for spec in specs:
        if "=" not in spec:
            sys.exit(f"FAIL: group spec {spec!r} is not NAME=a-b[,c-d]")
        name, ranges = spec.split("=", 1)
        spans = []
        for part in ranges.split(","):
            lo, hi = part.split("-", 1)
            spans.append((int(lo), int(hi)))
        groups[name] = spans
    return groups


def group_of(line: int, groups: dict[str, list[tuple[int, int]]]) -> str | None:
    for name, spans in groups.items():
        if any(lo <= line <= hi for lo, hi in spans):
            return name
    return None


def prose_refs(theory: str, entries: dict[str, int]) -> list[tuple[int, str]]:
    """Every (line, entry-name) a doc antiquotation in this theory refers to.

    Only names that are entries of *this* theory matter: a reference to
    another theory is settled by the imports and cannot cross the cut.  Term
    antiquotations are scanned by identifier, so a bound variable sharing an
    entry's name over-reports — which is the safe direction for a planner,
    and the per-pair listing shows the locus so it can be dismissed by eye.
    """
    out: list[tuple[int, str]] = []
    lines = run_query(["grep", "--with-comments",
                       r"\\<\^(const|term|prop|typ)>|@\{(const|term|prop|typ) ",
                       f"{theory}.thy"]).splitlines()
    for i, line in enumerate(lines):
        loc = GREP_LOC.match(line)
        if not loc or loc["file"] != f"{theory}.thy" or i + 1 >= len(lines):
            continue
        for m in ANTIQ.finditer(lines[i + 1]):
            for ident in IDENT.findall(m["body"] or m["brace"] or ""):
                if ident in entries:
                    out.append((int(loc["line"]), ident))
    return out


def main() -> int:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    theory = sys.argv[1]
    groups = parse_groups(sys.argv[2:])

    entries: dict[str, int] = {}
    for line in run_query(["outline", theory]).splitlines():
        m = OUTLINE_ENTRY.match(line)
        if m:
            entries[m["name"]] = int(m["start"])
    if not entries:
        sys.exit(f"FAIL: no entries parsed from outline of {theory}")

    unplaced = [(n, ln) for n, ln in entries.items()
                if group_of(ln, groups) is None]

    names = sorted(entries)
    edges: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    current = None
    for line in run_query(["callees", *names]).splitlines():
        h = CALLEE_HEADER.match(line)
        if h:
            current = h["name"]
            continue
        r = CALLEE_ROW.match(line)
        if r and current and r["theory"] == theory:
            src = group_of(entries.get(current, -1), groups)
            dst = group_of(int(r["line"]), groups)
            if src and dst and src != dst:
                edges[(src, dst)].append((current, r["name"]))

    prose = 0
    for line_no, target in prose_refs(theory, entries):
        src = group_of(line_no, groups)
        dst = group_of(entries[target], groups)
        if src and dst and src != dst:
            edges[(src, dst)].append((f"text@L{line_no}", target))
            prose += 1

    order = list(groups)
    print(f"# Split plan for {theory}")
    print(f"\n{prose} of the edges below are prose references "
          "(doc antiquotations), not proof steps.")
    print(f"\n{len(entries)} entries, {len(order)} groups: "
          + ", ".join(f"{g} ({sum(1 for n, ln in entries.items() if group_of(ln, groups) == g)})"
                      for g in order))

    if unplaced:
        print(f"\nWARN: {len(unplaced)} entries in no group (incomplete cut):")
        for n, ln in sorted(unplaced, key=lambda x: x[1]):
            print(f"  L{ln:<6} {n}")

    print("\n## Cross-group edges (rows reference columns)\n")
    width = max(len(g) for g in order) + 2
    print(" " * width + "".join(f"{g:>{width}}" for g in order))
    for src in order:
        row = "".join(f"{len(edges.get((src, dst), [])):>{width}}" for dst in order)
        print(f"{src:<{width}}{row}")

    for (src, dst), pairs in sorted(edges.items()):
        print(f"\n### {src} -> {dst}  ({len(pairs)} edges, "
              f"{len({p[1] for p in pairs})} distinct targets)")
        by_target: dict[str, list[str]] = defaultdict(list)
        for caller, callee in pairs:
            by_target[callee].append(caller)
        for callee in sorted(by_target):
            callers = sorted(set(by_target[callee]))
            shown = ", ".join(callers[:6]) + (" …" if len(callers) > 6 else "")
            print(f"  {callee:<34} <- {shown}")

    # A layering exists iff we can repeatedly peel a group referencing nothing
    # not yet peeled.  Peel order = import order, bottom first.
    # Peel by ROUNDS, not one at a time: groups peeled in the same round have
    # no edges between them, so they are siblings over the previous round and
    # neither has to import the other.  Reporting them as a chain would name
    # an import that the citation graph does not ask for.
    remaining = set(order)
    rounds: list[list[str]] = []
    while remaining:
        peel = sorted(g for g in remaining
                      if not any(edges.get((g, d)) for d in remaining if d != g))
        if not peel:
            print(f"\nFAIL: no layering — cycle among {sorted(remaining)}.")
            print("      Break it by moving the lemmas listed above, or merge groups.")
            return 1
        rounds.append(peel)
        remaining -= set(peel)

    print("\nPASS: a layering exists.  Import order, bottom first "
          "(same level = siblings, neither imports the other):")
    for i, level in enumerate(rounds):
        if i == 0:
            below = "(the current parent)"
        else:
            below = " / ".join(rounds[i - 1])
        for g in level:
            needs = sorted({d for d in order if edges.get((g, d))})
            detail = f"needs {', '.join(needs)}" if needs else "needs nothing here"
            print(f"  level {i + 1}: {g:<10} imports {below:<24} [{detail}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
