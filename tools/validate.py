#!/usr/bin/env python3
"""Validate the claude-lamora marketplace and its plugins.

Checks the structural invariants that the Claude plugin loader relies on:
  * ``.claude-plugin/marketplace.json`` parses and has the required fields.
  * Every plugin listed in the marketplace resolves to a real directory with a
    valid ``.claude-plugin/plugin.json``.
  * Each plugin's declared ``skills`` directory exists and every skill has a
    ``SKILL.md`` with ``name`` and ``description`` frontmatter.

Exits non-zero (and prints ``::error::`` lines for GitHub Actions) on any
problem. Run from the repo root: ``python3 tools/validate.py``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)
    print(f"::error::{msg}", file=sys.stderr)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        err(f"missing file: {path.relative_to(ROOT)}")
    except json.JSONDecodeError as e:
        err(f"invalid JSON in {path.relative_to(ROOT)}: {e}")
    return None


def read_frontmatter(skill_md: Path) -> dict:
    """Minimal YAML-frontmatter reader (key: value pairs between --- fences)."""
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end]
    out: dict[str, str] = {}
    for line in block.splitlines():
        if line.strip().startswith("#") or ":" not in line:
            continue
        if line[:1] in (" ", "\t"):  # skip nested keys (e.g. metadata children)
            continue
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def validate_skill(skill_dir: Path, plugin_name: str) -> None:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        err(f"[{plugin_name}] skill {skill_dir.name}: missing SKILL.md")
        return
    fm = read_frontmatter(skill_md)
    for field in ("name", "description"):
        if not fm.get(field):
            err(f"[{plugin_name}] {skill_dir.name}/SKILL.md: missing '{field}' in frontmatter")


def validate_plugin(entry: dict, marketplace_dir: Path) -> None:
    name = entry.get("name", "<unnamed>")
    source = entry.get("source")
    if not source:
        err(f"plugin '{name}': missing 'source'")
        return
    plugin_dir = (marketplace_dir / source).resolve()
    if not plugin_dir.is_dir():
        err(f"plugin '{name}': source directory not found: {source}")
        return

    manifest = load_json(plugin_dir / ".claude-plugin" / "plugin.json")
    if manifest is None:
        return
    if manifest.get("name") != name:
        err(f"plugin '{name}': plugin.json name is '{manifest.get('name')}' (marketplace says '{name}')")

    skills_rel = manifest.get("skills", "./skills")
    skills_dir = (plugin_dir / skills_rel).resolve()
    if not skills_dir.is_dir():
        err(f"plugin '{name}': skills directory not found: {skills_rel}")
        return
    skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir()]
    if not skill_dirs:
        err(f"plugin '{name}': no skills under {skills_rel}")
    for d in sorted(skill_dirs):
        validate_skill(d, name)


def main() -> None:
    marketplace_path = ROOT / ".claude-plugin" / "marketplace.json"
    mk = load_json(marketplace_path)
    if mk is None:
        sys.exit(1)

    if not mk.get("name"):
        err("marketplace.json: missing 'name'")
    if not mk.get("owner"):
        err("marketplace.json: missing 'owner'")
    plugins = mk.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        err("marketplace.json: 'plugins' must be a non-empty array")
        plugins = []

    for entry in plugins:
        validate_plugin(entry, ROOT)

    if errors:
        print(f"\n{len(errors)} problem(s) found.", file=sys.stderr)
        sys.exit(1)
    print("✓ marketplace and all plugins are valid")


if __name__ == "__main__":
    main()
