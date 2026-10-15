#!/usr/bin/env python3
"""Shift the indentation of a line range in a file.

Isar restructuring -- wrapping an existing proof block in one more
``proof (cases ...)`` level -- moves a region two columns right and
changes nothing else.  Retyping the region by hand risks corrupting the
``\\<...>`` symbol names it is full of, so shift it mechanically instead.

    bin/reindent.py FILE A..B N        # N may be negative

Lines are 1-indexed and the range is inclusive, matching ``query lines``
and ``bin/block.py``.  Blank lines are left alone.  A negative shift that
would eat non-space characters is refused, with the offending line named.
"""

import argparse
import sys


def parse_range(spec):
    for sep in ("..", "-"):
        if sep in spec:
            lo, _, hi = spec.partition(sep)
            return int(lo), int(hi)
    raise ValueError(f"not a line range: {spec!r}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file")
    ap.add_argument("range", help="A..B, 1-indexed inclusive")
    ap.add_argument("shift", type=int, help="columns to shift (may be negative)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    lo, hi = parse_range(args.range)
    with open(args.file, encoding="utf-8") as fh:
        lines = fh.readlines()

    if not 1 <= lo <= hi <= len(lines):
        print(f"FAIL: range {lo}..{hi} outside 1..{len(lines)}")
        return 1

    out = list(lines)
    touched = 0
    for n in range(lo, hi + 1):
        line = lines[n - 1]
        if not line.strip():
            continue
        if args.shift >= 0:
            out[n - 1] = " " * args.shift + line
        else:
            drop = -args.shift
            if line[:drop].strip():
                print(f"FAIL: line {n} has less than {drop} leading spaces: {line!r}")
                return 1
            out[n - 1] = line[drop:]
        touched += 1

    if args.dry_run:
        sys.stdout.write("".join(out[lo - 1:hi]))
        print(f"PASS: {touched} line(s) would shift by {args.shift:+d} (dry run)")
        return 0

    with open(args.file, "w", encoding="utf-8") as fh:
        fh.writelines(out)
    print(f"PASS: shifted {touched} line(s) in {args.file} {lo}..{hi} by {args.shift:+d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
