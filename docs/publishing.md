# Publishing a release

Do the steps in order.  **(Andras)** marks the outward steps.  The commands
run unchanged in any shell; replace `X.Y.Z` by hand.  Setup, once:
`.venv/bin/pip install build twine`.

## 1. Pre-flight and the release commit

- `.venv/bin/pip install '.[test]' && .venv/bin/pytest` passes.
- Python 3.9 syntax holds (only 3.14 is installed here).  Also check
  `__future__` annotations and stdlib calls by eye:
  `.venv/bin/python -c "import ast,pathlib; [ast.parse(p.read_text(), str(p), feature_version=(3,9)) for p in pathlib.Path('src').rglob('*.py')]"`
- `isabelle-query` has a floor and no `<` cap.
- Drop `.dev0` from `pyproject.toml` and reinstall.  Commit with the release
  notes as the message (`X.Y.Z — summary`, then markdown for users).  The
  workflow publishes that message as the GitHub Release.

## 2. Build, before tagging

```sh
.venv/bin/python -m build
.venv/bin/twine check --strict dist/isabelle_block-X.Y.Z-*.whl dist/isabelle_block-X.Y.Z.tar.gz
tar tzf dist/isabelle_block-X.Y.Z.tar.gz
```

The sdist should hold only `src/`, `tests/`, `README.md`, `LICENSE` and the
generated files.  Keep `dist/` for debugging, and name only this version's
files (`isabelle_block-X.Y.Z*` would also match `X.Y.Z.dev0`).

## 3. Publish **(Andras)**

```sh
git tag -a vX.Y.Z -m "isabelle-block X.Y.Z"
git push origin main vX.Y.Z
.venv/bin/twine upload -r pypi-isabelle-block dist/isabelle_block-X.Y.Z-*.whl dist/isabelle_block-X.Y.Z.tar.gz
```

The tag push creates the GitHub Release.  A pushed tag never moves, so fix
wrong notes by editing the Release.  For a GitHub-only release, skip the
upload.

## 4. Afterwards

- Install as a stranger would, into `python3 -m venv --clear
  scratch/stranger`: `pip install isabelle-block==X.Y.Z` (or
  `git+https://github.com/ott2/isabelle-block@vX.Y.Z`), then `block --version`.
- Bump to the next `.dev0` in its own commit.  A PyPI version is permanent.
- In alpha (as with `isabelle-query` before 1.0), use a patch release for
  fixes and additions.  Use a minor release for a change to output or
  behaviour that should stand out.
