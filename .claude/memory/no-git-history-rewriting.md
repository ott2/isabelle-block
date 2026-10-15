---
name: no-git-history-rewriting
description: Never use git amend/reset/force-push/merge-to-reconcile; cut a new version instead of tidying history
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1d0518c7-a5a2-43f2-8d90-afaed5930b8c
  modified: 2026-08-11T09:05:49.498Z
---

Do not rewrite or reconcile git history. No `git commit --amend`, no
`git reset`, no force-push, and no merging just to repair the effects of an
earlier rewrite. If a released or pushed commit has the wrong message or
content, **cut a new version** rather than tidying the past.

**Why:** the user's words — "There is no need to have a perfect git history,
no-one is grading our work; our users care about releases being good quality
and not how they got there." An `--amend` of an already-pushed release commit
turned a one-line task into a diverged branch that then needed a force-push or
a merge to fix, which was strictly worse than leaving the imperfect message
alone.

**How to apply:** when tempted to improve a past commit, stop and ask whether
the goal can be met by adding — a new commit and a new version. Version numbers
before publication are free; history other people may have fetched is not.
Do not use amend even on an unpushed commit, since whether it has been pushed
is easy to misjudge. If the branch is already diverged, hand the reconciliation
to the user with the exact command rather than running it. Notes that need
fixing get a new commit and a re-pushed tag — see
[[release-notes-go-in-the-release-commit]].
