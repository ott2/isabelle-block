# Use cases for `rename`, safe `delete` and visibility-checked `move`

Evidence from the NDTHT Isabelle formalisation's git history (about 3,960
commits, 2026-03 to 2026-10-15), collected to inform the design of three new
verbs for the block-surgery tool being extracted from `bin/block.py`.

The reader is assumed **not** to have the repository.  Every episode
therefore quotes the essential details, and the commit sha and date are
given as provenance only.

## 1. Method and counts

Source of truth: `git log --format='%h %ad %s' --date=short` (3,961
subjects), then commit bodies (`git show -s --format=%B`), the dated
`history/*.md` session records, and the project's knowledge base
(`insights/NNN.md`, `techniques/NNNN.md`).

Subject counts (case-insensitive `grep -ciE` over the subject list):

| Category | Pattern | Hits |
|---|---|---|
| Rename | `renam` | 38 |
| Move / promote | `promot\|hoist\|relocat\|moves? (down\|up\|into\|to\|from\|beside)\|moved (to\|into\|down)\|goes? home\|fold(s\|ed)? .* into` | 49 |
| Dedup / wrapper | `dedup\|duplicat\|re-?prov(ed\|ing)\|wrapper.* go\|wrappers? (go\|removed\|deleted)\|delete .*wrapper\|alias\|shadow` | 27 |
| Dead-code prune | `prune\|dead[- ]?code\|unused\|zero-caller\|vestig\|orphan\|superseded\|(remove\|delete\|drop\|retire)[sd]? (the )?dead` | 54 |

Each pattern has noise (e.g. "move" catches moves of docs and scripts,
"dead" catches "dead end" in machine semantics, "wrapper" catches
construction names such as "wrapper B"); hand-reading suggests roughly
80% of the rename hits, 70% of the move hits, 75% of the dedup hits and
70% of the prune hits are Isabelle-entity operations.  The earlier rough
counts (38 / 36 / 30 / 50) are consistent with these.

Subjects undercount: many renames, moves and deletions happen inside
commits whose subject names something else (e.g. a promotion that also
deletes two dead lemmas "on the way").  Tool mentions in full commit
messages:

