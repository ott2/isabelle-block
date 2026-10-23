# FR: a visibility-checked `block move`

**Status:** proposed (2026-10-15).  Tag: `[fr-checked-move]`.

## Problem

`block move SRC:NAME before DEST` relocates text.  It does not ask whether the
result still elaborates.  NDTHT records 36–49 promotions or moves between
theories and sessions (`../usecases.md` §3); "promote to the substrate" is
the typical one.  Each move was followed by build-driven repair:

- **Callees not visible at DEST.**  The moved proof cites a lemma that DEST
  does not import.  The build reports these one per attempt.
- **Prose antiquotations** (`\<^const>`, `@{thm}`) in a moved `text` block
  name constants DEST does not import.  These broke builds most often.  The
  recorded fix is to demote the antiquotation to a plain cartouche, not to
  add an import (`insights/201`).
- **Callers that no longer see the entry**, when it moves to a theory outside
  their import closure.
- **Visibility is by import closure, never by session**: importing a theory
  does not import its session siblings (`insights/206`).  A cross-session
  import must be qualified (`"Session.Theory"`).
- **A name already present** in DEST's closure creates a silent shadow.
- **`move … before NAME` lands under a heading** directly above NAME
  (2026-10-07).

## Requirements

These are `../usecases.md` §6.3, VM1–VM11.  The defining ones:

- **VM1, callee check**: every constant, type, fact and theory the block
  references must be declared in DEST's import closure.  This covers the
  statement, the proof *and* the prose antiquotations.  Within one theory, the
  reference must also be above the insertion point (`insights/192`).  Report
  each failure with its kind, and for a prose antiquotation suggest demotion.
- **VM2, caller check**: every theory citing a moved entry must have DEST in
  its closure after the move.  Warn for `[simp]`-style entries, whose implicit
  consumers cannot be enumerated.
- **VM3**: report the exact import line that would fix a failure.
- **VM4, `--with-callees`**: compute the closure of same-theory callees that
  would also have to move.  Print its size and the alternative of moving the
  callers instead.
- **VM5, shadow check** at DEST.
- **VM11**: multi-entry moves are checked as a unit, so references between
  the moved entries need no visibility.

## Proposed interface (draft)

```
block move SRC:NAME [SRC:NAME...] before DEST     # checked when DEST is another theory
block move SRC:A..B before DEST                   # spans: unchecked, as today
```

Options:

- `--with-callees` brings the needed same-theory callees along, listed first.
- `--force` moves despite failures, and lists them.
- `--root DIR` sets the project root for closures and callers.
- `--suggest` prints the lowest legal home for the block (the `hoist-scan.py`
  role) and does not move it.

## Phasing

1. **Phase 1, callee check only** (VM1, VM3).
   - Get the block's references from its `live_source()` tokens, plus its
     prose antiquotations.
   - Resolve each to a declaring theory with a project-wide name index from
     `parse_root`.
   - Test membership in DEST's import closure.
   - This catches the most common failure.
2. **Phase 2, caller check** (VM2), sharing `delete.md` phase 2's batched
   callers query.
3. **Phase 3**: `--with-callees` and `--suggest` (VM4).  This retires
   `hoist-scan.py`.
4. **Phase 4**: the shadow check, removable-import reporting (VM5, VM7), and
   cross-session updates of `@{theory}` and ROOT (VM6).

## The landing rule

When DEST is a NAME whose preamble directly follows a heading, land **above
the heading** if the moved block is itself headed, and otherwise below the
heading but above the preamble.  If that turns out to be wrong in practice,
replace it with an explicit `--above-heading` option.  This is the same
heading-awareness as `delete.md`'s preamble rule, and both should live in
one addressing helper.

**Built 2026-10-24, with two refinements:**

- **Rank.**  The block lands above NAME's heading only when it starts with a
  heading of the *same or higher* rank.  A `subsubsection` moved before a
  `subsection`'s first lemma belongs inside that subsection, as in an
  outline.
- **No preamble needed.**  The rule applies to any NAME directly under a
  heading, with or without a doc block, since either way the headed block
  would otherwise capture NAME.

The helpers are `_headings`, `_heading_directly_above` and
`_block_heading_level`, shared with `delete`'s empty-heading check.

## Decisions for Andras (recommendation first)

- **D1.**  Should the check run only for cross-theory moves?  **Yes.**
  Within a theory, the only hazard is order (a forward reference).  Check that
  cheaply as well, but do not build closures for it.
- **D2.**  Where should the import closure come from?  **The `query` CLI**:
  `query graph imports -f json`, one call, then a BFS in `block`.  Do not
  re-implement `Session.Theory` resolution.  This follows the same rule as
  `delete.md` D3: a library API (U3) is requested only if the CLI proves
  insufficient, citing the limit that was hit.
- **D3.**  Should the tool add a missing import itself?  **No, not in phase
  1.**  It should print the exact line.  Adding imports changes the
  dependency structure, which in NDTHT is a design decision (the substrate
  stays small).

## Dependencies and upstream asks (`../background.md` §2.5)

- **U3**: a public per-theory import closure that follows session-qualified
  imports.  Only if `query graph imports -f json` proves insufficient (D2).
- **U2**: `callees -f tsv`.  Not needed if phase 1 computes references
  itself.
- **U1** (only if needed) and **U4**: shared with `delete`.

## Test plan

A two-session fixture tree (parent and child ROOTs) with:

- a move whose callee is invisible at DEST;
- a moved `text` with a `\<^const>`;
- a caller in a third theory;
- a forward reference within one theory;
- a moved name that shadows one in DEST's closure;
- a heading directly above DEST.

Then a corpus replay: for NDTHT promotions recorded in `../usecases.md` §3,
`--dry-run` on the pre-move tree (from a scratch checkout) should report
exactly the failures that the history says the build found.
