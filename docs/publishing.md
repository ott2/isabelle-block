# Publishing a release

These are the steps, in order.  Where a step exists to prevent a specific
failure, it names that failure.  Steps marked **(Andras)** are outward-facing,
and Claude does not take them.

The commands are written for tcsh, and they use the repository's `.venv`
(`.venv/bin/pip install build twine` once).

## 1. Pre-flight

- **The tests pass against a real install:**
  `.venv/bin/pip install '.[test]' && .venv/bin/pytest`.
- **The Python 3.9 floor holds.**  It is checked statically, because only 3.14
  is installed here:

  ```sh
  .venv/bin/python -c "import ast,pathlib; [ast.parse(p.read_text(), str(p), feature_version=(3,9)) for p in pathlib.Path('src').rglob('*.py')]"
  ```

  This catches syntax only.  Also check by eye that every module with
  annotations has `from __future__ import annotations`, and that no
  post-3.9 stdlib call has crept in.
- **The dependency has a floor and no cap.**  `isabelle-query>=…` is fine.  A
  `<` bound can make a correct release uninstallable the day upstream bumps.
- **The version is unused on PyPI**:
  `curl -s -o /dev/null -w '%{http_code}\n' https://pypi.org/pypi/isabelle-block/X.Y.Z/json`
  should print 404.

## 2. The release commit

1. Drop `.dev0` from `version` in `pyproject.toml`, and reinstall.
2. Commit with the **release notes as the commit message**: a subject line
   `X.Y.Z — summary`, then markdown written for users about what changed.
   `.github/workflows/release.yml` publishes this message as the GitHub
   Release, and nothing else is read.  A tag annotation, in particular, is
   ignored.

## 3. Build, before tagging

```sh
rm -rf dist
.venv/bin/python -m build
.venv/bin/twine check --strict dist/*
tar tzf dist/*.tar.gz
```

- `rm -rf dist` is there because `twine upload dist/*` uploads whatever it
  finds, a stale artefact included.
- `build` makes the wheel *from the sdist*, so a file missing from the
  sdist's `include` fails here, not in a user's checkout.
- `tar tzf` should list `src/`, `tests/`, `README.md`, `LICENSE`,
  `pyproject.toml`, `PKG-INFO` and `.gitignore`, and nothing else.

Build before tagging.  A broken build costs nothing, while a pushed tag
should never move.

## 4. Tag and push **(Andras)**

```sh
git tag -a vX.Y.Z -m "isabelle-block X.Y.Z"
git push origin main
git push origin vX.Y.Z
```

`git push` does not push tags on its own.  The tag push triggers the workflow,
which runs as it exists in the tagged commit, so it must already be in that
tree (it is).  To check the Release:

```sh
curl -s https://api.github.com/repos/ott2/isabelle-block/releases/tags/vX.Y.Z
```

If the notes are wrong, fix them in a *new* commit, tag that commit, and
push.  The workflow edits an existing Release rather than failing.

## 5. Upload to PyPI **(Andras)**

```sh
.venv/bin/twine upload dist/*
```

- The username is the literal `__token__`.  `~/.pypirc` (mode 600) avoids
  shell quoting.  Under tcsh, the environment form is:

  ```sh
  env TWINE_USERNAME=__token__ TWINE_PASSWORD=… .venv/bin/twine upload dist/*
  ```
- **First upload only:** PyPI cannot scope a token to a project that does not
  exist yet.  So 0.1.0 needs an account-scoped token.  Revoke it straight
  afterwards, and create one scoped to `isabelle-block`.
- If an upload half-completes, re-run it with `--skip-existing`.

## 6. Verify as a stranger would

```sh
rm -rf scratch/stranger
python3 -m venv scratch/stranger
scratch/stranger/bin/pip install isabelle-block==X.Y.Z
scratch/stranger/bin/block --version
```

## 7. Afterwards

- Bump `version` to the next `.dev0` in its own commit, so that a later
  install from the checkout never claims to be the release.
- For NDTHT, after the first release: `tasks.md` `[ndtht-switchover]`.

## Versioning, while in alpha

This follows `isabelle-query`'s practice before its 1.0:

- a patch release for fixes and additions;
- a minor release (0.x.0) for a change that shifts existing output or
  behaviour and should stand out in the notes, whether or not it breaks
  anything;
- no major release before the CLI settles.

## What cannot be undone

- **A version number is permanent.**  PyPI refuses a file name it has seen
  before, even after the release is deleted.  A bad X.Y.Z is fixed by
  publishing X.Y.Z+1.
- **A pushed commit or tag is never rewritten.**  There is no `--amend`, no
  moved tag and no force-push (`CLAUDE.md`).
- The author email in `pyproject.toml` is public in every artefact.
