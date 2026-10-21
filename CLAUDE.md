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

- **Addressing**: `parse_target`, `parse_dest` and `resolve_entry`.
  - A target is `FILE:REGION`, one token.  REGION is `A..B`, `A-B`, `N`, an
    entry `NAME`, or `all`.
  - Spans are the grammar `query` prints, so its output pastes straight in.
  - A NAME resolves through `isabelle_query.api.parse_theory`.  The span starts
    at the entry's preamble and ends at the end of its proof.  It is **clipped
    below the next entry's preamble**, because writing through an unclipped
    span eats the next lemma's doc block.
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
- **Name addressing refuses a theory that declares `keywords`.**
  `parse_theory` sees only that file's header, so a custom command declared
  by a sibling theory would parse wrongly.  The tool checks this rather than
  assuming it.
- **Literal means literal.**  `sub` is `str.replace` on both sides.  The perl
  predecessors turned `\<lambda>` into `<lambda>`.  An `@FILE` argument reads a
  pattern or replacement from a file, which is the escape hatch for Isabelle
  symbols: the user's shell is tcsh, and it doubles backslashes on the way in.
- **Not concurrency-safe.**  The tool reads, then writes.  Never run it in the
  same parallel batch as another edit to the same file.

## Dependencies

- **`isabelle-query`** (`>=0.9.7`).  Import only from `isabelle_query.api`:
  `parse_theory`, `parse_root`, `Entry`, `TheorySection`.  Never import from
  `isabelle_query.parsing` or `.cli`, which move without notice.  The fields
  used today:
  - `Entry.name`, `thy_line`, `thy_end`, `preamble` and `body_end_line`;
  - `TheorySection.entries`, `text_blocks`, `heading_spans` and
    `nonisar_spans`.
- **`isabelle-layout`**: not yet a direct dependency.  The visibility-checked
  `move` needs a theory's import closure and session membership, and that is
  this package's job (see `docs/fr/move.md`).
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
.venv/bin/block --help
```

Reinstall after editing `src/`, as the sibling packages do.  The only machine
here has Python 3.14.  `requires-python >= 3.9` is checked only statically:
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
`~/projects/claudecode/ndtht`, on `stac/*` branches.  Until the first PyPI
release, NDTHT installs this package from the sibling directory:

```sh
~/projects/ndtht/venv/bin/pip install ~/projects/isabelle-block
```

Its `bin/block.py` is frozen meanwhile.  The NDTHT-side edits for the
switch-over are listed in `tasks.md` `[ndtht-switchover]`.

## Working boundaries

- **Edits stay in this repository.**  Do not edit NDTHT, `isabelle-query` or
  `isabelle-layout` from here.
- **Nothing outward-facing without a request from Andras.**  That covers:
  - no `git push`;
  - no GitHub repo creation;
  - no PyPI upload;
  - no issue or comment.

  A GitHub post is signed: `gh` runs as Andras's account.
- **Releasing** follows `isabelle-layout`'s runbook
  (`~/projects/isabelle-layout/docs/publishing.md`):
  - drop `.dev0`;
  - the release notes are the version-bump commit's message;
  - a tag push publishes via `.github/workflows/release.yml`;
  - PyPI is a manual `twine upload`.

  Copy the workflow from there at the first release.
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
