# Changelog

## Unreleased

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

First public release of **המשבץ (hameshabetz)** in the **קלוד-למורה (claude-lamora)**
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
