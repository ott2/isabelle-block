# Draft: isabelle-query — entries with a `[simp]`-like attribute are reported unused

**Status:** draft (2026-10-16), **not posted**; for Andras to check.
Checked against isabelle-query 0.9.8.  This is U5 in `docs/background.md`
§2.5.

**Title:** `unused` / `callers`: a lemma declared `[simp]` (or `[intro]`,
`[elim]`, …) has implicit users that no citation shows

---

`unused` already handles two kinds of implicit use correctly.  A
`declare quux [simp]` counts as a use of `quux`, through a `TOPLEVEL` row, and
a `lemmas grault = corge` counts as a use of `corge`.  What it does not see is
the attribute **on the lemma's own header**:

```isabelle
lemma baz [simp]: "foo n = Suc n" by (simp add: foo_def)
lemma qux: "foo (foo n) = Suc (Suc n)" by simp     (* needs baz *)
```

```
$ query unused
LEMMA     baz      Base  (10..12, 3 lines)
LEMMA     qux      Base  (13..15, 3 lines)
...
```

`baz` is listed with zero callers, but deleting it breaks `qux`.  No citation
graph can list `baz`'s users: the simplifier picks it up wherever it is
visible.  The answer that can be given is "this entry has implicit users".

**Evidence.**  In NDTHT, dead-code prunes guided by zero-caller lists deleted
`[simp]` rules that were in use.  The project's own pruning helper
(`unused_lib.py`) re-derives the attributes with a regex.  Its first version
read the attributes from the *first line of the entry's span*, which is the
preamble `text` when there is one, rather than from the header, and so missed
them.  This is exactly the kind of detail the parser gets right and a
consumer's regex gets wrong.

**The ask**, in order of preference:

1. **The attributes as parsed data on `Entry`**: for example `Entry.attributes:
   tuple[str, ...]`, taken from the header (`lemma baz [simp, intro]:` gives
   `("simp", "intro")`).  It belongs on the API surface (0.8.0+) so library
   consumers get it directly.
2. **`unused` uses it**: an entry with a rule-declaring attribute
   (`simp`, `intro`, `elim`, `dest`, `iff`, `cong`, `split`, `code`, …) is not
   called unused.  It is either listed separately as "implicitly used", or
   kept out of the zero-caller list unless a flag such as `--include-implicit`
   is given.  Which attribute names count is your call; the list above is
   what bit us.

Item 1 alone would unblock us.  Item 2 is where it would help other `unused`
users.

---
*Drafted by Claude (Opus 5.5, via Claude Code) on behalf of Andras Salamon,
from the isabelle-block project.*
