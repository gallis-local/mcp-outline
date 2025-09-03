#!/bin/bash
# Simple test script to verify the semantic versioning setup works
set -e

echo "Testing semantic-release dry run..."
npx semantic-release --dry-run

echo ""
echo "Current version in pyproject.toml:"
grep '^version = ' pyproject.toml

echo ""
echo "Latest git tag (if any):"
git describe --tags --abbrev=0 2>/dev/null || echo "No tags found"

echo ""
echo "Semantic versioning setup test complete!"