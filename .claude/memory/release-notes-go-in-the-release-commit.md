---
name: release-notes-go-in-the-release-commit
description: "Release notes belong in the version-bump commit's message, because CI publishes that"
metadata: 
  node_type: memory
  type: project
  originSessionId: 1d0518c7-a5a2-43f2-8d90-afaed5930b8c
  modified: 2026-08-11T09:05:39.498Z
---

Write the release notes as the **version-bump commit's message**, in markdown,
for users. `.github/workflows/release.yml` (in both `isabelle-layout` and
`isabelle-query`) reads `repos/<repo>/commits/<tag>` and publishes that
commit's message as the GitHub Release body, so a tag push is the whole
publish — no local `gh`, no web UI. See [[avoid-gh-cli-on-this-machine]].

**Why:** the tag *annotation* is read by nothing, on purpose.
`gh release create --notes-from-tag` reads the annotation but silently falls
back to the commit message when the runner's local tag is lightweight, which
mis-published `isabelle-query` v0.2.5's first run. Dereferencing the tag to its
commit is deterministic.

**How to apply:** the release commit is written for users (what changed since
the last release); how the work happened goes in the commits around it — so
there is no tension between a useful log and useful notes. Two traps: the
workflow must exist in the **tagged commit's tree**, because `on: push: tags`
resolves the workflow from the pushed ref rather than the default branch; and
the step is idempotent, so a re-pushed tag repairs a bad publish rather than
erroring. If notes are wrong, fix them on a *new* commit and re-tag — never
amend, see [[no-git-history-rewriting]].