| Tool named in message | Commits |
|---|---|
| `move-block` (block.py's predecessor) | 33 |
| `block.py` | 48 |
| `rename-ident` (literal substring rename, now `block.py sub`) | 7 |
| `rename-thy-names` (whole-identifier, prose-aware rename) | 4 |
| `prune-entries` / `prune-rounds` | 4 |
| `hoist-scan` (lowest legal home of an entry) | 13 |
| `query callers` / `query unused` | 43 |

Ad-hoc tools written for these jobs, all still in `bin/`:
`rename-thy-names.py`, `token-rename.py`, `rename-theories.py`,
`rename-base-theories.sh`, `rename-tex-names.py`,
`rename-isabelle-symbols.py`, `rename-wrap-in-docs.py`, `ktm-rename-map.py`,
`prose-token.py`, `old-names-sweep.py`, `prune-entries.py`,
`prune-rounds.py`, `unused_lib.py`, `classify-unused.py`, `hoist-scan.py`,
`split-plan.py`, `afp-name-clash.py`, `afp-names-diff.py`.  That eighteen
scripts exist for four operations is itself the main finding: each new
rename or move hit a case the previous script did not handle, and a
sibling was cheaper to write than the old one was to extend.

---

## 2. Rename

### Episodes

**R-1. The ktm rename, phase 1: 280 names, 77,606 sites**
(`8ba4f4e2`, 2026-10-04; leftovers `b44da50b`, 2026-10-05).
The substrate's core names clashed with another AFP entry (Dalvit and
Thiemann's `Multitape_To_Singletape_TM`), so a whole naming scheme
changed: `*mttm*` -> `*ktm*`, `mt_*` -> `ktc_*`, ten selectors `X_tm` ->
`X_ktm`, the datatype `dir` -> `move` (with `go_dir*`, `finite_UNIV_dir`),
and `relpow_mono` -> `relpow_subset_mono` (another AFP theory,
`TM_Common`, already had a `relpow_mono`).  Tooling: `ktm-rename-map.py`
generated a 280-line `OLD NEW` map from the tree, checking no new name
collided; `rename-thy-names.py` applied it to 458 theories and to
backticked names in 173 markdown docs; a new `rename-tex-names.py`
rewrote 124 LaTeX-spelled sites in `root.tex` / `glossary.tex`
(`valid\_mttm`, `\isasymGamma\_tm`).  What went wrong:
- the map generator's first version was too broad: it treated `\<open>`
  as an identifier character and matched `dir` inside `enc_dir`;
- names were missed because the generator spelled Gamma as the symbol
  `\<Gamma>`, so six lemmas with an ASCII `Gamma_tm` stem
  (`finite_patch_Gamma_tm`, `relabel_Gamma_tm`, ...) were never renamed;
  found a day later;
- markdown: phase 1 renamed only inside backticks, leaving about 1,000
  bare-prose and fenced-block mentions (345 in one design memo); the tool
  grew `--md-prose`, `--keep OLD` and `@FILE`;
- it also renamed *too much*: `t/<dir>/` (a path placeholder),
  `build-<dir>` and `pcommit_read/write/dir` (a fragment of `pcommit_dir`)
  all became `move` although they were in backticks; two documents that
  describe the *other* development's code had its names rewritten and
  were restored by hand.  Lesson recorded: "a code span is not proof of a
  reference"; documents about a foreign source must be excluded by file;
- dated records (history, journals) must keep old names; the rename was
  restricted to "live" docs by hand;
- a renamed local label in two big theories forced a full re-elaboration
  of the session and a watchdog timeout (build-time consequence, not a
  bug).

**R-2. Phase 2: constructors `R/L/N` -> `MoveR/MoveL/MoveN`**
(`ab4473f9`, 2026-10-04).  6,403 sites in 222 files.  Textual because a
`hide_const (open) L R N` had forced every use to be qualified (`move.R`),
so `move.X` -> `MoveX` was unambiguous.  The surprise: **a constructor's
name lives in two more namespaces** — Isar case names (`case N` after a
split on a `move` value) and the case's assumption fact (`using L`).  48
case names and 59 fact references in seven files, "checked split by
split"; `consider (R)` / `case R` labels in two other theories are *user*
labels that happen to coincide and had to stay.  "A first pass missed
seven references after a nested proof; tracking proof/qed depth found
them."  The `hide_const` itself had to be removed by hand.

**R-3. Word-shaped names: `restate`, `unary`** (`04c0685d`, 2026-10-03;
damage found `bd9aaff4`, 2026-10-05).  `unary` -> `unary_word`, `restate`
-> `mt_set_state`, `tapes_ok` -> `mt_tapes_fit`, `le_*` -> `endmarker_*`
(and `le_fix` -> `endmarker_normal`), each lemma following its constant
(`restate_self` -> `mt_set_state_self`, `embed_update_restate` ->
`embed_update_set_state`).  1,121 sites in 25 theories.  This is the
commit that created `rename-thy-names.py`, because `block.py sub` (a
substring rename) would rewrite the English words "restate" and "unary"
in prose and would also hit `unary_marks`, a different constant sharing
the stem.  Rule implemented: rename everywhere in source; in prose (`text`,
`section`, `\<comment>`, `(* *)`) only inside a nested cartouche or an
`@{...}` antiquotation.  **What went wrong:** the "nested cartouche =
reference" rule is wrong for `\<^emph>\<open>...\<close>` and
`\<^bold>\<open>...\<close>`, whose bodies are prose.  Seven NTH text
blocks became "a \emph{unary_word} run", which passes `_` unescaped to
LaTeX.  No proof build caught it; it surfaced two days later only in a
document build that a timeout had been hiding.  Two renames in a row had
each left prose damage that no build caught.

**R-4. The literal rename whose PASS was a lie** (insight 289,
2026-08-27; `a5994588`, 2026-09-07).  A fact label `back` (an Isar
command word, so a parse error) was renamed with the literal substring
tool to `invert`.  The tool printed `PASS:` naming one file, and in the
same pass turned "reading a run back the other way" into "reading a run
invert the other way" and three similar sentences.  Separately, the
literal rename tool interpolated NEW into a perl program unescaped, so a
replacement containing `\<lambda>` silently became `<lambda>` — "which the
rename itself reports as PASS and which surfaces two theories later as a
parse error naming neither the symbol nor the site."

**R-5. Theory renames inside one session: `EncodingWrap_Plant*` ->
`Wrap_*`** (`31b7a8b1`, 2026-07-03; docs `55b8543b`).  Ten theories,
e.g. `EncodingWrap_Plant` -> `Wrap_Defs`, `EncodingWrap_PlantReset` ->
`Wrap_Reset`.  New `rename-theories.py --dir t/ae OLD=NEW ...`: `git mv`,
then `\bOLD\b` -> NEW over `*.thy`, `ROOT` and `document/*.tex` under the
directory, refusing if any OLD is a substring of a NEW.  32 references:
`theory`/`imports` lines, ROOT, one `@{theory ...Forcing}` antiquotation,
two prose cartouches.  The word boundary is what stops
`EncodingWrap_Plant` matching inside `EncodingWrap_PlantReset`.  A
companion pass stripped generation tags from 54 lemma/constant names
(`wrap_delta_B` -> `wrap_delta`, `wf_B` -> `wrap_wf`) and needed a
*trailing* negative lookahead `(?![A-Za-z0-9])` instead of `\b`, because
`\b` does not fire between `X` and `_def` (insight 207: renaming a
definition must carry `X_def`, `X.simps`, `X.induct`, `X.cases`).  The
docs sweep used a third script with the same map and had to leave the
names of *deleted* constructions (`wrap_delta_tr`) alone as history.

**R-6. Theory renames across sessions: base theories to the `Multitape_`
prefix** (`5f5d4aa3`, 2026-07-13).  Six theories (`Substrate` ->
`Multitape_Substrate`, `OriginFloat` -> `Multitape_Origin_Float`, ...),
referenced from four other sessions as `MTTM.Substrate`.  One-off
`rename-base-theories.sh`.  **The bare word `Substrate` is also the domain
noun**: a blanket `\bSubstrate\b` would have mangled about twelve prose
section titles.  It was rewritten only in anchored contexts (theory
header, a bare `imports Substrate`, the `.Substrate` tail of a qualified
import, a `Substrate.thy` file reference); two prose cartouches, the ROOT
theory list entry and `\texttt{}` references in `root.tex` (escaped) were
done by hand.  Compound names were done first so the bare pattern could
not fire inside the freshly created `Multitape_Substrate_Core`.
Verification needed the document build: "make pdf renders all four
documents (the antiquotation + \texttt{} completeness gate, which make
build alone would miss)".

**R-7. Session renames colliding with a constructor** (`fba6a498`,
2026-07-08).  Sessions `MTTM` -> `Multitape_TM_Substrate`,
`Alphabet_Enlargement` -> `Multitape_Alphabet_Enlargement`, etc.  But
`MTTM` was also the datatype constructor (`datatype mttm = MTTM ...`).
Discriminator: in `.thy` files the session appears only as `MTTM.` (in
`imports` and `@{theory MTTM.X}`), the constructor never with a dot; in
ROOT and Makefile every occurrence is the session; in `root.tex` the
session sits in a `\newcommand` macro while the constructor renders as
`\mathrm{MTTM}`.  Session rename invalidates every heap, so the first
build is cold.  Design-doc prose was a separate follow-up (`8e68d941`)
that had to skip `case M of MTTM ...` in a memo.

**R-8. Small identifier-family renames** (`a9d1ec9c` 2026-07-05,
`6e388231` 2026-07-07, `2e0f1018` 2026-06-23).  `k_for` -> `bit_width`
-> `block_width` across 13 theories in two sessions, including
`block_width_def`, `block_width_pos`, `card_le_two_pow_block_width`,
`two_pow_block_width_pred_less_card`; an interim candidate `b_for`
collided with existing vocabulary.  `alphabet_reduce_arity` ->
`alphabet_reduce_preserves_tape_count`: zero-caller headline theorems,
so the rename touched only definitions and the `root.tex` `\texttt{}`
citations — which "a plain grep missed because LaTeX escapes the
underscores (alphabet\_reduce\_arity)" (insight 183).

**R-9. Prefix renames on a session move** (`548950c8`, 2026-10-11).
Five theories moved from session DLS into DTH and "every `dls_` name
becomes `dth_` (no collisions in DTH or DTR)" — a prefix-family rename
whose safety rested on a collision check against the destination.

**R-10. Lemma names containing Isabelle symbols** (`c7fb39c3`,
2026-05-20).  25 declared identifiers and 23 Isar-binding names like
`wrap_\<delta>` -> `wrap_delta`, 568 substitutions.  Order mattered:
`wrap_\<delta>` is a prefix of `wrap_\<delta>_W_Run_source_only_run`.
Body text keeps the symbol form; the split is identifier versus body.

**R-11. Residue of an older rename** (`08adf861`, 2026-05-19): the
`ae_bisim` -> `ae_simulates` rename (`b01491d4`, six names plus `_def`,
also Isar local fact names `bisim` inside proofs) missed one subsection
heading; found ten days later by a user question.

**R-12. The pre-check also applies to new names** (insight 236,
2026-08-29; `981b1d0f`, 2026-10-04).  A new family `dec_arm`,
`dec_delta` collided with an imported `dec_delta` (where `dec` meant
*decode*); the definition silently shadowed.  `CE` was renamed to
`conv_cex_ktm` (with its `ce_` family) because another AFP entry defines
`CE`, forcing qualified `Multitape_Time_Convention.CE` in any session
importing both.

### Edge cases distilled

1. Whole-identifier matching, not substring: `unary` vs `unary_marks`,
   `dir` vs `enc_dir`, `EncodingWrap_Plant` vs `EncodingWrap_PlantReset`.
2. But the generated family *must* follow: `X_def`, `X.simps`,
   `X.induct`, `X.cases`, `X.expand`, and for datatypes `X.split`,
   `X.exhaust`, `X.distinct`, `X.inject`.  Two approaches were used —
   explicit enumeration in the map (rename-thy-names) and a
   `(?![A-Za-z0-9])` stem lookahead (rename-wrap-in-docs).  Lemma names
   that merely *contain* the stem (`restate_self`, `card_le_two_pow_X`)
   are a policy choice and were listed explicitly.
3. Qualified forms: `Theory.name`, `move.R`, `Session.Theory` in
   `imports`, `@{theory Session.Theory}`.
4. Constructors also live as Isar case names and case-assumption fact
   names; user `consider (R)` labels look identical and must not change.
   Needs proof/qed depth tracking.
5. Prose: rename inside `@{...}` / `\<^const>\<open>..\<close>` /
   `\<^term>` antiquotations and code cartouches, **not** inside
   `\<^emph>`, `\<^bold>` or similar prose markup, and not bare
   words in `text`.  A word-shaped name (`back`, `restate`, `unary`,
   `Substrate`) needs per-hit review.
6. Escaped LaTeX spellings in `root.tex`: `foo\_bar`, `\isasymGamma`,
   `$_{x}$` for `\<^sub>x`; macros (`\newcommand`).
7. Markdown: backticks are evidence, not proof (`t/<dir>/`); some files
   describe foreign code and must be excluded wholesale; dated records
   (history/journals) keep old names.
8. Replacement text containing backslashes (`\<lambda>`) must be literal.
9. Map ordering / substring-in-NEW hazards (one OLD a prefix of another;
   one NEW containing an OLD); identifiers written with symbols vs ASCII
   (`\<Gamma>_tm` vs `Gamma_tm`).
10. Collision check of every NEW against: the session and its import
    closure, sibling sessions, and the AFP (`TM_Common.relpow_mono`,
    `Rewrite_Properties_Reduction.CE`).  Shadowing is silent in Isabelle.
11. Theory rename = `git mv` + `theory` header + every `imports` in any
    session (bare and `Session.`-qualified) + ROOT `theories` list +
    `document/root.tex` (`\input{Thy}` lines, `\texttt{}` refs) +
    `@{theory ...}` antiquotations + prose cartouches naming the file.
    A theory name that is also an English word needs anchored contexts
    only.
12. Session rename: ROOT `session` line, every child's parent and
    `sessions` block, every `Session.Theory` import, Makefile targets,
    root.tex macros; heaps invalidated.
13. Verification gates: proof build does not see prose damage; the
    document build does; neither sees English damage in `text` that
    still compiles.  So the tool must *report* every prose hit it
    changed, separately from code hits.

---

## 3. Move / promote between theories and sessions

### Episodes

**M-1. A theory moves to the ancestor session** (`89edf3ab`,
2026-07-03).  `OriginFloat` moved from session `Alphabet_Enlargement` to
the substrate session `MTTM`: `git mv`, import re-based from
`MTTM.Substrate` to the same-session `Substrate`, added to the target
ROOT, two dead lemmas dropped on the way.  **What broke:** the consumer
`EncodingWrap_Plant` had to import `"MTTM.OriginFloat"` explicitly —
"importing EncodingWrap_Base does not make a Substrate sibling visible"
(insight 206: a session is not an import; a handoff note had asserted
the opposite).  Three `@{theory Alphabet_Enlargement.OriginFloat}` prose
antiquotations had to be requalified to `MTTM.OriginFloat` (technique
0083: a cross-session move breaks `@{theory Sess.Thy}` antiquotations
with no deletion at all).

**M-2. Single lemmas promoted to the substrate**
(`0b9aa296` 2026-06-11, `37096e8e` 2026-06-04, `061926a5` 2026-07-10,
`6b7ffb8d` 2026-10-15, `f9a1e1eb` 2026-10-13).
- `valid_config_mttm_blank_tail`, `valid_reach_relpow_mttm` moved from AE
  to the substrate *because AR cannot import AE* (siblings): promotion as
  the cure for invisibility.
- `relpow_invariant_chain` moved verbatim (`move-block.py`) to a theory
  AR already imported, "so no AR import line changes and the four `_gen`
  loop callers resolve the name transitively" — the visibility argument
  was made by hand.  The moved preamble was rewritten (it named its old
  context).
- `mttm_step_functional` promoted, and two copies of acceptance
  monotonicity (in `Time_Convention` and in ART's `AlphabetRoundtrip`)
  unified under ART's name "so art's three call sites need no rename";
  Time_Convention's two `elim` sites repointed.  A move that is also a
  dedup, where the choice of surviving *name* minimised edits.
- `move_one` (+ `move_one_same`/`_other`) promoted from NTH's
  `Diagonal_Arms` into `Multitape_Substrate` "rather than Run_Facts
  because Finite_Patch, a client, is below Run_Facts" — the destination
  was chosen as the lowest theory visible to all intended clients.
- `clock_run_bounded` moved down; its preamble "no longer cites NTH's
  all_paths_in_time" (prose naming the source context had to change).

**M-3. Demotions out of the substrate: "the substrate stays small"**
(`180f3472`, `18d30075`, 2026-10-03; `be1f6ecd` 2026-10-02).
- `Multitape_Union` (642 lines, one client) became NTH's
  `Machine_Union`, "declared just before Class_Readings"; root.tex lost
  its item.
- Relabelling's NTH-only tail (~300 lines) became NTH's
  `State_Numbering`; one lemma used by both tracks stayed, and its
  subsection text was rewritten "without pointing at material that has
  left".
- 790 lines left `Multitape_Run_Facts` by `block.py split --cut` and
  joined `Embedding`'s `adv_head` family as NTH's `Run_Lemmas`.  "Texts
  that pointed at neighbours which stayed behind now name them."  Three
  zero-caller lemmas were deleted in the same move.
- `Speedup_Arithmetic` moved from the substrate into AE; "both clients
  already import AE's Wrap_Convention; they now import the AE theory
  instead" — every client's import had to be re-pointed.
- `bin/substrate-clients.py` computed, per entry, which downstream
  sessions reach it (`query callers -r`), producing the move list.
  Running 290 sequential `query callers -r` calls "cost about ten
  minutes of one core, because each re-parses the corpus" (history
  2026-10-02): a batch mode is needed.

**M-4. Accessors move from a sibling entry to the shared ancestor; an
import becomes droppable** (`ccffb37e`, 2026-10-03).  Three
`*_init_config` lemmas moved from AR to the substrate.  Attributes
differed by design: one gained `[simp]` there, a pointwise `[simp]` copy
elsewhere was deleted, another deliberately stayed without `[simp]`.
DTH's private copies were replaced by `declare mt_state_init_config
[simp]`.  `Clock_Decorate` "no longer imports AlphabetReduction_Theorems,
which it did for these three lemmas alone".  A related ledger item (R3,
history 2026-10-04) records that adding `[simp]` to the general lemma
made it fire before a specific one and broke three proofs.

**M-5. Hoists inside one session, and the prose they break**
(`1993ee87`, `abc536f7`, `b1f859cd`, `0832747b`, 2026-09-08).
`hoist-scan.py` names the lowest theories that could legally host each
entry (dependencies from `query callees`, DAG from `query deps -r`).
Seven `TP_*_not_sim` lemmas moved from `Diagonal_Sweeps` to
`Diagonal_Layout` and became visible to `Diagonal_Case2` "with no import
change".  23 codec facts moved to `Diagonal_Transcript` in three
contiguous spans, with their subsection heading and two prose blocks
("an orphaned heading is the reliable sign that a cut took the lemmas
and left their motivation").  **What broke, four times in one session:**
`\<^const>\<open>TP_TRS\<close>` and `\<^const>\<open>holds_word\<close>`
antiquotations in moved `text` blocks named constants that the
destination does not import.  "A hoist moves an entry *down* the import
DAG, and down means strictly less in scope."  No static check covered
it: the citation graph ignores prose, `split-plan.py` only models edges
inside the cut, `lint-latex` only checks forward references within one
theory.  "The build is the only detector, and it reports one per
attempt."  Recorded fix rule: **demote the antiquotation to a plain
cartouche; never add the import** (that would re-couple the layers the
hoist separated).  Also: `[simp]` lemmas have zero callers in the
citation graph, so the consumers of a moved simp rule cannot be
enumerated; "the build is the check".  And `hoist-scan.py --shadowed`
must be re-run after each move, "a move is precisely what turns a silent
shadow into a visible clash".

**M-6. Moving the smaller side** (`c0f2107e`, 2026-08-31).  Two step
lemmas were needed one theory *earlier* than their home.  "Moving the
runs down would have dragged `c1_run`, `copies_run` and `copies_budgets`
with them; moving the two step lemmas up costs nothing."  Verbatim
`move-block.py`, new subsection heading, "a pointer left at the product
where they used to be".  The callee-closure size decided the direction.

**M-7. A new intermediate theory instead of an import either way**
(`c5a2c882`, 2026-08-27).  `coverage` (in a deliberate leaf) and
`enumerable_sym4` (main line) shared a chain; an import in either
direction was wrong, so four entries moved to a new `Reduce_Chain` that
both import.  "What the split cost was prose": the header narrative
belonged to the moved steps.

**M-8. Splits leave dangling sibling references** (`c20eedf5`,
2026-08-28).  `Machine_Relabelling` split three ways into siblings;
`Machine_Embedding` kept three `\<^const>` references to a sibling it
does not import -> `Undefined constant` at build time.  `split-theory`
later gained guards (`522699bd`): overlapping ranges had "silently
extracted such a line into both files and cut it once, surfacing much
later as a duplicate-definition build error".

**M-9. Span edge errors in `move` / `delete`** (history 2026-10-02,
2026-10-04).  "`block.py move` with a line range took one line of the
next text block along.  Caught in the diff before building."  "A range
delete off by one line swallowed the next text block's opening line."
"`block.py delete FILE:NAME` takes the entry's preamble text with it;
read the span first."

**M-10. Session folds** (`efc24d77` 2026-09-29, `548950c8` 2026-10-11).
Eight theories of an unpublished session appended to the substrate with
renames (`Machine_Embedding` -> `Multitape_Embedding`, ...); consumers
"change qualifiers only" (`Multitape_TM_Substrate.Multitape_*`) and drop
the old session from their `sessions` blocks.  An import of
`HOL-Types_To_Sets` that was unused in the moved theory was removed, and
the two clients that *did* use it had to import it themselves.  The DLS
fold moved five theories into DTH with a `dls_` -> `dth_` prefix rename,
ROOT ordering ("lists the five before DTH_Class_Readings"), Makefile
targets, and a `root.tex` section; technique 0083 notes that after a
fold, documentation antiquotations keep the *qualified* name even for a
same-session citation.

### Edge cases distilled

1. Visibility is by `imports` closure, never by session membership
   (insight 206): a theory in an ancestor session is invisible unless
   some import chain reaches it, and the import must be session-qualified
   (`"Sess.Thy"`).
2. Callees: the moved block's proof-body references *and* its statement
   constants *and* its prose antiquotations (`\<^const>`, `\<^term>`,
   `@{thm}`, `@{theory}`) must all be visible at DEST.  The prose kind
   broke builds most often (M-5, M-8), and its correct fix is to demote
   the antiquotation, not add an import.
3. Callers: every theory that cites the moved entry must still see it.
   `[simp]`/`[intro]`/`declare`d rules have implicit callers that a
   citation graph cannot list.
4. Choice of DEST: lowest legal home (hoist-scan) is not always wanted;
   a theory may sit above its minimum by recorded decision.  The size of
   the callee closure decides which side moves (M-6).
5. A move can make an import droppable (M-4) or require one at every
   client (M-3, Speedup_Arithmetic).  A move across sessions also
   changes `@{theory Old.Thy}` antiquotations and ROOT `sessions` blocks.
6. A move into a theory that already has (or whose closure has) the
   same name creates a shadow, silently.  Re-check after every move.
7. Preambles: the doc block travels with the entry, but often names its
   old neighbours; section headings and introductory text may need to
   move with a group.  A pointer may be left at the old site.
8. Attribute changes are part of a promotion (`[simp]` added or not),
   and can change proof behaviour at distance.
9. Span boundaries: off-by-one into the next text block is the observed
   failure; name-addressed spans avoid it.
10. Batch queries: hundreds of `callers -r` calls must not re-parse the
    corpus each time.

---

## 4. Deduplication and wrapper removal

### Episodes

**D-1. Twelve exact duplicates collapsed onto published names**
(`1af14eae`, 2026-10-02).  Mapping chosen per pair, with the published
or ancestor name surviving:
`valid_mttm_delta_le` -> `valid_mttm_deltaLE`;
`mttm_step_not_halted` -> `mttm_step_src_neq_t` / `_neq_r` (one name to
*two*); `mttm_step_det` -> `mttm_step_det_at` / `det_mttm_step`, and
`mttm_step_functional` at two particular sites (call-site-dependent
target); `Lang_mttm_iff_accepts` -> `Lang_mttm_iff` (same theory, same
statement); `heads_ok` and its init/step/run lemmas -> `heads_parked`
family (a whole family, definition included);
`time_constructible_running` -> `mttm_relpow_not_halted`, where "two
sites move from the set form to the two-conjunct form" (not a pure
rename).  `relpow_transI`, HOL's `relpow_trans` verbatim, first became a
`lemmas` alias.

**D-2. Then the alias goes: 679 uses in 119 files** (`70b6b15b`,
2026-10-04).  "An alias would still declare the duplicate under the
flagged name."  `rename-thy-names.py` rewrote every use across four
sessions to HOL's `relpow_trans`; "same statement up to bound names and
no use instantiates it by name, so the rename is proof-neutral" — the
condition for a pure call-site rename.  Dated records kept the old name.

**D-3. A curried wrapper over a datatype rule** (`0082d0ad`,
2026-10-13).  `ktc_config_eqI` restated `ktc_config.expand` (a
generated name) curried.  Seven uses became `rule ktc_config.expand,
intro conjI` — the call site's *method* changed, not just the name.  An
earlier review had judged the same lemma "not a duplicate" because
`expand` takes one conjunctive premise (history 2026-10-04); the
verdict flipped once a field was renamed.

**D-4. IsaSearch's three wrappers** (`be1f6ecd`, 2026-10-02).
`s_tm_in_Q_tm` -> `valid_mttm_s_in_Q` and `bl_tm_notin_Sigma_tm` ->
`valid_mttm_blank_not_Sigma` (pure renames, including one site in a
downstream session); `mttm_step_functional_of_delta` -> the substrate's
`mttm_step_functional` with "the hypothesis by blast" (an argument
discharged differently).  `card_typedef` deleted in favour of
HOL-Library's `type_definition.card`, which "is in Main only from
Isabelle2026, so Enum_Type imports Cardinality" — **the canonical name
was not visible at the duplicate's call sites until an import was
added**.  Its one use had to switch to `type_definition.Abs_image`.

**D-5. Shadowed duplicates that had drifted** (`b1f859cd`, 2026-09-08;
insight 236).  `Diagonal_Sweeps` declared `sim_val_sim_cell` and
`sim_cell_Gamma`, both already declared by its transitive parent
`Diagonal_Arms`.  Isabelle resolves each citation to the nearest
declaration, so everything built green "for weeks".  The first was a
verbatim re-proof (deleted).  The second was *stronger* in the child
(one hypothesis fewer): "one name denoted two theorems and which one a
proof got depended on where it sat"; callers in `Diagonal_Case1` and
`Diagonal_Validity` passed two `OF` arguments, `Diagonal_Sweeps` one.
Resolution: the parent took the child's stronger statement and proof,
both child copies went, and two call sites dropped an argument.  The
moved prose cited a constant declared above the destination -> build
error, antiquotation demoted.  Detector: `query show NAME` appends
`[+N more match(es)]`, "a shadowing report that reads like pagination";
`hoist-scan.py --shadowed` session-wide found two more, one across a
session boundary from a published entry (`sym4_UNIV`).

**D-6. Definition-level duplicates across entries** (`a0e4fd45`,
2026-10-04).  AR's `nat_to_bits`/`bits_to_nat`/`bit_value` and NTR's
`nat_to_syms`/`syms_to_nat`/`bit_of` were "the same development twice";
NTR's `bwidth` an exact copy of AR's `block_width`.  A new substrate
theory took the generic codec; AR's three functions became
*abbreviations* at fixed digits "so its statements read as before"; seven
duplicated lemmas went and six call sites were repointed (injectivity
needing `BIT0 ~= BIT1` by simp); NTR's `bwidth` became `block_width`
across NTR and NTH with the prose-safe rename.

**D-7. Re-proved metatheory found by accident** (`849d5ace`,
2026-08-25).  `tapes_ok_init/_step/_run` re-proved what
`valid_reach_mttm` already gave.  The lemmas went; the *predicate*
stayed with a one-way bridge lemma because it is not literally the same
concept.

**D-8. `lemmas` aliases invisible to the index** (`4da961ec`,
2026-10-06).  Three DTH names were "plain renames" (`lemmas X = Y`) of
substrate facts, visible only after the query tool started indexing
`lemmas`.  And on a fold (`548950c8`), `dls_endmarker_reads_decode` "was
the substrate's `endmarker_dec_reads` verbatim".

### Edge cases distilled

1. Pure dedup = rename DUP -> CANON at all sites except DUP's own
   definition, then delete DUP.  Valid only if statements match up to
   bound names and no site depends on DUP's exact form (e.g. variable
   order for `of`/`where` instantiation, `[OF ...]` arity, `elim`/`intro`
   use).  D-1/D-3/D-4/D-5 each had sites that were *not* pure.
2. CANON must be visible at every DUP call site; sometimes an import
   must be added (D-4's `Cardinality`), sometimes DUP's home sits above
   CANON's and nothing changes.
3. Shadowing: DUP and CANON may share the *same name*, in different
   theories; "rename" then means delete the child and re-check that the
   parent's statement satisfies every child caller (argument counts).
4. One-to-many maps (`mttm_step_not_halted` -> two names) and per-site
   targets need a site-list mode, not a global map.
5. CANON may be generated (`ktc_config.expand`), library
   (`relpow_trans`, `type_definition.card`), or an alias declared with
   `lemmas`; DUP may be a `lemmas` alias too.
6. Families: a duplicate definition brings its `_def`, `.simps` and
   lemma family; sometimes DUP becomes an `abbreviation` rather than
   disappearing.
7. Choice of survivor: published/ancestor name wins; between peers, the
   name that minimises call-site edits (M-2's acceptance monotonicity).
8. Prose and docs cite DUP: rewrite present-tense docs, keep dated ones.

---

## 5. Dead-code prune

### Episodes

**P-1. Cascade deletion broke definitions and simp rules**
(`e969accd`, 2026-09-24).  First post-construction sweep of the NTH
machine internals, three attempts, the two failures reverted from saved
patches:
- "deleting in cascade removed definitions (`arm_states`, `num_len`):
  query's caller graph counts proof-body references, so a constant used
  only in statements looks dead once its lemmas go" (insight 37: one such
  deletion "broke 48 proofs at once");
- "then [simp] rules went (`mat_pos_R`, `le_stop_R`, ...): the classifier
  read the first line of an entry's span, which is its preamble text, not
  the header."
Third run guarded both, plus a third rule: an entry named in a theory's
prose or a design doc "is part of the explained design" (`ver_iter` was
discussed in five theories).  9 of 47 candidate roots kept; 40 entries,
316 lines removed.  New `prune-rounds.py` deletes only lemma-like kinds
(`LEMMA THEOREM COROLLARY PROPOSITION`) and reports the rest.

**P-2. Baseline rounds: 75 entries, 7,561 lines** (`87a9dd3c`,
2026-09-24).  An abandoned 9,419-line approach.  `prune-rounds.py`:
delete the roots, then repeatedly delete exactly the entries that are
zero-caller *now and were not at the baseline* (a saved `query unused`
taken before the first deletion), until a round finds none — 13 rounds,
then 2.  The baseline matters because the tree already held other dead
code and headline theorems with zero callers; a recursive
`query unused -r` would otherwise flag live lemmas hanging under a dead
chain (insight 37: it flagged 76 entries "including two written that
hour for live callers").  The build passed first time.

**P-3. Deleting by decision, with prose repair** (`88cc3147`,
2026-09-24).  36 entries / 864 lines; "prose naming the deleted entries
was reworded to state the fact instead, in eleven theories (including the
two definitions cited by `\<^const>`, which would have broken the
build)", plus five documents.  `--force-roots` lifts the
prose-mention guard for named roots only.  A name existing in two
sessions (`clock_halt_sink`: "Clock_Decorate's copy only; t/dth's
DTH_Clock copy untouched") — `prune-entries.py` refuses a name that
`query show` finds in more than one theory.

**P-4. A mutually-referencing island** (`0596b4c6`, 2026-10-07).
`trs_of`, `length_trs_of`, `bdecode_transcript`, `bdecode_entry`,
`bdec_state`, `length_read_blocks` "referenced only each other" — each
has callers, but all callers are in the deletion set.  One neighbour
(`bdec_field`) stayed because a live lemma used it.  Prose describing
them ("two decoders", "the round trip below") deleted too.  Similarly
`ea1be199` (2026-07-13): a definition plus three characterisation lemmas
(two `[simp]`) with no external callers, "a self-contained dead island".

**P-5. Prune plans decay; keep-registries** (`ea1be199`, 2026-07-13;
`547ff320`, 2026-06-03).  A 62-candidate prune list from a month earlier
was re-checked with `query callers -r`: 91 zero-caller entries now, but
only one cluster pruned; most had "become members of complete families
or documented general forms" and are kept by recorded decision
(`cleanup.md`, "the durable keep-registry").  `query unused --keep`
spares intentional AFP headline roots.  In `547ff320`, `git log -p -S`
distinguished "used then superseded" from "born unused" before pruning
five lemmas; the family's header comment had to be rewritten from "the
five" to "the three".

**P-6. Wholesale theory deletion and the antiquotation cascade**
(technique 0083, 2026-07-03; `e4bde644`, `52a12336`).  Deleting three
transpose theories and a constant orphaned `@{const ...}`,
`@{thm[source] ...}` and `@{theory Sess.Thy}` antiquotations in
surviving theories' prose — compile-time references, so build failures
"one per rebuild".  Recipe: derive the deleted-name list
programmatically, then a full word-boundary grep (bare names, because an
antiquotation may wrap across lines).

**P-7. Deletes riding along with moves** (`89edf3ab`, `18d30075`).  Two
zero-caller `rtrancl` lemmas dropped during a theory promotion "not
[simp]"; three no-caller lemmas deleted during a substrate demotion,
with one theory's prose citing a deleted one rewritten to cite "the
clause of valid_config_mttm's definition".

### Edge cases distilled

1. Zero callers in a proof-body citation graph is necessary, not
   sufficient: definitions used in statements, `[simp]`/`[intro]` and
   `declare`/`lemmas`-joined rules, and entries cited in prose
   (`\<^const>`, `@{thm}`) or design docs are all "used".
2. Attributes must be read from the *header*, not the first line of the
   span (the preamble).
3. Delete sets: callers inside the set do not count (islands, cascades).
4. Baselines: a cascade must distinguish "orphaned by this change" from
   "already dead" and from "intentionally uncalled" (headlines,
   keep-list).
5. Duplicate names across theories/sessions: resolve by theory, refuse
   ambiguous names.
6. Prose repair is the expensive part; the tool should list every prose
   and doc mention of every deleted name, splitting build-breaking
   (antiquotation) from non-breaking (plain cartouche, markdown).
7. Preamble travels with the entry; a section heading left with no
   entries is a sign of a bad cut.

---

## 6. Requirements implied

### 6.1 `rename`

| # | Requirement | Traced to |
|---|---|---|
| RN1 | Whole-identifier matching on Isabelle tokens (letters, digits, `_`, `'`, `.`-qualification, `\<X>` letter symbols, `\<^sub>`), never substring. | R-3 (`unary_marks`), R-1 (`enc_dir`), R-5 |
| RN2 | Input: `OLD=NEW` pairs or a map file (`#` comments, `@FILE`); reject maps where an OLD is a prefix/substring hazard for another pair's NEW; apply order-independently. | R-1, R-5, R-10 |
| RN3 | Family expansion as an explicit, reported option: `OLD_def`, `OLD.simps/.induct/.cases/.split/.exhaust/.expand/.inject/.distinct`, and optionally names *containing* OLD as a component (`restate_self`); print the expanded map before applying. | R-5 (insight 207), R-3, R-8 |
| RN4 | Qualified forms: `Theory.OLD`, `type.OLD` (constructors after `hide_const (open)`), `Session.Theory`. | R-2, R-7 |
| RN5 | Constructor renames also rename Isar case names (`case OLD`) and case-assumption facts (`using OLD`) that arise from splits on that type, but not user labels (`consider (OLD)`, `case (OLD)` of an `obtain`); requires proof/qed nesting awareness; at minimum, list such sites for review. | R-2 |
| RN6 | Prose classes: rename inside antiquotations (`@{...}`, `\<^const>`, `\<^term>`, `\<^typ>`, `@{theory}`) and code cartouches; *never* inside `\<^emph>`/`\<^bold>` bodies or bare `text`/`\<comment>`/`(* *)` words unless opted in; report every prose hit separately from code hits. | R-3 (`\<^emph>` damage), R-4, R-6 |
| RN7 | Word-shaped OLD detection: warn when OLD is an English word or occurs bare in prose; require `--review`/per-hit confirmation. | R-4 (`back`), R-3, R-6 (`Substrate`) |
| RN8 | Replacement text is literal (backslashes, `\<lambda>`, `$`) — never interpolated into a regex/program. | R-4 (`a5994588`) |
| RN9 | Collision check of each NEW against the session's import closure, sibling sessions in the tree, and optionally an AFP name index; also check NEW is not shadowed by / does not shadow an existing declaration. | R-1 (`relpow_mono`), R-9, R-12 |
| RN10 | LaTeX documents: rename the escaped spelling (`foo\_bar`, `\isasymGamma`, `$_{x}$`) in `document/*.tex`; handle `\newcommand` macro bodies. | R-1 (`rename-tex-names.py`), R-6, R-8 |
| RN11 | Markdown mode with tiers: backtick spans; `--md-prose`; `--keep OLD`; file excludes (dated records, docs about foreign code); report placeholders like `<dir>` inside code spans. | R-1, R-5 |
| RN12 | Theory-rename mode: `git mv`, `theory` header, every `imports` across all sessions (bare and `Session.`-qualified), ROOT `theories` lists, `document/root.tex` (`\input{}` and `\texttt{}` refs), `@{theory}` antiquotations, `.thy` file references in prose; English-word theory names restricted to anchored contexts. | R-5, R-6, M-10 |
| RN13 | Session-rename mode (or explicit refusal with a checklist): ROOT `session` line, children's parent and `sessions` blocks, qualified imports, Makefile; warn about constructor/name clashes via the dot discriminator. | R-7 |
| RN14 | Prefix/pattern renames (`dls_*` -> `dth_*`) expanded to an explicit map from the tree, then RN9 on the result. | R-9, R-1 (`ktm-rename-map.py`) |
| RN15 | Dry run and a residue sweep: after applying, report remaining occurrences of each OLD anywhere (the `old-names-sweep.py` role), and any OLD that matched zero sites (a sign of symbol/ASCII mismatch). | R-1 (missed `Gamma_tm`), R-11 |
| RN16 | Exit status and summary that do not claim success when prose was touched without review: counts per class (code / antiquotation / prose / tex / md). | R-4 ("PASS" while damaging prose) |

### 6.2 Safe `delete` (and dedup)

| # | Requirement | Traced to |
|---|---|---|
| SD1 | Refuse when the entry has callers outside the deletion set; accept a set of names and ignore callers inside it (islands, cascades). `--force` to override. | P-4, P-2 |
| SD2 | "Callers" must include: proof-body citations, statement uses of constants/types, implicit uses via `[simp]`/`[intro]`/`[elim]`/`declare`/`lemmas` bundles (reported as "possibly implicit", refused without `--force`), and antiquotations in prose. | P-1, M-5, P-6 |
| SD3 | Report prose and design-doc mentions (non-breaking) separately from antiquotations (build-breaking); optionally list them as a repair worklist. | P-3, P-6 |
| SD4 | Read attributes from the entry header line, not the span's first line. | P-1 |
| SD5 | Resolve names to a theory; refuse ambiguous names found in several theories/sessions unless qualified (`Theory.name`). | P-3 (`clock_halt_sink`) |
| SD6 | Cascade mode with a baseline: delete roots, then rounds of newly-orphaned lemma-like entries only, never definitions, never baseline-dead, never `--keep` names; print each round. Batch the caller queries (one parse). | P-2, P-1, M-3 (ten-minute serial `callers -r`) |
| SD7 | Span: preamble included by default and shown in dry run; never cross into the next entry's doc block; flag a section heading left with no entries beneath it. | M-9, M-5 |
| SD8 | Dedup `DUP -> CANON`: rename at all sites except DUP's definition, then delete DUP.  Before applying: check CANON is visible at every DUP call site (else name the import needed), compare the two statements (exact / up to bound names / differ) and refuse or warn on "differ"; flag sites that instantiate by variable name (`where`, `of`) or count `OF` arguments. | D-1, D-2, D-4, D-5 |
| SD9 | Dedup variants: CANON may be generated (`T.expand`), library (`relpow_trans`) or a `lemmas` alias; DUP may be a `lemmas` alias; DUP and CANON may share a name (shadow) — then the operation is "delete the shadowing child". | D-3, D-4, D-5, D-8 |
| SD10 | Per-site targets for one-to-many dedups (a site list, not a global map). | D-1 (`mttm_step_not_halted`) |
| SD11 | Dated-record exclusions as in RN11 for doc rewrites. | D-2 |

### 6.3 Visibility-checked `move`

| # | Requirement | Traced to |
|---|---|---|
| VM1 | Callee check: every constant, type, fact and theory the moved block references — in its statement, proof and *prose antiquotations* — must be declared in DEST's import closure (above DEST's insertion point if same theory).  Report each failure with its kind; for a prose antiquotation, suggest demoting to a plain cartouche rather than adding an import. | M-5, M-8, D-5 |
| VM2 | Caller check: every theory citing a moved entry must have DEST in its import closure after the move; for `[simp]`/`[intro]` entries warn that implicit consumers cannot be enumerated. | M-2, M-5 |
| VM3 | Visibility is computed from `imports` closures, never session membership; cross-session imports need the qualified `"Session.Theory"` form; report the exact import line that would fix a failure. | M-1 (insight 206) |
| VM4 | `--with-callees`: compute the closure of same-theory (or same-source) callees that would also have to move; print its size and the alternative (moving the callers instead), since the smaller side is usually right. | M-6, M-7 |
| VM5 | Shadow check at DEST: refuse (or warn) if a moved name is already declared in DEST's import closure or in any theory that imports DEST. | M-5, D-5 |
| VM6 | Cross-session moves: update `@{theory Old.Thy}` antiquotations, ROOT theory lists and `sessions` blocks; for whole-theory moves, the theory-rename machinery of RN12. | M-1, M-10 |
| VM7 | Report imports that become removable at the source/clients and imports that become necessary at clients. | M-4, M-3 |
| VM8 | Preamble handling: move the doc block with the entry; optionally move the enclosing subsection heading and intro text for a group; list prose in the moved block that names source-theory neighbours; optional `--leave-pointer`. | M-2, M-5, M-6, M-3 |
| VM9 | Report attributes of moved entries (`[simp]` etc.) so a promotion's change of simp set is visible. | M-4 |
| VM10 | Name-addressed spans by default; line spans only with a dry-run diff of the boundary lines. | M-9 |
| VM11 | Multi-entry and contiguous-span moves (groups of 7, 23 entries) in one invocation, with all checks over the group as a unit (internal references don't need visibility). | M-5, M-3 |

### 6.4 Cross-cutting

- **One parse, many queries.** The checks above need callers, callees,
  import closures and prose references for many names at once; the
  observed cost of per-name subprocesses (ten minutes for 290 names) is
  prohibitive.
- **Dry run is the default posture**, with output grouped by risk
  class; the observed failures were silent (shadows, prose damage) far
  more often than loud.
- **Verification hint**: after any rename or move that touched prose or
  `document/*.tex`, the proof build is not sufficient; say so and name
  the document build.
- **Keep-lists and dated-file excludes as configuration**, not flags
  re-typed per call (`query unused --keep`, `cleanup.md`, history/journal
  excludes).
