# `isabelle-block` extraction — background inventory

Surveyed 2026-10-15 on `stac/wip` (HEAD `f12c6062`), with `isabelle-query` 0.9.7
and `isabelle-layout` 0.2.2 installed in `/Users/as456/projects/ndtht/venv`.
Read-only. Nothing was run except `--help` and `query` reads.

`bin/block.py`: 1308 lines, 8 commits. First was `ad77b2ca` (2026-09-07, "one block
tool, because six of them were one tool"). Last was `37b8b9c4` (2026-10-15, reargs,
`--expect`, `--except`). It has ten verbs: move, copy, delete, emit, replace, sub,
resub, reargs, split, merge. Name addressing goes through
`isabelle_query.api.parse_theory`. There is a fixture `--selftest`.
`history/20261015-230902.md` records the open thread: a fourth `ott2/isabelle-*`
package was recommended as its home, and three verbs are proposed (`rename`, a
caller-checked `delete`, a visibility-checked `move`).

---

## 1. Adjacent scripts

Notation: **C** = commits touching the file (count, date of last). **Refs** = who
cites it, outside `bin/` itself and outside `history/` unless history is the only
citer.

### 1.1 `bin/rename-thy-names.py`: whole-identifier, prose-aware rename (215 lines)

- **Purpose.** Rename whole Isabelle identifiers from an explicit map without touching
  English prose. Written for the MAT `restate`/`unary` renames and the 280-name ktm
  rename.
- **CLI.** `rename-thy-names.py MAP FILE... [--dry-run] [--md-prose] [--keep OLD]...`,
  plus `@FILE` (argparse `fromfile_prefix_chars`).
  - **MAP format:** one `OLD NEW` pair per line, whitespace-separated, with `#`
    comments. It is the same format `ktm-rename-map.py` emits (tab-separated) and
    `rename-tex-names.py` consumes.
  - Prints per-file counts and `PASS: renamed N occurrence(s) in M file(s)`.
