#!/usr/bin/env python3
"""Insert a hypothesis line into a family of theorems, after a fixed anchor.

A migration that adds one `assumes` clause to every theorem in a chain is a
dozen identical edits with no line arithmetic worth doing by hand, and the
anchor line is the same in each.  This inserts NEW immediately after every
line equal to ANCHOR, optionally skipping named entries (the ones that keep
the weaker hypothesis set) and reporting where it landed.

    bin/insert-hyp.py t/nth/Diagonal_Order.thy \
        --after '      and T: "T = ..."' \
        --line  '      and fits: "body_off i \\<le> bitlen i"' \
        --skip order_hdr_run,order_hdr_parse --dry-run

Idempotent: a site whose next line already equals NEW is left alone.
"""

import argparse
import sys
from pathlib import Path

from isabelle_query.api import parse_theory


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--after", required=True, help="exact anchor line")
    ap.add_argument("--line", required=True, help="line to insert after it")
    ap.add_argument("--skip", default="", help="comma-separated entry names")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    skip = {s for s in args.skip.split(",") if s}
    text = Path(args.file).read_text(encoding="utf-8")
    lines = text.split("\n")

    owner = {}
    for e in parse_theory(text, Path(args.file)).entries:
        for n in range(e.thy_line, e.thy_end + 1):
            owner[n] = e.name

    out, hits, skipped = [], [], []
    for n, line in enumerate(lines, start=1):
        out.append(line)
        if line != args.after:
            continue
        name = owner.get(n, "?")
        if name in skip:
            skipped.append(f"{n} ({name})")
            continue
        if n < len(lines) and lines[n] == args.line:
            skipped.append(f"{n} ({name}, already present)")
            continue
        out.append(args.line)
        hits.append(f"{n} ({name})")

    for h in hits:
        print(f"  insert after line {h}")
    for s in skipped:
        print(f"  skip line {s}")
    if not hits:
        print("FAIL: no insertion sites")
        return 1
    if args.dry_run:
        print(f"PASS: {len(hits)} site(s) would change (dry run)")
        return 0
    open(args.file, "w", encoding="utf-8").write("\n".join(out))
    print(f"PASS: {len(hits)} site(s) changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
