#!/usr/bin/env python3
"""Bump the project version and propagate it to every version location.

Usage:
    python3 tools/bump-version.py <repo_root> <new_version>
    python3 tools/bump-version.py . 1.3.0

The source of truth is ``skill-packager.json`` (and the plain-text ``VERSION``
file). This script rewrites every other location listed in ``VERSIONING.md``,
skipping any that do not exist so the repo can enable/disable output formats
without breaking the bump.

Version strings must be plain SemVer (``MAJOR.MINOR.PATCH``).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def fail(msg: str) -> "None":
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def set_json_key(path: Path, dotted_key: str, value: str) -> bool:
    """Set a (possibly nested) key in a JSON file if the file exists.

    Returns True if the file was updated, False if it was absent.
    """
    if not path.exists():
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    node = data
    parts = dotted_key.split(".")
    for part in parts[:-1]:
        if part not in node or not isinstance(node[part], dict):
            # Nested container missing (e.g. optional metadata block) — skip.
            return False
        node = node[part]
    node[parts[-1]] = value
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def set_text(path: Path, value: str) -> bool:
    if not path.exists():
        return False
    path.write_text(value + "\n", encoding="utf-8")
    return True


def set_skill_frontmatter_version(path: Path, value: str) -> bool:
    """Update ``version:`` inside a SKILL.md YAML frontmatter block."""
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    new_text, n = re.subn(
        r'(?m)^(\s*version:\s*)"?[^"\n]+"?\s*$',
        rf'\g<1>"{value}"',
        text,
        count=1,
    )
    if n == 0:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> None:
    if len(sys.argv) != 3:
        fail("usage: bump-version.py <repo_root> <new_version>")

    root = Path(sys.argv[1]).resolve()
    new_version = sys.argv[2].strip()

    if not root.is_dir():
        fail(f"repo root is not a directory: {root}")
    if not SEMVER.match(new_version):
        fail(f"version must be MAJOR.MINOR.PATCH, got: {new_version!r}")

    updated: list[str] = []
    skipped: list[str] = []

    def record(rel: str, changed: bool) -> None:
        (updated if changed else skipped).append(rel)

    # 1. skill-packager.json — source of truth
    record("skill-packager.json", set_json_key(root / "skill-packager.json", "version", new_version))
    # 2. VERSION — plain text at repo root
    record("VERSION", set_text(root / "VERSION", new_version))
    # 3. plugin.json
    record(
        "hameshabetz/.claude-plugin/plugin.json",
        set_json_key(root / "hameshabetz/.claude-plugin/plugin.json", "version", new_version),
    )
    # 4. marketplace.json (metadata.version)
    record(
        ".claude-plugin/marketplace.json",
        set_json_key(root / ".claude-plugin/marketplace.json", "metadata.version", new_version),
    )
    # 5. Cursor plugin (optional)
    record(
        ".cursor-plugin/plugin.json",
        set_json_key(root / ".cursor-plugin/plugin.json", "version", new_version),
    )
    # 5b. Codex/ChatGPT native plugin (optional). The native marketplace
    # (.agents/plugins/marketplace.json) carries no version — the plugin does.
    record(
        "hameshabetz/.codex-plugin/plugin.json",
        set_json_key(root / "hameshabetz/.codex-plugin/plugin.json", "version", new_version),
    )
    # 6/7. Each skill's SKILL.md frontmatter + optional per-skill VERSION file
    skills_root = root / "hameshabetz" / "skills"
    if skills_root.is_dir():
        for skill_md in sorted(skills_root.glob("*/SKILL.md")):
            rel = skill_md.relative_to(root).as_posix()
            record(rel, set_skill_frontmatter_version(skill_md, new_version))
            record(
                skill_md.with_name("VERSION").relative_to(root).as_posix(),
                set_text(skill_md.with_name("VERSION"), new_version),
            )

    print(f"Bumped version to {new_version}")
    print("\nUpdated:")
    for rel in updated:
        print(f"  ✓ {rel}")
    if skipped:
        print("\nSkipped (absent / not applicable):")
        for rel in skipped:
            print(f"  - {rel}")


if __name__ == "__main__":
    main()
