# tasks.md — isabelle-block

This file lists work still to do; remove an item when it is done (the commit
log records completions).  Items are referenced by their `[tag]`, and a tag
is never reused.

Background for a cold start:

- `CLAUDE.md`: what the package is and the rules that hold.
- `docs/usecases.md`: NDTHT's history of renames, moves, dedups and prunes,
  with requirement IDs RN, SD and VM.
- `docs/background.md`: the prior scripts, the `isabelle-query` and
  `isabelle-layout` surfaces, the knowledge-base lessons, and the NDTHT
  switch-over edit list.
- `docs/prior-art/`: a snapshot of the scripts and lessons themselves.
- `docs/related-tools.md`: the external tools that overlap with `block`, and
  how it differs from each.

## Suggested order

1. `[fr-rename]` phase 1.
2. `[fr-safe-delete]` phase 2.
3. `[fr-checked-move]` phase 1.

Draft `[upstream-asks]` alongside the work as each gap is hit.

## Groundwork

- [ ] `[corpus-tests]` **Read-only tests against real trees**, under a pytest
  marker `corpus` and skipped when the tree is absent:
  - NDTHT `~/projects/ndtht/t/`;
  - the AFP `~/repos/afp/thys`.

  Checks:
  - ~~every entry name resolves, or is refused for a stated reason;~~
  - ~~no resolved span overreaches into the next entry's doc block;~~
  - `emit` of every span concatenates back to the file.

  The first two are `tests/test_corpus.py` (2026-10-23).  They cover NDTHT's
  `t/` and the 29 AFP entries that declare `keywords`, about a minute in
  all.  Breaking `resolve_entry` back to 0.1.0's clip fails them on the four
  AFP overreaches.  Still open: the concatenation check, and whether the
  whole AFP is worth a slower opt-in run.

  Never write into either tree.
- [ ] `[module-split]` **Split `cli.py`** into addressing, splicing, verbs and
  the CLI when `rename` lands, not before.  `USAGE`, `VERBS` and `VERB_FN`
  stay one table each.

## Feature requests

Each FR document carries its requirements, phasing, open decisions (with a
recommendation for each) and a test plan.

- [ ] `[fr-rename]` **`block rename`**: a whole-identifier, prose-aware rename
  with a derived-name family, a collision check and a theory mode.  See
  `docs/fr/rename.md`.
  - It retires NDTHT's `rename-thy-names.py`, `token-rename.py` and
    `rename-theories.py`.
- [ ] `[fr-safe-delete]` **A caller-checked `block delete NAME...`**, then
  `dedup`.  See `docs/fr/delete.md`.
  - It retires `prune-entries.py`, and later `prune-rounds.py`.
- [ ] `[fr-checked-move]` **A visibility-checked `block move`.**  See
  `docs/fr/move.md`.
  - It retires `hoist-scan.py`.
- [ ] `[fr-resub-cover]` **`resub --cover MARKER_RE`: check a fold's
  coverage before applying it.**  Folding a repeated multi-line term into a
  definition with `resub` rewrites the canonical spelling only.  A variant —
  `?T` for `T`, a reordered sum, a term split across a proof step — is left
  alone, and the build is the first to say so.  NDTHT `54beedd6` lost a build
  to eight `?T` spellings that way.
  - With `--cover`, report every MARKER_RE match lying outside all PATTERN
    matches as `FILE:LINE: text`, then `PASS:`/`FAIL:` with the counts, and
    exit non-zero on FAIL.  The default is a dry run; `--cover --apply`
    refuses to write on FAIL.
  - PATTERN, REGION and `@FILE` resolve exactly as for a normal `resub`, so
    the check runs on the very pattern that will be applied.  That shared
    resolution is why this is an option rather than a separate verb.
  - Prior art: `docs/prior-art/scripts/block-coverage.py` (66 lines, any
    files, no REGION).
  - Tests: a canonical-only file passes; a `?T` variant fails and is named
    with its line; a marker inside a match on a later line counts as covered.
