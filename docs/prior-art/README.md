# Prior art: NDTHT scripts and lessons

This directory is a snapshot taken from NDTHT at commit `f12c6062`
(2026-10-15).  It is reference material for designing the new verbs.  It is
**not shipped** (the sdist includes only `src/`, `tests/`, the README and the
LICENSE) and it is **not run**: the scripts have their exec bit cleared, and
several assume NDTHT's layout (`bin/`, `t/`, `scratch/`).  Do not edit these
files.  Port what is worth porting into `src/`, and say in the commit which
script it came from.

`../background.md` §1 describes each script in detail: its interface, its
algorithm, its gaps, and a recommendation.

## Scripts (`scripts/`)

| Script | Job | Destination |
|---|---|---|
| `rename-thy-names.py` | whole-identifier, prose-aware rename from a map, with a lossless code/prose split | **the core of `rename`** |
| `token-rename.py` | line-scoped regex rename in one file | `rename` with a REGION |
| `rename-theories.py` | theory-file rename within one session directory | `rename --theory` |
| `ktm-rename-map.py` | generates a rename map from the tree and checks NEW is free | `rename`'s map expansion and collision check |
| `rename-tex-names.py` | applies a map to LaTeX (`foo\_bar`, `\isasymX`) | `rename`'s document mode |
| `rename-wrap-in-docs.py` | stem-plus-lookahead rename over markdown | `rename`'s markdown mode |
| `old-names-sweep.py` | residue sweep: what OLD names survive anywhere | `rename`'s post-check (RN15) |
| `prose-token.py` | reports regex matches inside prose only | `rename`'s prose report |
| `prune-entries.py` | deletes named entries via `block.py delete` | **`delete NAME...`** |
| `prune-rounds.py`, `unused_lib.py`, `classify-unused.py` | baseline-rounds dead-code pruning, implicit-use detection | `delete --cascade` and its refusal rules |
| `hoist-scan.py` | lowest legal home of an entry, by import closure | `move`'s visibility check and DEST suggestion |
| `split-plan.py` | plans a theory split; scans prose antiquotations itself | `move`'s antiquotation check |
| `span-overreach-scan.py` | regression scan of name-resolved spans | a corpus test, once `Entry.cut_span` is used |
| `insert-after.py`, `insert-hyp.py` | insert text after an anchor; add a hypothesis | a possible `insert` verb (not yet an FR) |
| `reindent.py` | re-indent a region | a possible `indent` verb (not yet an FR) |

## Knowledge-base entries (`insights/`)

| Entry | Lesson for this tool |
|---|---|
| 37 | Unused code forms a forest of rooted subtrees, so prune by rounds against a baseline.  The first attempt read attributes from the wrong line. |
| 91 | Declared names stay ASCII; symbols in names defeat text tools. |
| 192 | Doc antiquotations cannot forward-reference lemmas in the same theory, which matters to `move` within a file. |
| 201 | Doc antiquotations type-check in the global namespace.  They are build dependencies, and `move`'s callee check must see them. |
| 206 | Importing a theory does not import its session-siblings.  Visibility is by import closure, never by session. |
| 207 | Mechanical identifier renaming: a word boundary avoids collisions, and a lookahead catches derived facts (`_def`, `.simps`). |
| 289 | A substring rename of a word-shaped identifier (`back`, `stop`) rewrites prose, and no build catches it. |
| 318 | A tool named for its first use case grows siblings instead of verbs.  This is why `block` exists. |
