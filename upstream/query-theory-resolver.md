# Draft: isabelle-query — a public resolver for a locus's theory part

**Status:** drafted 2026-10-24, not posted.  Checked against isabelle-query
1.2.0.  This is U11.  It comes from isabelle-block#3.

**Title:** `api`: resolve the THEORY in `THEORY:LINE` / `THEORY:A..B` the way
the CLI does

---

`query` prints a place as `THEORY:LINE` or `THEORY:A..B`: `enclosing`,
`callers` and `unused … --spans` all do, and `query enclosing` and
`query lines` read the form back.  THEORY is a label, not a path.  It is the
bare name in a session, and in a corpus it is the shortest directory-qualified
suffix that is unique (`beta/Examples`), or a path-spelled ROOT name
(`While/Hoare`).  `theory_labels` builds it and `_resolve_theory` reads it,
both over `label_chain`, so the two cannot drift.

isabelle-block wants to take these loci as targets, so that a `--spans`
column pastes straight into `block delete`:

```
$ query unused facts --spans t/nth
Diagonal_Machine:3608  cnum  have  case2_count_le  Diagonal_Machine:3608..3609
$ block delete Diagonal_Machine:3608..3609
FAIL: not a file: Diagonal_Machine
```

`block` imports only `isabelle_query.api` (`parse_theory`, `parse_root`,
`Entry`, `TheorySection`), and none of those resolves a label.  It could
re-derive one from `isabelle_layout`'s session walk.  But query's own comments
on `[disambig-names]` and `[label-depth]` record what goes wrong when the
reader and the printer disagree: `beta/Examples` resolved to `alpha/Examples`,
silently.  For an editing tool, a target that lands in the wrong file is the
worst failure, so the reader should be query's.

**Ask.** A public function in `api` that maps a locus's theory part to the
file(s) it names, under a root resolved as the CLI resolves `-R` (marker,
`$ISABELLE_QUERY_ROOT`, nearest `ROOT`).  For example:

```python
def resolve_theory(name: str, *, root: Path | None = None) -> list[Path]:
    """The .thy files `name` (a path, bare name, label, or path-spelled
    name) designates, in the order the CLI would try them."""
```

Two properties matter to a caller that writes:

- **Every candidate, not the first.**  Today a bare name that matches two
  sections resolves to whichever comes first (`for s in sections: if
  s.theory == name: return s`).  The CLI only prints a bare name when it is
  unique among the sections shown, but the reader may run over a wider
  root, where it is not.  Returning the list lets an editor refuse and name
  the candidates.  Returning the first, with a flag for "there were others",
  would also do.
- **The same tiers as the CLI**: path, exact name, label suffix, then stem.
  Whether the case-insensitive fallback belongs in an API for writers is
  your call; isabelle-block would not use it.

The cost of a whole-root parse is the caller's concern, but a resolver that
reads only ROOTs and theory headers (no Isar parse) would let `block`
resolve forty loci in one run cheaply.

---
*Drafted by Claude (Opus 5.5, via Claude Code) on behalf of Andras Salamon,
from the isabelle-block project.*
