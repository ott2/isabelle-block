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

1. Groundwork: `[cut-span]`, then `[heading-rule]`.
2. `[fr-rename]` phase 1.
3. `[fr-safe-delete]` phase 2.
4. `[fr-checked-move]` phase 1.

Draft `[upstream-asks]` alongside the work as each gap is hit.

## Groundwork

- [ ] `[cut-span]` **Resolve names through `Entry.cut_span`.**
  - `resolve_entry` re-implements the clipped span that `isabelle_query.api`
    already provides as `Entry.cut_span`, which is documented as the span a
    delete or move tool writes through.
  - Unlike the local code, `cut_span` is `None` when `shares_line` (two
    declarations on one line).  That must become a refusal.
  - Replace the `keywords` refusal in `_entries` by
    `parse_theory(..., root=ROOT)`, which builds the session-wide keyword
    table.  Discover ROOT from the `.isabelle-query` marker as `query` does,
    with `--root DIR` to override.
  - Keep `--no-preamble`.
  - Port `prior-art/scripts/span-overreach-scan.py` as a corpus test (see
    `[corpus-tests]`) and confirm that no resolved span changes on NDTHT's
    `t/` except at `shares_line` sites.
  - Background: `docs/background.md` §2.1 and §4.1.
- [ ] `[heading-rule]` **Section introductions are not preambles.**
  - `delete NAME` has taken a section's introductory `text` as the lemma's
    preamble in three NDTHT sessions.
  - `move … before NAME` lands under the heading directly above NAME.
  - Implement the rules in `docs/fr/delete.md` (§"The preamble rule") and
    `docs/fr/move.md` (§"The landing rule") in one addressing helper.
  - Report the attribution upstream as U7.
- [ ] `[corpus-tests]` **Read-only tests against real trees**, under a pytest
  marker `corpus` and skipped when the tree is absent:
  - NDTHT `~/projects/ndtht/t/`;
  - the AFP `~/repos/afp/thys`.

  Checks:
  - every entry name resolves, or is refused for a stated reason;
  - no resolved span overreaches into the next entry's doc block;
  - `emit` of every span concatenates back to the file.

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
  - U8, `<toplevel>` tsv rows (NDTHT already has a draft,
    `upstream/query-callers-batch.md`);
  - U9, bound names as call-graph nodes.

  Draft each one when the verb that needs it is being built, so the request
  carries a concrete use.

  **State (2026-10-16): `upstream/README.md` tracks each one.**
  - U2, U4, U5 and U7 are drafted, checked against 0.9.8, and await
    Andras's review.
  - U8 is fixed in 0.9.8.
  - U1 and U3 are conditional.
  - U6 and U9 are deferred to `rename`.

## Release and switch-over

- [ ] `[first-release]` **The first release on PyPI**, with Andras's go-ahead
  at each outward step.
  - **PyPI is postponed** (Andras, 2026-10-22) until the standalone tool has
    seen more use, since glitches are expected.  v0.1.0 is a GitHub-only
    release: tag and Release, and the README installs from the tag.
  - The first PyPI upload will be a later version, not 0.1.0.  Steps 4 and 6
    below then apply to that version.  When it happens, switch the README's
    install line back to `pip install isabelle-block`.

  Steps:
  1. ~~Check that the name `isabelle-block` is free on PyPI.~~  Done
     2026-10-21 (404).  Recheck just before uploading.
  2. ~~Andras creates `github.com/ott2/isabelle-block`.~~  Done 2026-10-22,
     and `main` was pushed through `45dc534`.
  3. ~~Copy `.github/workflows/release.yml` from `~/projects/isabelle-layout`,
     and adapt it.~~  Done 2026-10-22.  Only the Release title differs from
     the siblings' workflows.  The runbook is this repository's own, shorter
     `docs/publishing.md`, not a copy of isabelle-layout's (Andras,
     2026-10-22: that one carries an old to-do list).  Its build step was
     tried on 2026-10-22, and found the sdist shipping
     `docs/prior-art/README.md` and `upstream/README.md`.  The `include`
     patterns are now anchored.
  4. **Andras: the first-upload credential.**  The house workflow publishes
     only the GitHub Release, and PyPI is a manual `twine upload`.  A project
     that does not yet exist cannot have a token scoped to it, so there are
     two routes:
     - an account-scoped token for 0.1.0, revoked straight after in favour of
       a project-scoped one (`docs/publishing.md` §5);
     - Trusted Publishing, which needs an upload job added to the workflow.
       That would make it differ from its siblings beyond the title.
  5. ~~Check Python 3.9 compatibility statically.~~  Done 2026-10-22: the
     `ast` check in `docs/publishing.md` §1 passes.  The two modules without
     the `__future__` import have no annotations.
  6. Follow `docs/publishing.md` from §2: drop `.dev0`, write the release
     commit, build, then tag, push and upload (Andras).

  The order is settled (Andras, 2026-10-21).  0.1.0 ships after the
  contract tests (`tests/test_contract.py`) and before `[cut-span]`, so
  `[cut-span]` starts from a released, tested baseline.  The step 1 check was
  done the same day: PyPI returns 404 for `isabelle-block`.  Recheck it just
  before uploading.
  - For the release notes, the changes since `bin/block.py`:
    - `emit` now prints `PASS:` on stderr;
    - `split` no longer leaves earlier parts behind when a later spec is
      refused;
    - a crash ends in `FAIL:`.

    An NDTHT script that captures `emit` with `2>&1` would see the new line.
- [ ] `[ndtht-switchover]` **Point NDTHT at the package**, once it is on PyPI.
  This is done in NDTHT, not here.
  - Add a floor `isabelle-block>=0.1.0` to `requirements.txt`, with a comment
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
