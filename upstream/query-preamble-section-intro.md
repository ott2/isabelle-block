# Draft: isabelle-query — a section's introductory `text` is attributed as the first entry's preamble

**Status:** draft (2026-10-16), **not posted**; for Andras to check.
Checked against isabelle-query 0.9.8.  This is U7 in `docs/background.md`
§2.5.

**Title:** `Entry.preamble` / `cut_span`: tell a section introduction from an
entry's own doc block

---

`Entry.cut_span` is documented as the span that a delete or move tool writes
through, and it starts at the entry's `preamble`.  When a heading is followed
by a `text` block and then the section's first lemma, that `text` is
attributed as the lemma's preamble, even when it introduces the whole
section:

```isabelle
lemma corge: "foo 1 = 2" by simp

subsection ‹A section›

text ‹This paragraph introduces the whole section, not the lemma below.›

lemma first_in_section: "True" by simp

lemma second_in_section: "True" by simp
```

```python
>>> e = {e.name: e for e in parse_theory("Base", path).entries}["first_in_section"]
>>> e.preamble, e.cut_span
((29, 29), (29, 32))        # line 27 is the subsection, 29 the section text
```

`query unused` shows the same span (`first_in_section … (29..33)`).

**Why it matters.**  Moving or deleting the first lemma of a section carries
the section's introduction away with it, and the next lemma is left under a
heading with no introduction.  In NDTHT this happened in three separate
sessions (2026-10-02, 10-11 and 10-14), using a delete tool that writes
through this span.  Each time the text had to be restored by hand.  Twice it
was caught in review, and once only after an edit to that same text had been
lost with it.

**The ambiguity is real.**  A `text` directly under a heading is sometimes
the first lemma's documentation, so we don't think the attribution can simply
be switched off.  What would help is exposing the fact that makes the case
ambiguous, so a tool can refuse or ask for an explicit choice:

- **Preferred:** a field, for example `Entry.preamble_follows_heading: bool`.
  It is true when no other entry lies between the nearest heading above and
  the preamble.
- **Alternative:** a documented rule that `cut_span` excludes such a
  preamble, with the preamble still reported in `Entry.preamble`.  This is
  simpler for consumers, but it changes `cut_span` for everyone who uses it.

Either is fine for us.  The tool needs to know, not for `query` to decide.

---
*Drafted by Claude (Opus 5.5, via Claude Code) on behalf of Andras Salamon,
from the isabelle-block project.*
