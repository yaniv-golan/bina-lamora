# Changelog

## Unreleased

### Renamed: claude-lamora → bina-lamora
- Renamed the marketplace/repo/brand from **claude-lamora / קלוד־למורה** to
  **bina-lamora / בינה־למורה** ("AI for the teacher"), now that the tool runs on both
  Claude and ChatGPT and a vendor-specific name no longer fits. The skill itself
  (`hameshabetz` / המשבץ) is unchanged. The install address is now
  `yaniv-golan/bina-lamora`, and the site moves to
  `https://yaniv-golan.github.io/bina-lamora/`. Manifests, README, landing page,
  mockups, OG image, and the demo GIF were all updated. (The `.claude-plugin/` and
  `.codex-plugin/` directory names are format specs and intentionally unchanged.)

## 1.4.0 — 2026-07-19

### Native ChatGPT / Codex plugin
- Added first-class Codex/ChatGPT manifests so the repo is a native plugin in that ecosystem,
  not just legacy-compatible: `hameshabetz/.codex-plugin/plugin.json` (with `skills: "./skills/"`
  and a Codex `interface` block — displayName, category, brandColor, string `defaultPrompt`,
  websiteURL) and the native marketplace `.agents/plugins/marketplace.json` (`git-subdir` source).
  The Claude `.claude-plugin/` manifests are unchanged and still honored by older clients.
- Version tooling: `tools/bump-version.py` now propagates to the Codex plugin manifest, and
  `tools/validate.py` validates both the Codex plugin and the native marketplace (structure +
  version consistency). Schema verified against codex-cli 0.144.4.
- Install: `codex plugin marketplace add yaniv-golan/bina-lamora` — same address as Claude.

### Landing page
- Reworked `site/index.html` after an adversarial audience review: added an assistant
  **chooser** and a full, equally-detailed **ChatGPT install section** (plan-gate callout +
  desktop "Add marketplace" route with a copy chip + browser upload route with screenshots),
  so Claude and ChatGPT get equal, usable directions instead of ChatGPT being a FAQ footnote.
- Audience-fit fixes: resolved the "free tool" vs. paid-subscription contradiction (states the
  ~\$20/mo Pro price and that the free plan lacks plugins), a free-plan failure note on step 1,
  a Claude intro + privacy teaser in the hero, glossed English UI terms (Customize/Plugins/Sync),
  clearer marketplace-string wording, and Hebrew register cleanups (consistent plural address).

### ChatGPT parity
- Documented that ChatGPT (desktop app, Business/Enterprise/Edu/Healthcare) consumes this
  Claude marketplace repo **directly** — **Plugins → Add marketplace → `yaniv-golan/bina-lamora`**
  → Install — verified live. This is the real "equivalent target": same address as Claude, and
  updatable (`codex plugin marketplace upgrade` / refresh / restart), unlike the frozen zip upload.
  README (Hebrew + English) and the landing-page FAQ now lead with it; zip upload stays as the
  web fallback.
- Plugin manifest: added `homepage` and `interface.websiteURL` so ChatGPT's plugin detail page
  shows the landing page instead of "Website: Unavailable" (additive; Claude ignores `interface`).

## 1.3.0 — 2026-07-16

### Packaging
- **Universal repo**: the single canonical skill now fans out to every supported
  distribution format. Added a Cursor plugin manifest (`.cursor-plugin/plugin.json`)
  and the Agent Skills standard directory (`.agents/skills/hameshabetz`, a symlink to
  the canonical skill), alongside the existing Claude plugin and marketplace.
- README now documents installation on Claude Code, Cursor, Codex CLI, `npx skills add`,
  and manual Agent Skills targets, in addition to the Claude.ai/Cowork educator flow.
- `tools/validate.py` now also checks the Cursor manifest, the `.agents/skills/` copy,
  and version consistency across formats; release archives bundle the new formats.
- **One-click install**: added a hosted "Install in Claude Desktop" page
  (`static/install-claude-desktop.html`) deployed via GitHub Pages
  (`.github/workflows/deploy-pages.yml`), linked from the README with a button.
- **ChatGPT support**: releases now attach a bare-skill archive
  (`hameshabetz-skill-<version>.zip`, `SKILL.md` at the root) for ChatGPT Skills
  (Business/Enterprise/Edu/Healthcare) and other Agent-Skills uploads. README
  documents the ChatGPT path in both the Hebrew and English sections; Codex/manual
  install now point at the same bare-skill archive.

## 1.2.0 — 2026-07-15

First public release of **המשבץ (hameshabetz)** in the **בינה־למורה (bina-lamora)**
marketplace. Highlights of the v1.x line that led here:

### Board (לוח הסקירה)
- Versioned boards with a content fingerprint — a new board can never silently show an
  old board's edits.
- Every manual drag auto-locks the child (drag-back undoes it); undo button (↩, 20
  steps); in-page reset confirmation (no native dialogs — sandbox/kiosk safe).
- Selection info strip: clicking a child spells out, in words, whom they chose, who
  chose them, and any contradicted rules; ⚠ is clickable for details.
- Save dialog with three clear choices; JSON hidden behind a manual-copy button;
  versioned Hebrew file names; `saved_at` disambiguates duplicate saves.
- Read-only draft mode (`--draft`) for the first-look hand-off.
- Session capsule embedded in every board: a new chat can resume from the board + one
  export file (raw notes excluded — privacy).

### Pipeline
- Notes-column parsing to a human-confirmed constraints proposal ("לא עם", "עדיפות
  עם/לא עם", "כוכב", "שילוב", pre-assigned class column).
- `gan_class_restrictions` ("גן X רק בכיתות Y,Z") — hard, never auto-relaxed, loud
  errors on unresolvable names; a counselor's board lock overrides it per-child only.
- Multi-sheet xlsx auto-detection; gan-name normalization; duplicate-header guard.
- Local fallback engine with an explicit hard-constraint acceptance gate; relaxation-
  aware validator; deterministic pre-checks for contradictory locks.
- Deterministic exit-code contract and clean JSON errors everywhere (no stack traces).

### Docs
- Hebrew-first workflow for non-technical counselors: draft-board-first onboarding,
  scripted reconciliation dialogues, resume-in-a-new-chat protocol, error table.
