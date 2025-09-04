# Semantic Version Release Patching

This document describes the enhanced semantic versioning setup for mcp-outline that ensures proper dependency updates and release management.

## Overview

The semantic release flow has been enhanced to:
- Ensure version synchronization between `pyproject.toml` and git tags
- Properly include dependency updates in releases
- Prevent manual version bumps that break the flow
- Provide robust release detection in CI/CD

## Key Components

### 1. Version Synchronization (`scripts/validate-version.sh`)

Validates that the version in `pyproject.toml` matches the latest git tag, preventing manual version bumps that break semantic-release.

```bash
# Run validation
./scripts/validate-version.sh

# Auto-fix version mismatches
AUTO_FIX=true ./scripts/validate-version.sh
```

### 2. Enhanced Release Detection (`.github/workflows/docker.yaml`)

Improved Docker workflow that:
- Compares tag counts before/after semantic-release
- Checks multiple release success patterns
- Provides detailed logging for troubleshooting

### 3. Dependabot Integration (`.github/dependabot.yml`)

Configured to use conventional commits:
- `fix(deps):` for dependency updates (triggers patch releases)
- `chore(deps):` for development dependencies
- Automatic PR creation with proper labels

### 4. Version Validation Workflow (`.github/workflows/version-validation.yml`)

Prevents manual version bumps in pull requests by validating that only semantic-release modifies versions.

## Usage

### For Dependency Updates

Dependency updates are automatically handled by Dependabot:

1. Dependabot creates PR with `fix(deps):` commit
2. PR merge triggers semantic-release
3. Patch version is automatically bumped
4. Docker image is built with new version

### For Feature/Bug Fix Releases

Use conventional commits:

```bash
# Patch release (0.5.0 -> 0.5.1)
git commit -m "fix: resolve issue with document search"

# Minor release (0.5.0 -> 0.6.0)  
git commit -m "feat: add new collaboration features"

# Major release (0.5.0 -> 1.0.0)
git commit -m "feat!: redesign API interface

BREAKING CHANGE: API endpoints have been restructured"
```

### Testing Release Flow

```bash
# Validate current setup
./scripts/validate-version.sh

# Test complete release flow
./scripts/test-release-flow.sh

# Test semantic-release dry run
npx semantic-release --dry-run
```

## Branch Configuration

- **main**: Stable releases (v1.2.3) → Docker tags: `latest`, `v1.2.3`
- **rc**: Pre-releases (v1.2.3-rc.1) → Docker tags: `rc`, `v1.2.3-rc.1`

## Common Issues & Solutions

### Version Mismatch Error

```
❌ Manual version bump detected!
pyproject.toml: 0.5.1
Latest tag: 0.5.0
```

**Solution**: Reset version to match latest tag:
```bash
# Auto-fix
AUTO_FIX=true ./scripts/validate-version.sh

# Manual fix
sed -i 's/version = ".*"/version = "0.5.0"/' pyproject.toml
```

### Dependency Updates Not Creating Releases

**Causes**:
- Non-conventional commit messages
- Missing `fix:` or `feat:` prefix
- Commits on non-release branches

**Solution**: Ensure Dependabot PRs use conventional commits (configured in `.github/dependabot.yml`)

### Docker Build Not Triggering

**Causes**:
- Semantic-release didn't create a new tag
- Release detection logic failed

**Solution**: Check workflow logs for release detection output and semantic-release messages

## Files Modified

- `pyproject.toml`: Version reset to match latest tag (0.5.0)
- `.github/workflows/docker.yaml`: Enhanced release detection logic
- `.github/dependabot.yml`: Added conventional commit configuration
- `.github/workflows/version-validation.yml`: New workflow to prevent manual version bumps
- `scripts/validate-version.sh`: New validation script
- `scripts/test-release-flow.sh`: New integration test script

## Validation

All changes have been validated with:
- ✅ 83 test cases passing
- ✅ Version synchronization validation
- ✅ Integration test for release flow
- ✅ Semantic-release configuration validation

The enhanced semantic versioning setup ensures that dependency updates and code changes are properly included in releases, resolving the original issue where "updates are not properly being deployed during build for release and are missing fixes."