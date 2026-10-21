# Related tools

This page is for two readers.  One is deciding whether `block` adds anything
to their project.  The other is us, deciding whether to build a feature or
borrow it.  It was last checked on 2026-10-21; a claim marked *unchecked* has
not been tried.

## Where `block` sits

The generic layer of `block` is thin, and existing tools do it well: editing
by line span and literal or regex substitution.  The value is in the Isabelle
layer:

- **Entry names as addresses.**  `Foo.thy:helper` resolves through
  `isabelle-query`'s parser to the lemma's span, from its doc block to the end
  of its proof, clipped below the next entry's preamble.
- **Prose is told apart from code** by the parser, not by a regex: `text`
  blocks, headings and `\<comment>`.  A rewrite that also changes prose does
  damage that no build catches.
- **Verbs at theory level**: `split` and `merge` handle headers, `imports` and
  `begin`/`end`.
- **Planned checks against the theory graph**: `rename` (collisions),
  `delete` (callers) and `move` (import visibility).

If your edits never name an entry and never need to tell prose from code, the
tools below are enough.

All of the following hold across every verb, and the generic tools offer them
only in part:

- a refusal writes nothing, across all the files in a run;
- `--expect N` refuses an over-match;
- every run ends with `PASS:` or `FAIL:`.

## Editing by line span: `ed`, `sed`, `awk`

`ed` moves (`m`), copies (`t`), deletes (`d`) and reads in a file (`r`) on a
line range.  It also has regex and relative addresses (`/lemma foo/,+3`).

What `block` adds:

- name addressing;
- a move between files as one all-or-nothing edit;
- blank-seam healing (`norm_splice`).

**Worth borrowing:** nothing yet.  NAME covers what regex addresses would.

## Substitution: `sed`, `sd`, `fastmod`, `rg --replace`

- `sd` does literal (`-F`) or regex replacement, and a match may span lines.
- `fastmod` is a regex codemod across a tree.  It shows each hunk as a diff
  and asks before applying it.
- `rg --replace` shows a preview and writes nothing.

What `block` adds:

- scoping to entry names, with `--except`;
- `--expect N`;
- all-or-nothing writes across files;
- skipping prose (only `reargs` so far; `rename` is planned).

**Worth borrowing:** a `--dry-run` that prints a unified diff.  `fastmod`,
comby and ast-grep all show one, while `block`'s dry run reports only counts.

## Structural rewriting: comby

[comby](https://comby.dev) is the closest relative of `reargs`.  A comby
pattern is a template with holes:

- a hole inside delimiters matches within that balanced group, newlines
  included;
- `:[x:e]` is an expression-like hole, matching a contiguous non-whitespace
  run or a balanced group.  It is the analogue of `reargs`'s argument (`_arg_at`:
  a bracket group or an atom);
- `:[x~regex]` restricts a hole to a regex;
- `where` rules constrain holes, and `where rewrite` rewrites a hole's
  contents (but rewrites cannot nest);
- `-custom-matcher FILE.json` defines a new language: its delimiters, string
  literals and comments.

**Status.**  comby is an OCaml binary that pip does not install.  The last
release is 1.8.1 (2022-06), with commits as recent as 2026-06.  A `comby`
package exists on PyPI, but whether it bundles the binary is *unchecked*.

**How it would fit Isabelle (unchecked):**

- `"` cannot be declared a string literal.  comby does not match inside
  strings, and Isabelle's terms are written inside `"…"`, which is exactly
  where `reargs` must match.
- `\<open>…\<close>` can be declared as delimiters, and `(* … *)` as a
  comment.
- `text \<open>…\<close>` and `\<comment> \<open>…\<close>` cannot be
  declared at all.  Prose is marked by the command in front of the cartouche,
  not by its delimiters.  So prose skipping would still come from
  `isabelle-query`, applied as a mask over comby's match ranges (from
  `-json-lines`).
- It needs testing whether `:e` treats `\<le>` as part of an atom, as
  `_arg_at` does, and whether it stops at `\<open>`.
- `reargs` rewrites applications nested inside an argument first.  comby
  rewrites outermost matches, so it would need repeated passes.
- `reargs` reports two things comby has no notion of: a bare mention (counted
  and left alone) and a partial application (a refusal).  Both would have to
  be computed from comby's matches afterwards.

See `tasks.md` `[reargs-foundation]`.

**Worth borrowing:** `where` constraints on holes (for example, `$1` must be
an atom), and JSON output of matches for scripting.

## Tree-sitter tools: ast-grep, Semgrep

These match on a syntax tree, so they need a grammar for the language.  We
know of no maintained tree-sitter grammar for Isabelle/Isar (*unchecked*).
Isar's outer syntax is also extensible: a theory can declare `keywords`, so
no fixed grammar can be complete.  That is the same problem `block`'s
`keywords` refusal guards against.

## Refactoring tools for one language: Coccinelle, Rope, LibCST, LSP rename

These are the model for `rename`, `delete` and `move`.  They edit through a
semantic model of the program, not its text.  Isabelle's semantic model is
PIDE markup, which needs a build.  To our knowledge, neither Isabelle/jEdit
nor Isabelle/VSCode offers a rename or move refactoring as of Isabelle2025-2
(*unchecked*).

## Isabelle's own: `isabelle update`

`isabelle update` rewrites theory sources using the PIDE markup of a build,
so it is exact where it applies.  Its rewrites are fixed syntax updates,
selected by `-u`.  In Isabelle2025-2 they are:

- `update_inner_syntax_cartouches`;
- `update_mixfix_cartouches`;
- `update_control_cartouches`;
- `update_path_cartouches`;
- `update_cite`.

It has no user-defined rewrite.  `block` makes the opposite trade: it needs
no Isabelle process, and it works on text.  So for `block`, the build is the
correctness oracle.

## Using this page

- Before building a new mechanism, look here.  Building on a thorough
  existing tool usually beats a less thorough version written from scratch.
- When a tool not listed here turns up, add it.
- `tasks.md` `[borrow-features]` lists the features worth taking.  Take each
  one only when a use asks for it.