- **Algorithm.**
  - **Token rule:** one alternation regex, longest-first:
    `(?<![\w'])(OLD1|OLD2|...)(?![\w'])`. It is prime-aware.
    - `restate` matches inside `M.restate` and `restate.simps`, because `.` is not a
      word char.
    - It does not match `restated`, `restate_def` or `unary_marks`.
  - **`_def` / `.simps`:** `_def` and the other underscore families are *not* derived.
    The docstring says "list every family member you mean, so the change set is exactly
    the map". `ktm-rename-map.py` gets them automatically by enumerating every
    identifier in the tree. The dotted families come for free.
  - **Segmenter (`segments`), own lexer:**
    - **Code:** everything outside prose, *including* `"..."` inner-syntax strings,
      which are skipped as opaque and so stay "code".
    - **Prose:**
      - the cartouche body after `text|txt|text_raw|chapter|section|subsection|subsubsection|paragraph|subparagraph|title`
        (with an optional `(in loc)`-style parenthetical);
      - the body after `\<comment>`;
      - `(* *)` comments, nesting-aware.
    - **Inside prose (`prose()`):** a nested cartouche at depth 2 (for example
      `\<^const>\<open>foo\<close>` or `\<open>foo\<close>`) and any `@{...}`
      antiquotation (brace-balanced) count as code. Depth-1 text is English and is left
      alone.
    - The function asserts `''.join(pieces) == src`, a lossless partition.
  - **Markdown:** renames only inside single-line backtick spans
    (`re.split(r'(`[^`\n]*`)')`). `--md-prose` also renames bare prose for maps of
    non-word names. `--keep OLD` holds a word-shaped entry back to code spans only.
- **Worth porting.**
  - The lossless code/prose partition with the "nested cartouche or antiquotation is a
    reference" rule.
  - The map-file format.
  - Longest-first alternation, so the change set is exactly the map.
  - The markdown backtick rule, together with `--md-prose`/`--keep`.
- **Gets wrong / misses.**
  1. **Symbol suffixes:** `(?<![\w'])foo(?![\w'])` matches `foo` inside
     `foo\<^sub>1` or `foo\<gamma>`. `\` is a non-word char, but in Isabelle that is a
     different identifier.
  2. **No collision check** that NEW is free. `ktm-rename-map.py` has its own.
  3. **No derived-name expansion:** `_def`, `_def_raw`, `_eq`, `.cases` on a
     record/datatype, and so on.
  4. **No namespace awareness.** A local Isar binder, a bound variable or a case name
     spelled like OLD is renamed too. That was the ktm phase-2 lesson: a constructor
     name lives on as a `consider (R)` case name and its fact.
  5. **A fourth prose lexer** in the repo. `block.py._prose_mask`, `prose-token.py`
    and `lint-isar-names.blank_dead_source` each have their own. None of them uses
    `TheorySection.text_blocks/heading_spans/nonisar_spans`, except `block.py`.
  6. `.tex` and ROOT are not handled (that is `rename-tex-names.py`).
  7. Single-line backticks only, and fenced blocks are prose.
     `insights/289` (2026-10-05) documents the remaining damage: ``t/<dir>/``,
     ``build-<dir>``, ``pcommit_read/write/dir``.
- **C:** 2 (`04c0685d` 2026-10-03, `b44da50b` 2026-10-05).
- **Refs:** `insights/289.md` (prescribes it as *the* tool for word-shaped renames),
  `afp-submission/MAT-revision.md` (×2), `bin/ktm-rename-map.py`,
  `bin/rename-tex-names.py`, `history/20261004-002708`, `history/20261005-192325`.
- **Recommendation: PORT. It is the core of the `rename` verb.** Replace its lexer
  with the `isabelle_query.api` spans, then add:
  - symbol-suffix-aware boundaries (reuse the logic of `query`'s
    `_isa_word_pattern`, inverted for renames);
  - derived-family expansion (`foo` → `foo_def`, etc., opt-in);
  - a NEW-is-free check against the session namespace;
  - `--expect`/`--except` from `block.py`.

  Its two documented markdown failure modes become fixtures.

### 1.2 `bin/token-rename.py`: line-scoped regex rename in one file (72 lines)

- **Purpose:** a "disciplined `sed`": one file, a regex `--pattern` and a `--replace`,
  with `--exclude L,L` / `--only L,L` line lists and `--dry-run` printing a `-`/`+`
  diff per line.
- **Notable:** line allow/deny lists for a token whose sense depends on the line.
  This was the bit-width `k`→`b` sweep, used with `prose-token.py` to pick lines
  (technique 0087).
- **Wrong / misses:** no regions by name, no prose awareness, one file. It is
  functionally `block.py resub FILE:L` with several single-line regions, or with
  `--except`.
- **C:** 3 (content 2026-07-06; `50709001` 2026-07-13 restored +x).
- **Refs:** `techniques/0087.md` (×2), `history/20260706-*`.
- **Recommendation: RETIRE.** `resub` already covers it: a multi-region target list
  stands in for `--only`, and `--dry-run` exists. Before deleting, update
  technique 0087 to `block.py resub` (or a future `rename --prose-only`). The
  `-`/`+` dry-run diff display is worth porting as `--dry-run --diff`.

### 1.3 `bin/rename-theories.py`: theory-file rename within one session dir (72 lines)

- **CLI:** `rename-theories.py --dir DIR OLD=NEW ...`
- **Algorithm:**
  1. `git mv DIR/OLD.thy DIR/NEW.thy`.
  2. Over every `*.thy` (skipping `output/`), `ROOT` and `*.tex` under DIR, apply
     `\bOLD\b → NEW`. This catches `theory`/`imports`, `@{theory Sess.OLD}` and
     `\<open>OLD\<close>`.
  3. It refuses a pair when OLD is a substring of any NEW, which makes the
     replacements order-independent.
- **Wrong / misses:**
  - Scope is one directory. Importers in *other* sessions (`imports
    "Sess.OLD"`) are missed, as are `.md` docs.
  - `\b` is wrong at `'` and at symbol boundaries.
  - Prose is renamed too, which is acceptable for CamelCase theory names and wrong
    for a word-shaped one.
  - It shells to `git mv`, so the tool depends on git.
  - There is no check that NEW is free across the session or the AFP; that is
    `afp-name-clash.py`'s territory.
- **C:** 1 (`31b7a8b1` 2026-07-03).
- **Refs:** `history/20260703-103105.md` only.
- **Recommendation: PORT as `rename --theory`** (or a `rename-theory` verb). Use
  `isabelle_layout.iter_sessions` / `session_theories` for the importer set across
  all sessions under the root, and `parse_thy_imports` to find the `imports` tokens
  (bare and session-qualified). The OLD-in-NEW refusal is a good fixture.

### 1.4 `bin/ktm-rename-map.py`: generate a rename map from the tree (77 lines)

- **Purpose:** one-off generator for the 2026-10-04 ktm scheme. Rules:
  - `*mttm*`→`*ktm*`;
  - `mt_*`→`ktc_*`;
  - `X_tm`→`X_ktm` as a name component;
  - `dir`→`move` (type, `go_dir*`, `finite_UNIV_dir` only);
  - `FIXED` exceptions.
- **Notable logic:**
  - It enumerates *every identifier* in `t/*/*.thy` with
    `IDENT = (?:[A-Za-z]|SYM)(?:[A-Za-z0-9_']|SYM|\<^sub>)*`, an Isabelle-letter-symbol
    aware identifier regex, so derived names (`_def`, lemma families) are included.
  - Output is `OLD\tNEW` lines on stdout.
  - **Collision check:** it fails if any NEW is already an identifier in the tree or
    two OLDs map to one NEW, with hand-listed term/type exceptions (`ktm`, `move`).
- **Wrong / misses:** the first version caught `\<open>` as a name char and `dir`
  inside `enc_dir` (`history/20261004-230005`). The tree glob is hard-coded and
  NDTHT-specific.
- **C:** 1 (`8ba4f4e2` 2026-10-04).
- **Refs:** `afp-submission/MAT-revision.md`, `history/20261004-230005`.
- **Recommendation: LEAVE IN NDTHT** (the scheme is project-specific). **FOLD its
  collision check into `rename`**: refuse when NEW is already declared in a theory
  visible to any site, or when two OLDs map to one NEW. Keep a rule-driven map
  generator out of the package.

### 1.5 `bin/rename-base-theories.sh`: one-off `git mv` plus perl (70 lines)

- **Purpose:** the 2026-07-13 `Multitape_` prefix rename of six base theories.
  Compound names were replaced literally. The bare word `Substrate` was replaced only
  in four mechanical contexts:
  - `^theory Substrate$`;
  - `imports Substrate`;
  - `Multitape_TM_Substrate.Substrate\b`;
  - `Substrate.thy`.

  Prose cartouches, the ROOT theory-list entry and root.tex `\texttt{}` were done by
  hand.
- **Notable:** an explicit list of syntactic contexts in which a word-shaped theory
  name is a reference: header, `imports`, session-qualified, file reference. This is
  exactly the discriminator approach of `insights/226`.
- **C:** 1 (`5f5d4aa3` 2026-07-13).
- **Refs:** `history/20260713-174417` only.
- **Recommendation: RETIRE** (spent). Port the *context list* into the theory-rename
  verb as the rule for word-shaped theory names, and keep it as a fixture case
  (theory `Substrate` vs the noun "substrate").

### 1.6 `bin/rename-tex-names.py`: apply a rename map to LaTeX documents (63 lines)

- **Purpose:** rewrite map names in `root.tex` and `glossary.tex` in LaTeX spelling:
  - `_`→`\_`;
  - `\<X>`→`\isasymX`;
  - `\<^sub>c`→`$_{c}$`.
- **Token rule:** `(?<![A-Za-z0-9])(?<!\\_)(OLD)(?![A-Za-z0-9'])(?!\\_)`, so
  `valid\_ktm` is not renamed inside `valid\_ktm\_iff`. It renames in prose too, on
  the assumption that names in a document are always set as names.
- **Wrong / misses:**
  - It is only safe for maps of non-word names.
  - It does not handle `\isa{...}`-wrapped spellings of other shapes, or
    `\texttt{}` with `\textunderscore`.
- **C:** 1 (`8ba4f4e2` 2026-10-04).
- **Refs:** `afp-submission/MAT-revision.md`, `history/20261004-230005`.
- **Recommendation: PORT into `rename`** as the `.tex` file-type handler, the same
  way `.md` gets the backtick rule. Name renames then cover `.thy`/`.md`/`.tex` in
  one map-driven pass.

### 1.7 `bin/rename-isabelle-symbols.py`: hard-coded symbol-to-ASCII map (191 lines)

- **Purpose:** the 2026-05-20 audit that replaced 25 declared identifiers and 23 local
  binders containing `\<delta>`/`\<Gamma>`/`\<Sigma>`. The map (`RENAMES`) is in the
  file. `--scope theory|docs|both`, with `DOC_EXCLUDES` (history, isa, analysis,
  `.claude`, …).
- **Algorithm:** plain `str.replace`, longest-first. It is idempotent. `_def` follows
  because it shares the textual base.
- **Wrong / misses:**
  - Substring replace with no boundaries, so it is safe only because these OLDs are
    symbol-bearing and distinctive.
  - The hard-coded `t/generic/` era map is stale: it still names `valid_mttm_*`,
    which the ktm rename changed to `valid_ktm_*`.
  - The memory file still tells agents to "re-run it" if a symbol name reappears.
    That would no longer find anything, because the targets have been renamed twice.
- **C:** 2 (`c7fb39c3` 2026-05-20, `6f50d2fa` 2026-06-08).
- **Refs:** `.claude/memory/feedback_no_isabelle_symbols_in_names.md` (×2: "the rename
  script is at …", "re-run `bin/rename-isabelle-symbols.py` — it's idempotent"),
  `history/20260616-181748`.
- **Recommendation: RETIRE** (spent; the map is stale). Update the memory file to
  point at `block rename MAP`. The *auditor* half (`audit-isar-binding-names.py`, see
  §1.14) could become a `block` or `query` lint, but it is not a block verb.

### 1.8 `bin/rename-wrap-in-docs.py`: the 2026-07-03 wrap rename, applied to docs (102 lines)

- **Purpose:** 10 theory renames plus 54 lemma/constant `_B`/`_tr` tag strips, as a
  dict in the file. It was applied to `.md` with
  `\bOLD(?![A-Za-z0-9])`, a "derived-fact lookahead" so that `wrap_delta_B_cases`
  is renamed as itself and not as the stem. It deliberately contains only *current*
  names, so historical mentions survive. "Do NOT run over `history/`."
- **Wrong / misses:**
  - Note the lookahead: `(?![A-Za-z0-9])` lets `_` follow. So `wrap_delta_B` *would*
    match inside `wrap_delta_B_foo` if that were not itself in the map. Longest-first
    ordering is the only guard.
  - It prints counts but no PASS line.
- **C:** 1 (`55b8543b` 2026-07-03).
- **Refs:** `history/20260703-103105` only.
- **Recommendation: RETIRE** (spent). Its one durable idea is the *file-scope
  exclusion* for chronology (`history/`) and for documents about another development.
  That is the same point as `insights/148` and `insights/289` 2026-10-05: put
  `--exclude-file GLOB` on `rename`, or make the caller pass an explicit file list.

### 1.9 `bin/prose-token.py`: report regex matches inside prose only (117 lines)

- **Purpose:** after a code-level migration, find stale tokens surviving in prose.
- **Prose definition:** the body of a cartouche opened by
  `text|txt|section|subsection|subsubsection|paragraph|chapter|text_raw` or
  `\<comment>`, with nested cartouches inheriting the outermost opener's prose-ness;
  plus `(* *)`.
- **CLI:** `prose-token.py FILE... [--pattern REGEX]` (default `\bk\b`). It prints
  `FILE:LINE: text` and totals.
- **Notable:** its prose rule differs from `rename-thy-names.py`. Here a nested
  cartouche *inherits* prose-ness; there it is code. Both are right for their
  question: "where can a stale word survive?" versus "where is a name a reference?"
- **Wrong / misses:**
  - Its own lexer; it ignores `\<^cancel>` and `@{...}`.
  - It does not know `query grep --with-comments` exists, which covers most of its use.
- **C:** 2 (content 2026-07-06; +x fix 2026-07-13).
- **Refs:** `techniques/0087.md`, `history/20260706-010847`.
- **Recommendation: RETIRE in favour of `query grep --with-comments`** if `query`
  gains a prose-only mode (`--comments only` exists as a `CmdFlags` field,
  `comments: on/off/only`; check whether `grep` exposes it). Otherwise fold it into
  `rename --dry-run --prose-only` as the report mode. Either way, the
  "inherits vs reference" distinction must be a documented option.

### 1.10 `bin/prune-entries.py`: delete named entries via `block.py delete` (77 lines)

- **CLI:** `prune-entries.py [--dry-run] NAME... | @FILE`.
- **Algorithm:**
  1. For each NAME, run `query show NAME` and regex the header
     `^--- NAME (TAG) — (THY.thy)`.
  2. Refuse if the name is found in zero or more than one theory.
  3. Resolve the path with `rglob` under `t/`.
  4. Subprocess `bin/block.py delete PATH:NAME`.
  5. Print `PASS: all deleted` or `FAIL: N name(s) not deleted`.
- **Deliberately checks nothing about deadness** ("that is the audit's job, and the
  build's").
- **Wrong / misses:**
  - It parses human-oriented `query show` text.
  - It shells out to `block.py`.
  - It has a hard-coded `t/`.
  - It has no caller check: exactly the gap the proposed `delete` closes.
- **C:** 1 (`07ad3774` 2026-09-24).
- **Refs:** `bin/prune-rounds.py`, `insights/37.md`, `history/20260924-091339`.
- **Recommendation: PORT as `block delete NAME...`** with no FILE, resolved
  session-wide through `parse_root` (or `query show` until a library lookup exists),
  plus the new caller refusal. Then retire this script.

### 1.11 `bin/prune-rounds.py` + `bin/unused_lib.py` + `bin/classify-unused.py`: baseline-rounds dead-code pruning

- **`prune-rounds.py`** (135 lines). CLI:
  `[--dry-run] [--force-roots] SESSION_DIR BASELINE ROOT...`.
  - It deletes the roots, then loops. Each round:
    1. runs `query -R SESSION_DIR unused`;
    2. collects the entries that are zero-caller now and were not in the BASELINE
       file (saved `query unused` output);
    3. deletes them via `prune-entries.py`;
    4. stops when a round finds none.
  - **Guards:**
    - only `PRUNABLE = {LEMMA, THEOREM, COROLLARY, PROPOSITION}` are deleted;
      definitions are reported, never deleted;
    - `unused_lib.implicit_use` skips an entry with `[attr]` on its header line or
      named in a `declare`/`lemmas` block anywhere in the session;
    - `unused_lib.mentioned` skips an entry named outside its own span, in session
      prose or in six hard-coded design docs (`CLAUDE.md`, `nth-design.md`, …).
      `--force-roots` lifts this for the roots only.
- **`unused_lib.py`** (82 lines).
  - `locate(session_dir, name)` parses `query show`'s `[src A..B` header.
  - `implicit_use` and `mentioned` as above.
- **`classify-unused.py`:** sorts `query unused --roots` into ATTR / THEOREM / LEMMA.
  Read-only.
- **Worth porting** (they are exactly the refusal conditions a safe `delete NAME`
  needs):
  - "declared with an attribute or joined via `declare`/`lemmas`" means implicit use,
    so warn or refuse;
  - "named in prose / docs" means a dangling explanation, so warn;
  - "definition with statement-level uses" means refuse.
- **Possible staleness:** `prune-rounds`' comment says `query`'s graph "counts
  proof-body references, so a definition used only in *statements* looks
  zero-caller". In 0.9.7, `_build_call_graph` scans every live line of every entry
  (statements included), excluding only the defining span, and `unused` passes
  `derived=True` (so `foo_def` keeps `foo` alive). The 48-proof breakage in
  `insights/37` may predate that. Re-test before porting the "never delete
  definitions" rule as a hard refusal.
- **C:** prune-rounds 3 (last `88cc3147` 2026-09-24); unused_lib 1 (2026-09-24);
  classify-unused 1 (2026-09-24).
- **Refs:** `insights/37.md` (all three), `nth-journal.md` (classify-unused),
  `history/20260924-*`.
- **Recommendation:**
  - **FOLD `implicit_use` + `mentioned` into `delete`'s refusal logic.** `mentioned`
    becomes a warning, configurable with a docs glob instead of NDTHT's six files.
  - **LEAVE `prune-rounds` / `classify-unused` IN NDTHT** as workflow drivers. Later
    they could become a `block prune --baseline` verb, but the baseline-rounds method
    is a workflow, not surgery.

### 1.12 `bin/span-overreach-scan.py`: regression check for name-resolved spans (48 lines)

- **Purpose:** for every entry under `t/`, check
  `body_end_line or thy_end < next entry's preamble-or-start`. The expected answer is
  0. Re-run after an `isabelle-query` upgrade.
- **Notable:** its own docstring says this is what makes `block.py delete FILE:NAME`
  safe.
- **It is now redundant with the API.** `Entry.cut_span` (0.9.x) is documented as
  "the span a tool *writes through* … guaranteed to stop before the next entry", and
  is `None` when `shares_line`. `block.py.resolve_entry` re-implements the clip and
  does **not** handle `shares_line` (two declarations on one line, for example
  `consts F G`), so a delete there would cut both.
- **C:** 2 (`ad77b2ca` 2026-09-07, `d696edf4` 2026-09-08).
- **Refs:** `bin/block.py` (×2) only.
- **Recommendation: RETIRE once `block` switches to `Entry.cut_span`.** The guarantee
  then belongs to upstream (`isabelle-query`'s own tests). Keep one fixture in
  `block`'s test suite for a doc block between two lemmas, and add one for
  `shares_line`.

### 1.13 `bin/lint-isar-names.py`: Isar command words as labels and case names (276 lines)

Only the identifier/label-safety part is covered here.

- **Rules:**
  - `WORD:` (not `::`) in label position;
  - `(WORD)` after `consider` or `|`;
  - both over live source, with `blank_dead_source` blanking strings, cartouches and
    `(* *)`.
- **`COMMAND_WORDS`** is a hand-maintained union over Isabelle versions: `options` is
  a keyword only in the dev version (`00a3ddc9`, 2026-10-15), plus `nonterminal` and
  `setup`.
- **Has `--selftest`** with five collisions and six prose decoys.
- **Bearing on `rename`:** a rename whose NEW is an Isar command word (`back`,
  `write`, `options`, `setup`, `nonterminal`, …) yields a parse error that names
  neither the word nor the line (`insights/289`). `rename` should refuse such a NEW,
  or at least warn, when it is used in label or case position.
- **C:** 5 (last `00a3ddc9` 2026-10-15).
- **Refs:** `CLAUDE.md`, `Makefile` (×4; inside `lint-latex`'s recipe), `insights/289`,
  `nth-journal.md`, several `history/`.
- **Recommendation: LEAVE IN NDTHT** (it is a build gate). **FOLD the
  `COMMAND_WORDS` table, or better a keyword table derived from `query`'s
  `_isabelle_namespace.KEYWORDS`, into `rename`'s NEW-name check.** Ask upstream
  whether `isabelle_query` can export its keyword set publicly (see §2.5).

### 1.14 Other `bin/` scripts that move, rename, prune, insert or deduplicate

| script | purpose / notable logic | C (last) | refs | recommendation |
|---|---|---|---|---|
| `insert-after.py` (114) | Insert INSERT_FILE after every line exactly equal to ANCHOR_FILE's line; `--expect N`, `--dry-run`; both arguments are files *because of tcsh backslash doubling*. Its docstring: "`bin/block.py` … has no insert verb". | 1 (2026-09-16) | `history/20260916-155614` | **PORT as `block insert` (or `copy`-from-file `--after-each LINE --expect N`).** It is the one surgery operation `block` lacks. |
| `insert-hyp.py` (74) | Insert one `--line` after every `--after` anchor, with `--skip` by entry name (uses `parse_theory` to map lines to entries). Idempotent. **Bug:** it calls `parse_theory(text, Path(file))`, which passes the source text as the theory *name*. | 1 (2026-09-11) | `history/20260911-220450` | **FOLD into the same insert verb** (`--except NAME` is already `block`'s mechanism). Then retire. |
| `reindent.py` (72) | Shift a line range by N columns; refuses to eat non-space characters. Uses the same span grammar as `block.py`. | 1 (2026-09-20) | none outside history | **PORT as `block indent FILE:REGION N`.** It is block surgery and gets name addressing for free. |
| `hoist-scan.py` (325) | Lowest legal home of each entry in the import DAG (from `query callees --names --reach closure` + `query deps -r`, with an intra-theory fixpoint); `--visible-to THY`. Caveats: prose antiquotation references are invisible, and `[simp]` consumers cannot be enumerated. | 5 (2026-09-08) | `nth-design.md` ×2, `insights/192,236`, history | **LEAVE IN NDTHT** (an analysis). **Its visibility computation is the same one `move`'s check needs; reuse the approach**, and note it parses CLI text output. |
| `split-plan.py` (217) | Classify the cross-group citation edges of a proposed split (line-span groups). It also scans prose antiquotations (`ANTIQ = \\<\^(?:const|term|prop|typ)>\\<open>…\\<close>`), because a forward `\<^const>` breaks the build and `callers` cannot see it. | 2 (2026-08-30) | `.claude/skills/split-theory/SKILL.md`, `insights/163,192`, `nth-design.md` | **FOLD its antiquotation scan into `move`'s check** (a moved entry cited by `\<^const>` in prose above it at DEST is a forward reference). Keep `split-plan` as a pre-`split` planner, or make it `block split --plan`. |
| `dead-locals.py` (95) | Local Isar facts bound and never used in a `FILE:REGION`; heuristic. | 1 (2026-09-20) | `upstream/query-unused-locals.md` (posted as isabelle-query #12) | **LEAVE.** Upstream asked to own it. |
| `audit-isar-binding-names.py` (73) | Reports local binders embedding `\<X>`. | 2 (2026-06-08) | memory `feedback_no_isabelle_symbols_in_names` | **LEAVE / RETIRE.** Not surgery. |
| `old-names-sweep.py` (56) | Hard-coded post-ktm-rename stale-name report over a markdown file list, split into backticked and bare mentions; PASS/FAIL. | 1 (2026-10-05) | none | **RETIRE.** Superseded by `rename --dry-run` over the docs, with the same backtick split. |
| `msb-carry-sweep.py` (196), `carry-clause.py` (206), `flip-field-order.py`, `ar-thread-in-sub*.py`, `migrate-diag-*.py` (3) | One-off, project-specific migration rewriters with fixed target files and name lists. They are the motivating cases for `reargs`, `resub` and the insert verb. | 1–2 each | history only | **LEAVE (spent) or RETIRE.** Candidate *fixtures*: `migrate-diag-constructor.py`'s "rewrite `f kc` → `f C` but leave fact labels named `kc`" is a good `reargs`/`rename` fixture. |
| `substrate-clients.py` (88), `afp-names-diff.py` (75), `afp-name-clash.py` (348) | Analyses: per-entry downstream sessions via `callers -r -f tsv`; published-vs-revised name diff via `api.parse_theory`; AFP-wide genericness of our names. | 2026-10-11 / 10-06 / earlier | MAT docs | **LEAVE.** `afp-name-clash`'s namespace logic is a possible `rename --check-afp` later. |
| `dup-measure.sh`, `find-shim-consumers.sh`, `kb-renumber-merge.py` | Measurement, a spent grep, and KB (non-thy) renumbering. | — | — | Out of scope. |

### 1.15 Retired predecessors, absorbed into `block.py` on 2026-09-08 (`17e5cbcb`)

`move-block.py`, `replace-range.py`, `sub-range.sh`, `rename-ident.sh`,
`split-theory.py` and `merge-into-base.py` (`port-tr-to-B.py` had already been merged
into `move-block.py` on 2026-07-02). Live non-history docs that still name them:

- `ntr-count-refactor.md:301,370` (`move-block.py`, line 371 notes "now `bin/block.py
  move`");
- `pide-mcp-evaluation.md:69,104` (`move-block.py`);
- `linear-speedup-faithfulness.md:636,683` (`move-block.py … --transform`);
- `is/030-state-space.md` ×5 and `wrap-design.md` (`sub-range`);
- `textblock-attribution-design.md` (`move-block`).

`insights/318` says to rewrite reach-for surfaces and leave narrative. These are spent
or frozen memos, so they are probably fine as they are.

---

## 2. `isabelle-query` / `isabelle-layout` surfaces for the new verbs

### 2.1 `isabelle_query.api` (0.9.7): the four public names

`__all__ = ["Entry", "TheorySection", "parse_root", "parse_theory"]`. Policy: a
breaking change takes the minor slot.

- **`parse_theory(theory, path, lines=None, *, root=None) -> TheorySection`.**
  - Parses one file.
  - **Pass `root=`** (the `query -R` directory) to build the session-wide custom
    keyword table from every header and to fill `sec.session`. `block.py`
    currently refuses any file declaring `keywords` instead. It should pass `root`.
  - It saves and restores the module-global keyword table.
- **`parse_root(root) -> list[TheorySection]`.** Every theory of every ROOT session,
  plus the transitive in-entry import closure, de-duplicated by resolved path. It
  raises `ValueError` on an empty result.
- **`Entry` fields:**
  - `tag` (DEF, FUN, LEMMA, THEOREM, DATATYPE, TYPE, RECORD, AXIOM, ABBREV, LEMMAS, …);
  - `name`, `text`, `theory`;
  - `thy_line`, `decl_end_line`, `proof_line`;
  - `thy_end`: the span end. It stops before the next entry's `src_start` and
    includes trailing blanks.
  - `body_end_line`: the closing `qed`/`by`/`.`.
  - `preamble: (a,b) | None`: the `text` block "immediately preceding … within ~3
    blank lines".
  - `annotations` (`(line, content, kind∈{decl,statement,proof})`);
  - `bindings` (`(name, kind)`): extra names one command binds (conjunct, rule,
    sibling, constructor, discriminator, selector, field, assumption, definition,
    note);
  - `blocks`: the enclosing named locale or context;
  - `in_target`;
  - `shares_line`.
  - Properties: `target`, `bound_names`, `roadmap`, `src_start`, **`cut_span`**,
    `line_count`.
  - **`cut_span`** = `(src_start, min(body_end_line or thy_end, thy_end))`, or `None`
    if `shares_line` or unplaced. It is documented as *the* span a delete or move
    tool writes through. `block.py.resolve_entry` should become `e.cut_span` and
    handle `None` with a refusal.
- **`TheorySection` fields:**
  - `theory`, `path`, `entries`, `thy_lines`;
  - `outline` (`(kind, title, line)`);
  - `text_blocks`, `heading_spans`, `comment_ranges`, `nonisar_ranges`
    (line ranges);
  - `nonisar_spans`, `inner_spans` (`{line: [(c0, c1)]}`, column level);
  - `is_thy`, `session`, `line_window`.
  - Methods: `source()`, `slice(a,b)`; `live_source()` blanks noise (comments,
    cartouches, `\<^cancel>`, inline ML) and keeps terms; `outer_source()` also
    blanks terms (Isar command position). Both are line-preserving and
    column-preserving.
  - **These replace all four private prose lexers** (§1.1, 1.9, 1.13 and
    `block.py._prose_mask`). For `rename`:
    - "code" means `live_source()` non-blank;
    - "prose reference" means an antiquotation or nested cartouche inside
      `text_blocks`/`nonisar_spans`, which still needs a small cartouche-depth walk
      over the prose spans;
    - "inner-syntax term" means `inner_spans`.

### 2.2 Callers and callees: no public library surface

- **The library has only private functions.**
  - `isabelle_query.graph._build_call_graph(sections, drop_upto, derived, reach) ->
    model.CallGraph{callers, callees, all_names, toplevel}` builds the whole graph.
  - `isabelle_query.commands._find_callers(sections, name, external, reach)` is the
    single-name scan behind `query callers NAME`.
  - `graph.site_filter` and `graph._Visibility` are also private.
  - `model.CallGraph` is a class in a non-API module.
- **CLI surfaces that are machine-readable today:**
  - `query callers -f tsv NAME...`: one row per caller, no header:
    `subject, caller, tag, theory, session, depth, locus` (for example
    `enumerable_sym4	clock_decorate_NTIME	LEMMA	Enumerable	Nondeterministic_Time_Hierarchy	1	Enumerable:70`).
    `-r` gives the transitive closure with depth. `-c` gives `subject<TAB>count`.
    Several names make one table, with the graph built once (0.9.4).
    - Known gap, drafted and not posted
      (`upstream/query-callers-batch.md`): `<toplevel>` callers (`declare`,
      `lemmas`, `instance`) have empty theory and session columns.
  - `query callees` has **no `-f tsv`**: text only, or `--names`.
  - `query graph citation -f json` / `query graph imports -f json`: the whole graph
    as `{"edges": [[from, to], ...], ...}`. For imports the edge is
    `[importer, imported]`. `--theory THY` confines it.
  - `query deps -r THY` / `query uses -r THY`: import closure, as human text only
    (`NAME (N src lines, M entries) [depth k]`), with no tsv.

### 2.3 How `query callers` decides a reference

`_find_callers` with `_isa_word_pattern(name)`:

- **Token rule:**
  - prime-aware boundaries (`'` counts as an identifier char);
  - not inside a `\<...>` symbol body (`le` does not match in `\<le>`);
  - symbol-bearing names are not glued to a following symbol;
  - quoted special-character names only inside `"..."`.
  - A plain ASCII run abutting a symbol (`foo` in `foo\<gamma>`) **is** a match.
- **Qualified names:** `.` is a boundary, so `Theory.foo`, `M.foo`, `foo.simps`,
  `foo.induct` all count as `foo`. It does not resolve which `foo`; that is what
  visibility is for.
- **`_def`:** `callers foo` does **not** count `foo_def` (a different fact;
  `test_substring_is_not_a_call`). Only `unused` turns on `derived=True`
  (`foo_def`/`foo_defs` → `foo`). **A caller-checked `delete foo` of a definition
  must therefore also query `foo_def` (and `foo.simps`/`.cases` for FUN/DATATYPE are
  already covered by the dot rule).**
- **Skipped:**
  - lines in `text_blocks`, headings and comment ranges (`_noise_ranges`);
  - the defining entry's own span `thy_line..thy_end` (and the parent span for
    bound names);
  - mentions only inside `@{text|thm|term|const foo}`;
  - the redacted parts of `live_source()`;
  - a name shadowing a proof method or attribute, unless it is in citation position.
- **Implication for `delete`:** prose antiquotations (`\<^const>foo`,
  `@{thm foo}`, `@{const foo}` in `text`) are **not callers**, but they *are* build
  dependencies (`insights/192`, `insights/201`; `split-plan.py` scans them itself).
  Implicit uses (`[simp]`, `declare … [simp]`, `lemmas bundle = …`, `[intro]`) are
  invisible. Both need separate checks.
- **Visibility (`--reach closure`, the default):** a hit in theory T is attributed to
  the declaration only if T's in-project import closure contains a theory declaring
  the name (`_Visibility.sees`). An unreadable header means everything is visible.
  Known bug, posted as isabelle-query #18 (2026-10-07,
  `upstream/query-callees-name-collision.md`): `callees` attributes a colliding name
  (`sim_tape` in NTH and in NTR) to a declaration the citer cannot see.
- **Scope:** "who calls X" is corpus-global under `-R`/marker. `--external` skips the
  defining theory.
- **Call graph nodes:** only `_CITABLE_TAGS = {LEMMA, THEOREM, LEMMAS, FUN, DEF,
  ABBREV}`. DATATYPE, TYPE and RECORD entries are never nodes, so `callers -r` /
  `unused` say nothing about them. The non-recursive single-name `callers` still
  scans for any name.

### 2.4 `isabelle_layout` 0.2.2: what it gives for visibility

Public:

- `SessionInfo` with `name`, `root_path`, `in_subdir`, `parent`, `used_sessions`,
  `directories`, `theories`, `session_dir`;
- `discover_roots`, `iter_sessions(root_dir)`, `parse_root_sessions`;
- `resolve_session_theory`, `resolve_base_logic`;
- `iter_thy_files`;
- **`parse_thy_imports(path) -> [str]`**: raw import tokens, comment-stripped, whole
  file;
- **`session_theories(session, follow_imports=True) -> [(name, path)]`**: a
  session's declared theories plus the transitive closure of **in-entry** imports.
  Session-qualified (cross-session) and HOL imports are *not* followed;
- `default_t_dir`.

`isabelle_layout.distribution.is_hol_base` is separate.

- **Session membership:** available. Map a path to its `SessionInfo` by scanning
  `session_theories` per session, or use `parse_theory(..., root=)`, whose
  `sec.session` field is filled.
- **Per-theory transitive import closure across sessions:** **not public in either
  package.**
  - `layout._classify_import` (private, re-exported in the deprecated
    `isabelle_query.common` shim as `classify_import`) classifies a token as
    `in_entry` / cross-entry / infrastructure.
  - `query.graph._Visibility.closure(theory)` computes exactly "theory ∪ transitive
    in-project imports" and is private.
  - `query.graph._import_candidates` / `_resolve_import` resolve `"Sess.Thy"` and
    bare names; also private.
- **Workable today without private imports:** `query graph imports -f json` (one
  call, whole edge list), then BFS in `block`. Or `parse_root` plus `parse_thy_imports`
  plus own resolution of `Session.Theory` tokens. That re-implements
  `_import_candidates`, which `feedback_query_flag_defects` says to flag rather than
  do.

### 2.5 Gaps: upstream feature requests these verbs would need

1. **isabelle-query: a public callers/callees API.** For example
   `api.callers(sections_or_root, name, *, reach="closure", derived=False,
   prose=False) -> list[Site]` (with theory, line, enclosing entry), and
   `api.call_graph(root)`. Today `delete` must subprocess the CLI per call or import
   `graph._build_call_graph`.
2. **isabelle-query: `callees -f tsv`**, symmetric with `callers`. `move`'s
   callees-visible-at-DEST check needs the callee's declaring *theory*, which
   `callees --names` gives only as text.
3. **isabelle-query or isabelle-layout: a public per-theory import closure**
   (`api.import_closure(root, theory) -> frozenset[str] | None`, or
   `isabelle_layout.theory_import_closure(path, sessions)` that follows
   session-qualified imports). Also a `deps -r` / `uses -r` tsv format. `move` needs
   both directions: callees' theories ⊆ closure(DEST), and DEST ∈ closure(every
   caller's theory).
4. **isabelle-query: prose-antiquotation references as an opt-in to `callers`**
   (`--with-prose` or `--antiquotations`): `\<^const>`, `\<^term>`, `@{thm}`,
   `@{const}` in text blocks. These are elaboration dependencies, so a delete or move
   that ignores them breaks the build or the PDF. `split-plan.py` has its own regex
   today.
5. **isabelle-query: implicit-use evidence** — `[simp]`/`[intro]`/… on the header,
   membership via `declare`/`lemmas`/named bundles — as an `Entry` field (attributes
   parsed off the header) or a `callers` row kind. `unused_lib.implicit_use`
   re-derives it with regexes, and `insights/37` notes that the first attempt checked
   the wrong line.
6. **isabelle-query: a public `_isa_word_pattern` / identifier-boundary helper**, and
   ideally a "token of identifier X" iterator over `live_source()`, so `rename` and
   `reargs` share query's boundary rules (prime, symbol body, symbol suffix) instead
   of a fifth copy. Also export `KEYWORDS` (`_isabelle_namespace`) for the
   NEW-is-not-an-Isar-command check.
7. **isabelle-query: `preamble` attribution of section-intro text** (see §3, history
   2026-10-02 / 10-11 / 10-14). `delete NAME` repeatedly took a *section's*
   introductory `text` as the lemma's preamble. A field distinguishing "doc block of
   this entry" from "text following a heading", or `cut_span` excluding a preamble
   that directly follows a heading, would fix it upstream. Alternatively `block`
   offers `--no-preamble`, which already exists, plus a warning when the preamble
   follows a heading.
8. **isabelle-query: `callers -f tsv` `<toplevel>` rows lack theory and session**
   (draft `upstream/query-callers-batch.md`, not posted). A caller-checked delete
   would print an unattributed row.
9. **isabelle-query: bound names** (`Entry.bindings`: constructors, conjuncts) are
   not call-graph nodes, so `callers -r` cannot answer for them. `rename` of a
   constructor or a `shows a: … and b:` conjunct needs to know they are declared by
   the parent's span. That works with the non-recursive `callers`.

---

## 3. Knowledge-base lessons bearing on the tool

### Memory (`.claude/memory/`)

- **`feedback_copy_port_spans.md`** — *"get the slice bounds from `query show <first>
  <last>` … never by eyeballing raw line numbers … `query show <last-lemma>` reports
  the last entry's span running to the *file end* — it absorbs the trailing blank +
  theory `end`."* It prescribes `bin/block.py emit SRC:A..B --transform tr-to-B` and
  name addressing (`block.py emit SRC:<first-lemma>`). It also says to verify after a
  transform by grepping for stray `_tr`.
  - For the tool: name addressing removes the hazard. The memory still documents the
    dead `--transform tr-to-B` and the deleted `port-tr-to-B.py`, so it must be
    edited at switch-over.
- **`feedback_no_isabelle_symbols_in_shell.md`** — *"The session shell here is
  `/bin/tcsh` … A literal containing an Isabelle symbol … handed to the Bash tool
  comes back with its backslashes **doubled** … the damage looks like a proof error
  rather than a quoting error."* It says to use Edit or `bin/block.py` by entry name
  or span, and that *"For a literal-substring identifier rename across files,
  `bin/block.py sub OLD NEW FILE[:REGION]` is the supported path."*
  - For the tool: keep the `@FILE` argument convention (`block.py._arg_text`,
    `insert-after.py`, `rename-thy-names.py`'s `fromfile_prefix_chars`) on *every*
    verb taking a pattern, template, anchor or map. This memory also needs its
    pointer updated to `block sub` / `block rename`, and should note that `sub` is
    wrong for word-shaped names.
- **`feedback_no_isabelle_symbols_in_names.md`** — declared names and Isar binders
  should be ASCII (`wrap_delta`, not `wrap_\<delta>`); symbols only in body text.
  *"the convention is a **token-tool vs text-tool** mismatch."* It points at the
  stale `bin/rename-isabelle-symbols.py` ("idempotent … re-run").
  - For the tool: `rename` could warn on a NEW containing `\<`. This memory's
    "re-run the script" advice is stale.
- **`feedback_query_flag_defects.md`** — the three `isabelle-*` packages are
  published deliverables, so *"when one doesn't do what's needed, flag the gap … don't
  substitute grep/sed/awk"*. *"Lean on query's semantic model; grow it to expose
  more"*. Reports go as GitHub issues drafted in `upstream/` and signed. It names
  *"the various `bin/new-*.sh` / `bin/block.py` helpers: they're durable,
  project-shipped artifacts; defects in them are project bugs."*
  - For the tool: the §2.5 gaps go upstream as issues, and `block` should not
    re-implement the import closure or the call graph privately.
- **`feedback_scripts.md`** — every non-trivial script goes in `bin/<name>`, is `+x`
  and runs by path; never `python3 -c`, heredocs or `./bin/x`. Long Bash calls bust
  the prompt cache.
  - For the tool: once packaged, `block` is a console script on PATH (like `query`),
    which removes the `bin/` path.
- **`feedback_explicit_check_result.md`** — *"must print an explicit `PASS:` or
  `FAIL:` line … the PASS/FAIL line should be the *last* line of output"*, and the
  exit code still reflects the result. `block.py` already complies
  (`fail()` → `FAIL:` + exit 1). Keep that as a package invariant; the selftest
  ends in `PASS: all N selftest case(s)`.
- **`feedback_whole_match_set.md`** — inventory the whole match set before scoping.
  This supports the `--expect N` design and a `rename --dry-run` that lists every
  site, grouped.
- **`feedback_bin_executable.md`**, **`feedback_promote_reusable_scratch.md`** —
  general `bin/` hygiene. The latter is the rationale for promoting `insert-after`,
  `reindent` and the like to verbs.
- **`feedback_query_grep_comments.md`** — `query grep` is live-source-only; use
  `--with-comments` for prose. This overlaps `prose-token.py`.
- **`trajectory-tooling-packaged.md`** — the precedent for extraction: bin copies were
  deleted only after being *verified to produce identical numbers* upstream; NDTHT
  keeps only the joins; `requirements.txt` floors name the release that first carried
  something relied on. `isabelle-block` should follow the same pattern: add a floor
  line and delete `bin/block.py` after a byte-identical fixture run.
- **`feedback_no_bash_for_loops.md`, `feedback_no_tmp.md`** — the selftest writes
  under `scratch/block-selftest`, not `/tmp`. A packaged tool needs a configurable
  work dir (`tempfile` in a package is fine for others, but NDTHT's gate dislikes
  `/tmp`).

### Insights

- **`insights/318.md` — A tool named for its first use case grows siblings instead of
  verbs.**
  - The origin story of `block.py`: six scripts became one, 1001 lines deleted for 85.
  - "Name the tool for its domain, and make the operations verbs"; "Prove equivalence
    before deleting … promote its durable half to a `--selftest`"; "Rewrite the
    reach-for surfaces, not the narrative" (CLAUDE.md, skills, KB, memory, not
    history).
  - Direct guidance for the extraction itself, and for folding
    `rename-thy-names`/`insert-after`/`reindent` in as verbs.
- **`insights/289.md` — An Isar command word cannot be a case name or a fact label.**
  - A `block.py sub back invert` *printed `PASS:`* while turning prose "reading a run
    back the other way" into "…invert the other way". `sub` is wrong for word-shaped
    identifiers.
  - 2026-10-03: `rename-thy-names.py` is the right tool.
  - 2026-10-05: *"A code span is not proof of a reference"* (``t/<dir>/``,
    ``build-<dir>``, ``pcommit_read/write/dir`` all got renamed). Documents
    describing another development must be excluded *by file*.
  - These are the `rename` verb's must-pass fixtures, and the reason for its
    NEW-is-a-keyword check.
- **`insights/224.md` — Merging two synonyms is not a blind find/replace.** Confirm the
  stem set first (`rg -o '\w*STEM\w*' | sort -u`). A literal full-term substring is
  safer than a shorter-stem regex. Line-wrapped occurrences escape line-oriented
  renames. A `rename --dry-run` should print the superstring set it is *not* touching.
- **`insights/226.md` — Renaming a session whose name collides with a datatype
  constructor.**
  - Drive the rename off a *syntactic discriminator*: `Sess.` with a dot in `.thy`;
    every occurrence in ROOT/Makefile; the `\newcommand` in root.tex.
  - `@{theory Session.Thy}` antiquotations are build-checked.
  - A session rename invalidates heaps (expect a cold build).
  - This is the design for theory and session renames.
- **`insights/236.md` — A name you introduce that is already in scope.** New names
  collide with session siblings through `imports`, not only with the library. Run the
  stem check over the **session**. Two channels: constant shadowing surfaced by
  `\<^const>` in prose, and a fact name captured by a consumer's `note`. `rename`
  needs a "NEW visible anywhere OLD is used" check, not just "NEW unused in this file".
- **`insights/148.md` — One-shot rename scripts collide with intentional old-name
  mentions.** Drive from an explicit file allowlist, exclude provenance-bearing files,
  and *re-run and assert zero changes* (idempotency as a test). For `rename`: an
  `--exclude` glob and a documented idempotency check.
- **`insights/37.md` — Unused code as a forest of rooted subtrees.**
  - The baseline-rounds method.
  - The *three things a zero-caller list cannot see*: statement-only definitions,
    implicit `[simp]`/`declare`/`lemmas` rules ("read the header line itself, because
    an entry's span starts at its preamble"), and prose-explained entries.
  - These are the refusal and warning conditions for the caller-checked `delete`.
- **`insights/83.md`** — `block.py delete FILE:<name>` removes scaffolding together
  with its preamble, in one step. This prescribes the name-addressed delete.
- **`insights/85.md`** — top-down dependency order when splitting; the cross-file
  `block.py move` makes the mechanics cheap.
- **`insights/163.md` — Forward-only elaboration makes prefix-splits
  dependency-safe.** Every prefix is self-contained. `move` *downward* within a theory
  or *up the import chain* can break callers; a move to an earlier position can
  break callees. That is the same check as `move`'s visibility test, in the
  intra-file case.
- **`insights/192.md`** and **`insights/201.md`** — doc antiquotations cannot
  forward-reference same-theory lemmas, and they type-check in the *global*
  namespace. Moving an entry below a `@{thm}`/`\<^const>` that cites it breaks the
  build even though `callers` reports nothing.
- **`insights/155.md`** — non-prose citers (`ROOT`, `.thy`, sibling harnesses) are
  missed by markdown-only audits. This is relevant to the switch-over edit list.

### Techniques

- **`techniques/0087.md` — Prose-only token rename.**
  - `prose-token.py` to find the prose occurrences, then `token-rename.py --only
    <lines>`.
  - Verify every notation (`\bk\b`, juxtaposed `2k`, the full form).
  - Lesson: discriminate by *lexical region*, not by token, and check juxtaposition
    forms separately.
- **`techniques/0071.md` — Split a monolith by top-down front-peel.**
  - `block.py move THY:5..E before New.thy:5` into a stub; `norm_splice` heals both
    seams.
  - *"take a lemma's `body` end … not a `src`/`enclosing` endpoint, whose span
    over-reaches into the next lemma's leading doc block."* This is the
    span-overreach hazard that `cut_span` now solves.
- **`techniques/0084.md`** — merge a linear chain by byte-exact concatenation
  (`block.py merge`); imports and ROOT are re-pointed by hand. A `merge` that also
  rewrites importers and ROOT would be a natural extension that uses
  `isabelle_layout`.
- **`techniques/0091.md`** — for a non-contiguous partition, use `block.py split`.
  The coverage assertions (overlap is FAIL, unclaimed lines reported) are the point.
- **`techniques/0121.md`** — the emit → replace → delete → sub sequence. *"Name
  addressing for the delete is what keeps this safe — the span moved twice by then."*
- **`techniques/0025.md`** — `block.py move FILE:helper before first_user` states the
  constraint rather than the line numbers.
- **`techniques/0081.md`, `0082.md`** — document `--transform classical-to-B` and
  `tr-to-B`. Spent (see §4).

### `history/` (40 files mention `block.py`) — failure modes to fix in the package

- **2026-10-02 (`20261002-231410`):**
  - *"`bin/block.py delete FILE:NAME` takes the entry's preamble text with it; read the
    span first. A range delete off by one line swallowed the next text block's
    opening line."*
  - *"290 sequential `query callers -r` calls cost about ten minutes"*, which is why
    the caller check should batch.
- **2026-10-04 (`20261004-002708`):**
  - *"`block.py sub` is a substring rename and rewrites prose, and `restate`/`unary`
    are English words … `bin/rename-thy-names.py` takes an explicit table"*.
  - *"`block.py move` with a line range took one line of the next text block along.
    Caught in the diff."*
- **2026-10-04 (`20261004-230005`):**
  - ktm phase 1: the map generator *"caught `\<open>` as a name character and `dir`
    inside `enc_dir`"*.
  - Phase 2: *"a constructor name also lives on as an Isar case name and as that
    case's fact … `consider (R)` labels look the same, and `proof`/`qed` depth
    tracking"*.
- **2026-10-07 (`20261007-003500`):** *"`block.py move … before NAME` lands under a
  preceding subsection header."* When the DEST entry is the first after a heading, the
  landing point should probably be above the heading, or there should be a
  `--before-heading` option.
- **2026-10-11 (`20261011-231145`):** *"`block.py delete NAME` took the section's `text`
  with the lemma as its 'preamble' and the text had to be put back."*
- **2026-10-14 (`20261014-001419`):** *"`block.py delete NAME` takes the entry's preamble
  text with it. Edit the text first and the edit is lost."*
- **2026-09-24 (`20260924-091339`):** `resub` (with `@FILE` against tcsh) and
  `prune-entries.py` came out of the tally migration.
- **2026-10-15 (`20261015-230902`):** `reargs`, `--expect` and `--except` came from the
  spent `t/logs/resub` scripts. The three new verbs are proposed.

**Summary of the preamble lesson:** three separate sessions (10-02, 10-11, 10-14) lost
a section-intro `text` to `delete NAME`. `Entry.preamble` is "a `text` block
immediately preceding … within ~3 blank lines". That cannot tell a lemma's doc block
from a section's introduction that happens to sit above the first lemma. The fix is
either upstream (§2.5 item 7) or a `block` rule: when the preamble directly follows a
heading, or when deleting leaves a heading with no body, refuse or require
`--with-preamble` / `--no-preamble` explicitly.

### `proof-hints.md`, `CLAUDE.md`

- `proof-hints.md`: no tooling hits.
- `CLAUDE.md`'s "Reach-for tools" `bin/block.py` bullet (lines ~450–486) is the main
  prescriptive text. It covers:
  - name addressing;
  - `--transform tr-to-B`;
  - `sub`, with the `rg -o '\w*OLD\w*'` pre-check and **"Not for a word-shaped
    identifier (`back`, `stop`, `head`): the pass rewrites `text` / `\<comment>`
    prose too … (`insights/289`)"**;
  - `resub`, `reargs`, `--expect`, `--except`, `--selftest`.

---

## 4. NDTHT coupling in `bin/block.py`, and the switch-over edit list

### 4.1 NDTHT-specific places in `bin/block.py`

1. **`--transform` and `TRANSFORMS = {"tr-to-B", "classical-to-B"}`.**
   - `_TR_PROTECT`, `_tr_to_B` and `_classical_to_B` hard-code the 2026-07 AE wrap
     names (`wrap_delta_tr`, `encoding_wrap_B`,
     `linear_speedup_HU_12_4_nae[OF wf T_linear q_pos c_pos]`, a literal
     `and c_pos: "0 < (card (UNIV :: ('c :: enum) set))"` assumption text, …).
   - **Dead:** `rg 'wrap_delta_tr|encoding_wrap_B|wrap_delta_B|AlphabetEnlargement_Classical' t/`
     finds nothing. The wrap chain was renamed to `Wrap_*` and the `_B`/`_tr` tags
     were stripped on 2026-07-03 (`rename-wrap-in-docs.py`). The last real use was
     2026-07-02/03 (`history/20260702-*`, `20260703-024247`), through
     `move-block.py`. No `git log` subject since then mentions a transform run.
   - Still documented in:
     - `CLAUDE.md:466` (`--transform tr-to-B` for copy-ports);
     - `.claude/memory/feedback_copy_port_spans.md:9,21,25`;
     - `techniques/0081.md:31`, `techniques/0082.md:27`;
     - `linear-speedup-faithfulness.md:636–684` (as `move-block.py`);
     - `bin/block.py` docstring lines 63–66 and 90.
   - **Recommendation:** drop it from the package. If a generic form is wanted,
     `--transform` could take a *map file* (the `rename` map format) applied to the
     emitted or copied block, which subsumes `tr-to-B`'s token rename. The
     `_TR_PROTECT` hold-and-restore trick becomes "longest-first whole-identifier
     map".
2. **Selftest work dir:**
   `Path(__file__).resolve().parent.parent / "scratch" / "block-selftest"`
   (line 1031). It assumes `bin/` sits beside a project `scratch/`. A package needs a
   temp dir or `--workdir`. NDTHT's no-`/tmp` rule argues for a CWD-relative default,
   or for moving the selftest to a pytest suite.
3. **`bin/span-overreach-scan.py`** named in the docstring (lines 57–58) and in
   `resolve_entry` (line 264). That is an NDTHT script. Replace it with
   `Entry.cut_span` and drop the reference (§1.12).
4. **The `keywords` refusal** in `_entries` (lines 245–247), justified by "No
   theory in this tree declares `keywords`". It is NDTHT-specific reasoning. Replace
   it with `parse_theory(..., root=<query root>)`, discovering the root with
   `isabelle_layout.default_t_dir` or the `.isabelle-query` marker, as `query` does.
5. **The error message** `"pip install -r requirements.txt"` (line 243) refers to
   NDTHT's requirements file. In the package `isabelle-query` becomes a hard
   dependency, so the message disappears.
6. **Docstring examples** use NDTHT paths and names (`t/ae/A.thy`,
   `t/nth/Diagonal_Arms.thy`, `bor_cost`, `tape_val_dip`, `Substrate_Extras`,
   `tasks.md:1011..1024`).
7. **History prose** in the docstring (the six retired scripts, "May 2026").
8. **`USAGE` strings and `--help` text** say `block.py`; they become `block`.
9. **`v_split`** writes `theory NAME imports ... begin` with the imports joined as
   given, quoting tokens containing `.`. It updates neither ROOT nor `root.tex`
   (`feedback_pdf_root_tex`). It is generic, but NDTHT's split skill relies on the
   human doing those steps.
10. **The `.md`-aware behaviour** (`replace tasks.md:…`, `_prose_mask` returns `[]`
    for non-`.thy`). It is generic and fine.

### 4.2 Every place that invokes or documents `bin/block.py`: the switch-over edit list

**Invokes it (code):**

- `bin/prune-entries.py:8,23`: `BLOCK = ROOT / "bin" / "block.py"`, run via
  `sys.executable`. Must change to the `block` console script, or be retired by
  `block delete NAME...` (§1.10).

**Prescriptive docs (reach-for surfaces; must be edited at switch-over):**

- `CLAUDE.md:450–486`: the whole `bin/block.py VERB TARGET ...` bullet, including
  `--transform tr-to-B` (line 466) and `block.py --selftest` (line 486).
- `.claude/skills/split-theory/SKILL.md`:
  - line 4: the `allowed-tools` list includes `Bash(bin/block.py:*)`, which must
    become `Bash(block:*)`;
  - lines 25, 95, 96, 98, 100, 136: "with `bin/block.py` (never Edit-then-delete)";
    `bin/block.py move SRC:A..B before DST:T`; `block.py move SRC:lemma_name before
    DST:T`; `bin/block.py split SRC ...`; "Run every `bin/` tool by path
    (`bin/block.py`)".
- `.claude/memory/MEMORY.md:36` (`feedback_copy_port_spans` summary: "`bin/block.py
  emit SRC:A..B --transform tr-to-B`") and `MEMORY.md:72`
  (`feedback_no_isabelle_symbols_in_shell` summary).
- `.claude/memory/feedback_copy_port_spans.md:21–28`.
- `.claude/memory/feedback_no_isabelle_symbols_in_shell.md:3,20,22`.
- `.claude/memory/feedback_query_flag_defects.md:92` ("the various `bin/new-*.sh` /
  `bin/block.py` helpers").
- `.claude/memory/feedback_no_isabelle_symbols_in_names.md`: not `block.py`, but
  points at the to-be-retired `rename-isabelle-symbols.py`.
- `requirements.txt`: add an `isabelle-block>=X` floor with a rationale comment,
  following the existing house style.
- `t/nth/formalization.yaml:221`: "bin/block.py for mechanical edits; project lint
  scripts; …".
- `cleanup.md:23`: "before removal via `bin/block.py delete FILE:<name>`".

**KB entries (prescriptive; update the command spelling, keep the lesson):**

- `insights/83.md:51,55,90`
- `insights/85.md:51`
- `insights/226.md:12`
- `insights/236.md:59`
- `insights/289.md:59` (narrative: "then `bin/rename-ident.sh`, now `bin/block.py sub`")
- `insights/318.md` (narrative about the consolidation; leave, or add a pointer to
  the package)
- `techniques/0025.md:99,101`
- `techniques/0071.md:29,47,85`
- `techniques/0081.md:31` (`--transform classical-to-B`: dead)
- `techniques/0082.md:27` (`--transform tr-to-B`: dead)
- `techniques/0084.md:26–27`
- `techniques/0091.md:43–44`
- `techniques/0121.md:29,48–51`

**Design memos (live or semi-live):**

- `nth-design.md:3275` ("one `bin/block.py sub` over the 78 …").
- `ntr-count-refactor.md:371,464` (`block.py move … before NAME` behaviour note).

**Sibling `bin/` scripts that mention `block.py` in prose:**

- `bin/span-overreach-scan.py:5` (retire)
- `bin/reindent.py:12` (port)
- `bin/insert-after.py:7` (port)
- `bin/msb-carry-sweep.py:6` (spent)
- `bin/rename-thy-names.py:27` (port)

**Narrative — leave as written (`insights/318`):**

- `history/*.md` (40 files)
- `nth-journal.md`
- `linear-speedup-faithfulness.md`
- `pide-mcp-evaluation.md`
- `textblock-attribution-design.md`
- `is/030-state-space.md`
- `wrap-design.md`

**Not referenced:** the `Makefile` (no target runs `block.py` or its selftest).
Nothing under `t/` other than `formalization.yaml`.
