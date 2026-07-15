# Data formats

All files are UTF-8 JSON. IDs are stable strings (`s000`, `s001`, ...) assigned by
parse_input.py — everything downstream keys on them, never on names.

## mapping.json (input to parse_input.py)

```json
{
  "name": "שם התלמיד/ה",
  "gan": "מאיזה גן הגעתם?",
  "choices": ["חבר/ה 1", "חבר/ה 2", "חבר/ה 3"],
  "gender": null,
  "mishalevet": null,
  "notes": null,
  "class": null,
  "mishalevet_names": ["נועה כהן", "איתי לוי"]
}
```

Values are the *exact* column headers from the export (or null if absent).
`mishalevet_names` is the alternative when there's no form column — the counselor's list.
`class` is an optional pre-assigned class column (anchor kids); its raw value lands on
each student as `pre_class` and is interpreted by parse_notes.py, never by the solver
directly. Multi-sheet xlsx: pass `--sheet "שם"`, or let auto-detection pick the sheet
whose headers match the mapping (ambiguity = clean JSON error listing sheet names).

## proposed_constraints.json (parse_notes.py output — a PROPOSAL, human-confirmed)

```json
{
  "class_names": ["א1", "א2", "א3"],
  "locks": [{"student": "s011", "student_name": "אלונה", "raw": "א3", "class_name": "א3", "class_index": 2}],
  "apart": [{"chooser": "s007", "chooser_name": "...", "raw": "לא עם ינאי נא", "target": "s044", "target_name": "ינאי נא"}],
  "together": [{"chooser": "s005", "chooser_name": "...", "raw": "עדיפות עם אלון נז", "target": "s008", "target_name": "אלון נז"}],
  "tags": {"kochav": [{"student": "s049", "student_name": "ירדן"}], "shiluv": []},
  "unresolved": [{"student": "s050", "student_name": "כרמי", "kind": "apart", "raw": "לא עם ...", "raw_target": "...", "candidates": []}],
  "warnings": []
}
```

Nothing here is applied automatically — the assistant shows a Hebrew table, gets
confirmation, then writes the confirmed subset into config.json.

## students.json (parse_input.py output)

```json
{
  "students": [
    {"id": "s000", "name": "דני אברהם", "gan": "דקל", "gender": "M",
     "mishalevet": false, "raw_choices": ["יוסי לוי", "נעה", ""], "notes": "",
     "pre_class": ""}
  ],
  "warnings": ["duplicate student name ..."],
  "gans": ["דקל", "חרוב"],
  "counts": {"students": 100, "mishalevet": 4}
}
```

## reconciled.json (reconcile_names.py output)

students.json plus, per student:

```json
"choices": [{"rank": 1, "target": "s014", "raw": "יוסי לוי", "status": "matched", "score": 0.97}]
```

(`status` is "matched" for auto-accepted or "resolved" for human-decided choices; both
count identically downstream.)

and top-level:

```json
"reconciliation": {
  "matched": 270,
  "ambiguous": [{"chooser": "s003", "chooser_name": "...", "chooser_gan": "...", "rank": 2,
                 "raw": "נעה", "candidates": [{"id": "s011", "name": "נועה כהן", "gan": "דקל", "score": 0.9}]}],
  "unmatched": [{"chooser": "s005", "chooser_name": "...", "rank": 3, "raw": "...", "reason": "..."}],
  "zero_matched_choices": [{"id": "...", "name": "...", "gan": "..."}],
  "no_choices_on_form": []
}
```

`ambiguous` must be emptied (via resolutions) before solving — the solver ignores
pending ambiguous choices, which silently weakens the guarantee for those kids.

## resolutions.json (human decisions, input to reconcile_names.py)

```json
{"resolutions": [
  {"chooser": "s003", "rank": 2, "target": "s011"},
  {"chooser": "s007", "rank": 1, "target": null}
]}
```

`target: null` = drop that choice (e.g., friend moved to another school).

## config.json (input to solve/validate/board/excel)

```json
{
  "num_classes": 4,
  "class_names": ["א1", "א2", "א3", "א4"],
  "min_size": null,
  "max_size": null,
  "gan_tolerance": 1,
  "weights": {"rank1": 5, "rank2": 3, "rank3": 2, "gan_dev": 8, "gender_dev": 1},
  "locks": {"s001": 0},
  "apart": [["s004", "s009"]],
  "together": [["s012", "s013"]],
  "gan_class_restrictions": {"סיגלון": ["א1", "א3"]}
}
```