- [ ] `[resub-entry-bound]` **A lazy `[\s\S]*?` can cross entries.**  In
  NDTHT (2026-10-17) a `resub` over a whole file, `proof -\n  from step
  obtain …[\s\S]*?by (rule ae_delta_ss(\d)_only…)…qed`, began its first
  match at an *earlier* lemma with the same opening and deleted 418 lines,
  with the expected count of 8.  Naming each entry as a REGION fixed it.
  Offer `--within-entry`: reject (or report) a match that crosses an entry
  boundary, so a whole-file `resub` is safe by default for proof rewrites.
  Test: two lemmas with a shared prefix, the pattern matching only the
  second's body.
- [ ] `[resub-template-newline]` **`@FILE` drops the template's trailing
  newline.**  `resub`'s `@FILE` strips the file's final newline from the NEW
  template, so a template ending in a whole line joins onto the next source
  line.  It hit NDTHT `54beedd6` three times.  Keep the newline for a template
  (whole lines by intent); a pattern may still strip it.  Test both.
- [ ] `[maybe-insert-indent]` *(not yet a request)*.  NDTHT's
  `insert-after.py`, `insert-hyp.py` and `reindent.py` are block operations
  too (`docs/prior-art/README.md`).  Revisit once the three above are in.
- [ ] `[reargs-foundation]` **Decide what `reargs` is built on.**  Its
  argument matcher (`_arg_at`, about 30 lines) is a hand-rolled and less
  thorough version of comby's `:[x:e]` hole.  Before `reargs` grows, try
  each alternative against its tests and NDTHT's uses.  Growth here means
  constraints on holes, nested patterns, or a new kind of argument.
  - **comby with an Isabelle custom matcher.**  Apply the prose mask to its
    `-json-lines` match ranges.  The costs: an OCaml binary that pip does not
    install, no release since 2022, and `"` cannot be declared a string.
  - **A token stream from `isabelle_query.api`.**  If the API has none, this
    is an `[upstream-asks]` draft, but only for a demonstrated limit.
  - **Keep `_arg_at`**, with the reasons written down.
  - See `docs/related-tools.md` §comby for the fit questions to test first.
- [ ] `[reargs-term-bound]` **An argument can be the next command.**
  `_arg_at` skips every kind of whitespace, blank lines included, and an
  atom may be any identifier.  So a head outside a term takes what follows
  as its argument and joins it onto its own line, all under `PASS`.  That
  covers a method name, or a fact after `using`.  Found 2026-10-21:
  `reargs 'simp $1' 'auto $1'` on the test fixture turned `by simp`, a blank
  line and `lemma beta: …` into `by auto lemma beta: …`, three times over.
  Inside `"…"` the closing quote stops an argument, which is why NDTHT's uses
  did not hit it.  Only `--expect` would have caught it.
  - Bound an argument to the enclosing quote or cartouche of a term, or at
    least refuse one that follows a blank line or is an outer-syntax keyword.
    `[reargs-foundation]` decides which mechanism.
  - Test: the fixture case above refuses, or rewrites nothing.
- [ ] `[borrow-features]` *(not yet requests)* **Features the related tools
  have and `block` lacks** (`docs/related-tools.md`).  Take each one only when
  a use asks for it.
  - A `--dry-run` that prints a unified diff, not only counts (`fastmod`,
    comby, ast-grep).
  - Constraints on `reargs` holes, such as "`$1` is an atom" (comby `where`).
  - JSON output of matches, for scripting (comby `-json-lines`, ast-grep
    `--json`).

## Upstream

