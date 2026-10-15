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
- [ ] `[maybe-insert-indent]` *(not yet a request)*.  NDTHT's
  `insert-after.py`, `insert-hyp.py` and `reindent.py` are block operations
  too (`docs/prior-art/README.md`).  Revisit once the three above are in.

## Upstream

- [ ] `[upstream-asks]` **Draft the `isabelle-query` / `isabelle-layout`
  feature requests** into `upstream/`, one file each, signed, for Andras to
  check and post.  Do not post them yourself.  The list is
  `docs/background.md` §2.5, U1–U9:
  - U1, a public callers API;
  - U2, `callees -f tsv`;
  - U3, a per-theory import closure across sessions;
  - U4, prose antiquotations as callers;
  - U5, implicit-use evidence;
  - U6, the identifier-boundary helper and Isar keyword table;
  - U7, preamble versus section introduction;
  - U8, `<toplevel>` tsv rows (NDTHT already has a draft,
    `upstream/query-callers-batch.md`);
  - U9, bound names as call-graph nodes.

  Draft each one when the verb that needs it is being built, so the request
  carries a concrete use.

## Release and switch-over

- [ ] `[first-release]` **0.1.0 on PyPI**, with Andras's go-ahead at each
  outward step.  Steps:
  1. Check that the name `isabelle-block` is free on PyPI.
  2. Andras creates `github.com/ott2/isabelle-block`.
  3. Copy `.github/workflows/release.yml` and `docs/publishing.md` from
     `~/projects/isabelle-layout`, and adapt them.
  4. Check Python 3.9 compatibility statically.
  5. Drop `.dev0`, write the release notes as the version-bump commit's
     message, tag, push, and `twine upload`.

  Whether 0.1.0 waits for `[fr-rename]` phase 1 is Andras's call.  It does
  not need to: today's verbs are already useful outside NDTHT.
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

- The package name `isabelle-block` and the command name `block` (chosen
  2026-10-15, to match how NDTHT already says it).
- Whether 0.1.0 ships before `rename`.
- The decisions listed in each FR document (D1–D4 apiece), each with a
  recommendation.