null sizes → even split ±2. `locks` maps student id → class index (0-based). Canonical
class-name style is geresh-free ("א1"); matching is lenient ("א'1" resolves too), but
two names identical after normalization are a loud error.
`gan_class_restrictions` maps a (normalized) gan name → list of class names the gan is
allowed in. Hard, never auto-relaxed; a gan or class name that doesn't resolve is a hard
error in solve.py, validate_solution.py AND build_board.py (silent no-ops forbidden).
A CONFIG lock that contradicts a restriction is an immediate error; a lock from a
fingerprinted BOARD export (counselor decision) overrides the restriction for that
child only, with a warning — see solver-notes.md.

## solution.json (solve.py output)

```json
{"assignment": {"s000": 2}, "engine": "cpsat", "status": "OPTIMAL",
 "objective": 412.0, "relaxations": [], "fallback": false, "proven_optimal": true,
 "num_classes": 4, "class_names": ["א'1", "..."]}
```

Non-empty `relaxations` = tell the user what was given up. `fallback: true` = OR-Tools
was unavailable and the local engine ran instead — MUST be relayed to the user in plain
language (see SKILL.md "Network access"). An explicit `--engine local` is not a fallback.

## board_state.json (downloaded/pasted from the board's save button)

```json
{"assignment": {"s000": 2, "...": 1}, "locks": ["s000", "s017"],
 "autoPinned": {"s017": 0},
 "version": 2, "fingerprint": "a1b2c3d4e5f6", "saved_at": "2026-07-15T19:04:11.000Z"}
```

`autoPinned` maps drag-created locks to the child's pre-drag class (deliberate pins and
anchors are absent from it) — use it in Stage 5 to distinguish decisions from drags.
`saved_at` (ISO) disambiguates multiple saves of the SAME version ("(1).json" files):
the later saved_at is the newer save; confirm with the user. Both fields are ignored by
solve/validate (safe passthrough).

Feed to `solve.py --board-state` and `validate_solution.py --board-state` — locked kids
keep their class, the rest re-optimize (current assignment is a warm-start hint). Also
feed to `build_board.py --board-state` when REBUILDING a board: the export's locks come
back pre-locked as plain pins, never as "נקבע מראש" anchors (that marker is provenance
of config locks / pre-assigned kids only).
**Lock semantics:** when `fingerprint`/`version` is present (any board built by the
current build_board.py), the export's lock list REPLACES config locks — the board
pre-locks all config anchors, so an anchor absent from the list was deliberately
unlocked by the counselor. Legacy exports without a fingerprint merge over config locks
(old behavior). Compare `version` against your newest board to catch edits made on a
stale file.

## Board DATA payload extras (v1.2)

Beyond students/assignment/classNames/anchors/apart/together/version/generated/
fingerprint, the payload carries: `restrictions` (gan → allowed class INDICES, resolved
and validated at build time), `preLocked` (counselor pins carried from a previous
export via build_board --board-state), `draft` (read-only preview flag), per-student
`gender` + `pre_class`, and `capsule` — the session capsule for resuming in a new chat:

```json
"capsule": {
  "config": { "...the raw config.json..." },
  "reconciliation_summary": {
    "unmatched": [{"chooser_name": "...", "raw": "..."}],
    "zero_matched_choices": [{"name": "...", "gan": "..."}],
    "no_choices_on_form": [{"name": "...", "gan": "..."}]
  },
  "warnings": ["..."]
}
```

Raw notes are EXCLUDED from the payload (privacy — the board circulates). The
`unmatched.raw` strings are parent-typed names, not behavioral notes. Canonicity:
config.json is canonical while the session lives; the capsule is canonical only in a
FRESH chat, and only from the board whose fingerprint/version matches the export being
processed; every config edit must be flushed into a new board build (version bump)
before hand-off — a config hash is folded into the fingerprint as defense-in-depth.

## Exit codes (contract)

| script               | 0            | 1                          | 2 |
|----------------------|--------------|----------------------------|---|
| parse_input.py       | ok           | file/usage error           | mapping/sheet/duplicate-header error |
| reconcile_names.py   | ok           | —                          | bad resolution target |
| parse_notes.py       | ok           | —                          | bad args / class-name collision |
| solve.py             | ok           | ortools missing (--engine cpsat) | config error (unknown ids, range, restriction conflicts, locked-pair conflict) / no solution |
| validate_solution.py | no hard violations (warnings allowed) | — | hard violations |
| build_board.py       | ok           | template error             | config/roster mismatch, restriction/class-name errors |
| export_excel.py      | ok           | file error                 | — |
