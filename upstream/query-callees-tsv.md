# Draft: isabelle-query — `callees -f tsv`, symmetric with `callers`

**Status:** draft (2026-10-16), **not posted**; for Andras to check.
Checked against isabelle-query 0.9.8.  This is U2 in `docs/background.md`
§2.5.

**Title:** `callees`: add `-f tsv`, matching `callers -f tsv`

---

`callers -f tsv NAME...` has become the way a script reads the call graph.  It
gives one attributed row per caller, and the graph is built once for all the
names.  `callees` has no counterpart:

```
$ query callees uses_grault -f tsv
query: error: unrecognized arguments: -f tsv
```

The text output carries the same facts, but only for a human reader:

```
2 callee(s) of uses_grault:

  foo (DEF) — Base [L5]
  grault (LEMMAS) — Base [L24]
```

**The use.**  `isabelle-block` is the region-editing tool extracted from NDTHT
(not yet public).  It is gaining a `move` verb that checks, before moving an
entry to another theory, that everything the entry cites is visible from the
destination.  That needs each callee's declaring *theory* (and session), for
several entries at once.  Today the only ways to get it are to parse the text
format above or to import `graph._build_call_graph`, which is private.

**The ask.**  `query callees -f tsv NAME...`, with the same columns and
conventions as `callers -f tsv`, so one parser reads both:

```
subject  callee  tag  theory  session  depth  locus
```

It should keep the same properties as `callers`:

- several names in one call, with the graph built once;
- `-r` with depth;
- an unknown name reported without leaving misattributable rows;
- since 0.9.8, a row names a declaration the citing theory can see
  (`[callee-attribution]`).

The `locus` column could be the callee's declaration site, or the line where
the subject cites it.  We'd use the declaration site.  The citation line
would be a bonus, but is not needed.

---
*Drafted by Claude (Opus 5.5, via Claude Code) on behalf of Andras Salamon,
from the isabelle-block project.*
