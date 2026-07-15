---
name: hameshabetz
description: המשבץ (HaMeshabetz) — assigns incoming students (e.g., ~100 first-graders) into balanced classes from a Google Forms friend-choice export. Handles Hebrew name reconciliation, hard/soft constraints (every child with at least one chosen friend, one special-ed "mishalevet" child per class, kindergarten/gan spread, class sizes), CP-SAT optimization, an RTL drag-and-drop review board for counselors, and Excel rosters. Use when the user mentions class placement, "שיבוץ כיתות", splitting a grade into classes, friend choices from a form, sociometric class assignment, or wants to rebalance/re-solve after manual edits.
metadata:
  author: Yaniv Golan (lool ventures)
  version: "1.2.0"
---

# Class Builder (שיבוץ כיתות)

Turn a Google Forms "pick 3 friends" export into a balanced class assignment, then hand
the counselors a drag-and-drop review board and final Excel rosters. Replaces the
two-day memo-sticker ritual with an hour of guided work.

**Users are school counselors, not technical people.** Communicate in plain language
(**Hebrew whenever the roster is Hebrew, regardless of the language the user writes
in**), never show raw JSON or stack traces, and always explain *what* you found and
*what you need from them*. Pacing: Stage 1's parameters may be asked as ONE compact
message; the ambiguity and proposal tables are batched by design; everything else is
one question at a time.

**Privacy: this is data about minors.** Process everything locally. Never web-search
children's names, never send the roster to external services, and remind the user the
final files contain sensitive data.

## Pipeline overview

```
Form export (CSV/XLSX)
  → 1. Intake & column mapping          (you + parse_input.py)
  → 2. Name reconciliation              (reconcile_names.py + human review)
  → 2.5 Notes & pre-assigned classes    (parse_notes.py + human confirmation)
  → 3. Solve                            (solve.py — CP-SAT or fallback)
  → 4. Review board                     (build_board.py → single-file, VERSIONED)
  → 5. Manual edits round-trip          (board export file → re-solve with locks)
  → 6. Final Excel + validation         (export_excel.py, validate_solution.py)
```

All scripts live in `scripts/`, are non-interactive, print JSON to stdout, and support
`--help`. Canonical data schemas are in `references/data-formats.md` — read it before
writing any intermediate file by hand. Work in a scratch directory; keep the
intermediate JSON files, they are the state of the session.

## Stage 1 — Intake & column mapping

Ask the user for the form export and, before running anything, establish the parameters:

- How many classes? (default: ask; typically 3–4)
- **What are the class names?** (e.g., א1, א2, א3 — these exact strings appear on the
  board, in the Excel, in parse_notes --class-names, and in config.json. Canonical
  style is geresh-free "א1"; the scripts tolerate "א'1" via normalization, but two
  names that normalize identically are a loud error.)
- Class size bounds (default: even split ±2)
- Where is the mishalevet (special-ed with aide) info? Often NOT in the form — it may be
  a short list the counselor knows by heart. Accept it as a typed list of names.
- Any pre-known constraints: kids who must be separated, must be together, or are
  pre-assigned ("locks"). Counselors always have a few — ask explicitly.

Then inspect the file's headers yourself (read the first few rows) and build a column
mapping: student name, gan (kindergarten of origin), the 3 friend-choice columns, and
optional gender / mishalevet / notes / pre-assigned-class columns. Google Forms headers
are the question texts, often long Hebrew sentences — map by meaning, confirm with the
user in one short message ("אני מזהה: שם התלמיד = 'שם מלא', גן = ..., נכון?").

Run:

```bash
python scripts/parse_input.py <export.csv|.xlsx> --mapping mapping.json -o students.json
```

Handles UTF-8/UTF-8-BOM/cp1255 encodings and xlsx. Duplicate student names get
disambiguating suffixes and a warning — surface these to the user (two ילדים בשם נועה כהן
is a real scenario; they must say which gan each is from).

Counselor-curated files (not raw Google Forms) are common and fine — that's exactly what
the mapping is for. Multi-sheet workbooks: the script auto-picks the sheet whose headers
match the mapping and warns; if ambiguous it errors with the sheet names — ask the user
in plain language ("באיזה גיליון נמצאים הנתונים? יש: ...") and re-run with `--sheet`. Gan
names are normalized automatically ('גן דקל' → 'דקל', stray spaces); relay the merge
warnings so a real distinction isn't collapsed silently.

