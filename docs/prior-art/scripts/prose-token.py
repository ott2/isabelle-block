#!/usr/bin/env python3
"""Report token matches inside Isabelle *prose* (document text), not code.

Prose = the body of a cartouche ``\\<open>...\\<close>`` opened by a document
command (``text``, ``txt``, ``section``, ``subsection``, ``subsubsection``,
``paragraph``, ``chapter``, ``text_raw``) or an inline ``\\<comment>``;
nested cartouches inherit the prose-ness of their outermost opener.  Old-style
``(* ... *)`` comments (nesting-aware) count as prose too.

Motivation: after a code-level identifier migration, a stale symbol can only
survive in prose -- but the same token may be a perfectly correct *code*
variable in thousands of places.  This isolates the prose occurrences so a
rename never touches a code binder.

Usage:
  bin/prose-token.py FILE... [--pattern REGEX]
Default pattern is ``\\bk\\b`` (standalone k).  Prints ``FILE:LINE: <line>``
for every match inside prose, then a per-file and total count.
"""
import argparse
import re

OPEN = r'\<open>'
CLOSE = r'\<close>'
PROSE_KW = {'text_raw', 'text', 'txt', 'section', 'subsection',
            'subsubsection', 'paragraph', 'chapter'}


def prose_spans(src):
    """List of (start, end) char offsets of prose regions in src."""
    spans = []
    i, n = 0, len(src)
    depth = 0
    outer_is_prose = False
    outer_start = None
    while i < n:
        # old-style (* ... *) comment (nesting-aware), only when not in a cartouche
        if depth == 0 and src.startswith('(*', i):
            d, j = 1, i + 2
            start = j
            while j < n and d > 0:
                if src.startswith('(*', j):
                    d += 1; j += 2
                elif src.startswith('*)', j):
                    d -= 1; j += 2
                else:
                    j += 1
            spans.append((start, j - 2))
            i = j
            continue
        if src.startswith(OPEN, i):
            if depth == 0:
                before = src[:i].rstrip()
                if before.endswith(r'\<comment>'):
                    is_prose = True
                else:
                    m = re.search(r'([A-Za-z_]+)$', before)
                    is_prose = bool(m and m.group(1) in PROSE_KW)
                outer_is_prose = is_prose
                outer_start = i + len(OPEN)
            depth += 1
            i += len(OPEN)
        elif src.startswith(CLOSE, i):
            if depth > 0:
                depth -= 1
                if depth == 0 and outer_is_prose:
                    spans.append((outer_start, i))
            i += len(CLOSE)
        else:
            i += 1
    return spans


def line_of(src, off, line_starts):
    # binary-search the line number (1-based) containing char offset off
    import bisect
    return bisect.bisect_right(line_starts, off)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('files', nargs='+')
    ap.add_argument('--pattern', default=r'\bk\b')
    args = ap.parse_args()

    pat = re.compile(args.pattern)
    grand = 0
    for path in args.files:
        with open(path, encoding='utf-8') as f:
            src = f.read()
        line_starts = [0]
        for idx, ch in enumerate(src):
            if ch == '\n':
                line_starts.append(idx + 1)
        spans = prose_spans(src)
        hits = []
        for (a, b) in spans:
            for m in pat.finditer(src, a, b):
                hits.append(m.start())
        hits = sorted(set(hits))
        seen_lines = set()
        for off in hits:
            ln = line_of(src, off, line_starts)
            if ln in seen_lines:
                continue
            seen_lines.add(ln)
            text = src.splitlines()[ln - 1]
            print(f'{path}:{ln}: {text.strip()}')
        if hits:
            print(f'  -- {path}: {len(hits)} prose match(es) on {len(seen_lines)} line(s)')
        grand += len(hits)
    print(f'TOTAL: {grand} prose match(es)')


if __name__ == '__main__':
    main()
