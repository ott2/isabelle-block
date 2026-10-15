---
name: feedback_explicit_check_result
description: Every block verb and check prints an explicit PASS:/FAIL: last line; never infer results from $?; stage, inspect, then commit as separate calls
metadata:
  type: feedback
---

Every verb of `block`, and every check script, ends its output with an explicit
`PASS: …` or `FAIL: …` line, and its exit status agrees.  Never rely on
`; echo $?` to learn an outcome.

**Why:** Andras (NDTHT, 2026-04-25): "please change lint-is to output an
explicit error if you want the exit value".  The verdict belongs on the last
line, where the eye lands.

There is a second reason particular to this tool.  The failures that mattered
in NDTHT's history were the ones that **printed PASS while doing damage**: a
literal `back` → `invert` rename rewrote four English sentences, and an
over-matching substitution edited a sibling lemma (`docs/usecases.md`).  So
PASS must mean what it says.  Report prose hits separately from code hits,
and support `--expect N`.

**The same root on the git side:** never chain `git add … && git commit`.
Stage the files, run `git status --short` and look at it, then commit, as
three calls with stderr visible.  A chained command once committed a bare
rename without the edits that gave it meaning.
