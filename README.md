# isabelle-block

**Mechanical edits to regions of Isabelle theory files, where a region is
named by a line span or by the name of a lemma.**

```sh
block move Foo.thy:helper_lemma before first_user     # hoist a helper
block delete Foo.thy:dead_lemma
block move Foo.thy:1669..2657 before Bar.thy:46       # between theories
block reargs 'cost $1 $2' 'Suc (len $1)' Foo.thy --expect 14
```

Name addressing is the reason to use it.  `Foo.thy:helper_lemma` resolves,
through [`isabelle-query`](https://github.com/ott2/isabelle-query)'s parser,
to the lemma's span, from its doc block through the last line of its proof.
So an edit needs no line arithmetic, and it cannot go stale between looking
a lemma up and editing it.

## Install

```sh
python3 -m pip install isabelle-block
```

This puts `block` on your `PATH`.  Needs Python 3.9 or later; depends on
`isabelle-query`.  It needs no Isabelle process.

## Verbs

| verb | does |
|---|---|
| `move SRC:REGION before DEST` | relocate a block, within a file or between files |
| `copy SRC:REGION before DEST` | place a copy and keep the source |
| `delete FILE:REGION` | excise a block |
| `emit FILE:REGION` | print a block verbatim |
| `replace FILE:REGION NEWFILE` | swap a block for a file's contents |
| `sub OLD NEW FILE[:REGION]...` | literal substring substitution |
| `resub PAT NEW FILE[:REGION]...` | regex substitution; a match may span lines |
| `reargs 'F $1 $2' TMPL FILE[:REGION]...` | rewrite `F`'s applications by their (bracket-aware) arguments; skips prose |
| `split SRC 'NAME\|IMPORTS\|RANGES'... [--cut]` | cut a theory into several |
| `merge BASE.thy SRC.thy...` | splice theory bodies into one |

A **REGION** is `A..B` (or `A-B`), a single line `N`, an entry `NAME`, or
`all`, which is also what a bare `FILE` means.  A **DEST** is `LINE`, `NAME`,
`FILE:LINE` or `FILE:NAME`; the block lands immediately before it, preamble
included.

**Modifiers:**

- `--dry-run` reports the edit and writes nothing.
- `--expect N` makes `sub`, `resub` and `reargs` refuse unless exactly N
  substitutions are made.
- `--except NAME` leaves an entry out of every region.
- `--no-preamble` starts a resolved span at the entry, not its doc block.
- `--no-trailing-blank` cuts verbatim, without blank-line healing.

`block --help` gives the full grammar, and `block VERB --help` gives one
verb's.

Every run ends with an explicit `PASS:` or `FAIL:` line, and the exit status
agrees.  `emit` prints its `PASS:` on stderr, so `block emit … > FILE` is a
clean copy.  A refusal writes nothing.

## Related tools

Editing by line span and plain substitution are what `ed`, `sed`, `sd` and
`fastmod` already do.  [comby](https://comby.dev) does bracket-aware
rewriting much as `reargs` does.  `block` is worth installing if your edits
need what those tools cannot see:

- lemma names as addresses;
- the difference between Isar code and prose (`text`, headings,
  `\<comment>`);
- edits at theory level.

`docs/related-tools.md` compares them in detail.

## Status

This is alpha, extracted from the NDTHT formalisation's `bin/block.py`, where it
did the project's mechanical theory surgery.  The planned verbs (`rename`, a
caller-checked `delete` and an import-checked `move`) are in `tasks.md`.

## Development

```sh
python3 -m venv .venv
.venv/bin/pip install -e '.[test]'
.venv/bin/pytest
```