- [ ] `[upstream-asks]` **Draft the `isabelle-query` / `isabelle-layout`
  feature requests** into `upstream/`, one file each, signed, for Andras to
  check and post.  Do not post them yourself.  The list is
  `docs/background.md` §2.5, U1–U9.

  **Rule (Andras, 2026-10-15): the `query` CLI first.**
  - Callers come from `query callers -f tsv NAME...`, batched into one call.
  - Import closures come from `query graph imports -f json`.
  - A *library* API is requested only when the CLI is shown insufficient,
    and the request cites the limit that was hit.  `isabelle-query` adds a
    public name only for a demonstrated consumer need.  So U1 and U3 are
    conditional; the rest are gaps the CLI does not cover either.

  The requests:
  - U1, a public callers API (conditional);
  - U2, `callees -f tsv`;
  - U3, a per-theory import closure across sessions (conditional);
  - U4, prose antiquotations as callers;
  - U5, implicit-use evidence;
  - U6, the identifier-boundary helper and Isar keyword table;
  - U7, preamble versus section introduction;
  - U8, `<toplevel>` tsv rows;
  - U9, bound names as call-graph nodes;
  - U10, a declaration in mid-line;
  - U11, a public resolver for a locus's theory part (isabelle-block#3).

  Draft each one when the verb that needs it is being built, so the request
  carries a concrete use.

  **State (2026-10-24): `upstream/README.md` tracks each one.**
  - U2, U4 and U5 are drafted, checked against 0.9.8, and not yet posted.
    Recheck each against the current isabelle-query before posting.
  - U7 and U10 were posted as isabelle-query#28 and #29, and fixed in
    1.1.1.
  - U8 is fixed in 0.9.8.
  - U1 and U3 are conditional.
  - U6 and U9 are deferred to `rename`.
  - U11 was posted as isabelle-query#34 (2026-10-24).

- [ ] `[locus-targets]` **Accept a `query` locus as a target** (#3):
  `Diagonal_Machine:3608..3609`, a theory name or label where a FILE goes.
  **Upstream only** (Andras, 2026-10-24): no local resolver, since query's
  label grammar (bare name, `beta/Examples`, `While/Hoare`) is query's to
  read, and a target resolved to the wrong file is the dangerous failure.
  Waits on U11 (isabelle-query#34).  When it lands: try the FILE as a path first, then the
  resolver; more than one candidate is a refusal that lists them.  The
  other half of #3, several `delete` targets in one call, is done
  (0.1.5).

## Release and switch-over

- [x] `[first-release]` **On PyPI since 0.1.2** (Andras's uploads; 0.1.2 and
  0.1.3 are there, checked with `pip index versions --no-cache-dir` on
  2026-10-24).  Earlier: v0.1.0 (2026-10-22, `867adad`) and v0.1.1
  (2026-10-23, `b32c74d`) were GitHub-only, while PyPI was postponed.
  v0.1.2 (`3b42ce1`) brought `[heading-rule]`, and v0.1.3 (`4c0aadc`) issue
  #1.  The process is `docs/publishing.md`; the upload is `twine upload -r
  pypi-isabelle-block`, from Andras's `~/.pypirc`.
  - v0.1.4 (2026-10-24): issue #2, a multi-line `sub` OLD and the README's
    PyPI install line.
  - The README shown on PyPI is the one in the uploaded version.  So 0.1.3's
    PyPI page still says "not on PyPI yet" (#2), until 0.1.4 is uploaded.
  - `pip index versions` may serve a stale list from pip's cache just after
    an upload; `--no-cache-dir` sees the new version.
- [ ] `[ndtht-switchover]` **Point NDTHT at the package**.  Unblocked: it is on
  PyPI since 0.1.2.  This is done in NDTHT, not here.
  - Add a floor `isabelle-block>=0.1.3` (or later) to `requirements.txt`, with a comment
    in its house style.
  - Delete `bin/block.py`.
  - Rewrite every `bin/block.py` reference as `block`.  The edit list is
    `docs/background.md` §4.2: CLAUDE.md, the `split-theory` skill's
    `allowed-tools`, memory files, KB entries, `prune-entries.py`.
  - Drop the dead `--transform tr-to-B` / `classical-to-B` documentation.
  - Leave dated history as written.
  - Until the switch-over, NDTHT uses the sibling install
    (`pip install ~/projects/isabelle-block`), and `bin/block.py` is frozen.

## Decisions for Andras

- The decisions listed in each FR document (D1–D4 apiece), each with a
  recommendation.
