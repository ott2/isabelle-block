---
name: feedback_design_before_build
description: Settle a feature's design in its docs/fr/ document (whole case family enumerated, decisions written down) before implementing; small increments with tests between; no effort estimates
metadata:
  type: feedback
---

Settle a verb's design in its `docs/fr/<verb>.md` before writing code:

- enumerate the whole family of cases (`docs/usecases.md` lists them per verb);
- classify each one: handled, refused, or reported for review;
- write the rule down.

Then implement in small increments, with a test per behaviour and the suite
run between steps.

**Why:** Andras's working rule across NDTHT is that less gets built and then
deleted.  NDTHT's eighteen rename, move and prune scripts are what happens
otherwise: each new case was met by a new sibling script rather than a
designed extension.

**How to apply:**

- Open questions for Andras go in the FR document's "Decisions" section,
  each with a recommended answer.  Do not stall on them; proceed on the
  recommendation, and say so.
- A working implementation outranks adherence to an earlier decision.  If
  building shows the design is wrong, change the document.
- Do not give effort or line-count estimates.
- Continue autonomously between checkpoints rather than asking "shall I
  continue?".
