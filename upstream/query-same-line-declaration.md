# Draft: isabelle-query — a declaration that follows a proof on the same line is not an entry

**Status:** posted 2026-10-23 as
[isabelle-query#29](https://github.com/ott2/isabelle-query/issues/29), at
Andras's request.  Checked against isabelle-query 1.1.0.  This is U10.

**Title:** A `lemma` after `by …` on the same line is missed, and the previous
entry's `cut_span` takes it

---

Isabelle reads a command keyword wherever a token starts, so a declaration may
follow the previous proof on the same line.  `parse_theory` does not see such a
declaration.  The previous entry's `thy_end`, `body_end_line` and `cut_span`
then run on through it, and `shares_line` stays `False`:

```isabelle
lemma a: True
  by simp lemma b: True by simp

lemma c: True by simp
```

```python
>>> {e.name: (e.cut_span, e.shares_line) for e in parse_theory("Shared", path).entries}
{'a': ((7, 8), False), 'c': ((10, 10), False)}      # no entry 'b'
```

It occurs in the AFP once.  `Simpl/Semantic.thy:1666` reads
`by (auto simp add: final_notin_def intro: exec_Seq') lemma Seq_NoFaultStuckD1:`,
and `Seq_NoFaultStuckD2` gets `cut_span (1661, 1700)`.  That span holds all of
`Seq_NoFaultStuckD1`, which is absent from `entries`.

**Why it matters.**  `cut_span` is documented as holding one entry and no part
of another.  Here a tool that writes through it (`block delete
Semantic.thy:Seq_NoFaultStuckD2`) removes two lemmas and reports success.
`query callers Seq_NoFaultStuckD1` cannot find the lemma either.

**What would help:**

- Recognise the declaration, so `b` is an entry.  Both `a` and `b` then get
  `shares_line = True` and `cut_span = None`, which is the documented answer
  for two declarations on one line.
- Failing that, set `shares_line` on the entry whose span contains a command
  keyword at a token start, so that its `cut_span` is `None` rather than too
  wide.

---
*Drafted by Claude (Opus 5.5, via Claude Code) on behalf of Andras Salamon,
from the isabelle-block project.*
