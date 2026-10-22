---
name: feedback_outward_actions
description: "No push, repo creation or issue/comment without a fresh request; a release request covers tag, push and GitHub Release; the PyPI upload is Andras's only; sign posts; no gh"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1bab4b32-1bb1-4b31-bb39-14f6b5e5202c
  modified: 2026-10-22T22:16:45.270Z
---

Nothing leaves this machine without a fresh request from Andras:

- no `git push`;
- no creating the GitHub repo;
- no PyPI upload;
- no issue, PR or comment.

Approval for one push does not extend to the next.

- **A release request covers the whole GitHub side** (Andras, 2026-10-22).
  When Andras asks for a release, Claude runs `docs/publishing.md` through
  pushing `main` and the tag and checking the GitHub Release; the notes are
  the significant changes since the last release.  **The PyPI upload is
  never Claude's**: Andras runs `twine upload -r pypi-isabelle-block`
  himself.  See [[feedback_release_commands]].

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
