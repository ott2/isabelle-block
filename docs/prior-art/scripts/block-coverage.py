#!/usr/bin/env python3
"""block-coverage.py --- which occurrences of a marker lie outside a block?

    bin/block-coverage.py BLOCK_RE MARKER_RE FILE...

BLOCK_RE is a regex matched across lines (whitespace in the source may be any
run of spaces and newlines; write it as `\\s*` or `\\s+`).  MARKER_RE is a
single-line regex.  Either may be `@FILE`, read from FILE, so the pattern a
`bin/block.py resub` will use can be checked first.  Prints every line holding a MARKER_RE match that is not
inside some BLOCK_RE match, then a PASS/FAIL summary.

Use: before folding a repeated multi-line term into a definition, confirm that
every occurrence is the canonical contiguous form, and list the ones that are
not (reordered, split across a step, partially instantiated).
"""
import re
import sys


def main(argv):
    if len(argv) < 4:
        print(__doc__.strip())
        return 2
    def arg(s):
        # `@FILE` reads the pattern from FILE, as `block.py resub` does
        if s.startswith("@"):
            return open(s[1:], encoding="utf-8").read().rstrip("\n")
        return s

    block = re.compile(arg(argv[1]))
    marker = re.compile(arg(argv[2]))
    total_blocks = 0
    outside = []
    for path in argv[3:]:
        text = open(path, encoding="utf-8").read()
        covered = []
        for m in block.finditer(text):
            covered.append((m.start(), m.end()))
            total_blocks += 1
        line_starts = [0]
        for i, ch in enumerate(text):
            if ch == "\n":
                line_starts.append(i + 1)
        for m in marker.finditer(text):
            if not any(a <= m.start() < b for a, b in covered):
                # line number of the marker
                lo, hi = 0, len(line_starts)
                while hi - lo > 1:
                    mid = (lo + hi) // 2
                    if line_starts[mid] <= m.start():
                        lo = mid
                    else:
                        hi = mid
                line = text[line_starts[lo]:text.find("\n", line_starts[lo])]
                outside.append(f"{path}:{lo + 1}: {line.strip()}")
    for o in outside:
        print(o)
    if outside:
        print(f"FAIL: {len(outside)} marker occurrence(s) outside {total_blocks} block(s)")
        return 1
    print(f"PASS: every marker occurrence lies inside one of {total_blocks} block(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
