# FR: `block rename`, a whole-identifier, prose-aware rename

**Status:** proposed (2026-10-15).  The design is not yet settled; see
"Decisions".  Tag: `[fr-rename]`.

## Problem

Renaming an Isabelle entity is the most frequent of the four recurring
operations in NDTHT's history: 38 commit subjects, and more renames hidden
inside commits about something else.  It is also the one that has produced the
most single-purpose scripts: eight of the eighteen in `prior-art/scripts/`.

`block sub` does a *substring* rename.  That is correct for a family stem
(`bit_width` → `block_width` should also carry `card_le_two_pow_bit_width`).
It is wrong for a word-shaped name, because it rewrites prose too, and the
damage is grammatical, so no build catches it (`insights/289`).

The failures recorded in `../usecases.md` §2 were silent, not loud:

- `unary` → `unary_word` changed English inside `\<^emph>` bodies.  Only a
  document build, two days later, exposed it.
- A literal `back` → `invert` printed PASS while rewriting four sentences.
- A map that spelled `\<Gamma>` as a symbol renamed none of the six ASCII
  `Gamma_tm` names.  It also reported nothing, because a zero-match OLD was
  not an error.
- Renaming a constructor missed Isar case names (`case OLD`) and case facts
  (`using OLD`).  A naive fix would also have renamed user labels
  (`consider (OLD)`), which look the same.
- A new name collided with an AFP name (`TM_Common.relpow_mono`).  Shadowing
  in Isabelle is silent.

## Requirements

These are `../usecases.md` §6.1, RN1–RN16.  The defining ones:

- **RN1, whole-identifier matching** on Isabelle tokens: `'` is an identifier
  character, a `\<X>` symbol body is not a match site, and `.` qualifies.
  Use `isabelle-query`'s boundary rule, not a fifth copy of it (upstream ask
  U6 below).
- **RN3, derived-name family**: `OLD_def`, `OLD.simps`, `.induct`, `.cases`,
  `.split`, `.exhaust`, `.inject`, `.distinct`, `.expand`.  This should be an
  explicit, reported expansion: print the expanded map before applying it.
- **RN6, classes of occurrence**:
  - live code;
  - inner-syntax terms;
  - antiquotations in prose (`@{const OLD}`, `\<^const>\<open>OLD\<close>`):
    rename;
  - bare prose words and `\<^emph>` / `\<^bold>` bodies: do **not** rename
    unless opted in.

  Count each class separately in the report.
- **RN9, collision check** of each NEW against the import closure, sibling
  sessions and, optionally, an AFP name index.
- **RN15, residue sweep**: after applying, list surviving OLD occurrences
  anywhere.  An OLD that matched nothing is an error.
- **RN16**: PASS must not hide prose edits.

## Proposed interface (draft)

```
block rename OLD=NEW [OLD=NEW...] FILE[:REGION]...
block rename @MAP FILE[:REGION]...           # MAP: one OLD NEW per line, # comments
block rename --theory OLD_THY=NEW_THY ROOT_DIR
```

Options:

- `--family` expands each OLD to its derived names, printed before applying
  (RN3).
- `--prose` also renames bare prose words, each listed (RN6, RN7).
- `--expect N`, `--except NAME` and `--dry-run` work as they do for `sub`.
- `--no-check` skips the collision check (RN9).

The default posture is a full report with code, antiquotation and prose hits
counted separately, and a refusal if any OLD matches zero sites.

## Phasing

1. **Phase 1, in-file whole-identifier rename.**  Port the core of
   `rename-thy-names.py`: the lossless code/prose split and the map format.
   - Code hits are taken from `TheorySection.live_source()`, which is
     line- and column-preserving.
   - Prose antiquotation hits are taken from `text_blocks` / `nonisar_spans`
     with a cartouche-depth walk.
   - Add `--family`, the zero-match refusal and per-class counts.
   - This retires `token-rename.py` and `rename-thy-names.py`.
2. **Phase 2, collision check** (RN9).  It needs the import closure
   (`move.md`'s dependency U3) and a name index of the closure.  A first cut
   can use `parse_root` over the project, with no AFP.
3. **Phase 3, constructor case names** (RN5).  Track `proof`/`qed` depth.
   Rename `case OLD` and `OLD` facts where the case comes from a split on
   OLD's datatype.  Leave user labels alone, and at minimum list them.
4. **Phase 4, theory rename** (RN12).  This touches:
   - `git mv`, which the tool should print rather than run (decision D3);
   - the `theory` header;
   - every `imports`, bare and `Session.`-qualified;
   - the ROOT `theories` list;
   - `document/root.tex` (`\input{}`);
   - `@{theory}` antiquotations.

   It retires `rename-theories.py`.  Session rename (RN13) stays a refusal
   that prints a checklist.
5. **Later:** LaTeX and markdown modes (RN10, RN11), and prefix maps (RN14).

## Decisions for Andras (recommendation first)

- **D1.**  Should `sub` stay a substring rename?  **Yes.**  It is the right
  tool for family stems.  `rename` is the default for a single name, and the
  docs should say which to use when.
- **D2.**  Should prose words be renamed by default?  **No.**  Antiquotations
  are renamed by default; bare words only with `--prose`.  The episodes show
  that prose damage is the silent failure.
- **D3.**  Should the tool run `git mv` for a theory rename?  **No.**  It
  should print the command.  A file tool that drives git is surprising, and
  NDTHT's auto-gate treats file moves cautiously anyway.
- **D4.**  Is the AFP name index in scope for the collision check?  **Not in
  phase 2.**  Make it an optional `--against DIR`, using `parse_root` on
  `~/repos/afp/thys` when given.

## Dependencies and upstream asks

These are numbered as in `../background.md` §2.5.

- **U6**: a public identifier-boundary helper and Isar keyword table in
  `isabelle_query.api`.  The keyword table is also needed to refuse a NEW
  that is an Isar command word, which is NDTHT's `options` and `back` lesson.
- **U3**: the import closure, for phase 2.
- **U9**: bound names (constructors, conjuncts) as call-graph nodes would
  help with phase 3.

## Test plan

Fixtures, each one a regression from `../usecases.md` §2:

- a word-shaped OLD in `text` and in `\<^emph>`;
- `foo` against `foo_bar` and `foo\<^sub>1`;
- the derived family;
- a symbol-spelled OLD against ASCII occurrences, which must fail with a
  zero match;
- a constructor with `case` and with `consider (R)`;
- a NEW that collides.

Then a corpus dry run over NDTHT's `t/`, renaming each of 50 random entries to
a fresh name, with a check that every class count is explained.
