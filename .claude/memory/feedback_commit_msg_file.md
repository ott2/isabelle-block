---
name: feedback_commit_msg_file
description: Write commit messages with the Write tool to .gitcommit.txt (gitignored) and `git commit -F` it; never under .git/, never via printf/echo
metadata:
  type: feedback
---

To make a commit:

1. Write the message to `.gitcommit.txt` at the repo root, using the **Write
   tool**.
2. Run `git commit -F .gitcommit.txt`.

**Why:**

- A path under `.git/` trips a per-edit approval gate.
- Building the message with `printf` or `echo` passes backticks through the
  shell as command substitution.  In NDTHT that silently deleted identifiers and
  a `Co-Authored-By` line.
- A mangled message is not worth `--amend`, which is forbidden; see
  [no-git-history-rewriting](no-git-history-rewriting.md).

**How to apply:** end every message with
`Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.
The body should be substantive: carry the reasoning, and put a stable `[tag]`
on a decision.
