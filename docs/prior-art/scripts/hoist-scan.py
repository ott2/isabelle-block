#!/usr/bin/env python3
"""Find entries sitting higher in the import DAG than their dependencies require.

A lemma lands in whatever theory its *first consumer* happened to be in.  That
is fine until a second consumer appears in a sibling branch: the lemma is now
invisible to it, and the cheap move is to prove it again.  This reports, for
every entry of a target theory, the lowest theories that could legally host it
--- so a misplaced stratum is found before it is duplicated rather than after.

Two questions, one pass:

    bin/hoist-scan.py Diagonal_Sweeps
        For each entry, the minimal legal homes in the import DAG.  An entry
        whose homes do not include its current theory is over-placed.

    bin/hoist-scan.py Diagonal_Sweeps --visible-to Diagonal_Case2
        Filter to the entries a named theory could *already* see if they were
        hoisted --- i.e. exactly what that theory would otherwise re-prove.

Dependencies come from `query callees --names --reach closure` (the proof-body
citation graph) and the import DAG from `query deps -r`.  Intra-theory edges
are resolved to a fixpoint, so an entry is bounded below by the homes of the
same-theory lemmas it cites.

Two caveats, both about what a proof-body citation graph cannot see:

- Prose references (`\\<^const>`, `\\<^term>` in `text` blocks) are real
  elaboration dependencies and are invisible to it.  This is `split-plan.py`'s
  caveat too; check a proposed move with that script before performing it.
- A `[simp]` lemma fires through the simplifier rather than by name, so it has
  no callers in the graph even when it is load-bearing.  That does not affect
  the direction computed here (dependencies are read *downward*, from the
  entry's own body), but it does mean the consumers of a moved `[simp]` rule
  cannot be enumerated first --- the build is the check.

**This is a candidate generator, not a verdict.**  Run it on a theory that has
*not* accreted anything and it still reports most of its entries as
over-placed, because most lemmas need only what their parent already provides
--- `Diagonal_Case1`'s run lemmas would all typecheck in
`Diagonal_Preprocessing`, and are not misplaced.  What makes a report
actionable is a *group* of entries that is about the destination's own
definitions, or that a sibling branch also needs.  A single entry, or a group
whose only common property is that it compiles lower down, is noise.  The
judgement is the reader's; the scan only narrows where to look.

And one caveat about the criterion itself: *lowest legal* is not *wanted*.  A
theory can sit above its minimum on purpose --- for build cost, or because the
minimum is conceptually the wrong place --- and such a theory would otherwise
be reported as over-placed forever, telling each session to undo the last
one's work.  Register it in `DELIBERATE` below and it reports `BY DESIGN`
instead, with the reason.  Do that only for a *recorded* decision: the reason
string should point at where the argument lives, not restate it.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict

# Theories deliberately above their lowest legal home.  See the docstring:
# the value is a pointer to where the decision is argued, not the argument.
DELIBERATE = {
    "Diagonal_Simulation":
        "a sibling of Diagonal_Validity rather than more of Diagonal_Arms, "
        "so an edit here does not rebuild the audit session — t/nth/ROOT",
}

ENTRY_RE = re.compile(r"^(\S+) \((\w+)\) — (\S+) \[src (\d+)\.\.(\d+)")
CALLEE_HDR_RE = re.compile(r"^\d+ callee\(s\) of (\S+):")
CALLEE_NONE_RE = re.compile(r"^No references found in (\S+)'s body\.")
CALLEE_RE = re.compile(r"^\s+(\S+) \((\w+)\) — (\S+) \[")
DEPS_HDR_RE = re.compile(r"^Import-transitive dependencies of (\S+):")
DEPS_DIRECT_RE = re.compile(r"^Direct imports of (\S+):")
DEP_RE = re.compile(r"^\s+(\S+)\s+\(")


def run(args: list[str]) -> str:
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"FAIL: {' '.join(args[:3])}... exited {proc.returncode}\n{proc.stderr}")
    return proc.stdout


def theory_entries(theory: str) -> list[tuple[str, str, int]]:
    """(name, kind, src_lines) for each entry, in source order."""
    out = []
    for line in run(["query", "theory", theory, "--names"]).splitlines():
        m = ENTRY_RE.match(line)
        if m:
            name, kind, thy, lo, hi = m.groups()
            if thy == theory:
                out.append((name, kind, int(hi) - int(lo) + 1))
    return out


def callees(names: list[str], theory: str) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """One `query callees` pass, split two ways.

    Returns (external theories cited, same-theory entries cited).  The second
    feeds the fixpoint: an entry citing a sibling inherits that sibling's floor.
    """
    if not names:
        return {}, {}
    text = run(["query", "callees", "--names", "--reach", "closure"] + names)
    extern: dict[str, set[str]] = {n: set() for n in names}
    sibs: dict[str, set[str]] = {n: set() for n in names}
    current = None
    for line in text.splitlines():
        m = CALLEE_HDR_RE.match(line)
        if m:
            current = m.group(1)
            continue
        if CALLEE_NONE_RE.match(line):
            current = None
            continue
        m = CALLEE_RE.match(line)
        if m and current is not None:
            cname, _, cthy = m.groups()
            if cthy == theory:
                sibs.setdefault(current, set()).add(cname)
            else:
                extern.setdefault(current, set()).add(cthy)
    return extern, sibs


def import_closures(theories: list[str]) -> dict[str, set[str]]:
    """theory -> its transitive imports (not including itself)."""
    if not theories:
        return {}
    text = run(["query", "deps", "-r"] + theories)
    closures: dict[str, set[str]] = {}
    current = None
    for line in text.splitlines():
        m = DEPS_HDR_RE.match(line) or DEPS_DIRECT_RE.match(line)
        if m:
            current = m.group(1)
            closures.setdefault(current, set())
            continue
        m = DEP_RE.match(line)
        if m and current is not None:
            closures[current].add(m.group(1))
    for t in theories:
        closures.setdefault(t, set())
    return closures


def report_shadowed(theories: list[str]) -> int:
    """Names a theory declares that an ancestor already declared.

    Isabelle resolves each citation to the nearest declaration, so a shadow is
    consistent within every theory and nothing fails --- see insights/236.  The
    cost is a lemma proved twice, or worse, two statements under one name.
    """
    closures = import_closures(theories)
    cache: dict[str, dict[str, str]] = {}

    def names_of(thy: str) -> dict[str, str]:
        if thy not in cache:
            cache[thy] = {n: k for n, k, _ in theory_entries(thy)}
        return cache[thy]

    findings = 0
    for theory in theories:
        own = names_of(theory)
        hits, notes = [], []
        for anc in sorted(closures.get(theory, set())):
            for n, k in names_of(anc).items():
                if n not in own:
                    continue
                # A datatype declares a *type*; everything else declares a
                # constant or a fact.  Isabelle keeps those namespaces apart,
                # so such a pair is a readability hazard, not a shadow.
                if ("DATATYPE" == k) != ("DATATYPE" == own[n]):
                    notes.append((n, own[n], anc, k))
                else:
                    hits.append((n, own[n], anc, k))
        print(f"=== {theory} — {len(own)} entries, "
              f"{len(closures.get(theory, set()))} ancestors ===")
        for n, k, anc, ak in sorted(notes):
            print(f"  note: {n:32s} {k:8s} reuses a {ak} name in {anc} "
                  f"(distinct namespace)")
        if not hits:
            if not notes:
                print("  no shadowed names")
            print()
            continue
        findings += len(hits)
        for n, k, anc, ak in sorted(hits):
            print(f"  {n:38s} {k:8s} shadows {ak} in {anc}")
        print()
    if findings:
        print(f"FAIL: {findings} shadowed name(s) — "
              f"confirm with `query show NAME --all`")
        return 1
    print("PASS: no shadowed names")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Report entries placed higher than their dependencies require.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("theory", nargs="+", help="target theory name(s)")
    ap.add_argument(
        "--visible-to",
        metavar="THY",
        help="filter to entries THY could already see if hoisted",
    )
    ap.add_argument(
        "--min-lines",
        type=int,
        default=0,
        help="only report entries of at least N source lines",
    )
    ap.add_argument(
        "--shadowed",
        action="store_true",
        help="report entries whose name is already declared in an ancestor "
        "(Isabelle allows this silently; see insights/236)",
    )
    args = ap.parse_args()

    if args.shadowed:
        return report_shadowed(args.theory)

    for theory in args.theory:
        entries = theory_entries(theory)
        if not entries:
            print(f"{theory}: no entries found")
            continue
        names = [n for n, _, _ in entries]
        span = {n: ln for n, _, ln in entries}
        kind = {n: k for n, k, _ in entries}

        extern, sibs = callees(names, theory)
        for _ in range(50):
            changed = False
            for n in names:
                merged = set(extern[n])
                for s in sibs.get(n, set()):
                    merged |= extern.get(s, set())
                if merged != extern[n]:
                    extern[n] = merged
                    changed = True
            if not changed:
                break

        universe = sorted({t for ds in extern.values() for t in ds} | {theory})
        if args.visible_to:
            universe = sorted(set(universe) | {args.visible_to})
        closures = import_closures(universe)

        print(f"=== {theory} — {len(entries)} entries ===\n")
        if theory in DELIBERATE:
            print(f"placed above its minimum on purpose: {DELIBERATE[theory]}\n")

        if args.visible_to:
            vis = closures.get(args.visible_to, set()) | {args.visible_to}
            shareable, pinned = [], []
            for n in names:
                if span[n] < args.min_lines:
                    continue
                (shareable if extern[n] <= vis else pinned).append(n)
            sh_lines = sum(span[n] for n in shareable)
            pn_lines = sum(span[n] for n in pinned)
            print(
                f"Visible to {args.visible_to} if hoisted: "
                f"{len(shareable)} entries / {sh_lines} lines"
            )
            print(f"Pinned above it:                    "
                  f"{len(pinned)} entries / {pn_lines} lines\n")
            print("-- shareable (would otherwise be re-proved) --")
            for n in shareable:
                blockers = ", ".join(sorted(extern[n])) or "(nothing)"
                print(f"  {n:38s} {kind[n]:8s} {span[n]:4d}L  needs: {blockers}")
            print("\n-- pinned --")
            for n in pinned:
                out = ", ".join(sorted(extern[n] - vis))
                print(f"  {n:38s} {kind[n]:8s} {span[n]:4d}L  blocked by: {out}")
        else:
            homes = defaultdict(list)
            for n in names:
                if span[n] < args.min_lines:
                    continue
                legal = [
                    h
                    for h in universe
                    if extern[n] <= (closures.get(h, set()) | {h})
                ]
                minimal = [
                    h
                    for h in legal
                    if not any(
                        other != h and other in (closures.get(h, set()))
                        for other in legal
                    )
                ]
                homes[", ".join(sorted(minimal)) or "(unplaceable)"].append(n)
            for home, ns in sorted(homes.items(), key=lambda kv: -len(kv[1])):
                total = sum(span[n] for n in ns)
                if theory in home.split(", "):
                    flag = ""
                elif theory in DELIBERATE:
                    flag = "   <-- BY DESIGN"
                else:
                    flag = "   <-- OVER-PLACED"
                print(f"-- lowest home: {home}  ({len(ns)} entries / {total}L){flag}")
                for n in ns:
                    print(f"     {n:38s} {kind[n]:8s} {span[n]:4d}L")
                print()
            print("(candidates, not a verdict: a lemma typechecking lower down "
                  "is not misplaced.\n Act on a group that is about the "
                  "destination's own definitions, or that a\n sibling branch "
                  "also needs.)")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