## Stage 1.5 — Draft board (earn trust BEFORE the long questions)

Right after the mapping is confirmed — before name reconciliation and the notes table —
give the counselor something to see. Run reconcile_names, solve with the auto-matched
choices only and NO constraints yet (except pre_class locks if they parse trivially via
parse_notes — display value only, never written to config before Stage 2.5), and:

```bash
python scripts/build_board.py reconciled.json solution_draft.json --config config_draft.json --draft -o "לוח שיבוץ - טיוטה.html"
```

The draft is READ-ONLY (no dragging, no locks, no saving — by design; edits made on a
draft could never be exported and would be lost). Hand it over with the right script:
- If pre_class locks were seeded: "זו טיוטה — ככה זה ייראה. השיבוצים מראש כבר משוקפים;
  עוד לא בפנים: ההערות (לא-עם/עדיפות) והאיזונים המיוחדים — נאשר אותם יחד בשלב הבא."
- If not seeded: "זו טיוטה — ככה זה ייראה. עוד לא בפנים: השיבוצים מראש מעמודת הכיתה,
  ההערות, והאיזונים — זה השלב הבא."
Then proceed to Stages 2/2.5 with her motivation earned.

## Stage 2 — Name reconciliation

Friend choices are free text typed by parents: typos, nicknames, missing surnames, kids
who aren't in this roster at all (chose a friend going to another school). This stage is
where most of the human time goes — budget for it.

```bash
python scripts/reconcile_names.py students.json -o reconciled.json
```

Output buckets every choice as `matched` (high-confidence, auto-accepted), `ambiguous`
(candidates with scores — needs a human), or `unmatched` (no plausible candidate).
Hebrew normalization (final letters, nikud, ktiv male/haser variants) is built in; see
`references/hebrew-names.md` for what it does and doesn't catch.

Present ambiguous cases to the user in a compact table (chooser → what they wrote →
candidates), collect decisions, write them to `resolutions.json`
(format in data-formats.md), and re-run with `--resolutions resolutions.json`.
**Never silently guess an ambiguous match** — a wrong merge puts a kid next to a
stranger and the error surfaces in September.

Unmatched choices are fine — they're simply dropped from that child's list, but if a
child ends up with ZERO matched choices, flag them by name: the solver cannot guarantee
them a friend and the counselors should handle them personally.

## Stage 2.5 — Notes & pre-assigned classes (DO NOT SKIP)

Counselor files often carry a free-text notes column (הערות) full of constraints — "לא
עם X", "עדיפות עם X", "עדיפות לא עם X", "כוכב", "שילוב" — and sometimes a pre-filled
class column (anchor kids). Skipping these was the #1 real-world complaint. Run:

```bash
python scripts/parse_notes.py students.json --class-names "א1,א2,א3" -o proposed_constraints.json
```

The output is a PROPOSAL. Present it as one compact Hebrew table, **grouped by kind**
(נעילות מראש / הפרדות / ביחד / תגים), with the parser-confident rows framed as
pre-approved — "אלו נראים ברורים; תגידי רק אם משהו לא נכון" — and per-row questions only
for `unresolved`/ambiguous entries. Ask the policy questions ONCE, globally, in the same
message: for "עדיפות עם" pairs — enforce as hard must-together or drop? (the solver has
no soft pairs); for "כוכב" kids — usual meaning is socially dominant children to spread.
**Dedupe against anything the counselor already told you verbally in Stage 1 — never ask
twice about the same pair.** **Never auto-apply. Never silently drop** — a note the
parser didn't understand goes in the table too (warnings).

**What confirmed proposals become (exact application map):**
- locks → `config.locks` (student id → 0-based class index).
- apart / together → `config.apart` / `config.together` id pairs.
- כוכב, confirmed as "spread": if the kochav kids number ≤ num_classes, pairwise `apart`
  among them; if MORE, propose CONCRETE pairs to the counselor (e.g., the two most
  connected) and apply only what she approves — never invent pairs silently.
