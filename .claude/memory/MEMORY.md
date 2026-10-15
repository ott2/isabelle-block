# isabelle-block — project memory

Durable facts are in `CLAUDE.md`, work in flight in `tasks.md`, and feature
designs in `docs/fr/`.

## Project
- [project_ndtht_consumer](project_ndtht_consumer.md) — NDTHT is the first consumer.  Where it lives, how to try verbs on its tree read-only, and the switch-over from `bin/block.py`.
- [release-notes-go-in-the-release-commit](release-notes-go-in-the-release-commit.md) — CI publishes the version-bump commit's message as the GitHub Release.

## Feedback
- [feedback_shell_tcsh](feedback_shell_tcsh.md) — tcsh: no `cd`, no `for`, no `$(...)`, no `\<…>` in shell args (use Edit or `@FILE`); scratch files go in `scratch/`, never `/tmp`.
- [feedback_explicit_check_result](feedback_explicit_check_result.md) — every verb and check ends with PASS:/FAIL:, and PASS must not hide prose edits.  Run add, status and commit as separate calls.
- [feedback_commit_msg_file](feedback_commit_msg_file.md) — commit messages go in `.gitcommit.txt` via the Write tool, then `git commit -F`.  Includes the trailer.
- [feedback_outward_actions](feedback_outward_actions.md) — no push, repo creation, post or upload without a fresh request.  Sign GitHub posts; no `gh`.
- [no-git-history-rewriting](no-git-history-rewriting.md) — no amend, reset or force-push; add a commit or a version instead.
- [feedback_design_before_build](feedback_design_before_build.md) — settle the design in `docs/fr/` first, then work in small tested increments.  No estimates; work autonomously.
