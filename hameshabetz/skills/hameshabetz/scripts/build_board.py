#!/usr/bin/env python3
"""Render the drag-and-drop review board (single-file RTL Hebrew HTML).

Usage:
  python build_board.py reconciled.json solution.json --config config.json
                        [--version N] [--draft] [--board-state export.json] -o board.html

The board is fully self-contained (no CDN, works offline). Manual edits persist in the
browser's localStorage; the "save" button downloads JSON that solve.py accepts via
--board-state for re-optimization.

--version   display-only version shown in the header; bump on EVERY regeneration and put
            it in the filename too ("לוח שיבוץ - גרסה 2.html").
--draft     read-only preview board ("טיוטה"): no dragging, no locks, no persistence,
            no export. For the first-look hand-off before names/constraints are final.
--board-state  a previous board export: its locked kids are pre-locked on the new board
            WITHOUT being marked "נקבע מראש" (that marker is reserved for config
            anchors, i.e. pre-assigned/pre_class kids).

The payload embeds a `capsule` (full config + reconciliation summary) so a NEW chat can
resume from the board + an export alone. Raw notes are deliberately EXCLUDED (privacy).
Exit codes: 0 ok, 1 template error, 2 config/roster mismatch.
"""
import argparse, datetime, hashlib, json, os, sys

from parse_notes import norm_class


def die(msg, **extra):
    print(json.dumps({"error": msg, **extra}, ensure_ascii=False), file=sys.stderr)
    sys.exit(2)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("reconciled")
    ap.add_argument("solution")
    ap.add_argument("--config", required=True)
    ap.add_argument("--version", type=int, default=1)
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--board-state", help="previous export whose locks are carried over as plain pins")
    ap.add_argument("-o", "--output", default="board.html")
    a = ap.parse_args()

    data = json.load(open(a.reconciled, encoding="utf-8"))
    sol = json.load(open(a.solution, encoding="utf-8"))
    config = json.load(open(a.config, encoding="utf-8"))
    prev = json.load(open(a.board_state, encoding="utf-8")) if a.board_state else None
    k = config["num_classes"]
    class_names = [str(c) for c in (sol.get("class_names") or config.get("class_names")
                                    or [f"כיתה א'{i+1}" for i in range(k)])]

    # constraint sids must exist in the roster — an unknown sid in a together pair
    # would throw inside the board's render() and blank-screen the whole board.
    roster = {s["id"] for s in data["students"]}
    bad = sorted({sid for sid in (config.get("locks") or {}) if sid not in roster}
                 | {x for p in (config.get("apart") or []) + (config.get("together") or [])
                    for x in p if x not in roster})
    if bad:
        die("config locks/apart/together reference student ids not in the roster — fix "
            "config.json before building the board", unknown_ids=bad)

    # class-name normalization: same leniency + same loud errors as solve.py.
    cname_idx = {}
    for i, cn in enumerate(class_names):
        key = norm_class(cn)
        if key in cname_idx:
            die(f"class names '{class_names[cname_idx[key]]}' and '{cn}' are identical "
                f"after normalization — rename one")
        cname_idx[key] = i

    # gan restrictions resolved to INDICES at build time (board JS never string-matches
    # class names); unresolvable names are a loud error — never a silent no-op.
    student_gans = {s["gan"] for s in data["students"]}
    restrictions = {}
    for gan, allowed in (config.get("gan_class_restrictions") or {}).items():
        if gan not in student_gans:
            die(f"gan_class_restrictions: gan '{gan}' not in roster",
                roster_gans=sorted(student_gans))
        idxs = []
        for cn in allowed:
            key = norm_class(cn)
            if key not in cname_idx:
                die(f"gan_class_restrictions: class '{cn}' not in class_names",
                    class_names=class_names)
            idxs.append(cname_idx[key])
        restrictions[gan] = sorted(set(idxs))

    # counselor pins carried over from a previous export — plain locks, NOT anchors
    # (the "נקבע מראש" marker is provenance of the pre-assigned/config kids only).
    pre_locked = []
    if prev:
        pre_locked = [sid for sid in prev.get("locks", [])
                      if sid in roster and sid not in (config.get("locks") or {})]

    payload = {
        "students": [{"id": s["id"], "name": s["name"], "gan": s["gan"],
                      "gender": s.get("gender"), "pre_class": s.get("pre_class") or "",
                      "mishalevet": bool(s.get("mishalevet")),
                      "choices": [{"target": c["target"], "rank": c["rank"]}
                                  for c in s.get("choices", []) if c["target"] in roster]}
                     for s in data["students"]],
        "assignment": {sid: int(c) for sid, c in sol["assignment"].items()},
        "classNames": class_names,
        "anchors": {sid: int(c) for sid, c in (config.get("locks") or {}).items()},
        "apart": [list(p) for p in (config.get("apart") or [])],
        "together": [list(p) for p in (config.get("together") or [])],
        "restrictions": restrictions,   # gan -> allowed class indices
        "preLocked": pre_locked,        # counselor pins carried from a previous board
        "draft": bool(a.draft),
        "version": a.version,
        "generated": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
        # session capsule: everything a FRESH chat needs to rebuild config and produce
        # the final Excel. Raw notes deliberately excluded (privacy). The unmatched raw
        # strings below are parent-typed NAMES, not behavioral notes.
        "capsule": {
            "config": config,
            "reconciliation_summary": {
                "unmatched": [{"chooser_name": u.get("chooser_name"), "raw": u.get("raw")}
                              for u in (data.get("reconciliation", {}) or {}).get("unmatched", [])],
                "zero_matched_choices": [{"name": z.get("name"), "gan": z.get("gan")}
                                         for z in (data.get("reconciliation", {}) or {}).get("zero_matched_choices", [])],
                "no_choices_on_form": [{"name": z.get("name"), "gan": z.get("gan")}
                                       for z in (data.get("reconciliation", {}) or {}).get("no_choices_on_form", [])],
            },
            "warnings": data.get("warnings", []),
        },
    }
    # Content fingerprint, computed here (deterministic, no JS hashing quirks). It salts
    # the board's localStorage key so a NEW board file can never silently resurrect an
    # OLD board's saved edits — the root cause of "the HTML didn't update".
    # The config hash is defense-in-depth for a violated version-bump discipline or two
    # builds in the same minute; do NOT "simplify" by removing `generated` — that would
    # create real collisions.
    cfg_hash = hashlib.md5(json.dumps(config, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:8]
    fp_src = json.dumps({"a": payload["assignment"], "v": payload["version"],
                         "g": payload["generated"], "anchors": payload["anchors"],
                         "cfg": cfg_hash, "draft": payload["draft"]},
                        sort_keys=True, ensure_ascii=False)
    payload["fingerprint"] = hashlib.md5(fp_src.encode("utf-8")).hexdigest()[:12]
    tpl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "board_template.html")
    tpl = open(tpl_path, encoding="utf-8").read()
    marker = "/*__DATA__*/null"
    if marker not in tpl:
        print(json.dumps({"error": "template marker not found"}), file=sys.stderr); sys.exit(1)
    html = tpl.replace(marker, json.dumps(payload, ensure_ascii=False))
    open(a.output, "w", encoding="utf-8").write(html)
    print(json.dumps({"ok": True, "output": a.output, "students": len(payload["students"]),
                      "classes": payload["classNames"], "version": payload["version"],
                      "draft": payload["draft"], "pre_locked": len(pre_locked),
                      "fingerprint": payload["fingerprint"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