- שילוב → add the names to mapping.json `mishalevet_names` and re-run parse_input +
  reconcile_names (student ids are stable for the same file). Precedence: an explicit
  mishalevet column/list from Stage 1 wins; the tag route only ADDS kids.

## Stage 3 — Solve

**Hard gate: never present a non-draft solution while reconciliation `ambiguous` is
non-empty** — the solver skips pending ambiguous choices, silently weakening the friend
guarantee for exactly those kids.

```bash
pip install ortools --break-system-packages   # once; ok if it fails, see fallback
python scripts/solve.py reconciled.json --config config.json -o solution.json
```

`config.json` carries num_classes, class_names, size bounds, locks/apart/together,
`gan_class_restrictions` (gan → allowed classes, e.g. `{"סיגלון": ["א1","א3"]}` — use
this instead of hand-locking every child; it's hard, never auto-relaxed, and errors
loudly on unresolvable names), and optional weight overrides (schema in
data-formats.md). The model, the relaxation ladder (what the solver gives up, in what
order, when constraints can't all hold), and how to explain infeasibility to the user
are documented in `references/solver-notes.md` — read it if the solve is infeasible,
slow, or the user questions the result.

If OR-Tools can't install, solve.py falls back to a bundled pure-Python
simulated-annealing solver: same inputs/outputs, not provably optimal but fine at n≈100.
When the output has `"fallback": true` you MUST tell the user, in plain language: the
result is good but not mathematically proven best, it happened because the environment
has no network for installing the optimizer, and here is how to get the full optimizer —
see "Network access" below. Don't be alarmist: at ~100 kids the fallback result is
typically excellent, and they may well need nothing.

### Network access (for installing OR-Tools) — how to guide a non-technical user

Try `pip install ortools --break-system-packages` once. If it fails with a network
error, explain (in the user's language):

1. **"אפשר להמשיך גם בלי זה"** — the built-in solver works offline and gives good
   results; the only difference is a mathematical optimality proof. Offer to continue.
2. If they want the full optimizer and the task runs **on their computer**: as of
   mid-2026 the Claude desktop app has a network-egress setting for Cowork tasks,
   usually under **Settings → Cowork** — look for "network"/"egress"/"גישה לרשת" and
   choose at least **"Package managers only"** (allows pip/npm registries and nothing
   else — the roster never leaves the machine). Then start a NEW task; the setting
   applies from the next task. Menus move between versions — describe this as "where it
   usually is", and if it's missing tell them to ask whoever manages their Claude
   account.
3. **Cloud as last resort**: starting the task again with "Run this task → In the
   cloud" gives an environment where package installs work out of the box — but say
   explicitly that this uploads the children's roster to a cloud environment, and the
   school should be OK with that before choosing it.

After solving, always run:

```bash
python scripts/validate_solution.py reconciled.json solution.json --config config.json
```

and report the human-readable summary: per-class sizes, gan mix, mishalevet placement,
how many kids got their 1st/2nd/3rd choice, and every kid with no satisfied choice.

## Stage 4 — Review board

```bash
python scripts/build_board.py reconciled.json solution.json --config config.json --version 1 -o "לוח שיבוץ - גרסה 1.html"
```

Produces a **single self-contained RTL Hebrew HTML file** — no internet needed, so the
counselors can open it on any school computer. Features (all client-side): drag cards
between class columns, cards colored by gan, live indicators (green/red friend-
satisfaction dot per child, class size counters, gan distribution bars, mishalevet
badge ⭐, "נקבע מראש" edge marker on pre-assigned kids), search box, click a card to
highlight the child's chosen friends and who chose them, locking (🔒) — **and every
manual drag auto-locks the child** so the next re-solve keeps her decision (drag-back
undoes it; the toast explains), undo (↩), warning toasts when a drag contradicts a
pre-defined rule (the move still happens — counselors are the authority), and a
**"שמירה ושליחה ל-Claude" button** whose dialog downloads a small versioned file to
send back to you (manual copy-paste hidden behind a link, for locked-down computers).

**Versioning discipline (prevents the "it didn't update" confusion):**

- Every regeneration bumps `--version` and the filename matches: "לוח שיבוץ - גרסה 2.html".
- The board header shows the version + generation time; the localStorage key is salted
  automatically with a content fingerprint, so a new file never silently shows an old
  file's edits.
- Your hand-off message MUST say, every time: זהו קובץ חדש (גרסה 2) — פתחו אותו, לא את
  הישן, ומחקו את הקבצים הקודמים (כולל הטיוטה). הלוח הישן לא מתעדכן מעצמו; כל עדכון
  בשיחה = קובץ חדש להורדה. And the reverse: שינויים בלוח לא מגיעים לשיחה לבד — מסיימים,
  לוחצים "שמירה ושליחה ל-Claude", מורידים את קובץ השינויים ושולחים לי אותו. Edits also
  live only in that browser on that computer — moving between computers requires the
  export file.
- **Migrating a user from an older board (e.g., v3 → v4):** the hand-off starts with
  "אם עשית שינויים בגרסה הקודמת — קודם 'שמירה ושליחה' משם, שלחי לי את הקובץ, ורק אז
  עברי לקובץ החדש." Old boards had no auto-lock, so their exports need the Stage 5
  moved-but-unlocked diff below.
- **Carrying counselor locks onto a rebuilt board:** pass the export to build_board via
  `--board-state` — her locked kids come back pre-locked WITHOUT the "נקבע מראש" marker
  (that marker is reserved for pre-assigned kids). Never fold counselor locks into
  config.locks; that would mislabel them as school decrees.

## Stage 5 — Re-solve round-trip

When the user sends back the board's export file (or pastes its JSON): save as
`board_state.json`. **MANDATORY reconciliation BEFORE invoking solve** (the solver
pre-checks are backstops against YOUR error, never a counselor-facing interface):

(a) **Gan-rule conflicts** — a board-locked kid in a class their gan is restricted from.
    The solver will honor it (a board lock overrides the gan rule for that child only,
    with a warning) — but confirm first: "X נגררה לכיתה ש{גן} לא אמור להיות בה. להשאיר
    אותה שם (הכלל ממשיך לחול על שאר ילדי הגן), או להחזיר?"
(b) **Locked-pair conflicts** — an apart pair locked into the same class (or a together
    pair split). Ask: "נעלת את X ואת Y באותה כיתה, אבל הוגדר שהם לא ביחד. להשאיר אותם
    יחד (אבטל את הכלל), או להפריד?" On "keep" — REMOVE/adjust the pair in config.json
    before solving (note it in your summary). Solving without doing this dies fast with
    a named error.
(c) **Moved-but-unlocked diff** — diff the export's assignment against the previous
    solution; any child who moved but is NOT in the export's locks (old boards without
    auto-lock, or a child deliberately unlocked after moving) gets listed with ONE
    question: "לנעול אותם למקום החדש או לתת לחישוב להחליט?"
(d) **Duplicate saves** — if the export could be one of several saves of the SAME
    version ("(1).json" in the filename, or the user is unsure), compare `saved_at`
    across the files and confirm which save is final.

Then:

```bash
python scripts/solve.py reconciled.json --config config.json --board-state board_state.json -o solution2.json
python scripts/validate_solution.py reconciled.json solution2.json --config config.json --board-state board_state.json
```

Locked kids stay put; everyone else re-optimizes. Exports from versioned boards REPLACE
config locks — a deliberately-unlocked pre-assigned kid stays unlocked (confirm, then
update config.json locks so later runs agree). The export's `autoPinned` map tells you
which locks came from drags vs deliberate pins. If the export's `version` is older than
the newest board you generated, the counselor edited a stale file — tell them and
confirm before proceeding. Rebuild the board (bump the version! carry her locks with
`--board-state`) and validate again. Iterate as many times as they want — this loop is
the product.

## Resuming in a NEW chat (no session files)

The newest board file is a session capsule: its embedded DATA carries the roster,
matched choices, anchors, pairs, gan restrictions, the full config, and a
reconciliation summary. To resume from scratch: ask for (1) the newest board HTML and
(2) the newest export file. Extract DATA (the `/*__DATA__*/` JSON in the single script
tag), write config.json from `DATA.capsule.config`, rebuild reconciled.json from the
students+choices (+ capsule reconciliation_summary for the Excel issues sheet), and
process the export as Stage 5. Caveats: a capsule-rebuilt Excel has an EMPTY notes
column (notes are excluded from the board for privacy) — say so, and offer to ask for
the original Excel if the notes matter. NEVER re-parse a modified Excel against an old
export (student ids drift). Scripted hand-off line for every delivery: "אם השיחה הזו
תיסגר — פתחו חדשה וצרפו את קובץ הלוח האחרון + קובץ השינויים. זה כל מה שצריך."

## Stage 6 — Final Excel

```bash
python scripts/export_excel.py reconciled.json solution_final.json --config config.json -o shibutz.xlsx
```

RTL workbook: one sheet per class (name, gan, which choice was satisfied, notes),
a summary sheet (sizes, gan matrix, satisfaction stats), and an issues sheet (kids with
no satisfied choice, unmatched names, warnings). Present the xlsx AND the board html as
the final deliverables. Also save your final plain-Hebrew summary (what worked, what
needs their attention, per-child flags) as `summary.md` next to the deliverables — the
counselors forward it to each other, and it must survive after the chat is closed.

## Errors and how to explain them (counselor Hebrew, no config-speak)

- **Duplicate mapped headers** (parse_input exit 2): fix the header yourself — copy the
  file, rename the duplicate column via xlsx tooling, re-run. Never bounce "תשני שם של
  עמודה" to the counselor.
- **Stale board export / roster mismatch** (solve exit 2, unknown_ids): "הלוח שערכת
  נבנה מרשימת תלמידים ישנה. אבנה לוח חדש ונשחזר יחד את השינויים."
- **Locked-pair conflict** (solve exit 2): you skipped Stage 5(b) — go back, ask, adjust
  config, re-run. To the counselor: "שני הילדים שביקשת להפריד ננעלו יחד — רק תאשרי מה
  גובר ונמשיך."
- **Board lock overrides gan rule** (solve warning): relay per Stage 5(a) if you didn't
  already confirm it.
- **Network / OR-Tools install failure**: to a counselor say ONLY: "אפשר להמשיך רגיל —
  התוצאה טובה מאוד. אם חשוב לך 'המנוע המלא', זו בקשה של דקה ממי שמנהל לכם את Claude."
  Offer the settings walk (below) only if asked or if the user is technical.

## Gotchas

- **Friendship is directed.** דני picked יוסי doesn't mean יוסי picked דני. "Every child
  with a friend" means every child has someone *they* chose — being chosen doesn't count.
- **Guarantee applies only to matched choices.** A child whose 3 picks all left the
  school has zero edges; the hard constraint auto-skips them. Always name these kids in
  your summary — they're the ones the counselors would have caught with stickers.
- **Mishalevet count ≠ class count** happens (2 kids, 4 classes). The script downgrades
  "exactly one per class" to "spread, max one per class" and warns. Tell the user rather
  than hiding it.
- **Don't over-promise optimality of soft goals.** Only the friend guarantee, sizes, and
  mishalevet placement are hard. Gan spread and choice ranks are traded off; show the
  numbers and let humans judge.
- **Excel + Hebrew:** exports from Excel (as opposed to Google Forms) may be cp1255 —
  parse_input handles it, but if names look like gibberish (מ×•×©×”), re-read with a
  different encoding before concluding the file is broken.
- **The board must stay a single file with zero CDN dependencies** — school computers
  may be offline/filtered. build_board.py inlines everything; never "improve" it with
  external libraries.
- **The board is a snapshot, not a live view.** Real-world confusion: a counselor kept
  an old board open and thought chat changes would appear in it. They never do — say so
  proactively at every hand-off (see Stage 4 versioning discipline), and bump the
  version on every regeneration so stale files are self-evident.
- **Names in outputs are sensitive.** Don't paste full rosters into your visible
  reasoning more than needed; keep files local.

## What NOT to do

- Don't hand-roll a solver in the conversation — use the scripts; they're tested.
- Don't skip validation after ANY change to assignments (solver or human).
- Don't ask the counselor for JSON, schemas, or technical formats — you translate.
