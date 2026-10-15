---
name: feedback_shell_tcsh
description: The session shell is tcsh — no cd, no bash for-loops, no $(...), no `\<…>` literals in shell args, temp files under scratch/ never /tmp
metadata:
  type: feedback
---

The Bash tool runs `/bin/tcsh` on this machine.  Carried over from NDTHT, where
each rule was learnt the hard way:

- **No `cd`.**  Use absolute paths, or tool flags such as `git -C`.
- **No bash `for` loops, and no `$(...)`.**  Each trips a per-call permission
  gate.  Use several separate calls, or write a script file under `scratch/`
  and run it by path.
- **No Isabelle symbols in shell arguments.**  A literal containing `\<open>` or
  `\<lambda>` comes back with its backslashes doubled, and the damage reads as a
  proof error.  Write such text with the Edit or Write tool.  For `block`
  itself, pass it as an `@FILE` argument, which is why `@FILE` exists.
- **Temporary files go under `scratch/`** (gitignored), never `/tmp`.
  Out-of-project paths trip the approval gate.
- **`>` and `&` in a command can arrive HTML-escaped.**  Prefer a tool's own
  output option (`git show --output=`) to redirection.
- **No `make` piping.**  Run checks bare and read their PASS/FAIL line.  See
  [feedback_explicit_check_result](feedback_explicit_check_result.md).

**Why:** each of these produced silent corruption or a stalled approval prompt
in the NDTHT sessions this package came from.

**How to apply:** before any shell command, ask whether it uses one of the
constructs above, and route around it.
