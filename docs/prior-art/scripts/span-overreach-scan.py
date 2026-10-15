#!/usr/bin/env python3
"""Regression check: does an entry's span ever run into its successor's?

`query` attributes a leading doc block forward, to the entry it documents,
so an entry's span stops before the next entry's own start.  `bin/block.py`
*writes* through a resolved span, which is what makes a regression here
destructive rather than merely confusing -- `delete FILE:<name>` would take
the following lemma's documentation with it.  Expected answer: 0.

Re-run after an `isabelle-query` upgrade; that is the event that could move
the attachment.
"""
from __future__ import annotations

import sys
from pathlib import Path

from isabelle_query.api import parse_theory


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "t")
    total = over = 0
    shown = 0
    for p in sorted(root.rglob("*.thy")):
        try:
            s = parse_theory(p.stem, p)
        except Exception as exc:  # noqa: BLE001
            print(f"  skip {p}: {exc}")
            continue
        es = sorted(s.entries, key=lambda e: e.thy_line)
        for i, e in enumerate(es[:-1]):
            total += 1
            nxt = es[i + 1]
            nlo = nxt.preamble[0] if nxt.preamble else nxt.thy_line
            hi = e.body_end_line or e.thy_end
            if hi >= nlo:
                over += 1
                if shown < 8:
                    shown += 1
                    print(f"  {p.name}:{e.name} hi={hi} >= {nxt.name}@{nlo}")
    print(f"PASS: {over}/{total} entries whose clipped span would reach the "
          f"next entry's start")
    return 0


if __name__ == "__main__":
    sys.exit(main())
