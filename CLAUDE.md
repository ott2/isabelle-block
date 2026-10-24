# CLAUDE.md

Guidance for Claude Code working in this repository.  This file says what the
package is, how it is shaped, and which rules hold.  It is not a log.  Work in
flight is in `tasks.md`, and each feature request has its own document under
`docs/fr/`.

## What this repository is

`isabelle-block` provides the `block` command.  It makes mechanical edits to a
region of an Isabelle theory file (also markdown, for the line-span verbs),
and the region is named either by a line span or by an entry name.

It began in the NDTHT formalisation as `bin/block.py`.  On 2026-09-08 that
script replaced six siblings, each of which did one slice of the job
(`move-block.py`, `replace-range.py`, `sub-range.sh`, `rename-ident.sh`,
`split-theory.py`, `merge-into-base.py`).  It has grown through use since then
(`resub` and `reargs`, `--expect` and `--except`).  It was extracted on
2026-10-15 so it could be developed and released like its siblings,
`isabelle-query`, `isabelle-layout` and `isabelle-watchdog`.

The name is settled (Andras, 2026-10-21): the package is `isabelle-block` and
the command is `block`.  It is tied to Isabelle on purpose.  The generic
layer, spans and substitution, is thin, and `docs/related-tools.md` shows
existing tools doing it well.  The value is in the Isabelle layer.

The next work is three verbs, all of which NDTHT's history shows recurring:

- `rename`;
- a `delete` that checks for callers first;
- a `move` that checks import visibility.

Each currently survives as a one-off script in NDTHT.  Start with:

- `tasks.md`;
- `docs/fr/`;
- `docs/usecases.md` — what happened in NDTHT, and what each verb must therefore
  handle;
- `docs/background.md` — the NDTHT scripts and lessons the verbs inherit.

## Shape

At present everything lives in `src/isabelle_block/cli.py`, one module ported
almost verbatim from `bin/block.py`.  Splitting it is `[module-split]` in
`tasks.md`; do that when `rename` lands, not before.  These are its layers:

