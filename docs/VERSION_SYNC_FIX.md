# Version Synchronization Fix

## Problem

The pyproject.toml version was not staying in sync with git release tags. For example:
- Latest git tag: `v0.4.0`
- pyproject.toml version: `0.3.0`

This caused confusion for end users who would see inconsistent version information.

## Root Cause

The semantic-release configuration was missing the `@semantic-release/git` plugin. While the `@semantic-release/exec` plugin was correctly updating the pyproject.toml version during releases, those changes were never committed back to the repository.

The release process was:
1. ✅ `@semantic-release/exec` updates pyproject.toml version
2. ❌ No commit of the updated version file
3. ✅ `@semantic-release/github` creates release tag
4. ❌ Repository still shows old version in pyproject.toml

## Solution

Added the `@semantic-release/git` plugin to commit the version changes back to the repository.

### Changes Made

1. **package.json**: Added `@semantic-release/git` dependency
2. **.releaserc.json**: Added `@semantic-release/git` plugin configuration

The new release process is:
1. ✅ `@semantic-release/exec` updates pyproject.toml version
2. ✅ `@semantic-release/git` commits the updated pyproject.toml
3. ✅ `@semantic-release/github` creates release tag
4. ✅ Repository version stays in sync with release tags

### Plugin Order

The plugins execute in this order:
1. `@semantic-release/commit-analyzer` - determines if a release is needed
2. `@semantic-release/release-notes-generator` - generates release notes
3. `@semantic-release/exec` (prepare) - updates pyproject.toml version
4. `@semantic-release/git` (prepare) - commits the updated file
5. `@semantic-release/github` (publish) - creates the GitHub release

### Git Plugin Configuration

```json
[
  "@semantic-release/git",
  {
    "assets": ["pyproject.toml"],
    "message": "chore(release): v${nextRelease.version} [skip ci]\n\n${nextRelease.notes}"
  }
]
```

This configuration:
- Only commits `pyproject.toml` (not other generated files)
- Uses a consistent commit message format
- Includes `[skip ci]` to prevent triggering CI on the version bump commit
- Includes release notes in the commit message

## Testing

The fix includes a test script `test_version_sync.py` that validates:
- All required semantic-release plugins are configured
- The git plugin includes pyproject.toml in assets
- The exec plugin updates pyproject.toml
- Dependencies are properly installed

## Expected Behavior

Going forward, when releases are created:
1. The release process will automatically update pyproject.toml with the new version
2. Commit that change back to the repository with message "chore(release): vX.Y.Z [skip ci]"
3. Create the GitHub release tag
4. Users will always see consistent version information between git tags and pyproject.toml