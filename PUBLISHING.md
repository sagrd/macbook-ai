# Publishing Guide

This project uses GitHub Actions to automatically build and publish to PyPI when you push a version tag.

## Setup

### Configure Trusted Publishing on PyPI

Trusted Publishing is more secure than API tokens - it uses OpenID Connect to authenticate directly from GitHub Actions.

1. Go to https://pypi.org/manage/project/macbook-ai/settings/publishing/
2. Scroll to "Trusted Publishers"
3. Click "Add a new publisher"
4. Fill in:
   - **PyPI Project Name**: `macbook-ai`
   - **Owner**: Your GitHub username (e.g., `sagrd`)
   - **Repository name**: `macbook-ai`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`
5. Click "Add"

That's it! No API tokens needed. GitHub Actions will authenticate automatically using OpenID Connect.

### Alternative: Using API Token (Old Method)

If you prefer using an API token instead:

1. Go to https://pypi.org/manage/account/token/
2. Create a token scoped to "Project: macbook-ai"
3. Add it as `PYPI_API_TOKEN` in GitHub Secrets
4. Update `.github/workflows/publish.yml` to include:
   ```yaml
   - name: Publish to PyPI
     uses: pypa/gh-action-pypi-publish@release/v1
     with:
       password: ${{ secrets.PYPI_API_TOKEN }}
   ```

## Publishing a New Version

### Secure Tag-Based Publishing

1. **Update version** in `pyproject.toml`:
   ```toml
   [project]
   version = "0.1.7"  # Bump this
   ```

2. **Commit and push to main**:
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.1.7"
   git push origin main
   ```

3. **Create and push release tag**:
   ```bash
   git tag v0.1.7
   git push origin v0.1.7
   ```

### What Happens Next

1. Tests run on Python 3.10, 3.11, and 3.12
2. Version in tag is verified against `pyproject.toml`
3. Package is built and published to PyPI (if tests pass)

### Why Tags?

Tag-based publishing gives you a **final review checkpoint** before publishing to PyPI. This prevents:
- Accidental publishes from merged PRs
- Malicious code being auto-published
- Version mismatches

See [SECURITY.md](SECURITY.md) for complete security guidelines.

## Pipeline Behavior

- **Pull Requests**: Only runs tests (no publish)
- **Push to main**: Only runs tests (no publish)
- **Push tag `v*`**: Runs tests + publishes to PyPI if tests pass

## Manual Publishing (if needed)

If you need to publish manually:

```bash
# Build the package
uv build

# Upload to PyPI
uv publish

# Or use twine
pip install twine
twine upload dist/*
```

## Troubleshooting

### Tests fail on GitHub but pass locally

- Check Python version compatibility (tests run on 3.10, 3.11, 3.12)
- Verify all dependencies are in `pyproject.toml`

### Publishing fails with authentication error

- Verify `PYPI_API_TOKEN` secret is set correctly in GitHub
- Ensure the token has the correct scope (Project: macbook-ai)
- Check that the token hasn't expired

### Version already exists on PyPI

- You cannot re-upload the same version
- Bump the version number in `pyproject.toml`
- Create a new tag with the new version

## Best Practices

1. **Test locally first**: Run `uv run pytest` before pushing
2. **Version format**: Use semantic versioning (MAJOR.MINOR.PATCH)
3. **Tag format**: Always prefix with `v` (e.g., `v0.1.6`)
4. **Changelog**: Consider maintaining a CHANGELOG.md
5. **Release notes**: Add GitHub release notes when creating tags