- **Addressing**: `parse_target`, `parse_dest`, `resolve_entry` and
  `_section`.
  - A target is `FILE:REGION`, one token.  REGION is `A..B`, `A-B`, `N`, an
    entry `NAME`, or `all`.
  - Spans are the grammar `query` prints, so its output pastes straight in.
    Its THEORY part does not yet: FILE must be a path.  A theory name or
    label waits on query's resolver (U11, `[locus-targets]`); do not
    re-derive query's label grammar here (Andras, 2026-10-24).
  - `delete` takes several targets (#3).  They are resolved against the
    files on disk and removed as one line set per file, so order does not
    matter.  An identical region given twice is deleted once, and a
    partial overlap is refused.
  - A NAME resolves to the entry's **`Entry.cut_span`**, the span
    `isabelle_query` documents as the one a tool writes through.  It runs
    from the doc preamble to the end of the proof, and never reaches the next
    entry's doc block.  It is `None` when two entries share a line, and that
    is a refusal.  `block` does not compute spans itself: 0.1.0's local clip
    reached into the next doc block wherever `body_end_line` did.
  - `_section` parses each file once per run, with its **session's keyword
    table**: `parse_theory(..., root=)`, the root coming from `--root` or
    `isabelle_layout.default_t_dir`, as in `query`.
  - **A doc block under a heading needs a choice** (Andras, 2026-10-23).
    When `Entry.preamble_follows_heading` holds, the `text` may be the
    section's introduction.  A verb that removes the span (`delete`,
    `move`, `replace`) then refuses until given `--with-preamble` or
    `--no-preamble`.  `emit` and `copy` remove nothing and keep it.  The
    rule fires on 8% of NDTHT's entries.
  - **So does a heading left empty.**  `delete` of a section's only entry
    refuses until given `--keep-heading` or `--with-heading` (the whole
    section goes).  It fires on 2.7% of NDTHT's entries.  Section extents
    and heading ranks come from `TheorySection.outline` and `heading_spans`
    (`_headings`, `_section_of`).
  - **The landing rule.**  `move`/`copy … before NAME` lands above NAME's
    heading when the block starts with a heading of the same or higher
    rank, and under it otherwise.  Landing under it, when NAME's doc block
    is flagged, refuses until given `--land-above-text` or
    `--land-below-text` (#1).  This pair is separate from the preamble
    pair, because one `move` may raise both questions, about two different
    texts.
  - **Choices are collected, not failed one by one** (#1): `_ask` records
    one, and `_settle` refuses with all of them.  Each verb settles after
    addressing, and `write` settles as a backstop, so an open choice never
    reaches the disk.
- **Splicing**: `norm_splice`.  This is the blank-seam healing, which leaves
  exactly one blank line between blocks.  It is the code that looks harmless to
  adjust, and its tests assert properties rather than golden bytes.
- **Verbs**: `v_*`.  `USAGE`, `VERBS` and `VERB_FN` are the tables `--help`
  reads from.  A new verb goes in all three.
- **Region rewriting**: `_regions` (applies `--except`), `_rewrite_regions` (the
  bottom-up multi-region driver for `resub` and `reargs`), and `_prose_mask`
  (the `text`, heading and `\<comment>` intervals that `reargs` skips).

## Invariants: the tool's contract

- **A refusal writes nothing.**  Every verb computes all its edits in memory
  across all files, checks the counts, and only then writes.  `sub` buffers
  per *file*, not per target, because two targets may be regions of one file;
  buffering per target once let the last write discard the others while every
  target reported success.
- **Every run ends with `PASS:` or `FAIL:`**, and the exit status agrees.
- **Over-matching is the dangerous failure**, not zero matches.  `--expect N`
  exists for this reason, and a new rewriting verb should support it.
- **Prose is not code.**  A substitution that also rewrites `text` blocks and
  comments does damage that is *grammatical*, so no build or lint catches it.
  NDTHT's `insights/289` covers word-shaped identifiers such as `back`, `stop`
  and `head`.  Prose intervals come from `isabelle_query.api`
  (`TheorySection.text_blocks`, `heading_spans`, `nonisar_spans`); do not
  re-derive them with regexes.
- **Name addressing parses with the session's keyword table.**  A theory may
  use a command that a *sibling's* `keywords` declares.  Parsed alone, that
  command is not recognised, and the entry above it swallows it.  0.1.0
  refused the declaring theory instead, which parses fine alone, and missed
  the theory that uses the command.  On the AFP, 111 spans were wrong that
  way.  A file in no named session gets a NOTE on stderr.
- **Literal means literal.**  `sub` is `str.replace` on both sides, and a
  newline in OLD is literal too (#2): a multi-line OLD goes through
  `_rewrite_regions`, since it changes the line count.  The perl
  predecessors turned `\<lambda>` into `<lambda>`.  An `@FILE` argument reads a
  pattern or replacement from a file, which is the escape hatch for Isabelle
  symbols: the user's shell is tcsh, and it doubles backslashes on the way in.
- **Not concurrency-safe.**  The tool reads, then writes.  Never run it in the
  same parallel batch as another edit to the same file.

## Dependencies

- **`isabelle-query`** (`>=1.1.1`).  1.1.0's `[early-end]` fix stops an entry
  ending at a heading inside its own proof.  1.1.1 (#29) makes a mid-line
  declaration an entry, so no `cut_span` holds a second lemma.  Import only from
  `isabelle_query.api`: `parse_theory`, `parse_root`, `Entry`,
  `TheorySection`.  Never import from `isabelle_query.parsing` or `.cli`,
  which move without notice.  The fields used today:
  - `Entry.name`, `thy_line`, `cut_span`, `runs_into_next`, `preamble` and
    `preamble_follows_heading`;
  - `TheorySection.entries`, `session`, `outline`, `text_blocks`,
    `heading_spans` and `nonisar_spans`.
- **`isabelle-layout`** (`>=0.2.2`): `default_t_dir`, the session-root
  discovery `query` uses.  The visibility-checked `move` will also need a
  theory's import closure and session membership from it (see
  `docs/fr/move.md`).
- **A gap in either package is reported upstream, not worked around.**  Draft
  a GitHub issue in `upstream/` for Andras to check and post.
- **Borrow before building.**  `docs/related-tools.md` records which external
  tools overlap with `block` (`ed`, `sd`, `fastmod`, comby, `isabelle
  update`) and how `block` differs.
  - Check it before writing a new mechanism.
  - Add any new tool you find.

## Commands

```sh
python3 -m venv .venv
.venv/bin/pip install '.[test]'      # NOT -e: test what a user installs
.venv/bin/pytest
.venv/bin/pytest -m corpus           # read-only, NDTHT t/ and the AFP: ~1 min
.venv/bin/block --help
```

Reinstall after editing `src/`, as the sibling packages do.  The machine has
Python 3.14 (the `.venv`) and 3.15, so `requires-python >= 3.9` is checked
only statically:
keep `from __future__ import annotations`, and use no `match` statement and no
post-3.9 stdlib call.

**Trying a verb on a real tree.**  NDTHT's theory tree is at
`~/projects/ndtht/t/`, about 400 theories.  The AFP is at `~/repos/afp/thys`,
parked at Isabelle2025-2; never `hg update` it.  Both are **read-only from
here**:

- use `--dry-run`;
- or `emit`;
- or copy a theory into `scratch/` first.

Never write into either tree from this repository.

## The consumer

NDTHT is the first user.  Its main checkout is `~/projects/ndtht`, with a venv
at `~/projects/ndtht/venv`.  Claude works in a separate worktree at
`~/projects/claudecode/ndtht`, on `stac/*` branches.  The package is on
PyPI since 0.1.2.  Until NDTHT's switch-over, NDTHT installs it from the
sibling directory, to try unreleased changes:

```sh
~/projects/ndtht/venv/bin/pip install ~/projects/isabelle-block
```

Its `bin/block.py` is frozen meanwhile.  The NDTHT-side edits for the
switch-over are listed in `tasks.md` `[ndtht-switchover]`.

## Working boundaries

- **Edits stay in this repository.**  Do not edit NDTHT, `isabelle-query` or
  `isabelle-layout` from here.
- **Nothing outward-facing without a request from Andras.**  That covers:
  - no `git push` (a release request covers the release's pushes; see
    **Releasing**);
  - no GitHub repo creation;
  - no PyPI upload, ever: that step is Andras's;
  - no issue or comment.

  A GitHub post is signed: `gh` runs as Andras's account.
- **Releasing** follows `docs/publishing.md`:
  - drop `.dev0`;
  - the release notes are the version-bump commit's message, describing the
    significant changes since the last release, as for the sister projects;
  - build before tagging;
  - a tag push publishes via `.github/workflows/release.yml`;
  - PyPI is a manual `twine upload -r pypi-isabelle-block`, naming this
    version's files.

  When Andras asks for a release, Claude does all of it through the tag
  push and the GitHub Release.  The PyPI upload is Andras's alone.  Keep the
  workflow
  mechanism-identical to the siblings' workflows, so that only the Release
  title differs.  The repository is `github.com/ott2/isabelle-block`
  (`origin`).
- **Never rewrite history**: no `--amend`, `reset` or force-push.  Add a
  commit, or a version, instead.

## Shell and commit conventions

The session shell is tcsh.  The project memory has the details; in brief:

- no `cd`;
- no bash `for` loops;
- no `$(...)`;
- no `\<…>` literals in shell arguments (use the Edit tool or `@FILE`);
- temporary files go under `scratch/` (gitignored), never `/tmp`.

For commits:

- write the message to `.gitcommit.txt` with the Write tool, then
  `git commit -F .gitcommit.txt`;
- stage by name, check `git status --short`, and only then commit, as three
  separate calls.

Trailer:
`Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`
