# Publishing a release

Claude runs the steps in order once Andras asks for a release, up to and
including the GitHub Release.  The PyPI upload is Andras's.  The commands run
unchanged in any shell; replace `X.Y.Z` by hand.  Setup, once:
`.venv/bin/pip install build twine`.

## 1. Pre-flight and the release commit

- `.venv/bin/pip install '.[test]' && .venv/bin/pytest` passes.
- Python 3.9 syntax holds (only 3.14 is installed here).  Also check
  `__future__` annotations and stdlib calls by eye:
  `.venv/bin/python -c "import ast,pathlib; [ast.parse(p.read_text(), str(p), feature_version=(3,9)) for p in pathlib.Path('src').rglob('*.py')]"`
- `isabelle-query` has a floor and no `<` cap.
- Drop `.dev0`, reinstall, and commit.  The message becomes the GitHub
  Release: `X.Y.Z — summary`, then markdown for users on the significant
  changes since the last release (`git log vPREV..HEAD`), as for sister projects.

## 2. Build, before tagging

```sh
.venv/bin/python -m build
.venv/bin/twine check --strict dist/isabelle_block-X.Y.Z-*.whl dist/isabelle_block-X.Y.Z.tar.gz
tar tzf dist/isabelle_block-X.Y.Z.tar.gz
```

The sdist should hold only `src/`, `tests/`, `README.md`, `LICENSE` and the
generated files.  Keep `dist/` for debugging, and name only this version's
files (`isabelle_block-X.Y.Z*` would also match `X.Y.Z.dev0`).

## 3. Publish

```sh
git tag -a vX.Y.Z -m "isabelle-block X.Y.Z"
git push origin main vX.Y.Z
.venv/bin/twine upload -r pypi-isabelle-block dist/isabelle_block-X.Y.Z-*.whl dist/isabelle_block-X.Y.Z.tar.gz
```

- The tag push creates the GitHub Release; check it.  A pushed tag never
  moves, so fix wrong notes by editing the Release.
- The upload is **Andras's**, and is skipped for a GitHub-only release.

## 4. Afterwards

- Install as a stranger would: `pip install isabelle-block==X.Y.Z` (or
  `git+https://github.com/ott2/isabelle-block@vX.Y.Z`) into
  `python3 -m venv --clear scratch/stranger`, then run `block --version`.
- Bump to the next `.dev0` in its own commit.  A PyPI version is permanent.
- In alpha, a patch release is for fixes and additions.  A minor release is
  for a change to output or behaviour that should stand out.
