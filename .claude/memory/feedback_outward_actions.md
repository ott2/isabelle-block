---
name: feedback_outward_actions
description: No push, GitHub repo creation, issue/comment, or PyPI upload without a fresh request from Andras; sign GitHub posts; no gh CLI locally
metadata:
  type: feedback
---

Nothing leaves this machine without a fresh request from Andras:

- no `git push`;
- no creating the GitHub repo;
- no PyPI upload;
- no issue, PR or comment.

Approval for one push does not extend to the next.

- **Upstream gaps** in `isabelle-query` or `isabelle-layout` are drafted as
  issue text in `upstream/` for Andras to check and post.  They are not worked
  around here and not patched in the other repo.
- **Sign every GitHub post.**  `gh` runs as Andras's account (`ott2`), so an
  unsigned post reads as his.  End it with a line such as
  `*Drafted and posted by Claude (Opus 5.5, via Claude Code) on behalf of
  Andras Salamon.*`
- **No `gh` CLI for routine work.**  Plain git over SSH pushes branches and
  tags.  A GitHub Release is created by CI from the release commit's message;
  see [release-notes-go-in-the-release-commit](release-notes-go-in-the-release-commit.md).

**Why:** Andras's standing rules across the NDTHT family of repos
(2026-10-04 onward), and the sibling packages' release practice.
