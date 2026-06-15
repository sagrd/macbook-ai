# Security Guidelines

## CI/CD Security

This project uses GitHub Actions with the following security measures:

### ✅ Implemented Protections

1. **Trusted Publishing (OIDC)** - No long-lived API tokens
2. **Tag-based releases** - Only tagged commits are published to PyPI
3. **Version verification** - Tag version must match `pyproject.toml`
4. **Test gating** - All tests must pass before publish
5. **Minimal permissions** - Workflows use least-privilege access
6. **Environment protection** - PyPI publishes use protected `pypi` environment

### 🔐 Recommended GitHub Repository Settings

#### 1. Enable Branch Protection for `main`

Go to **Settings > Branches > Add branch protection rule**:

- **Branch name pattern**: `main`
- ✅ **Require a pull request before merging**
  - ✅ Require approvals: 1 (or more for team projects)
  - ✅ Dismiss stale pull request approvals when new commits are pushed
- ✅ **Require status checks to pass before merging**
  - ✅ Require branches to be up to date before merging
  - Add required checks: `test (3.10)`, `test (3.11)`, `test (3.12)`
- ✅ **Require conversation resolution before merging**
- ✅ **Do not allow bypassing the above settings**

#### 2. Configure Environment Protection

Go to **Settings > Environments > pypi**:

- ✅ **Required reviewers** (optional): Add yourself or trusted maintainers
- ✅ **Deployment branches**: Only protected branches
- This adds a manual approval step before PyPI publish (recommended for critical packages)

#### 3. Enable Security Features

Go to **Settings > Code security and analysis**:

- ✅ **Dependency graph**
- ✅ **Dependabot alerts**
- ✅ **Dependabot security updates**
- ✅ **Secret scanning**

## Publishing Workflow

### Secure Release Process

1. **Update code** via pull request (requires review)
2. **Bump version** in `pyproject.toml` (manual, deliberate)
3. **Merge to main** (after review and tests pass)
4. **Create and push tag**:
   ```bash
   git tag v0.1.7
   git push origin v0.1.7
   ```
5. **Automated publish** triggers only on tag push (with optional manual approval)

### Why Tag-Based Publishing is Safer

- ❌ **Auto-publish on every main push**: Malicious PR → merge → immediate PyPI publish
- ✅ **Tag-based publish**: Malicious PR → merge → you review → manual tag → publish

Tags give you a final checkpoint before publishing.

## Dependency Security

### Current Dependencies

- `pyobjc-framework-Cocoa` - Official Apple framework bindings
- `pyobjc-framework-Speech` - Official Apple framework bindings
- `pyobjc-framework-AVFoundation` - Official Apple framework bindings

All are from the trusted PyObjC project (maintained since 2002).

### Monitoring

- Dependabot will alert you to vulnerable dependencies
- Review `uv.lock` changes in PRs carefully
- Pin versions in `pyproject.toml` for stability

## Reporting Security Issues

If you discover a security vulnerability, please email the maintainer directly rather than opening a public issue.

## Additional Best Practices

### For Solo Maintainers

1. **Use 2FA** on GitHub and PyPI accounts
2. **Review all PRs carefully** before merging
3. **Check `pyproject.toml` changes** in every PR
4. **Verify built packages** before tagging releases

### For Team Projects

1. **Require 2+ approvals** for PRs
2. **Separate roles**: Some can merge, only leads can tag
3. **Enable environment protection** with manual approval
4. **Regular security audits** of dependencies and workflows

## Audit Log

- 2026-06-15: Switched from auto-publish to tag-based releases
- 2026-06-15: Added version verification step
- 2026-06-15: Reduced publish job permissions to read-only
