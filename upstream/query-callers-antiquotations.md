# Draft: isabelle-query — prose antiquotations as an opt-in kind of reference

**Status:** draft (2026-10-16), **not posted**; for Andras to check.
Checked against isabelle-query 0.9.8.  This is U4 in `docs/background.md`
§2.5.

**Title:** `callers` / `unused`: optionally count references from document
antiquotations

---

`callers` deliberately skips `text` blocks, and it skips names whose only
occurrence on a line is inside `@{thm …}`, `@{const …}` or `@{term …}`.  For
the question "which proofs depend on this?", that is right.

It is wrong for a different question, which tools now ask: **"can I delete
or move this without breaking the build?"**  A document antiquotation is
checked when the theory is processed: `@{thm bar}` fails if `bar` is not
visible.  So prose references are build dependencies, even though they are not
proof dependencies.

**Reproduction** (session `Repro`; `Client` imports `Base`):

```isabelle
(* Base.thy *)
definition foo :: "nat ⇒ nat" where "foo n = n + 1"
lemma bar: "foo 0 = 1" by (simp add: foo_def)

(* Client.thy *)
text ‹The constant \<^const>‹foo› and the fact @{thm bar} are
  named here, in prose only.›
```

```
$ query callers bar -f tsv
$ query unused
LEMMA     bar      Base  (7..9, 3 lines)
...
```

`bar` is reported as having no callers and as unused, but deleting it breaks
`Client`.  The same holds for moving `bar` into a theory that `Client` does
not import.

**Evidence that this costs real work.**  NDTHT keeps a history of its
mechanical edits.  These failures recur there:

- **Moves into a lower theory broke builds through prose more often than
  through proofs.**  A `\<^const>` in a moved `text` block named a constant
  the destination does not import, and the build reported them one per
  attempt.
- **Dead-code prunes guided by `unused` deleted entries cited in prose.**
- **The project's theory-split planner** (`split-plan.py`) carries its own
  regex for antiquotations, because `callers` would not report them.

**The ask.**  An opt-in flag on `callers` (and on `unused`, with the same
meaning): for example `--with-prose`, or `--antiquotations`.  With it:

- antiquotation references count as references, wherever they sit:
  - in `text` blocks, headings and `\<comment>`;
  - in both spellings, `@{thm bar}` / `@{const foo}` and
    `\<^const>‹foo›` / `\<^term>‹…›`;
- the rows are distinguishable from proof references, by a tag value or an
  extra `kind` column in `-f tsv`, so a tool can report "3 proof callers, 1
  prose reference" separately.

Two parts of this are already in place:

- the default stays as it is, so census figures do not move;
- the parser already has the prose spans (`text_blocks`, `heading_spans`,
  `nonisar_spans`), so finding antiquotations inside them is local work.

A note in case it helps: the `antiq_re` in `graph.py` today covers only the
`@{…}` spelling, not the `\<^const>‹…›` cartouche form.  With `text` blocks
skipped wholesale this makes no difference now, but it would for this flag.

---
*Drafted by Claude (Opus 5.5, via Claude Code) on behalf of Andras Salamon,
from the isabelle-block project.*
