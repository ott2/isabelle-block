#!/usr/bin/env python3
"""Insert a block of text after every line matching an anchor, verified.

The additive pass -- threading one new conjunct through a chain of
`obtains` lemmas -- is the recurring shape in `t/nth` (`nth-design.md`
G-T, G-AC).  Every site restates the same clause, so the edit is
"after each line that reads exactly A, put B".  `bin/block.py` addresses
*blocks* and has no insert verb; Edit needs a unique anchor per site and
there is none when fifteen statements are byte-identical.

The verification is the point.  The anchor must match exactly (leading
and trailing whitespace included), and `--expect N` asserts how many
sites were found, so a pass that silently hits fourteen or sixteen
places fails loudly instead of building red somewhere else.

Usage:

    bin/insert-after.py FILE ANCHOR_FILE INSERT_FILE --expect 15
    bin/insert-after.py FILE ANCHOR_FILE INSERT_FILE --expect 15 --dry-run

ANCHOR_FILE holds the single line to match; INSERT_FILE holds the lines
to place after it.  Both are files rather than arguments because an
Isabelle clause contains `\\<le>` and the shell here is tcsh, which
doubles the backslashes (memory: feedback_no_isabelle_symbols_in_shell).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def run(path: Path, anchor: str, insert: list[str], expect: int | None,
        dry_run: bool) -> int:
    lines = path.read_text().splitlines(keepends=True)
    hits = [n for n, line in enumerate(lines) if line.rstrip("\n") == anchor]

    if expect is not None and len(hits) != expect:
        print(f"FAIL: {path}: anchor matched {len(hits)} line(s), "
              f"expected {expect}")
        for n in hits:
            print(f"  hit at line {n + 1}")
        return 1

    if not hits:
        print(f"FAIL: {path}: anchor matched no line")
        return 1

    for n in reversed(hits):
        lines[n + 1:n + 1] = insert

    verb = "would insert" if dry_run else "inserted"
    print(f"PASS: {path}: {verb} {len(insert)} line(s) after "
          f"{len(hits)} site(s): "
          + ", ".join(str(n + 1) for n in hits))
    if not dry_run:
        path.write_text("".join(lines))
    return 0


def selftest() -> int:
    import tempfile

    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as d:
        f = Path(d) / "t.txt"
        f.write_text("a\nX\nb\nX\n")
        rc = run(f, "X", ["Y\n"], 2, False)
        ok = rc == 0 and f.read_text() == "a\nX\nY\nb\nX\nY\n"
        if not ok:
            print("FAIL: selftest: insertion wrong")
            return 1
        f.write_text("a\nX\n")
        if run(f, "X", ["Y\n"], 2, False) == 0:
            print("FAIL: selftest: wrong --expect was accepted")
            return 1
        f.write_text("a\n  X\n")
        if run(f, "X", ["Y\n"], 1, False) == 0:
            print("FAIL: selftest: leading whitespace was ignored")
            return 1
    print("PASS: selftest")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("file", nargs="?")
    p.add_argument("anchor_file", nargs="?")
    p.add_argument("insert_file", nargs="?")
    p.add_argument("--expect", type=int)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()

    if a.selftest:
        return selftest()
    if not (a.file and a.anchor_file and a.insert_file):
        p.error("FILE, ANCHOR_FILE and INSERT_FILE are all required")

    anchor_lines = Path(a.anchor_file).read_text().splitlines()
    if len(anchor_lines) != 1:
        print(f"FAIL: {a.anchor_file}: anchor must be exactly one line, "
              f"got {len(anchor_lines)}")
        return 1

    insert = Path(a.insert_file).read_text().splitlines(keepends=True)
    if insert and not insert[-1].endswith("\n"):
        insert[-1] += "\n"

    return run(Path(a.file), anchor_lines[0], insert, a.expect, a.dry_run)


if __name__ == "__main__":
    sys.exit(main())
