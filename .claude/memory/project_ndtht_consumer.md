---
name: project_ndtht_consumer
description: NDTHT is the first consumer — where it lives, how to try verbs on its tree read-only, and the switch-over plan from bin/block.py to the pip-installed `block`
metadata:
  type: project
---

`isabelle-block` was extracted on 2026-10-15 from NDTHT's `bin/block.py`.  NDTHT
is an Isabelle formalisation of the nondeterministic time hierarchy theorem;
its four MAT sessions are live AFP entries.  NDTHT is the package's first
consumer and the source of every feature request so far.

Where it lives:

- The main checkout is `~/projects/ndtht`, with its venv at
  `~/projects/ndtht/venv`.  `~/projects/ndtht/t/` is the theory tree: about
  400 theories in ten sessions (`t/base`, `t/ae`, `t/ar`, `t/art`, `t/ntr`,
  `t/dtr`, `t/nth`, `t/dth`, …).
- Claude's NDTHT worktree is `~/projects/claudecode/ndtht`, on branch
  `stac/wip`.  It never touches `main`.

Plan:

1. Develop here, against `.venv`.
2. Install into NDTHT from the sibling directory:
   `~/projects/ndtht/venv/bin/pip install ~/projects/isabelle-block`.
   This is a snapshot, so reinstall to pick up changes.
3. Release to PyPI, with Andras's go-ahead.
4. NDTHT then switches to `isabelle-block>=X` in `requirements.txt` and deletes
   `bin/block.py` (`tasks.md` `[ndtht-switchover]`).

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
