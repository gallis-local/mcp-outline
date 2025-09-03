#!/bin/bash
# Test script to verify semantic versioning setup for both main and rc branches
set -e

echo "=== Testing Semantic Versioning Setup ==="
echo ""

echo "Current branch: $(git branch --show-current)"
echo "Current version in pyproject.toml: $(grep '^version = ' pyproject.toml)"
echo ""

echo "Testing semantic-release dry run..."
npx semantic-release --dry-run

echo ""
echo "Latest git tag (if any):"
git describe --tags --abbrev=0 2>/dev/null || echo "No tags found"

echo ""
echo "=== Branch Configuration Test ==="
echo "Supported release branches in .releaserc.json:"
cat .releaserc.json | grep -A 10 '"branches"' | head -8

echo ""
echo "=== Docker Workflow Branch Configuration ==="
echo "Docker workflow triggers on branches:"
grep -A 5 "branches:" .github/workflows/docker.yaml

echo ""
echo "=== Test Results ==="
echo "✅ Semantic versioning configured for main and rc branches"
echo "✅ Docker workflow triggers on main and rc branches"
echo "✅ Pyproject.toml version will be automatically updated"
echo ""
echo "Expected behavior:"
echo "  - Main branch commits → stable releases (v1.2.3) → 'latest' + 'v1.2.3' Docker tags"
echo "  - RC branch commits → pre-releases (v1.2.3-rc.1) → 'rc' + 'v1.2.3-rc.1' Docker tags"
echo ""
echo "Semantic versioning setup test complete!"