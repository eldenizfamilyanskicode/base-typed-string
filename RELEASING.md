# Releasing base-typed-string

This repository publishes one universal wheel and one source distribution. A
release is approved, built, and published as one bundle: one reviewed commit, one
annotated tag, one GitHub Release, and the exact same distribution files on PyPI.

## One-time repository setup

1. Create a GitHub Environment named `pypi`.
2. Configure that environment with the protection appropriate for the repository.
   The process must remain usable by a sole maintainer; an independent second
   reviewer is not required by this repository.
3. In the PyPI `base-typed-string` project, add a Trusted Publisher with:

   - Owner: `eldenizfamilyanskicode`
   - Repository: `base-typed-string`
   - Workflow: `release.yml`
   - Environment: `pypi`

4. Protect `main` and require the `CI` workflow before release commits are
   accepted when repository settings allow it.
5. Keep workflow files under code-owner review and leave GitHub Actions default
   permissions read-only.

The release workflow does not use a PyPI API token. Only its publish job receives
`id-token: write`, and all external actions are pinned to full commit SHAs.

## Prepare a release

1. Update the single version source:

   ```python
   # src/base_typed_string/_version.py
   __version__: str = "X.Y.Z"
   ```

2. Move the release notes from `Unreleased` into a dated `## [X.Y.Z]` section in
   `CHANGELOG.md` and update its comparison links.
3. Refresh and verify the development lock:

   ```bash
   uv lock
   uv lock --check
   ```

4. Run the complete local release gate:

   ```bash
   uv sync --frozen --extra dev
   uv run ruff check .
   uv run ruff format --check .
   uv run mypy
   uv run pyright
   uv run pytest
   uv run python scripts/check_release.py
   uv run python -m build --outdir dist
   uv run twine check --strict dist/*
   uv run python scripts/verify_distribution.py \
     --dist-dir dist \
     --expected-version X.Y.Z
   ```

5. Review the complete diff and obtain the explicit user approval required for
   the release bundle. Before that approval, do not commit, tag, push, create a
   GitHub Release, or publish to PyPI.

## Commit and tag

After explicit approval:

```bash
git add <reviewed release files>
git commit -m "Release X.Y.Z"
git push origin main
git tag -a vX.Y.Z -m "Release X.Y.Z" <release-commit-sha>
git push origin vX.Y.Z
```

The tag must be annotated, resolve to the reviewed release commit, and be
contained in `origin/main`. Verify it before creating the GitHub Release:

```bash
git fetch origin main --tags
uv run python scripts/check_release.py \
  --tag vX.Y.Z \
  --require-annotated-tag \
  --require-clean \
  --require-tag-on-main
```

Do not use `gh release create` to create a missing tag implicitly. The annotated
tag must already exist on the remote.

## Publish

1. Create a draft GitHub Release for the existing `vX.Y.Z` tag.
2. Copy the matching `CHANGELOG.md` section into the release notes.
3. Check that the release is neither a prerelease nor attached to another target.
4. Publish the GitHub Release. This single explicit action authorizes the complete
   publication bundle.
5. The `Release` workflow then:

   - checks the version, changelog, annotated tag, clean checkout, and `main`
     ancestry;
   - reruns the quality gate;
   - builds the wheel and sdist exactly once;
   - validates and isolated-installs both artifacts;
   - publishes those artifacts to PyPI through Trusted Publishing;
   - attaches the same files plus `SHA256SUMS` to the GitHub Release;
   - verifies a clean install from production PyPI.

If publication fails after PyPI accepts a file, do not delete and reuse that
version. PyPI filenames cannot be overwritten; diagnose the run and release a new
patch version if artifact contents must change.

## Post-release verification

Confirm all of the following:

- GitHub Actions `Release` completed successfully.
- The GitHub Release contains the wheel, sdist, and `SHA256SUMS`.
- PyPI shows version `X.Y.Z`, both distribution formats, and attestations.
- A clean environment can install both the base package and the Pydantic extra.
- `base_typed_string.__version__` and
  `importlib.metadata.version("base-typed-string")` both return `X.Y.Z`.
- The GitHub repository description and documentation describe both public base
  classes.

The next development change belongs under `CHANGELOG.md`'s `Unreleased` heading;
the repository does not need an immediate `.dev0` version bump.
