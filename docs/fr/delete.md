# FR: caller-checked `block delete NAME`, and dedup

**Status:** proposed (2026-10-15).  Tag: `[fr-safe-delete]`.

## Problem

`block delete FILE:NAME` removes an entry without asking whether anything
uses it.  NDTHT's history (`../usecases.md` §4 and §5) has 50 or so prune
commits and about 30 dedup or wrapper removals.  Its tooling grew alongside:

- `prune-entries.py`, a loop over `block.py delete`;
- `prune-rounds.py` with `unused_lib.py` and `classify-unused.py`, which prune
  by baseline rounds;
- per-name `query callers -r` subprocesses.  290 of them took about ten
  minutes.

These are the failures it recorded:

- **Zero proof-body callers did not mean unused.**  Prunes deleted:
  - definitions used only in *statements*;
  - `[simp]` rules, after the tool read attributes from the preamble line
    instead of the header;
  - names cited in prose antiquotations, which are build dependencies
    (`insights/201`).
- **`delete NAME` took a section's introductory `text` as the lemma's
  preamble.**  This happened in three separate sessions (2026-10-02, 10-11 and
  10-14), and each time the text had to be restored by hand.
  `Entry.preamble` is "a text block within ~3 blank lines above", which cannot
  tell a doc block from a section introduction.
- **Duplicate names across theories were silent.**  A child re-declared a
  parent's lemma with a stronger statement, so one name meant two theorems,
  and everything still built.

## Requirements

These are `../usecases.md` §6.2, SD1–SD11.  The defining ones:

- **SD1**: refuse while the entry has callers outside the deletion set.
  Several NAMEs delete as a set, and callers inside the set do not count.
  `--force` overrides.
- **SD2**: callers are counted in four classes, reported separately:
  1. proof-body citations;
  2. statement uses of constants and types;
  3. prose antiquotations;
  4. implicit uses (`[simp]`, `[intro]` or `[elim]` on the header,
     `declare`, `lemmas` bundles), which are only "possibly used".

  For a definition, also query `NAME_def`; `query callers` does not count it.
- **SD4**: read attributes from the header line.
- **SD5**: refuse an ambiguous name unless it is qualified (`Theory.name`).
- **SD7**: show the span in a dry run.  Never cross into the next entry's doc
  block.  Flag a heading left with no entries beneath it.
- **SD6**: cascade mode with a baseline, as a later phase.
- **SD8**: dedup, `DUP → CANON`.  Rename every site except DUP's
  definition, then delete DUP.  Before that:
  - check that CANON is visible at every site;
  - compare the two statements;
  - flag sites that instantiate by variable name (`of`, `where`) or count
    `OF` arguments.

## Proposed interface (draft)

```
block delete FILE:NAME [FILE:NAME...]        # caller-checked; a set
block delete FILE:A..B                       # spans: unchecked, as today
block dedup DUP=CANON ROOT_DIR               # later phase
```

Options:

- `--force` deletes despite callers, and lists them.
- `--root DIR` sets the project root for the caller query.  It defaults to the
  `.isabelle-query` marker, discovered as `query` does.
- `--with-preamble` / `--no-preamble` choose explicitly when the preamble is
  ambiguous (see the preamble rule below).
- `--cascade` deletes in rounds (SD6, later).

## The preamble rule (fixes the three-session bug)

When the resolved preamble directly follows a section heading, **refuse**
and ask for `--with-preamble` or `--no-preamble`.  Do the same when deleting
the entry would leave a heading with no entries.

The fact comes from upstream: isabelle-query 1.1.1 (#28, U7) provides
`Entry.preamble_follows_heading`.  The source cannot say which of the two a
`text` under a heading is, so the refusal, an explicit choice, is the rule
itself and not a stopgap.

The same rule fixes `move … before NAME`, which lands *under* a heading
directly above NAME.  See `move.md`.

## Phasing

1. **Phase 1**: switch addressing to `Entry.cut_span`, and add the preamble
   rule.  Both help today's `delete` and `move` before any caller check
   exists.  The switch is done (2026-10-23, with the session keyword table).
   The preamble rule is done (2026-10-23/24).  `--with-preamble` and
   `--no-preamble` choose, using `preamble_follows_heading` (isabelle-query
   1.1.1).  For a section's only entry, `--keep-heading` and
   `--with-heading` choose whether the bare heading stays or the whole
   section goes.  A heading with a sub-heading under it is not empty.
2. **Phase 2**: the caller check over a set of names, done in one batch:
   - classes 1 and 2 from `query callers -f tsv`, one subprocess for all
     names (see D3);
   - `NAME_def` queried alongside;
   - class 3 by scanning prose antiquotations;
   - class 4 by reading attributes off the header and scanning `declare` and
     `lemmas`.

   This retires `prune-entries.py`.
3. **Phase 3**: cascade with a baseline and a keep-list (retires
   `prune-rounds.py`).
4. **Phase 4**: `dedup`, built on `rename` phase 1 plus phase 2 here.

## Decisions for Andras (recommendation first)

- **D1.**  Should a caller check be the default for a NAME target?  **Yes.**
  A line span stays unchecked, since spans are for surgery the user has
  already reasoned about.
- **D2.**  Should implicit uses (`[simp]` and the like) refuse or warn?
  **Refuse**, overridable with `--force`.  The episodes where they were
  deleted cost more than a re-run with `--force` does.
- **D3.**  Where do callers come from?  **Settled (Andras, 2026-10-15): the
  `query` CLI, `query callers -f tsv NAME...`**, batched into one call per
  run, which builds the graph once and costs seconds.
  - Importing the private `isabelle_query.graph._build_call_graph` is ruled
    out by CLAUDE.md.
  - A public library API (U1) is **not** requested up front.  The CLI's tsv
    is already a versioned contract, and `isabelle-query` adds a public name
    only when a consumer has shown it needs one.
  - U1 becomes worth filing only if building this verb or `move` hits a
    concrete limit of the CLI, and the request then cites it.  Examples: the
    same parse being needed for callers, closure and name index at once, so
    that separate subprocesses re-parse the project; or a field the tsv
    lacks, beyond U8.
- **D4.**  How do keep-lists work?  **A config file** (`.isabelle-block.toml`
  or a section of the `.isabelle-query` marker), not a flag retyped on every
  call.

## Dependencies and upstream asks (`../background.md` §2.5)

- **U1**: a public callers API.  Only if the CLI proves insufficient (D3).
- **U4**: prose antiquotations as an opt-in caller class.
- **U5**: implicit-use evidence (attributes parsed off the header).
- **U7**: preamble attribution versus section introductions.
- **U8**: `<toplevel>` rows of `callers -f tsv` lack theory and session.

## Test plan

Fixtures:

- a definition used only in a statement;
- a `[simp]` lemma with no citations;
- a `\<^const>` mention in a `text` block;
- a section intro directly above the first lemma;
- a set of two lemmas that cite only each other;
- the same name declared in two theories.

Then a corpus dry run: `query unused` on NDTHT's `t/`, then `block delete
--dry-run` for each result.  Every refusal should be explained by one of the
four classes.
