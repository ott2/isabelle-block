"""Mechanical block surgery on Isabelle theory and markdown sources.

One tool for "rewrite this region of this file", where the region is named
by a line span or by an entry name.  The domain is *blocks*: every verb
below takes a block of a source file and moves, copies, removes, prints,
rewrites or substitutes inside it.

Verbs
-----
  block move    SRC:REGION before DEST      relocate the block
  block copy    SRC:REGION before DEST      place a copy, source kept
  block delete  FILE:REGION                 excise the block
  block emit    FILE:REGION                 print the block to stdout
  block replace FILE:REGION NEWFILE         swap the block for a file
  block sub     OLD NEW FILE[:REGION]...    literal substring rename
  block resub   PAT NEW FILE[:REGION]...    regex substitution, may span lines
  block reargs  'F $1 $2' TMPL FILE[:R]...  rewrite F's applications by
                                            their (bracket-aware) arguments
  block split   SRC 'NAME|IMPORTS|RANGES'.. cut a theory into theories
  block merge   BASE.thy SRC.thy...         splice theory bodies into BASE

Addressing
----------
A target is `FILE:REGION`, one token, where REGION is:

  A..B    1-indexed inclusive line span -- what `query outline`, `query
          largest`, `query sorry` and `query enclosing` all print, so their
          output pastes straight in
  A-B     the same, hyphenated
  N       one line -- the locus form `query enclosing` prints
  NAME    an entry name, resolved through `isabelle_query.api` to the
          entry's `cut_span`: its doc preamble, if it has one, through the
          end of its proof
  all     the whole file; also the meaning of a bare FILE with no `:REGION`

DEST, for `move`/`copy`, is `FILE:LINE`, or `LINE` for the same file, or
`FILE:NAME` / `NAME` to land immediately before that entry (its preamble
included).  Landing before a *name* is the point of name addressing: hoisting
a helper above its first user needs no line arithmetic and cannot go stale
between the `query` call and the edit.

`cut_span` is the span `isabelle_query` documents as the one a tool writes
through: it holds the entry and no part of another, so it stops before the
next entry's doc block.  An entry that shares a line with another (two
declarations on one line) has no such span, and naming it is refused; use a
line span.

A doc block directly under a section heading may introduce the section
rather than document the entry, and the source cannot say which.  There,
`delete`, `move` and `replace` refuse until told: `--with-preamble` takes
the text with the entry, and `--no-preamble` leaves it under the heading.
`emit` and `copy` remove nothing, so they take it as usual.

Isabelle's keyword table is session-wide, so a theory may use a command that
another theory's `keywords` declares.  Name resolution therefore parses with
the table of the file's session.  The session root is `--root DIR` if given,
otherwise what `isabelle_layout.default_t_dir` finds from the file's
directory: `$ISABELLE_LAYOUT_ROOT` / `$ISABELLE_QUERY_ROOT`, a
`.isabelle-layout` / `.isabelle-query` marker, or the nearest `ROOT`.  With
none of these, the file's own directory stands in, and its theories supply
the table, as in `query`.  A file in no named session gets a NOTE on stderr
saying so.  Spans never touch the parser, so they are unaffected.

Modifiers
---------
  --dry-run              report the edit, write nothing
  --no-trailing-blank    verbatim cut with no blank-seam healing
  --no-preamble          a resolved NAME span starts at the entry, not its
                         doc block
  --with-preamble        a resolved NAME span keeps its doc block even when
                         that sits directly under a section heading
  --root DIR             the session root whose keyword table NAME
                         resolution parses with (default: discovered)
  --cut                  (split only) remove the extracted ranges from SRC
  --expect N             (sub, resub, reargs) refuse unless exactly N
                         substitutions are made; nothing is written
  --except NAME          (sub, resub, reargs; repeatable) leave entry NAME
                         out of every target region; refused if NAME is in
                         no target file

`block VERB --help` prints that verb's grammar (and its docstring, where it
has one) and exits 0 -- asking a verb for its own usage is not an error.

Examples
--------
  block move Foo.thy:3924..4274 before 3573      # hoist a helper
  block move Foo.thy:bor_cost_le before tape_val_dip
  block move Foo.thy:1669..2657 before Foo_Classical.thy:46
  block delete Foo.thy:dead_lemma
  block emit Src.thy:103..1528
  block replace tasks.md:1011..1024 new-item.txt
  block sub bit_width block_width A.thy B.thy
  block sub TP_TRS tp 'Arms.thy:1200..1260'
  block reargs 'bor_cost $1 $2' 'Suc (tape_len $1)' Foo.thy \
      --except bor_cost_def_lemma --expect 14
  block split Big.thy 'Part_A|Main|584..677' --cut
  block merge Base.thy Part1.thy Part2.thy

Substitution is literal on both sides.  The shell/perl predecessors passed
both through the environment because `\\Q..\\E` protects the pattern only and
an interpolated replacement is read as replacement syntax -- so `\\<lambda>`
became `<lambda>`, silently.  In Python `str.replace` is literal both ways
and that failure mode does not exist.

Blank seams: by default a move/copy heals to the .thy convention of one
blank line between blocks -- it absorbs a single trailing blank after the
block and splices with exactly one blank on each abutting side, collapsing
any pre-existing stack.  `--no-trailing-blank` keeps the boundaries
verbatim; `emit` is always verbatim.

Race-safety: reads then writes files in sequence; NOT safe to run
concurrently with another write (Edit / Write / a linter) on the same files.
Never put it in the same parallel-tool batch as an Edit/Write of that file.

Every run ends with an explicit PASS:/FAIL: line, and the exit status agrees
(0 or 1).  `emit` prints its PASS: on stderr, so stdout is the block alone.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


# --- reporting -------------------------------------------------------------

def fail(msg: str) -> "NoReturn":  # noqa: F821
    print(f"FAIL: {msg}")
    raise SystemExit(1)


# --- addressing ------------------------------------------------------------

SPAN_RE = re.compile(r"^(\d+)\s*(?:\.\.|-)\s*(\d+)$")


def read_lines(path: Path) -> list[str]:
    if not path.is_file():
        fail(f"not a file: {path}")
    return path.read_text().splitlines(keepends=True)


# `--root DIR`, set by main(); None means discover the root per file.
_ROOT: Path | None = None
# One parse per file per run: `--except` and the prose mask ask again, and a
# parse with a session's keyword table costs a walk of its theory headers.
# Every verb resolves before it writes, so a cached parse is never stale.
_SECTIONS: dict = {}


def _section(path: Path):
    """``path`` parsed by `isabelle_query.api.parse_theory`, with the keyword
    table of the file's session.

    Isabelle's keyword table is session-wide, so a theory can use a command
    that a sibling theory's `keywords` declares.  Parsed alone, that command
    is not recognised, and the entry above it swallows it: its span then
    takes the command's lines too.  Hence `root=`, which builds the table
    from every theory header under the root, as `query` does.  The root is
    found by `isabelle_layout.default_t_dir`, the discovery `query` itself
    uses, unless `--root` names one.  With no `ROOT` file, that is the file's
    own directory, whose `.thy` files then stand in for a session, again as
    in `query`.  When the file belongs to no named session, a NOTE says where
    its keyword table came from."""
    key = path.resolve()
    if key in _SECTIONS:
        return _SECTIONS[key]
    try:
        from isabelle_layout import default_t_dir
        from isabelle_query.api import parse_theory
    except ImportError as e:
        fail(f"{e.name} is not installed (a dependency of isabelle-block); "
             "name addressing needs it, spans do not")
    root = _ROOT if _ROOT is not None else default_t_dir(start=key.parent)
    try:
        sec = parse_theory(path.stem, path, root=root)
    except ValueError as e:
        if _ROOT is not None:
            fail(f"--root {_ROOT}: {e}")
        print(f"  NOTE: {path}: {e}; parsed alone, so a command declared by "
              "another theory's `keywords` is not recognised.  Pass --root "
              "DIR if it has a session.", file=sys.stderr)
        sec = parse_theory(path.stem, path)
    else:
        if sec.session is None:
            print(f"  NOTE: {path} is in no session under {root}; its keyword "
                  f"table comes from the theory headers there.  Pass --root "
                  "DIR if its session is elsewhere.", file=sys.stderr)
    _SECTIONS[key] = sec
    return sec


def _entries(path: Path):
    """Every Entry of ``path``, in source order."""
    return sorted(_section(path).entries, key=lambda e: e.thy_line)


def resolve_entry(path: Path, name: str, preamble: str = "auto",
                  removes: bool = False) -> tuple[int, int]:
    """The span of entry ``name``: its `Entry.cut_span`.

    `isabelle_query` documents `cut_span` as the span a tool writes through.
    It holds this entry and no part of another, so it stops before the next
    entry's doc block, and it is None when no line span can do that: two
    declarations on one line (`shares_line`).  That is a refusal here, never
    a fall-back to a wider span.

    ``preamble`` is "auto", "with" (`--with-preamble`) or "without"
    (`--no-preamble`, which starts the span at the declaration).  A doc
    preamble directly under a section heading (`preamble_follows_heading`)
    may introduce the section rather than document the entry, and the
    source cannot say which.  So a verb that ``removes`` the span (delete,
    move, replace) refuses there in "auto" and asks for one of the two.
    Binding it either way by default loses text silently some of the time.
    NDTHT lost a section's introduction that way three times.
    """
    entries = _entries(path)
    hits = [e for e in entries if e.name == name]
    if not hits:
        near = [e.name for e in entries if name in e.name][:5]
        hint = f"; did you mean {', '.join(near)}?" if near else ""
        fail(f"no entry named {name!r} in {path}{hint}")
    if len(hits) > 1:
        fail(f"{len(hits)} entries named {name!r} in {path}; use a line span")
    e = hits[0]
    span = e.cut_span
    if span is None:
        if not e.thy_line:
            fail(f"entry {name!r} in {path} has no place in the file; "
                 "use a line span")
        if e.runs_into_next:
            # This entry's own proof ends on the line where the next
            # declaration starts (`by simp lemma b: …`).
            fail(f"{path}:{e.thy_line}: entry {name!r} ends on the line where "
                 "the next declaration starts, so no line span holds it "
                 "alone; use a line span")
        fail(f"{path}:{e.thy_line}: entry {name!r} shares a line with another "
             "entry, so no line span holds it alone; use a line span")
    lo, hi = span
    if preamble == "without":
        return e.thy_line, hi
    if removes and preamble == "auto" and e.preamble and e.preamble_follows_heading:
        a, b = e.preamble
        fail(f"{path}:{a}: the text at lines {a}..{b} above {name!r} sits "
             "directly under a section heading, so it may introduce the "
             f"section rather than document {name!r}.  Say which: "
             "--with-preamble takes it with the entry, --no-preamble leaves "
             "it under the heading")
    return lo, hi


def parse_target(spec: str, preamble: str = "auto", removes: bool = False
                 ) -> tuple[Path, int, int]:
    """`FILE`, `FILE:A..B`, `FILE:A-B` or `FILE:NAME` -> (path, lo, hi).
    ``preamble`` and ``removes`` apply to a NAME; see `resolve_entry`."""
    path_s, sep, region = spec.rpartition(":")
    if not sep:
        path, region = Path(spec), "all"
    else:
        path = Path(path_s)
    if not path.is_file():
        # A colon may belong to the path rather than the region.
        if sep and Path(spec).is_file():
            path, region = Path(spec), "all"
        else:
            fail(f"not a file: {path}")
    n = len(read_lines(path))
    if region == "all":
        return path, 1, n
    m = SPAN_RE.match(region)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
    elif region.isdigit():
        # A bare line number is the one-line span: `query enclosing` prints
        # loci as `THY:LINE`, and locations and spans share one grammar.
        lo = hi = int(region)
    else:
        lo, hi = resolve_entry(path, region, preamble, removes)
    if lo < 1 or hi < lo:
        fail(f"bad region {region!r} -> {lo}..{hi}")
    if hi > n:
        fail(f"region end {hi} > {path} length ({n})")
    return path, lo, hi


def parse_dest(spec: str, src: Path) -> tuple[Path, int]:
    """`LINE`, `NAME`, `FILE:LINE` or `FILE:NAME` -> (path, line)."""
    path_s, sep, where = spec.rpartition(":")
    if sep and Path(path_s).is_file():
        path = Path(path_s)
    else:
        path, where = src, spec
    if where.isdigit():
        return path, int(where)
    lo, _ = resolve_entry(path, where)
    return path, lo


# --- splice helpers --------------------------------------------------------

def _is_blank(line: str) -> bool:
    return line.strip() == ""


def norm_splice(left: list[str], block: list[str], right: list[str]
                ) -> tuple[list[str], int, int]:
    """Splice ``left + block + right`` with exactly one blank line at each
    seam where both sides carry content.

    The moved block is treated like a paragraph: pre-existing blank lines at
    the destination insertion point and the block's own outer blanks are
    collapsed, then a single blank separator is reinstated on each side that
    abuts content.  This stops a non-blank-leading block from stacking
    against blanks that already sat above the target (e.g. the double blank
    a file keeps before a subsection header).  Interior blanks are untouched.

    Returns ``(lines, offset, block_len)`` with ``offset`` the 0-based index
    of the block's first line, so the caller can report a landing range.
    """
    l, b, r = list(left), list(block), list(right)
    while l and _is_blank(l[-1]):
        l.pop()
    while b and _is_blank(b[0]):
        b.pop(0)
    while b and _is_blank(b[-1]):
        b.pop()
    while r and _is_blank(r[0]):
        r.pop(0)
    head = l + (["\n"] if l and b else [])
    tail = (["\n"] if b and r else []) + r
    return head + b + tail, len(head), len(b)


def write(path: Path, lines: list[str], dry: bool) -> None:
    if not dry:
        path.write_text("".join(lines))


# --- verbs -----------------------------------------------------------------

# One grammar line per verb, used by both the argument-count refusals and
# `block VERB --help`.  Keeping them in one table is the point: a verb
# whose usage string lived only inside its own `fail` could not answer
# `--help` without the string being written twice and drifting.
USAGE = {
    "move": "block move SRC:REGION before DEST",
    "copy": "block copy SRC:REGION before DEST",
    "delete": "block delete FILE:REGION",
    "emit": "block emit FILE:REGION",
    "replace": "block replace FILE:REGION NEWFILE",
    "sub": "block sub OLD NEW FILE[:REGION]...",
    "resub": "block resub PATTERN NEW FILE[:REGION]...",
    "reargs": "block reargs 'HEAD $1 .. $n' TEMPLATE FILE[:REGION]...",
    "split": "block split SRC 'NAME|IMPORTS|RANGES'... [--cut]",
    "merge": "block merge BASE.thy SRC.thy...",
}


def v_move(args, opt, copy: bool) -> int:
    if len(args) != 3 or args[1] != "before":
        fail(f"usage: {USAGE['copy' if copy else 'move']}")
    # A move takes the block away from where it was; a copy leaves it there.
    src, start, end = parse_target(args[0], opt["preamble"], removes=not copy)
    dst, target = parse_dest(args[2], src)
    verb = "copied" if copy else "moved"
    absorb = opt["absorb"]
    intra = src.resolve() == dst.resolve()

    src_lines = read_lines(src)
    n_src = len(src_lines)
    start_idx, end_idx = start - 1, end

    if absorb and end_idx < n_src and _is_blank(src_lines[end_idx]):
        block_end_idx = end_idx + 1
    else:
        block_end_idx = end_idx
    raw_block = src_lines[start_idx:block_end_idx]
    block = raw_block

    if intra:
        if target < 1 or target > n_src + 1:
            fail(f"target ({target}) outside 1..{n_src + 1} in {src}")
        if copy:
            left, right = src_lines[:target - 1], src_lines[target - 1:]
        else:
            if start <= target <= end + 1:
                fail(f"target line {target} sits inside source range "
                     f"{start}..{end}")
            if target < start:
                left = src_lines[:target - 1]
                right = src_lines[target - 1:start_idx] + src_lines[block_end_idx:]
            else:
                post = src_lines[:start_idx] + src_lines[block_end_idx:]
                cut = target - 1 - len(raw_block)
                left, right = post[:cut], post[cut:]
        if absorb:
            new_lines, off, blen = norm_splice(left, block, right)
            lo2, hi2 = off + 1, off + blen
        else:
            new_lines = left + block + right
            lo2, hi2 = len(left) + 1, len(left) + len(block)
        write(src, new_lines, opt["dry"])
        print(f"  {len(block)} lines, {n_src} -> {len(new_lines)} in {src.name}")
        print(f"PASS: {verb} {src}[{start}..{end}] -> {src}[{lo2}..{hi2}]"
              + (" (dry run)" if opt["dry"] else ""))
        return 0

    dst_lines = read_lines(dst)
    n_dst = len(dst_lines)
    if target < 1 or target > n_dst + 1:
        fail(f"target ({target}) outside 1..{n_dst + 1} in {dst}")
    if absorb:
        new_dst, off, blen = norm_splice(
            dst_lines[:target - 1], block, dst_lines[target - 1:])
        lo2, hi2 = off + 1, off + blen
    else:
        new_dst = dst_lines[:target - 1] + block + dst_lines[target - 1:]
        lo2, hi2 = target, target + len(block) - 1
    if not copy:
        write(src, src_lines[:start_idx] + src_lines[block_end_idx:], opt["dry"])
    write(dst, new_dst, opt["dry"])
    print(f"  {len(block)} lines, {dst.name} {n_dst} -> {len(new_dst)}")
    print(f"PASS: {verb} {src}[{start}..{end}] -> {dst}[{lo2}..{hi2}]"
          + (" (dry run)" if opt["dry"] else ""))
    return 0


def v_delete(args, opt) -> int:
    if len(args) != 1:
        fail(f"usage: {USAGE['delete']}")
    path, start, end = parse_target(args[0], opt["preamble"], removes=True)
    lines = read_lines(path)
    n = len(lines)
    end_idx = end
    if opt["absorb"] and end_idx < n and _is_blank(lines[end_idx]):
        end_idx += 1
    kept = lines[:start - 1] + lines[end_idx:]
    write(path, kept, opt["dry"])
    print(f"  removed {end_idx - start + 1} line(s)")
    print(f"PASS: deleted {path}[{start}..{end}] ({n} -> {len(kept)} lines)"
          + (" (dry run)" if opt["dry"] else ""))
    return 0


def v_emit(args, opt) -> int:
    if len(args) != 1:
        fail(f"usage: {USAGE['emit']}")
    path, start, end = parse_target(args[0], opt["preamble"])
    block = read_lines(path)[start - 1:end]
    sys.stdout.write("".join(block))
    # stdout is the block, verbatim, so that `emit ... > FILE` is a clean
    # copy; the verdict every run ends with goes to stderr instead.
    sys.stdout.flush()
    print(f"PASS: emitted {path}[{start}..{end}] ({len(block)} lines)",
          file=sys.stderr)
    return 0


def v_replace(args, opt) -> int:
    if len(args) != 2:
        fail(f"usage: {USAGE['replace']}")
    path, start, end = parse_target(args[0], opt["preamble"], removes=True)
    newpath = Path(args[1])
    new = read_lines(newpath)
    if new and not new[-1].endswith("\n"):
        new[-1] += "\n"
    lines = read_lines(path)
    out = lines[:start - 1] + new + lines[end:]
    write(path, out, opt["dry"])
    print(f"  replaced {end - start + 1} line(s) with {len(new)}")
    print(f"PASS: {path}[{start}..{end}] <- {newpath}"
          + (" (dry run)" if opt["dry"] else ""))
    return 0


def _regions(targets: list[str], opt) -> list[tuple[Path, int, int]]:
    """Each target's (path, lo, hi), with the `--except` entries cut out.

    An excluded entry inside a region splits it in two, so the result may
    hold more regions than there were targets.  A name that resolves in none
    of the target files is a refusal: a typo there would otherwise widen the
    edit silently, which is the opposite of what the option is for."""
    excl: list[str] = opt["except"]
    found: set[str] = set()
    out: list[tuple[Path, int, int]] = []
    for spec in targets:
        path, lo, hi = parse_target(spec, opt["preamble"])
        cuts = []
        if excl:
            names = {e.name for e in _entries(path)}
            for name in excl:
                if name in names:
                    found.add(name)
                    clo, chi = resolve_entry(path, name, opt["preamble"])
                    if chi >= lo and clo <= hi:
                        cuts.append((clo, chi))
        cur = lo
        for clo, chi in sorted(cuts):
            if clo > cur:
                out.append((path, cur, clo - 1))
            cur = max(cur, chi + 1)
        if cur <= hi:
            out.append((path, cur, hi))
    missing = [n for n in excl if n not in found]
    if missing:
        fail(f"--except names no entry in any target: {', '.join(missing)}")
    return out


def _check_expect(total: int, opt) -> None:
    """`--expect N`: the run must make exactly N substitutions.

    `sub` and `resub` already refuse zero; this refuses every other wrong
    count, and the over-match is the one that matters -- a pattern that also
    hits a sibling lemma reports success and edits it."""
    if opt["expect"] is not None and total != opt["expect"]:
        fail(f"{total} substitution(s), --expect {opt['expect']}; nothing written")


def v_sub(args, opt) -> int:
    if len(args) < 3:
        fail(f"usage: {USAGE['sub']}")
    old, new, targets = args[0], args[1], args[2:]
    if old == new:
        fail("OLD and NEW are identical")
    # Every target is rewritten in memory first: a run that matches nowhere
    # is a mistake (wrong name, wrong span, already renamed), and the report
    # is only honest if no file has been touched by the time it is printed.
    total = 0
    # One buffer per FILE, not per target.  Two targets may name two regions
    # of the same file, and re-reading it for each would make the last write
    # discard the others -- silently, since every target still reports its own
    # match count.  Substitution is line-preserving, so a span resolved
    # against the file on disk stays valid as the buffer is edited.
    bufs: dict[Path, list[str]] = {}
    order: list[Path] = []
    for path, lo, hi in _regions(targets, opt):
        if path not in bufs:
            bufs[path] = read_lines(path)
            order.append(path)
        lines = bufs[path]
        n = 0
        for i in range(lo - 1, hi):
            c = lines[i].count(old)
            if c:
                lines[i] = lines[i].replace(old, new)
                n += c
        total += n
        scope = "all" if (lo, hi) == (1, len(lines)) else f"{lo}..{hi}"
        print(f"  {path}[{scope}]: {n} substitution(s)")
    if total == 0:
        fail(f"{old!r} occurs nowhere in the {len(targets)} target(s); "
             "nothing written")
    _check_expect(total, opt)
    for path in order:
        write(path, bufs[path], opt["dry"])
    print(f"PASS: {old!r} -> {new!r}, {total} substitution(s) in "
          f"{len(targets)} target(s)" + (" (dry run)" if opt["dry"] else ""))
    return 0


def _arg_text(a: str) -> str:
    """`@FILE` reads the argument from FILE, trailing newline dropped.

    The escape hatch for a pattern or replacement carrying Isabelle symbols:
    the project shell is tcsh, which doubles the backslash in `\\<and>` on the
    way through, and the damage surfaces later as a proof error."""
    if a.startswith("@") and Path(a[1:]).is_file():
        return Path(a[1:]).read_text().rstrip("\n")
    return a


def v_resub(args, opt) -> int:
    """Python-regex substitution over each region's text as one string, so a
    match may span lines (`re.MULTILINE`; `\\s` crosses newlines).  NEW is a
    `re.sub` template: `\\1` and `\\g<name>` expand, and an escape that is not
    a letter (`\\<`) is kept, so Isabelle symbols survive.  Either argument may
    be `@FILE`.  The line count may change, so the regions of one file are
    resolved against the file on disk and applied bottom-up; overlapping
    regions are refused.  Zero matches across all targets is a refusal, as
    for `sub`."""
    if len(args) < 3:
        fail(f"usage: {USAGE['resub']}")
    pat_s, new, targets = _arg_text(args[0]), _arg_text(args[1]), args[2:]
    try:
        pat = re.compile(pat_s, re.MULTILINE)
    except re.error as e:
        fail(f"bad PATTERN: {e}")
    return _rewrite_regions(targets, opt,
                            lambda path, lo, text: (*pat.subn(new, text), ""),
                            "pattern")


def _rewrite_regions(targets: list[str], opt, fn, what: str) -> int:
    """Apply ``fn(path, lo, text) -> (out, n, note)`` to each region's text.

    The driver shared by `resub` and `reargs`.  The line count may change, so
    the regions of one file are resolved against the file on disk and applied
    bottom-up; overlapping regions are refused.  Nothing is written until
    every region is rewritten and the counts pass."""
    spans: dict[Path, list[tuple[int, int]]] = {}
    order: list[Path] = []
    for path, lo, hi in _regions(targets, opt):
        if path not in spans:
            spans[path] = []
            order.append(path)
        spans[path].append((lo, hi))
    total = 0
    bufs: dict[Path, list[str]] = {}
    for path in order:
        lines = read_lines(path)
        regs = sorted(spans[path], reverse=True)
        for (lo2, _), (_, hi1) in zip(regs, regs[1:]):
            if hi1 >= lo2:
                fail(f"{path}: overlapping regions")
        for lo, hi in regs:
            text = "".join(lines[lo - 1:hi])
            out, n, note = fn(path, lo, text)
            total += n
            scope = "all" if (lo, hi) == (1, len(lines)) else f"{lo}..{hi}"
            print(f"  {path}[{scope}]: {n} substitution(s)"
                  + (f"; {note}" if note else ""))
            lines = lines[:lo - 1] + out.splitlines(keepends=True) + lines[hi:]
        bufs[path] = lines
    if total == 0:
        fail(f"{what} matches nowhere in the {len(targets)} target(s); "
             "nothing written")
    _check_expect(total, opt)
    for path in order:
        write(path, bufs[path], opt["dry"])
    print(f"PASS: {total} substitution(s) in {len(targets)} target(s)"
          + (" (dry run)" if opt["dry"] else ""))
    return 0


# Argument syntax for `reargs`: a bracket group, or an atom made of identifier
# characters and Isabelle symbols.  `\<open>` / `\<close>` end an atom, so a
# prose mention `\<open>f\<close>` reads as a bare head and is left alone.
_BRACKETS = {"(": ")", "[": "]", "{": "}"}
_ATOM_CH = re.compile(r"[A-Za-z0-9_'.?]")
_SYMBOL = re.compile(r"\\<\^?[A-Za-z]+>")
_HOLE = re.compile(r"\$(\d+|\$)")


def _arg_at(s: str, i: int) -> tuple[str, int] | None:
    """The argument starting at or after ``i`` (whitespace skipped, newlines
    included), as ``(text, end)``, or None if what follows is no argument."""
    while i < len(s) and s[i] in " \t\n":
        i += 1
    if i >= len(s):
        return None
    if s[i] in _BRACKETS:
        stack: list[str] = []
        for j in range(i, len(s)):
            c = s[j]
            if c in _BRACKETS:
                stack.append(_BRACKETS[c])
            elif c in ")]}":
                if not stack or c != stack[-1]:
                    return None
                stack.pop()
                if not stack:
                    return s[i:j + 1], j + 1
        return None
    j = i
    while j < len(s):
        if _ATOM_CH.match(s, j):
            j += 1
            continue
        m = _SYMBOL.match(s, j)
        if m and m.group() not in ("\\<open>", "\\<close>"):
            j = m.end()
            continue
        break
    return (s[i:j], j) if j > i else None


def _prose_mask(path: Path, lo: int, text: str) -> list[tuple[int, int]]:
    """Character intervals of ``text`` (which starts at line ``lo`` of
    ``path``) lying in prose: `text` blocks, section headings and
    `\\<comment>`s, as `isabelle_query.api` reports them.  Empty for a file
    that is not a theory."""
    if path.suffix != ".thy":
        return []
    sec = _section(path)
    starts = [0]
    for line in text.splitlines(keepends=True):
        starts.append(starts[-1] + len(line))
    nlines = len(starts) - 1
    out: list[tuple[int, int]] = []

    def whole(a: int, b: int) -> None:
        for ln in range(max(a, lo), min(b, lo + nlines - 1) + 1):
            out.append((starts[ln - lo], starts[ln - lo + 1]))

    for a, b in list(sec.text_blocks) + list(sec.heading_spans):
        whole(a, b)
    for ln, cols in sec.nonisar_spans.items():
        if lo <= ln < lo + nlines:
            base = starts[ln - lo]
            out.extend((base + c0, base + c1) for c0, c1 in cols)
    return out


def v_reargs(args, opt) -> int:
    """Rewrite each application of a function by its arguments, where a regex
    cannot: an argument may be a bracketed term with brackets inside it.

    PATTERN is the head followed by `$1` .. `$n` in order; TEMPLATE places
    them, and `$$` is a literal `$`.  So `'bor_cost $1 $2'` with
    `'Suc (tape_len $1)'` turns `bor_cost (f x) y` into
    `Suc (tape_len (f x))`.  An argument is a bracket group (`()`, `[]`,
    `{}`, balanced) or an atom of identifier characters and Isabelle symbols,
    and may follow on the next line.  Arguments are copied verbatim, so the
    template supplies any brackets the new context needs; applications
    nested inside an argument are rewritten first.

    Left alone, and counted in the report: the head with no argument after
    it (a bare mention, `\\<open>f\\<close>`, a point-free use) and anything in
    prose (`text`, headings, `\\<comment>`).  A head with some but fewer than
    n arguments is a partial application the template cannot place, and is
    a refusal naming its line; cut it out with `--except` or a narrower
    region.  The head matches as a whole identifier, never as a prefix
    (`f_def`) and never after a `.` (a qualified name is left alone).
    Either argument may be `@FILE`."""
    if len(args) < 3:
        fail(f"usage: {USAGE['reargs']}")
    pat_s, tmpl, targets = _arg_text(args[0]), _arg_text(args[1]), args[2:]
    toks = pat_s.split()
    if not toks or toks[0].startswith("$"):
        fail("PATTERN must start with the function's name")
    head, holes = toks[0], toks[1:]
    if holes != [f"${k}" for k in range(1, len(holes) + 1)] or not holes:
        fail("PATTERN must be HEAD $1 $2 .. $n, in order, with n >= 1")
    n_args = len(holes)
    for m in _HOLE.finditer(tmpl):
        if m.group(1) != "$" and not 1 <= int(m.group(1)) <= n_args:
            fail(f"TEMPLATE uses {m.group()} but PATTERN binds $1..${n_args}")
    head_re = re.compile(r"(?<![A-Za-z0-9_'.])" + re.escape(head)
                         + r"(?![A-Za-z0-9_'])")

    def expand(argv: list[str]) -> str:
        return _HOLE.sub(lambda m: "$" if m.group(1) == "$"
                         else argv[int(m.group(1)) - 1], tmpl)

    def rewrite(s: str, prose, where) -> tuple[str, int, int, int]:
        out: list[str] = []
        i = done = bare = in_prose = 0
        while True:
            m = head_re.search(s, i)
            if not m:
                out.append(s[i:])
                return "".join(out), done, bare, in_prose
            if any(a <= m.start() < b for a, b in prose):
                in_prose += 1
                out.append(s[i:m.end()])
                i = m.end()
                continue
            got: list[str] = []
            j = m.end()
            for _ in range(n_args):
                r = _arg_at(s, j)
                if r is None:
                    break
                got.append(r[0])
                j = r[1]
            if not got:
                bare += 1
                out.append(s[i:m.end()])
                i = m.end()
                continue
            if len(got) < n_args:
                fail(f"{where(m.start())}: {head} applied to {len(got)} of "
                     f"{n_args} argument(s); nothing written")
            inner = []
            for a in got:
                a2, d2, _, _ = rewrite(a, [], lambda _o: where(m.start()))
                inner.append(a2)
                done += d2
            out.append(s[i:m.start()])
            out.append(expand(inner))
            done += 1
            i = j

    def fn(path: Path, lo: int, text: str):
        def where(off: int) -> str:
            return f"{path}:{lo + text.count(chr(10), 0, off)}"
        out, done, bare, in_prose = rewrite(text, _prose_mask(path, lo, text),
                                            where)
        notes = []
        if bare:
            notes.append(f"{bare} bare mention(s) left")
        if in_prose:
            notes.append(f"{in_prose} in prose left")
        return out, done, ", ".join(notes)

    return _rewrite_regions(targets, opt, fn, f"{head!r} applied")


def _split_ranges(text: str) -> list[tuple[int, int]]:
    out = []
    for part in text.split(","):
        m = SPAN_RE.match(part.strip())
        if not m:
            fail(f"bad range {part!r} in split spec, want A..B or A-B")
        out.append((int(m.group(1)), int(m.group(2))))
    return out


def v_split(args, opt) -> int:
    """Cut one theory into several.

    Every range indexes the ORIGINAL file: the source is read once, all
    ranges are sliced from that unmodified list, and the cut is a single
    filter pass -- so nothing is renumbered mid-run and range order cannot
    affect the result.  That is why there is no sort-descending dance here,
    unlike `move`, which inserts as well as deletes.  What the design does
    not rule out is checked: overlapping ranges FAIL, and lines claimed by
    no range are reported (they stay behind silently otherwise).  Every
    part is built before any is written, so a refusal in the last spec
    leaves no earlier part behind.
    """
    if len(args) < 2:
        fail(f"usage: {USAGE['split']}")
    src = Path(args[0])
    lines = read_lines(src)
    n = len(lines)
    owner: dict[int, str] = {}
    parts: list[tuple[Path, str, int, int]] = []

    for spec in args[1:]:
        try:
            name, imports, ranges = spec.split("|")
        except ValueError:
            fail(f"spec {spec!r} is not NAME|IMPORTS|RANGES")
        spans = _split_ranges(ranges)
        body: list[str] = []
        for lo, hi in spans:
            hi = min(hi, n)
            if lo < 1 or lo > hi:
                fail(f"{name}: bad range {lo}..{hi} (file has {n} lines)")
            body.extend(lines[lo - 1:hi])
            for i in range(lo, hi + 1):
                prior = owner.get(i)
                if prior is not None and prior != name:
                    fail(f"line {i} claimed by both {prior} and {name}; "
                         "ranges must not overlap")
                owner[i] = name

        while body and body[-1].strip() in ("", "end"):
            body.pop()

        imp = " ".join(f'"{i}"' if "." in i else i for i in imports.split(","))
        out = src.parent / f"{name}.thy"
        header = f"theory {name}\n  imports {imp}\nbegin\n\n"
        parts.append((out, header + "".join(body) + "\n\nend\n",
                      len(body), len(spans)))

    for out, text, n_body, n_spans in parts:
        if not opt["dry"]:
            out.write_text(text)
        print(f"  wrote {out} ({n_body} body lines from {n_spans} range(s))")

    gaps: list[tuple[int, int]] = []
    for i in range(1, n + 1):
        if i in owner:
            continue
        if gaps and gaps[-1][1] == i - 1:
            gaps[-1] = (gaps[-1][0], i)
        else:
            gaps.append((i, i))
    if gaps:
        spans_s = ", ".join(f"{lo}..{hi}" if lo != hi else str(lo)
                            for lo, hi in gaps)
        print(f"  NOTE: {sum(hi - lo + 1 for lo, hi in gaps)} lines in no "
              f"range stay in {src.name}: {spans_s}")

    if opt["cut"]:
        kept = [l for i, l in enumerate(lines, start=1) if i not in owner]
        while kept and kept[-1].strip() in ("", "end"):
            kept.pop()
        if not opt["dry"]:
            src.write_text("".join(kept) + "\n\nend\n")
        print(f"  cut {len(owner)} lines from {src}, {len(kept) + 2} remain")
    else:
        print(f"  NOTE: {src} unchanged; re-run with --cut to remove "
              f"the {len(owner)} extracted lines")
    print(f"PASS: split {src} into {len(args) - 1} theor"
          f"{'y' if len(args) == 2 else 'ies'}"
          + (" (dry run)" if opt["dry"] else ""))
    return 0


def _theory_parts(path: Path):
    """(header incl. `begin`, body, `end` line) for a .thy file."""
    lines = read_lines(path)
    try:
        begin_i = next(i for i, l in enumerate(lines) if l.strip() == "begin")
        end_i = max(i for i, l in enumerate(lines) if l.strip() == "end")
    except (StopIteration, ValueError):
        fail(f"{path} has no `begin`/`end` pair")
    return lines[:begin_i + 1], lines[begin_i + 1:end_i], lines[end_i]


def v_merge(args, opt) -> int:
    """Splice a linear chain of theory bodies into BASE, byte-exact.

    BASE keeps its own header and final `end`; each SRC has its header (up to
    and including `begin`) and its trailing `end` stripped and the body
    spliced in, in argument order, before BASE's `end`.  SRCs are NOT deleted
    and imports are NOT rewritten -- do that separately (git rm, re-point
    importers, ROOT).  The build is the correctness oracle.
    """
    if len(args) < 2:
        fail(f"usage: {USAGE['merge']}")
    base = Path(args[0])
    b_header, b_body, b_end = _theory_parts(base)
    merged = list(b_header) + list(b_body)
    for s in args[1:]:
        _, s_body, _ = _theory_parts(Path(s))
        while merged and _is_blank(merged[-1]):
            merged.pop()
        merged.append("\n")
        b = list(s_body)
        while b and _is_blank(b[0]):
            b.pop(0)
        while b and _is_blank(b[-1]):
            b.pop()
        merged.extend(b)
        print(f"  spliced {len(b)} body lines from {s}")
    while merged and _is_blank(merged[-1]):
        merged.pop()
    merged.append("\n")
    merged.append(b_end if b_end.endswith("\n") else b_end + "\n")
    write(base, merged, opt["dry"])
    print(f"PASS: merged {len(args) - 1} theor"
          f"{'y' if len(args) == 2 else 'ies'} into {base} "
          f"({len(merged)} lines)" + (" (dry run)" if opt["dry"] else ""))
    return 0


VERBS = {
    "move": lambda a, o: v_move(a, o, copy=False),
    "copy": lambda a, o: v_move(a, o, copy=True),
    "delete": v_delete,
    "emit": v_emit,
    "replace": v_replace,
    "sub": v_sub,
    "resub": v_resub,
    "reargs": v_reargs,
    "split": v_split,
    "merge": v_merge,
}

# The implementation behind each verb, for `--help` to read a docstring off.
# `move`/`copy` share one, so `VERBS` cannot serve: its values are lambdas.
VERB_FN = {
    "move": v_move, "copy": v_move, "delete": v_delete, "emit": v_emit,
    "replace": v_replace, "sub": v_sub, "resub": v_resub, "reargs": v_reargs,
    "split": v_split, "merge": v_merge,
}


def main(argv: list[str] | None = None) -> int:
    """The `block` console script.  ``argv`` excludes the program name."""
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        print(__doc__.rstrip())
        return 0
    if args[0] in ("-V", "--version"):
        from . import __version__
        print(f"isabelle-block {__version__}")
        return 0

    opt = {"absorb": True, "dry": False, "preamble": "auto",
           "cut": False, "expect": None, "except": []}
    choices = [f for f in ("--with-preamble", "--no-preamble") if f in args]
    if len(choices) == 2:
        fail("--with-preamble and --no-preamble contradict each other")
    if choices:
        opt["preamble"] = "with" if choices[0] == "--with-preamble" else "without"
        args = [a for a in args if a != choices[0]]
    while "--expect" in args:
        i = args.index("--expect")
        if i + 1 >= len(args) or not args[i + 1].isdigit():
            fail("--expect needs a count N")
        opt["expect"] = int(args[i + 1])
        del args[i:i + 2]
    while "--except" in args:
        i = args.index("--except")
        if i + 1 >= len(args):
            fail("--except needs an entry NAME")
        opt["except"].append(args[i + 1])
        del args[i:i + 2]
    global _ROOT
    _ROOT = None
    _SECTIONS.clear()
    while "--root" in args:
        i = args.index("--root")
        if i + 1 >= len(args) or not Path(args[i + 1]).is_dir():
            fail("--root needs a session root DIR")
        _ROOT = Path(args[i + 1])
        del args[i:i + 2]
    for flag, key in (("--no-trailing-blank", "absorb"),
                      ("--dry-run", "dry"),
                      ("--cut", "cut")):
        while flag in args:
            args.remove(flag)
            opt[key] = (flag != "--no-trailing-blank")

    verb = args[0]
    if verb not in VERBS:
        fail(f"unknown verb {verb!r} (known: {', '.join(VERBS)}); "
             "block --help for the grammar")
    rest = args[1:]
    # `block sub --help` used to be read as OLD="--help" and then refused
    # for the argument count -- a usage line, but reached through an error and
    # with the wrong exit status.  Asking a verb for its own grammar is not a
    # mistake, so it answers.
    if any(a in ("-h", "--help") for a in rest):
        print(f"usage: {USAGE[verb]}")
        doc = (VERB_FN[verb].__doc__ or "").strip()
        if doc:
            print()
            print(doc)
        print("\nblock --help for the addressing grammar and modifiers.")
        return 0
    # Every run ends with PASS: or FAIL:, a crash included.  The traceback
    # still goes to stderr for whoever debugs it.  Verbs write only after
    # every check, so an exception before then has written nothing; one
    # raised while writing may not have, and the message does not claim so.
    try:
        return VERBS[verb](rest, opt)
    except Exception as e:  # not SystemExit: `fail` has already reported
        import traceback
        traceback.print_exc()
        sys.stderr.flush()
        print(f"FAIL: {verb}: unexpected {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
