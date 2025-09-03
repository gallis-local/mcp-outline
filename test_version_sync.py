#!/usr/bin/env python3
"""
Test script to validate semantic-release version synchronization.
This script tests that the semantic-release configuration will properly
update and commit the pyproject.toml version.
"""

import json
import re
import subprocess
import sys
from pathlib import Path


def read_pyproject_version():
    """Read the current version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()
    match = re.search(r'version = "([^"]+)"', content)
    if match:
        return match.group(1)
    return None


def read_releaserc_config():
    """Read and validate the .releaserc.json configuration."""
    releaserc_path = Path(".releaserc.json")
    with open(releaserc_path) as f:
        config = json.load(f)
    return config


def check_dependencies():
    """Check that all required dependencies are installed."""
    try:
        result = subprocess.run(
            ["npm", "list", "@semantic-release/git"],
            capture_output=True,
            text=True,
            check=True
        )
        return "@semantic-release/git" in result.stdout
    except subprocess.CalledProcessError:
        return False


def test_semantic_release_config():
    """Test that semantic-release configuration is correct."""
    config = read_releaserc_config()
    
    # Check that required plugins are present
    plugins = config.get("plugins", [])
    plugin_names = []
    
    for plugin in plugins:
        if isinstance(plugin, str):
            plugin_names.append(plugin)
        elif isinstance(plugin, list) and len(plugin) > 0:
            plugin_names.append(plugin[0])
    
    required_plugins = [
        "@semantic-release/commit-analyzer",
        "@semantic-release/release-notes-generator", 
        "@semantic-release/exec",
        "@semantic-release/git",
        "@semantic-release/github"
    ]
    
    missing_plugins = [p for p in required_plugins if p not in plugin_names]
    if missing_plugins:
        print(f"❌ Missing required plugins: {missing_plugins}")
        return False
    
    # Check @semantic-release/git configuration
    git_plugin = None
    for plugin in plugins:
        if isinstance(plugin, list) and plugin[0] == "@semantic-release/git":
            git_plugin = plugin[1] if len(plugin) > 1 else {}
            break
    
    if not git_plugin:
        print("❌ @semantic-release/git plugin not configured")
        return False
    
    if "pyproject.toml" not in git_plugin.get("assets", []):
        print("❌ pyproject.toml not included in git assets")
        return False
    
    # Check @semantic-release/exec configuration
    exec_plugin = None
    for plugin in plugins:
        if isinstance(plugin, list) and plugin[0] == "@semantic-release/exec":
            exec_plugin = plugin[1] if len(plugin) > 1 else {}
            break
    
    if not exec_plugin:
        print("❌ @semantic-release/exec plugin not configured")
        return False
    
    prepare_cmd = exec_plugin.get("prepareCmd", "")
    if "pyproject.toml" not in prepare_cmd:
        print("❌ prepareCmd does not update pyproject.toml")
        return False
    
    print("✅ All semantic-release plugins configured correctly")
    return True


def main():
    """Run all tests."""
    print("=== Testing semantic-release version synchronization ===")
    print()
    
    current_version = read_pyproject_version()
    print(f"Current pyproject.toml version: {current_version}")
    
    # Test dependencies
    if not check_dependencies():
        print("❌ @semantic-release/git dependency not installed")
        sys.exit(1)
    print("✅ @semantic-release/git dependency installed")
    
    # Test configuration
    if not test_semantic_release_config():
        sys.exit(1)
    
    print()
    print("=== Test Results ===")
    print("✅ Dependencies installed correctly")
    print("✅ Semantic-release configuration is correct")
    print("✅ Version synchronization should work properly")
    print()
    print("Expected behavior:")
    print("  1. @semantic-release/exec updates pyproject.toml version")
    print("  2. @semantic-release/git commits the updated pyproject.toml")
    print("  3. @semantic-release/github creates the release tag")
    print("  4. Repository version stays in sync with release tags")


if __name__ == "__main__":
    main()