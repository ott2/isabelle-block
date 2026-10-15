#!/usr/bin/env python3
"""Delete named entries (with their preambles) from the theory tree.

Usage: bin/prune-entries.py [--dry-run] NAME...
       bin/prune-entries.py [--dry-run] @FILE      (one name per line)

Each NAME is resolved to its theory through `query show`, then removed with
`bin/block.py delete THEORY.thy:NAME`, which takes the preamble with it and
heals the blank seam.  A name that `query show` cannot find, or finds in more
than one theory, is refused and nothing is deleted for it.

The companion of a dead-code audit: `query unused` against a baseline says
*which* entries have just lost their last caller, this removes them, and the
next round of the audit finds what their removal orphaned in turn.  It checks
nothing about deadness itself; that is the audit's job, and the build's.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOCK = ROOT / "bin" / "block.py"


def names_from(args):
    out = []
    for a in args:
        if a.startswith("@"):
            out += [l.strip() for l in Path(a[1:]).read_text().splitlines()
                    if l.strip() and not l.startswith("#")]
        else:
            out.append(a)
    return out


def locate(name):
    r = subprocess.run(["query", "show", name], capture_output=True, text=True,
                       cwd=ROOT)
    hits = set(re.findall(rf"^--- {re.escape(name)} \(\w+\) — (\S+\.thy)",
                          r.stdout, re.M))
    return hits


def theory_path(thy):
    found = list((ROOT / "t").rglob(thy))
    return found[0] if len(found) == 1 else None


def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]
    bad = 0
    for name in names_from(args):
        hits = locate(name)
        if len(hits) != 1:
            print(f"FAIL: {name}: found in {sorted(hits) or 'no theory'}")
            bad += 1
            continue
        path = theory_path(hits.pop())
        if path is None:
            print(f"FAIL: {name}: theory file not unique on disk")
            bad += 1
            continue
        cmd = [sys.executable, str(BLOCK), "delete",
               f"{path.relative_to(ROOT)}:{name}"] + (["--dry-run"] if dry else [])
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        last = (r.stdout.strip().splitlines() or [r.stderr.strip()])[-1]
        print(f"  {name}: {last}")
        bad += r.returncode != 0
    print("PASS: all deleted" if not bad else f"FAIL: {bad} name(s) not deleted")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
