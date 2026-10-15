#!/usr/bin/env python3
"""old-names-sweep.py — find pre-rename MAT names left in live Markdown.

Usage: bin/old-names-sweep.py [LISTFILE]   (default scratch/live-md.txt)

Reads a list of Markdown paths and reports each line naming one of the
names the 2026-10-04 ktm rename and the CE rename retired, split into
backticked mentions (code spans) and bare prose mentions.  Prints a
per-file count table, then the bare-prose lines in full, then PASS/FAIL
(FAIL if any mention remains).
"""
import re
import sys
from collections import Counter

OLD = (r"mttm|MTTM|mt_config|go_dir|finite_UNIV_dir|Q_tm|Sigma_tm|bl_tm|le_tm|"
       r"delta_tm|s_tm|t_tm|r_tm|k_tm|Gamma_tm|mt_state|mt_tape|mt_pos|"
       r"relpow_transI|relpow_mono|CE|ce_read|ce_delta|ce_tape|ce_cfg")
WORD = re.compile(r"\b(?:\w+_)?(?:" + OLD + r")(?:_\w+)?\b")
CODE = re.compile(r"`[^`]*`")


def main():
    listfile = sys.argv[1] if len(sys.argv) > 1 else "scratch/live-md.txt"
    paths = [p.strip() for p in open(listfile) if p.strip()]
    ticked, bare = Counter(), Counter()
    bare_lines = []
    for p in paths:
        try:
            text = open(p, encoding="utf-8").read().splitlines()
        except OSError:
            continue
        for i, line in enumerate(text, 1):
            spans = CODE.findall(line)
            outside = CODE.sub("", line)
            nt = sum(len(WORD.findall(s)) for s in spans)
            nb = len(WORD.findall(outside))
            ticked[p] += nt
            if nb:
                bare[p] += nb
                bare_lines.append(f"{p}:{i}: {line.strip()}")
    files = sorted(set(ticked) | set(bare), key=lambda f: -(ticked[f] + bare[f]))
    total = 0
    print(f"{'ticked':>7} {'bare':>5}  file")
    for f in files:
        if ticked[f] + bare[f]:
            total += ticked[f] + bare[f]
            print(f"{ticked[f]:>7} {bare[f]:>5}  {f}")
    print("\n== bare-prose mentions ==")
    print("\n".join(bare_lines))
    print(f"\n{'FAIL' if total else 'PASS'}: {total} old-name mention(s) "
          f"in {sum(1 for f in files if ticked[f] + bare[f])} file(s)")


if __name__ == "__main__":
    main()
