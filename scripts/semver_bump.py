#!/usr/bin/env python3
"""
Compute semantic version bump from recent commits and update pyproject.toml.

Heuristics:
- Major: commits containing "BREAKING CHANGE" or conventional commit with '!': e.g., feat!:, refactor!: etc.
- Minor: commits starting with "feat" (Conventional Commits).
- Patch: commits starting with fix/perf/refactor/chore/docs/build/test/ci/style or Dependabot bump messages.

If no qualifying commits since last tag, no change is made and the current version is printed.

Outputs new version on stdout.
Exit codes:
  0: success (version may or may not have changed)
  10: no bump detected (version unchanged)
  non-zero other: error
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from typing import List, Optional, Tuple
import argparse


RE_CONV_BREAKING = re.compile(r"^[a-zA-Z]+(?:\([^)]+\))?!:\s")
RE_CONV_FEAT = re.compile(r"^feat(?:\([^)]+\))?:\s")
RE_CONV_PATCH_TYPES = re.compile(
    r"^(fix|perf|refactor|chore|docs|build|test|ci|style)(?:\([^)]+\))?:\s"
)


def run_git(*args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def last_tag() -> Optional[str]:
    try:
        return run_git("describe", "--tags", "--abbrev=0") or None
    except Exception:
        return None


def commit_messages_since(ref: Optional[str]) -> List[str]:
    range_arg = f"{ref}..HEAD" if ref else "HEAD"
    try:
        log = run_git("log", "--pretty=%s%n%b", range_arg)
    except RuntimeError:
        # Probably no commits yet
        return []
    msgs = [m.strip() for m in log.splitlines() if m.strip()]
    return msgs


def detect_bump(messages: List[str]) -> Optional[str]:
    bump = None  # 'major' | 'minor' | 'patch'
    for msg in messages:
        # Dependabot merge/bump detection
        if "dependabot" in msg.lower() or msg.startswith("Bump "):
            bump = max_bump(bump, "patch")
            continue

        # Conventional Commits detection
        if "BREAKING CHANGE" in msg or RE_CONV_BREAKING.search(msg):
            bump = max_bump(bump, "major")
            continue
        if RE_CONV_FEAT.search(msg):
            bump = max_bump(bump, "minor")
            continue
        if RE_CONV_PATCH_TYPES.search(msg):
            bump = max_bump(bump, "patch")
            continue

    return bump


def max_bump(a: Optional[str], b: str) -> str:
    order = {"patch": 0, "minor": 1, "major": 2}
    if a is None:
        return b
    return a if order[a] >= order[b] else b


def read_current_version(pyproject_path: str) -> Tuple[str, int, int, int]:
    with open(pyproject_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find [project] table block, then version within it
    project_start = None
    for m in re.finditer(r"^\s*\[project\].*$", content, flags=re.MULTILINE):
        project_start = m.end()
        break
    if project_start is None:
        raise RuntimeError("[project] table not found in pyproject.toml")

    # Find the next table header or end of file to bound the project table
    next_table = re.search(r"^\s*\[.+\].*$", content[project_start:], flags=re.MULTILINE)
    if next_table:
        project_block_end = project_start + next_table.start()
    else:
        project_block_end = len(content)
    project_block = content[project_start:project_block_end]

    # Allow single or double quotes and optional trailing comments
    version_match = re.search(
        r"^\s*version\s*=\s*[\"'](\d+)\.(\d+)\.(\d+)[\"']",
        project_block,
        flags=re.MULTILINE,
    )
    if not version_match:
        raise RuntimeError("version not found in [project] table")
    major, minor, patch = map(int, version_match.groups())
    return content, major, minor, patch


def write_new_version(pyproject_path: str, content: str, new_version: str) -> None:
    # Replace only inside [project] table
    def repl(m: re.Match) -> str:
        block = m.group(0)
        block = re.sub(
            r"^(\s*version\s*=\s*)['\"]\d+\.\d+\.\d+['\"](.*)$",
            rf'\1"{new_version}"\2',
            block,
            flags=re.MULTILINE,
        )
        return block

    new_content, count = re.subn(
        r"(?ms)(^\s*\[project\]\s*$)(.*?)(?=^\s*\[|\Z)",
        lambda m: m.group(1) + repl(m),
        content,
    )
    if count == 0:
        raise RuntimeError("Failed to update version in [project] table")

    with open(pyproject_path, "w", encoding="utf-8") as f:
        f.write(new_content)


def bump_version(maj: int, min_: int, pat: int, bump: str) -> Tuple[int, int, int]:
    if bump == "major":
        return maj + 1, 0, 0
    if bump == "minor":
        return maj, min_ + 1, 0
    if bump == "patch":
        return maj, min_, pat + 1
    raise ValueError(f"Unknown bump: {bump}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bump pyproject version based on commits or a requested bump.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--bump", choices=["major", "minor", "patch"], help="Force a bump level regardless of commits.")
    group.add_argument("--version", help="Set an explicit version (e.g., 1.2.3). Overrides --bump.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = run_git("rev-parse", "--show-toplevel")
    os.chdir(repo_root)

    # Ensure tags are available (in CI, runner should fetch tags beforehand)
    try:
        run_git("fetch", "--tags", check=False)
    except Exception:
        pass

    tag = last_tag()
    messages = commit_messages_since(tag)
    bump = args.bump or detect_bump(messages)

    pyproject_path = os.path.join(repo_root, "pyproject.toml")
    content, maj, min_, pat = read_current_version(pyproject_path)
    current_version = f"{maj}.{min_}.{pat}"

    # If explicit --version is provided, set it directly
    if args.version:
        new_version = args.version.strip()
        if new_version == current_version:
            print(new_version)
            return 10
        write_new_version(pyproject_path, content, new_version)
        print(new_version)
        return 0

    if not bump:
        print(current_version)
        return 10  # No bump

    nmaj, nmin, npat = bump_version(maj, min_, pat, bump)
    new_version = f"{nmaj}.{nmin}.{npat}"

    if new_version == current_version:
        print(new_version)
        return 10

    write_new_version(pyproject_path, content, new_version)
    print(new_version)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
