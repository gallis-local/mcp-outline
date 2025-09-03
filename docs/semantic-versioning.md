# Semantic Versioning for Docker Builds

This repository now implements automatic semantic versioning for Docker image builds using conventional commits and semantic-release.

## How it works

1. **Conventional Commits**: Commits must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:
   - `feat:` for new features (minor version bump)
   - `fix:` for bug fixes (patch version bump)  
   - `feat!:` or `BREAKING CHANGE:` for breaking changes (major version bump)
   - `docs:`, `chore:`, `style:`, etc. for non-versioned changes

2. **Semantic Release**: On pushes to `main`, semantic-release analyzes commit messages and:
   - Determines the next version number
   - Updates the version in `pyproject.toml`
   - Creates a git tag

3. **Docker Image Tagging**: The Docker CI workflow builds and tags images with:
   - `latest` tag (always)
   - Semantic version tag (e.g., `v1.2.3`) when a new version is released

## Configuration Files

- `.releaserc.json`: Semantic-release configuration
- `.commitlintrc.json`: Commit message linting rules
- `package.json`: Node.js dependencies for semantic-release
- `.github/workflows/commitlint.yml`: PR commit message validation
- `.github/workflows/docker.yaml`: Updated Docker build with semantic versioning

## Testing

Run `./test_semantic_release.sh` to test the semantic versioning setup locally.

## Workflow Behavior

- **On main branch**: Semantic-release runs and may create new versions/tags
- **On feature branches**: No versioning occurs
- **Manual workflow dispatch**: Always builds with current version
- **Docker images**: Tagged with both `latest` and semantic version when a release is made

This approach provides automatic, consistent versioning based on the semantic meaning of changes while maintaining compatibility with existing deployment processes.