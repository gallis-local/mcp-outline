#!/bin/bash
# Semantic Version Validation Script
# This script validates that version changes follow semantic-release conventions

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Semantic Version Validation ===${NC}"

# Get current version from pyproject.toml
CURRENT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/' | tr -d '\r\n')
echo "Current pyproject.toml version: $CURRENT_VERSION"

# Get latest git tag
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null | sed 's/^v//' | tr -d '\r\n' || echo "0.0.0")
echo "Latest git tag version: $LATEST_TAG"

# Check if versions are in sync
if [[ "$CURRENT_VERSION" != "$LATEST_TAG" ]]; then
    echo -e "${YELLOW}⚠️  Version mismatch detected!${NC}"
    echo "pyproject.toml: $CURRENT_VERSION"
    echo "Latest tag: $LATEST_TAG"
    
    # Check if this is a semantic-release commit
    LAST_COMMIT_MSG=$(git log -1 --pretty=%s)
    if [[ "$LAST_COMMIT_MSG" == "chore(release):"* ]]; then
        echo -e "${GREEN}✅ This appears to be a semantic-release commit${NC}"
        exit 0
    fi
    
    echo -e "${RED}❌ Manual version bump detected!${NC}"
    echo ""
    echo -e "${YELLOW}Manual version changes break semantic versioning.${NC}"
    echo "Please use conventional commits to trigger automatic releases:"
    echo ""
    echo "  feat: description     → minor version bump"
    echo "  fix: description      → patch version bump"  
    echo "  feat!: description    → major version bump"
    echo "  BREAKING CHANGE       → major version bump"
    echo ""
    echo "To fix this, either:"
    echo "1. Reset version in pyproject.toml to match latest tag: $LATEST_TAG"
    echo "2. Or create a proper semantic-release with conventional commits"
    echo ""
    
    # Check if we should auto-fix
    if [[ "${AUTO_FIX:-}" == "true" ]]; then
        echo -e "${YELLOW}Auto-fixing version synchronization...${NC}"
        sed -i "s/version = \".*\"/version = \"$LATEST_TAG\"/" pyproject.toml
        echo -e "${GREEN}✅ Version reset to $LATEST_TAG${NC}"
    else
        exit 1
    fi
else
    echo -e "${GREEN}✅ Versions are synchronized${NC}"
fi

# Validate semantic-release configuration
echo ""
echo -e "${GREEN}=== Validating Semantic Release Configuration ===${NC}"

# Check if required semantic-release files exist
if [[ ! -f ".releaserc.json" ]]; then
    echo -e "${RED}❌ Missing .releaserc.json${NC}"
    exit 1
fi

if [[ ! -f "package.json" ]]; then
    echo -e "${RED}❌ Missing package.json${NC}"
    exit 1
fi

# Check if required plugins are installed
echo "Checking semantic-release plugins..."
required_plugins=(
    "@semantic-release/commit-analyzer"
    "@semantic-release/release-notes-generator"
    "@semantic-release/exec"
    "@semantic-release/git"
    "@semantic-release/github"
)

for plugin in "${required_plugins[@]}"; do
    if npm list "$plugin" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $plugin${NC}"
    else
        echo -e "${RED}❌ $plugin (missing)${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✅ All semantic-release plugins are installed${NC}"

# Validate release configuration
echo ""
echo "Validating .releaserc.json configuration..."
if jq empty .releaserc.json 2>/dev/null; then
    echo -e "${GREEN}✅ .releaserc.json is valid JSON${NC}"
    
    # Check for required plugins in config
    config_plugins=$(jq -r '.plugins[]' .releaserc.json 2>/dev/null || jq -r '.plugins[][]' .releaserc.json 2>/dev/null | head -5)
    echo "Configured plugins:"
    echo "$config_plugins" | while read -r plugin; do
        if [[ -n "$plugin" && "$plugin" != "null" ]]; then
            echo "  - $plugin"
        fi
    done
else
    echo -e "${RED}❌ .releaserc.json is invalid JSON${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=== Validation Complete ===${NC}"
echo "✅ Semantic versioning setup is valid"
echo "✅ Use conventional commits for automatic releases"
echo "✅ Dependency updates will trigger patch releases"