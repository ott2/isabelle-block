---
name: feedback_release_commands
description: "Release runbook rules: shell-agnostic commands, keep dist/, name this version's files, `twine upload -r pypi-isabelle-block`, at most ~50 lines"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1bab4b32-1bb1-4b31-bb39-14f6b5e5202c
  modified: 2026-10-22T22:13:38.112Z
---

Andras asked for three changes to `docs/publishing.md` (2026-10-22).  They
apply to any documented command and any release step:

1. **Documented commands are shell-agnostic.**  Each one must run unchanged
   in sh, bash, zsh and csh/tcsh: no shell variables, no `$(...)`, and no
   `VAR=value cmd` (use `env VAR=value cmd`).  Write placeholders such as
   `X.Y.Z` out by hand.  This is separate from [[feedback_shell_tcsh]], which
   is about Claude's own session shell.
2. **Never `rm -rf dist`.**  Old artefacts are kept for debugging, since file
   names carry the version.
3. **Name this version's files, never `dist/*`**:
   `dist/isabelle_block-X.Y.Z-*.whl dist/isabelle_block-X.Y.Z.tar.gz`.  The
   tempting `isabelle_block-X.Y.Z*` also matches `X.Y.Z.dev0` builds, and with
   patch 1 it matches patch 10.
4. **The upload is `twine upload -r pypi-isabelle-block FILES`**, using a
   repository entry in Andras's `~/.pypirc`.  Don't document token or
   credential handling; that's his setup.
5. **Runbooks stay short**: about 50 lines at most.  Give the steps and one
   reason each, and leave out history and side-routes.

**Why:** a runbook is run by people in whatever shell they have.  `dist/` is
the only local record of what each version actually shipped.

**How to apply:** before committing a documented command, run it verbatim
under `sh` and `tcsh` (and `zsh`).  If I have deleted artefacts by mistake,
rebuild them from the tag: `git archive vX.Y.Z` into `scratch/`, then
`python -m build DIR --outdir dist`.
