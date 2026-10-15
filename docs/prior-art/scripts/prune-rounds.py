#!/usr/bin/env python3
"""Prune a dead subtree in rounds against a baseline zero-caller list.

Usage: bin/prune-rounds.py [--dry-run] [--force-roots] SESSION_DIR BASELINE ROOT...

Deletes each ROOT, then repeats: list the zero-caller entries of SESSION_DIR
(`query -R SESSION_DIR unused`), delete exactly those that are not in the
BASELINE list, and stop when a round finds none.  BASELINE is a saved
`query unused` output taken before the first deletion, so entries that were
already zero-caller -- headline theorems, implicitly used [simp] rules, other
dead code awaiting its own decision -- are never touched.

This is the static half of insights/37's baseline-rounds method: it trusts
`query`'s call graph, so the build is the check.  A [simp] or [intro] rule
whose only uses are implicit looks zero-caller once its explicit callers go,
and would be deleted here; the build then fails at the use, and the rule
goes back.  So neither is deleted: definitions and other non-lemma entries
(see PRUNABLE), and lemmas unused_lib.implicit_use flags, are kept and
reported.  So is anything unused_lib.mentioned finds named outside its own
span -- in the session's prose or the design docs -- because deleting it
leaves the explanation pointing at nothing; that applies to roots too, unless
--force-roots is given, for roots already decided on by hand whose prose the
caller will repair (the cascade rounds stay guarded either way).  Prints each
round's names and a total.  --dry-run stops after reporting the first round.
"""
import re
import subprocess
import sys
from pathlib import Path

from unused_lib import implicit_use, mentioned

ROOT = Path(__file__).resolve().parent.parent
PRUNE = ROOT / "bin" / "prune-entries.py"
ROW = re.compile(r"^([A-Z]+)\s+(\S+)\s+\S+\s+\((\d+)\.\.(\d+), (\d+) lines\)")
# Only these are deleted.  `query`'s caller graph counts proof-body
# references, so a definition used only in *statements* looks zero-caller
# once the lemmas that unfold it go; deleting it breaks every statement that
# names it.  Such entries are reported, never deleted.
PRUNABLE = {"LEMMA", "THEOREM", "COROLLARY", "PROPOSITION"}


def unused(session_dir):
    r = subprocess.run(["query", "-R", session_dir, "unused"], capture_output=True,
                       text=True, cwd=ROOT)
    out = {}
    for line in r.stdout.splitlines():
        m = ROW.match(line)
        if m:
            out[m.group(2)] = (m.group(1), int(m.group(5)))
    return out


def names_in(path):
    out = set()
    for line in Path(path).read_text().splitlines():
        m = ROW.match(line)
        if m:
            out.add(m.group(2))
    return out


def prune(names):
    r = subprocess.run([str(PRUNE)] + sorted(names), capture_output=True, text=True,
                       cwd=ROOT)
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr)
    return r.returncode == 0


def main(argv):
    dry = "--dry-run" in argv
    force = "--force-roots" in argv
    argv = [a for a in argv if a not in ("--dry-run", "--force-roots")]
    if len(argv) < 3:
        print(__doc__)
        return 2
    session_dir, baseline, roots = argv[0], argv[1], argv[2:]
    base = names_in(baseline)
    if not base:
        print(f"FAIL: no entries parsed from {baseline}")
        return 1
    before = unused(session_dir)
    root_lines = sum(before.get(r, ("", 0))[1] for r in roots)
    print(f"round 0: {len(roots)} root(s), {root_lines} lines: {' '.join(roots)}")
    kept_roots = []
    for r in roots:
        why = implicit_use(session_dir, r) or (not force and mentioned(session_dir, r))
        if why:
            print(f"round 0: kept root {r} ({why})")
            kept_roots.append(r)
    roots = [r for r in roots if r not in kept_roots]
    root_lines = sum(before.get(r, ("", 0))[1] for r in roots)
    print(f"round 0: pruning {len(roots)} root(s), {root_lines} lines")
    if not roots:
        return 0
    if dry:
        return 0
    if not prune(roots):
        print("FAIL: could not delete the roots")
        return 1
    total, lines, rnd, skipped = len(roots), root_lines, 0, set()
    while True:
        rnd += 1
        now = unused(session_dir)
        fresh = {n: tl for n, tl in now.items() if n not in base}
        for n, (tag, _) in fresh.items():
            if n in skipped:
                continue
            if tag not in PRUNABLE:
                print(f"round {rnd}: kept {tag} {n} (statement-level uses are invisible)")
                skipped.add(n)
            else:
                why = implicit_use(session_dir, n) or mentioned(session_dir, n)
                if why:
                    print(f"round {rnd}: kept {tag} {n} ({why})")
                    skipped.add(n)
        new = {n: l for n, (tag, l) in fresh.items() if tag in PRUNABLE and n not in skipped}
        if not new:
            break
        n_lines = sum(new.values())
        print(f"round {rnd}: {len(new)} entries, {n_lines} lines: {' '.join(sorted(new))}")
        if not prune(new):
            print(f"FAIL: round {rnd} could not delete every name")
            return 1
        total += len(new)
        lines += n_lines
    print(f"PASS: {rnd - 1} round(s) after the roots; {total} entries, {lines} lines deleted;"
          f" {len(skipped)} entries kept (definitions, possibly implicit rules, or named"
          f" in prose)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
