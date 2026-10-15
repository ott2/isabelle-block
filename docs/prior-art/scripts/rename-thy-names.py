#!/usr/bin/env python3
"""Rename whole Isabelle identifiers in .thy files, leaving English prose alone.

    bin/rename-thy-names.py MAP FILE... [--dry-run]

MAP has one ``OLD NEW`` pair per line (``#`` comments allowed).  Each OLD is
a whole identifier: ``restate`` renames ``restate`` and ``M.restate`` but not
``restated``, ``restate_def`` or ``unary_marks`` -- list every family member
you mean, so the change set is exactly the map.

Where a rename applies:
  * source outside prose: everywhere (terms, proofs, ``"..."`` strings);
  * prose -- the body of ``text`` / ``txt`` / ``text_raw`` / section headings
    / ``\\<comment>`` cartouches and ``(* *)`` comments: only inside a nested
    cartouche or an ``@{...}`` antiquotation, where a name is a reference.
    A bare word there is English ("we restate the theorem") and is kept.

A ``.md`` file is renamed only inside backtick code spans, by the same
principle: there a name is a reference, elsewhere a word.  Design memos also
cite names in fenced blocks, bare prose and ``\<open>..\<close>``; for a map
whose names are not English words, ``--md-prose`` renames there too, and
``--keep OLD`` (repeatable) holds back a word-shaped entry such as ``dir``.
``--keep`` does not protect code spans: a name that is both an identifier and
a placeholder (``t/<dir>/``) needs its own map without it.  ``@FILE`` reads
arguments, one per line.

``block.py sub`` is a substring rename and rewrites prose too, so it is the
wrong tool for a word-shaped identifier (insights/289); this is the right one.
"""
import argparse
import re
import sys

OPEN, CLOSE = '\\<open>', '\\<close>'
PROSE_KW = re.compile(
    r'(?<![\w\'])(text|txt|text_raw|chapter|section|subsection|subsubsection|'
    r'paragraph|subparagraph|title)\s*(\([^()]*\)\s*)?(?=\\<open>)'
    r'|\\<comment>\s*(?=\\<open>)')


def segments(src):
    """Split SRC into (is_code, text) pieces."""
    out, buf, i, n = [], [], 0, len(src)

    def flush(code):
        if buf:
            out.append((code, ''.join(buf)))
            buf.clear()

    while i < n:
        if src.startswith('(*', i):
            flush(True)
            depth, j = 0, i
            while j < n:
                if src.startswith('(*', j):
                    depth += 1
                    j += 2
                elif src.startswith('*)', j):
                    depth -= 1
                    j += 2
                    if depth == 0:
                        break
                else:
                    j += 1
            out.extend(prose(src[i:j]))
            i = j
            continue
        if src[i] == '"':
            j = i + 1
            while j < n and src[j] != '"':
                j += 2 if src[j] == '\\' and src[j + 1:j + 2] == '"' else 1
            buf.append(src[i:j + 1])
            i = j + 1
            continue
        m = PROSE_KW.match(src, i)
        if m:
            buf.append(m.group(0))
            flush(True)
            j = m.end()
            depth = 0
            k = j
            while k < n:
                if src.startswith(OPEN, k):
                    depth += 1
                    k += len(OPEN)
                elif src.startswith(CLOSE, k):
                    depth -= 1
                    k += len(CLOSE)
                    if depth == 0:
                        break
                else:
                    k += 1
            out.extend(prose(src[j:k]))
            i = k
            continue
        buf.append(src[i])
        i += 1
    flush(True)
    return out


def prose(s):
    """Pieces of a prose block: depth-1 text is prose, nested cartouches and
    @{...} antiquotations are code."""
    out, buf, i, n = [], [], 0, len(s)
    depth = 0     # cartouche depth; the block's own cartouche is depth 1
    code_from = None

    def flush(code):
        if buf:
            out.append((code, ''.join(buf)))
            buf.clear()

    while i < n:
        if code_from is None and s.startswith('@{', i):
            flush(False)
            j, d = i + 2, 1
            while j < n and d:
                d += {'{': 1, '}': -1}.get(s[j], 0)
                j += 1
            out.append((True, s[i:j]))
            i = j
            continue
        if s.startswith(OPEN, i):
            depth += 1
            if depth == 2 and code_from is None:
                buf.append(OPEN)
                flush(False)
                code_from = i
                i += len(OPEN)
                continue
            buf.append(OPEN)
            i += len(OPEN)
            continue
        if s.startswith(CLOSE, i):
            depth -= 1
            if depth == 1 and code_from is not None:
                flush(True)
                code_from = None
            buf.append(CLOSE)
            i += len(CLOSE)
            continue
        buf.append(s[i])
        i += 1
    flush(code_from is not None)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 fromfile_prefix_chars='@')
    ap.add_argument('map')
    ap.add_argument('files', nargs='+')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--md-prose', action='store_true',
                    help='in .md files rename outside code spans too: '
                         'design memos also cite names in bare prose and '
                         'in \\<open>..\\<close>; pair with --keep for any '
                         'map entry that is also an English word')
    ap.add_argument('--keep', action='append', default=[], metavar='OLD',
                    help='with --md-prose: a map entry renamed in code '
                         'spans only (a word-shaped name such as dir); '
                         'repeatable')
    args = ap.parse_args()

    pairs = []
    with open(args.map, encoding='utf-8') as f:
        for line in f:
            line = line.split('#', 1)[0].split()
            if line:
                if len(line) != 2:
                    sys.exit(f'FAIL: bad map line: {line}')
                pairs.append(tuple(line))
    table = dict(pairs)
    def alternation(names):
        return re.compile(r"(?<![\w'])(" + '|'.join(
            re.escape(o) for o in sorted(names, key=len, reverse=True))
            + r")(?![\w'])")
    tok = alternation(table)
    prose_names = [o for o in table if o not in set(args.keep)]
    prose_tok = alternation(prose_names) if args.md_prose and prose_names else None

    total = 0
    for path in args.files:
        with open(path, encoding='utf-8') as f:
            src = f.read()
        if path.endswith('.md'):
            pieces = [(k % 2 == 1, t) for k, t in
                      enumerate(re.split(r'(`[^`\n]*`)', src))]
        else:
            pieces = segments(src)
        assert ''.join(t for _, t in pieces) == src, path
        count = 0

        def sub(m):
            nonlocal count
            count += 1
            return table[m.group(1)]
        md_prose = prose_tok if path.endswith('.md') else None
        new = ''.join(tok.sub(sub, t) if code
                      else md_prose.sub(sub, t) if md_prose else t
                      for code, t in pieces)
        if count:
            total += count
            print(f'{path}: {count}')
            if not args.dry_run:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new)
    verb = 'would rename' if args.dry_run else 'renamed'
    print(f'PASS: {verb} {total} occurrence(s) in {len(args.files)} file(s)')


if __name__ == '__main__':
    main()
