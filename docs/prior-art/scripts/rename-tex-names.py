#!/usr/bin/env python3
"""Apply a bin/rename-thy-names.py map to LaTeX document files.

A document's root.tex (and glossary.tex) spells Isabelle names the LaTeX way:
`valid\\_mttm`, `\\isasymGamma\\_tm`.  This tool rewrites each OLD of the map,
in that spelling, to NEW in the same spelling, as a whole name: not when it
is part of a longer name (`valid\\_mttm\\_iff` is renamed only if the map has
it).  Unlike the theory tool it renames in prose too: in a document a name
is always set as a name (\\texttt, \\mathrm, \\isa...), never as an English word,
so only use it with maps of non-word identifiers.

Usage: bin/rename-tex-names.py MAP FILE... [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys


def tex(name: str) -> str:
    """Isabelle spelling -> LaTeX spelling."""
    name = re.sub(r"\\<\^sub>(\w)", r"$_{\1}$", name)
    name = re.sub(r"\\<(\w+)>", r"\\isasym\1", name)
    return name.replace("_", r"\_")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("map")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    table = {}
    with open(args.map, encoding="utf-8") as f:
        for line in f:
            parts = line.split("#", 1)[0].split()
            if parts:
                if len(parts) != 2:
                    print(f"FAIL: bad map line: {parts}")
                    return 1
                table[tex(parts[0])] = tex(parts[1])
    # a name character in LaTeX spelling: a letter, a digit, or an escaped _
    tok = re.compile(r"(?<![A-Za-z0-9])(?<!\\_)(" + "|".join(
        re.escape(o) for o in sorted(table, key=len, reverse=True))
        + r")(?![A-Za-z0-9'])(?!\\_)")
    total = 0
    for path in args.files:
        with open(path, encoding="utf-8") as f:
            src = f.read()
        new, n = tok.subn(lambda m: table[m.group(1)], src)
        if n:
            print(f"{path}: {n}")
            total += n
            if not args.dry_run:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new)
    print(f"PASS: renamed {total} occurrence(s)" + (" (dry run)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
