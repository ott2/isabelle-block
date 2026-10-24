---
name: project_ndtht_consumer
description: "NDTHT is the first consumer — where it lives, how to try verbs on its tree read-only, and the switch-over plan from bin/block.py to the pip-installed `block`"
metadata:
  node_type: memory
  type: project
  originSessionId: 1bab4b32-1bb1-4b31-bb39-14f6b5e5202c
  modified: 2026-10-24T04:40:53.397Z
---

`isabelle-block` was extracted on 2026-10-15 from NDTHT's `bin/block.py`.  NDTHT
is an Isabelle formalisation of the nondeterministic time hierarchy theorem;
its four MAT sessions are live AFP entries.  NDTHT is the package's first
consumer and the source of every feature request so far.

Where it lives:

- The main checkout is `~/projects/ndtht`, with its venv at
  `~/projects/ndtht/venv`.  `~/projects/ndtht/t/` is the theory tree: about
  450 theories in ten sessions (`t/base`, `t/ae`, `t/ar`, `t/art`, `t/ntr`,
  `t/dtr`, `t/nth`, `t/dth`, …).  It has a `.isabelle-query` marker, so
  `block` finds its session root unaided.
- Claude's NDTHT worktree is `~/projects/claudecode/ndtht`, on branch
  `stac/wip`.  It never touches `main`.

Plan:

1. Develop here, against `.venv`.
2. Install into NDTHT from the sibling directory:
   `~/projects/ndtht/venv/bin/pip install ~/projects/isabelle-block`.
   This is a snapshot, so reinstall to pick up changes.
3. Release on GitHub when Andras asks (v0.1.0–v0.1.3, 2026-10-22 to
   10-24).  The PyPI upload is Andras's, and may happen unannounced: 0.1.2 and 0.1.3
   are there (learnt 2026-10-24 from issue #2).  Check with `pip index
   versions isabelle-block --no-cache-dir` rather than assuming.
4. NDTHT can now switch to `isabelle-block>=X` in `requirements.txt` and
   delete `bin/block.py` (`tasks.md` `[ndtht-switchover]`).  That is
   NDTHT-side work.

Until step 4, `bin/block.py` in NDTHT is frozen.  Fixes are made here, not
there.

**Why:** the user wants `block` developed and released like its siblings
`isabelle-query`, `isabelle-layout` and `isabelle-watchdog`, and used from
NDTHT throughout.

**How to apply:**

- To exercise a verb on real theories, run it read-only against
  `~/projects/ndtht/t/`: use `--dry-run`, `emit`, or a copy under `scratch/`.
  Never write into NDTHT from this repo.
- NDTHT's own conventions (its CLAUDE.md, `insights/`, `techniques/`) explain
  the use cases.  `docs/usecases.md` and `docs/background.md` quote the parts
  that matter, so reading NDTHT is optional.
