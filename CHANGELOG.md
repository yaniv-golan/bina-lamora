# Changelog

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
