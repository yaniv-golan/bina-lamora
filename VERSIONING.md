# Versioning

This project uses [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`).

## Version Source of Truth

The canonical version lives in `skill-packager.json` (and the root `VERSION` file) at the repo root. All other version locations are updated from it.

## Version Locations

The version appears in these files (all managed by the bump script):

1. `skill-packager.json` — source of truth
2. `VERSION` — plain-text copy at repo root
3. `hameshabetz/.claude-plugin/plugin.json` — `"version"` field
4. `.claude-plugin/marketplace.json` — `metadata.version` (if marketplace format enabled)
5. `.cursor-plugin/plugin.json` — `"version"` field (if Cursor format enabled)
6. `hameshabetz/.codex-plugin/plugin.json` — `"version"` field (native Codex/ChatGPT plugin;
   the native marketplace `.agents/plugins/marketplace.json` carries no version, the plugin does)
7. `hameshabetz/skills/*/SKILL.md` — `metadata.version` in YAML frontmatter
8. `hameshabetz/skills/*/VERSION` — copied from root (if present)
9. `.agents/skills/` copies (if they exist) — in this repo `.agents/skills/hameshabetz`
   is a **symlink** to the canonical skill, so it tracks the version automatically and
   the bump script does not need to touch it

The bump script updates whichever of these are present and skips the optional
ones that are not enabled. Run `python3 tools/validate.py` (also enforced in CI)
to confirm the marketplace, plugin manifest, and skills stay structurally valid.

## Bumping the Version

```bash
# Set a new version and propagate to all locations:
python3 tools/bump-version.py . 0.2.0

# Or from the repo root with current directory:
python3 tools/bump-version.py . 0.2.0
```

## Release Process

```bash
# 1. Bump version
python3 tools/bump-version.py . X.Y.Z
# 2. Update CHANGELOG.md with release notes
# 3. Commit
git commit -am "chore: bump version to X.Y.Z"
# 4. Tag and push
git tag vX.Y.Z
git push origin main --tags
```

Pushing a `vX.Y.Z` tag triggers `.github/workflows/release.yml`, which validates
the repo and creates a GitHub Release with plugin and marketplace zips attached.
Every push and pull request also runs `.github/workflows/validate.yml`.
