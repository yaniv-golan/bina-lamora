#!/usr/bin/env python3
"""Extract PROPOSED constraints from free-text notes (הערות) and a pre-assigned class
column. Output is a proposal only — the assistant must show it to the counselor as a
compact Hebrew table and get explicit confirmation before writing config.json.
NOTHING here is auto-applied.

Usage:
  python parse_notes.py students.json --class-names "א1,א2,א3" -o proposed_constraints.json

Recognized note patterns (a note may contain several, e.g. "כוכב לא עם יונתן"):
  apart:    [עדיפות] לא [ביחד|יחד] עם <שם>      (checked FIRST so 'עדיפות לא עם' is
                                                  never misread as a together-preference)
  together: עדיפות עם / ביחד עם / יחד עם <שם>
  tags:     כוכב (socially dominant — suggest spreading), שילוב/משלבת (mishalevet)
Pre-class values are matched against --class-names (accepts "א1", "א'1", "1").

Free-text names are resolved with the same Hebrew-aware matcher as reconcile_names.py.
Anything below confidence lands in "unresolved" with candidates — never silently guessed.
Exit codes: 0 ok, 1 file error, 2 bad arguments.
"""
import argparse, json, re, sys

from reconcile_names import norm, score

APART_RE = re.compile(r"(?:עדיפות\s+)?לא\s+(?:ביחד\s+עם|יחד\s+עם|עם)\s+(.+)")
TOGETHER_RE = re.compile(r"(?:עדיפות\s+עם|ביחד\s+עם|יחד\s+עם)\s+(.+)")
# boundary includes punctuation, not just whitespace: 'כוכב, לא עם X' must still tag
# (but 'כוכבית'/'משולב' must not)
_B = r"[\s,.;:!?()\-]"
KOCHAV_RE = re.compile(rf"(?:^|{_B})כוכב(?=$|{_B})")
SHILUV_RE = re.compile(rf"(?:^|{_B})(?:שילוב|משלבת)(?=$|{_B})")


def norm_class(v):
    """'א'1' / 'א 1' / 'a1' → comparable form; bare digits also accepted."""
    v = re.sub(r"[\s'׳`\"]+", "", str(v or ""))
    return v


def resolve_name(raw, students, exclude_id, match_th=0.93, cand_th=0.60):
    """Returns (student or None, candidates list). Same thresholds as reconcile_names."""
    raw_n = norm(raw)
    for s in students:
        s.setdefault("_n", norm(s["name"]))
        s.setdefault("_first", s["_n"].split(" ")[0] if s["_n"] else "")
    scored = sorted(((score(raw_n, t), t) for t in students if t["id"] != exclude_id),
                    key=lambda x: -x[0])
    if not scored:
        return None, []
    top, second = scored[0], (scored[1] if len(scored) > 1 else (0, None))
    if top[0] >= match_th and top[0] - second[0] >= 0.04:
        return top[1], []
    cands = [{"id": t["id"], "name": t["name"], "gan": t["gan"], "score": round(sc, 3)}
             for sc, t in scored[:4] if sc >= cand_th]
    return None, cands


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("students")
    ap.add_argument("--class-names", required=True,
                    help='comma-separated, e.g. "א1,א2,א3" — order defines class indices')
    ap.add_argument("-o", "--output", default="proposed_constraints.json")
    a = ap.parse_args()

    class_names = [c.strip() for c in a.class_names.split(",") if c.strip()]
    if not class_names:
        print(json.dumps({"error": "empty --class-names"}), file=sys.stderr); sys.exit(2)
    class_lookup = {}
    for i, cn in enumerate(class_names):
        key = norm_class(cn)
        if key in class_lookup:
            print(json.dumps({"error": f"class names '{class_names[class_lookup[key]]}' and "
                              f"'{cn}' are identical after normalization — rename one"},
                             ensure_ascii=False), file=sys.stderr)
            sys.exit(2)
        class_lookup[key] = i
    for i, cn in enumerate(class_names):
        m = re.search(r"(\d+)$", cn)
        if m:
            class_lookup.setdefault(m.group(1), i)  # bare "1" also accepted

    data = json.load(open(a.students, encoding="utf-8"))
    students = data["students"]

    locks, apart, together, unresolved, warnings = [], [], [], [], []
    tags = {"kochav": [], "shiluv": []}

    for s in students:
        # --- pre-assigned class column ---
        pre = (s.get("pre_class") or "").strip()
        if pre:
            idx = class_lookup.get(norm_class(pre))
            if idx is None:
                unresolved.append({"student": s["id"], "student_name": s["name"],
                                   "kind": "lock", "raw": pre,
                                   "reason": f"'{pre}' does not match any of {class_names}"})
            else:
                locks.append({"student": s["id"], "student_name": s["name"],
                              "raw": pre, "class_name": class_names[idx], "class_index": idx})

        # --- notes ---
        note = (s.get("notes") or "").strip()
        if not note:
            continue
        rest = note
        if KOCHAV_RE.search(f" {rest} "):
            tags["kochav"].append({"student": s["id"], "student_name": s["name"]})
            rest = KOCHAV_RE.sub(" ", f" {rest} ").strip()
        if SHILUV_RE.search(f" {rest} "):
            tags["shiluv"].append({"student": s["id"], "student_name": s["name"]})
            rest = SHILUV_RE.sub(" ", f" {rest} ").strip()
        rest = rest.strip(" ,.;:!?()-")  # leftover punctuation after tag removal
        if not rest:
            continue

        m = APART_RE.search(rest)   # MUST run before TOGETHER_RE
        kind, target_raw = None, None
        if m:
            kind, target_raw = "apart", m.group(1).strip()
        else:
            m = TOGETHER_RE.search(rest)
            if m:
                kind, target_raw = "together", m.group(1).strip()
        if kind is None:
            warnings.append(f"{s['name']}: note not understood, left for the human: '{note}'")
            continue

        target, cands = resolve_name(target_raw, students, s["id"])
        if target is None:
            unresolved.append({"student": s["id"], "student_name": s["name"],
                               "kind": kind, "raw": note, "raw_target": target_raw,
                               "candidates": cands,
                               "reason": "no confident roster match" if cands else "no plausible roster match"})
        else:
            entry = {"chooser": s["id"], "chooser_name": s["name"], "raw": note,
                     "target": target["id"], "target_name": target["name"]}
            (apart if kind == "apart" else together).append(entry)

    for s in students:
        s.pop("_n", None); s.pop("_first", None)

    out = {"class_names": class_names, "locks": locks, "apart": apart,
           "together": together, "tags": tags, "unresolved": unresolved,
           "warnings": warnings}
    json.dump(out, open(a.output, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"ok": True, "locks": len(locks), "apart": len(apart),
                      "together": len(together), "kochav": len(tags["kochav"]),
                      "shiluv": len(tags["shiluv"]), "unresolved": len(unresolved),
                      "warnings": warnings}, ensure_ascii=False))


if __name__ == "__main__":
    main()
