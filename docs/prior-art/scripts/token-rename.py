#!/usr/bin/env python3
"""Safe, dry-runnable regex token rename in one text file.

A disciplined stand-in for ad-hoc ``sed``: it always reports the *whole*
change set (``--dry-run``) before writing, and it can leave named lines
untouched (``--exclude``) for the occurrences a blanket regex would get
wrong -- e.g. a token that means one thing in most lines and something
unrelated in a few.

Word boundaries do the heavy lifting: ``--pattern '\\bk\\b'`` renames a
standalone ``k`` while leaving ``k_tm`` / ``tape_k_M`` intact (the ``k``
there abuts ``_``, a word char, so there is no boundary).

Examples
--------
  # preview every change, skipping a line where `k` is a different `k`:
  bin/token-rename.py doc.md --pattern '\\bk\\b' --replace bit_width \\
      --exclude 453 --dry-run
  # apply it:
  bin/token-rename.py doc.md --pattern '\\bk\\b' --replace bit_width --exclude 453
"""
import argparse
import re


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('file')
    ap.add_argument('--pattern', required=True, help='regex to match (e.g. \\bk\\b)')
    ap.add_argument('--replace', required=True, help='replacement string')
    ap.add_argument('--exclude', default='',
                    help='comma-separated 1-based line numbers to leave untouched')
    ap.add_argument('--only', default='',
                    help='comma-separated 1-based line numbers to change (all others left '
                         'untouched); use for a token whose sense is line-dependent')
    ap.add_argument('--dry-run', action='store_true',
                    help='report every proposed change without writing')
    args = ap.parse_args()

    pat = re.compile(args.pattern)
    exclude = {int(x) for x in args.exclude.split(',') if x.strip()}
    only = {int(x) for x in args.only.split(',') if x.strip()}
    with open(args.file, encoding='utf-8') as f:
        lines = f.readlines()

    changed = 0
    out = []
    for i, line in enumerate(lines, start=1):
        if i in exclude or (only and i not in only):
            out.append(line)
            continue
        new = pat.sub(args.replace, line)
        if new != line:
            changed += 1
            if args.dry_run:
                print(f'LINE {i}:')
                print(f'  - {line.rstrip()}')
                print(f'  + {new.rstrip()}')
        out.append(new)

    if args.dry_run:
        print(f'\n{changed} line(s) would change (excluded: {sorted(exclude)})')
    else:
        with open(args.file, 'w', encoding='utf-8') as f:
            f.writelines(out)
        print(f'PASS: rewrote {changed} line(s) in {args.file} '
              f'(excluded: {sorted(exclude)})')


if __name__ == '__main__':
    main()
