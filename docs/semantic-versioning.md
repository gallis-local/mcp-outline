# Semantic Versioning for Docker Builds

This repository implements automatic semantic versioning for Docker image builds using conventional commits and semantic-release, supporting both stable releases and release candidates.

## How it works

1. **Conventional Commits**: Commits must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:
   - `feat:` for new features (minor version bump)
   - `fix:` for bug fixes (patch version bump)  
   - `feat!:` or `BREAKING CHANGE:` for breaking changes (major version bump)
   - `docs:`, `chore:`, `style:`, etc. for non-versioned changes

2. **Semantic Release**: On pushes to `main` or `rc` branches, semantic-release analyzes commit messages and:
   - Determines the next version number
   - Updates the version in `pyproject.toml`
   - Creates a git tag
   - **Main branch**: Creates stable releases (e.g., `v1.2.3`)
   - **RC branch**: Creates pre-releases (e.g., `v1.2.3-rc.1`)

3. **Docker Image Tagging**: The Docker CI workflow builds and tags images differently based on the branch:
   - **Main branch releases**: `latest` + semantic version tag (e.g., `v1.2.3`)
   - **RC branch releases**: `rc` + semantic version tag (e.g., `v1.2.3-rc.1`)

## Configuration Files

- `.releaserc.json`: Semantic-release configuration (supports main and rc branches)
- `.commitlintrc.json`: Commit message linting rules
- `package.json`: Node.js dependencies for semantic-release
- `.github/workflows/commitlint.yml`: PR commit message validation
- `.github/workflows/docker.yaml`: Docker build with dual-branch semantic versioning

## Testing

Run `./test_semantic_release.sh` to test the semantic versioning setup locally.

## Workflow Behavior

- **On main branch**: Creates stable releases and tags Docker images with `latest` + `v{version}`
- **On rc branch**: Creates pre-releases and tags Docker images with `rc` + `v{version}-rc.{number}`
- **On feature branches**: No versioning occurs
- **Manual workflow dispatch**: Always builds with current version
- **Docker image promotion**: RC images never override `latest` tag, ensuring production stability

## Release Strategy

### Stable Releases (main branch)
```bash
# Example: Add new feature to main
git checkout main
git commit -m "feat: add document export feature"
git push
# Result: v1.2.0 release, Docker tags: latest + v1.2.0
```

### Release Candidates (rc branch)
```bash
# Example: Prepare release candidate
git checkout rc
git commit -m "feat: add experimental search filters"
git push
# Result: v1.3.0-rc.1 release, Docker tags: rc + v1.3.0-rc.1
```

This approach provides automatic, consistent versioning for both stable and pre-release versions while maintaining clear separation between production-ready and candidate releases.