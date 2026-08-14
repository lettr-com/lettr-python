# Releasing

This project uses [Semantic Versioning](https://semver.org/). Releases are
published to PyPI automatically by GitHub Actions when a GitHub Release is
published.

## Versioning policy

- **MAJOR** (`1.0.0` → `2.0.0`): breaking API changes
- **MINOR** (`0.2.0` → `0.3.0`): new features, backwards-compatible
- **PATCH** (`0.2.0` → `0.2.1`): bug fixes only

Pre-1.0 minor bumps may contain breaking changes (noted in the changelog).

## Version lives in exactly one place

`pyproject.toml` → `version = "X.Y.Z"`. That is the only file to edit.

Everything else derives from it at runtime:

- `src/lettr/_version.py` reads the installed distribution's version via
  `importlib.metadata.version("lettr")` and exports it as `__version__`
- `src/lettr/__init__.py` re-exports that `__version__`
- `src/lettr/_client.py` builds `USER_AGENT = f"lettr-python/{__version__}"`
  from it

Never hardcode the version anywhere else.

## Release checklist

1. **Update the changelog.** Move items from `[Unreleased]` into a new
   `[X.Y.Z]` section in `CHANGELOG.md`. Add a new empty `[Unreleased]`
   section at the top. Update the compare links at the bottom.

2. **Bump the version** in `pyproject.toml` — the one place it lives.

3. **Run the checks locally.** These are exactly what CI's
   "Lint & Type Check" and "Test" jobs run; `ruff format --check` is easy
   to forget and will fail the build on its own.
   ```bash
   source .venv/bin/activate
   pip install -e .              # so __version__ picks up the new version
   ruff check src/lettr tests
   ruff format --check src/lettr tests
   mypy src/lettr
   python -m pytest -q
   python -c "import lettr; print(lettr.__version__)"   # should print X.Y.Z
   ```

4. **Commit and push on `main`:**
   ```bash
   git add CHANGELOG.md pyproject.toml
   git commit -m "chore(release): X.Y.Z"
   git push origin main
   ```

5. **Tag the release:**
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

6. **Create a GitHub Release** from the tag. The body should mirror the
   changelog entry for this version.
   ```bash
   gh release create vX.Y.Z --title "vX.Y.Z" --notes-from-tag
   ```
   (or use the GitHub web UI)

7. **Watch the workflow.** The `.github/workflows/publish.yml` workflow
   fires on release publish:
   - Builds the sdist and wheel
   - Publishes to TestPyPI
   - Publishes to PyPI

   Both PyPI targets use [trusted publishing](https://docs.pypi.org/trusted-publishers/)
   via OIDC, so no API tokens are needed — but the `testpypi` and `pypi`
   environments must be configured in the GitHub repo settings with
   matching trusted publisher entries on PyPI.

8. **Verify** the new version appears at
   <https://pypi.org/project/lettr/> and installs cleanly:
   ```bash
   pip install --upgrade lettr
   python -c "import lettr; print(lettr.__version__)"
   ```

## What if the workflow fails?

- **TestPyPI step fails:** TestPyPI rejects re-uploads of an existing
  version. Delete the release, bump to the next patch, and retry.
- **PyPI step fails:** same constraint — a published version cannot be
  overwritten. You must bump to the next version.
- **Never yank/delete a PyPI release** unless it has a critical issue;
  prefer publishing a fix release instead.

## Cutting a v1.0.0

When the API surface is considered stable:

1. Ensure the changelog's `[Unreleased]` section is clean.
2. Add a `## [1.0.0]` section documenting the stability commitment.
3. Follow the release checklist above with `X.Y.Z = 1.0.0`.
