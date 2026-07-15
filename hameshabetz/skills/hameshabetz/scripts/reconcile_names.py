#!/usr/bin/env python3
"""Fuzzy-match free-text friend choices against the roster (Hebrew-aware).

Usage:
  python reconcile_names.py students.json -o reconciled.json [--resolutions resolutions.json]

Buckets each non-empty choice as:
  matched    score >= 0.93 and clearly best  -> auto-accepted
  ambiguous  plausible candidates, needs a human decision
  unmatched  nothing plausible (score < 0.60) -> dropped from the child's list

resolutions.json: {"resolutions": [{"chooser": "s001", "rank": 1, "target": "s017"}]}
(target null = drop the choice). Re-run with --resolutions after collecting decisions.

Exit codes: 0 ok. Output JSON includes reconciliation.ambiguous — empty means done.
"""
import argparse, json, re, sys, unicodedata
from difflib import SequenceMatcher

FINALS = str.maketrans("ךםןףץ", "כמנפצ")


def norm(s: str) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", str(s))
    s = "".join(ch for ch in s if not ("֑" <= ch <= "ׇ"))
    s = s.translate(FINALS)
    s = re.sub(r"[\"'`’׳״]", "", s)
    s = re.sub(r"[^\w\s֐-׿-]", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def ratio(a, b):
    return SequenceMatcher(None, a, b).ratio()


def score(raw_n, student):
    """Best similarity between the raw (normalized) text and a student's name forms."""
    full = student["_n"]
    first = student["_first"]
    cands = [ratio(raw_n, full)]
    if " " not in raw_n:                      # first-name-only pick
        cands.append(ratio(raw_n, first) * 0.97)
    else:                                     # maybe reversed order "כהן נועה"
        toks = raw_n.split(" ")
        cands.append(ratio(" ".join(reversed(toks)), full) * 0.98)
    if raw_n and (full.startswith(raw_n + " ") or raw_n.startswith(full + " ")):
        cands.append(0.96)
    return max(cands)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("students")
    ap.add_argument("-o", "--output", default="reconciled.json")
    ap.add_argument("--resolutions")
    ap.add_argument("--match-threshold", type=float, default=0.93)
    ap.add_argument("--candidate-threshold", type=float, default=0.60)
    a = ap.parse_args()

    data = json.load(open(a.students, encoding="utf-8"))
    students = data["students"]
    for s in students:
        s["_n"] = norm(s["name"])
        s["_first"] = s["_n"].split(" ")[0] if s["_n"] else ""
    by_id = {s["id"]: s for s in students}

    resolutions = {}
    if a.resolutions:
        for r in json.load(open(a.resolutions, encoding="utf-8")).get("resolutions", []):
            resolutions[(r["chooser"], int(r["rank"]))] = r.get("target")

    ambiguous, unmatched, matched_ct = [], [], 0
    for s in students:
        s["choices"] = []
        for rank, raw in enumerate(s.get("raw_choices", []), start=1):
            raw = (raw or "").strip()
            if not raw:
                continue
            if (s["id"], rank) in resolutions:
                tgt = resolutions[(s["id"], rank)]
                if tgt is None:
                    unmatched.append({"chooser": s["id"], "chooser_name": s["name"], "rank": rank,
                                      "raw": raw, "reason": "dropped by human decision"})
                elif tgt in by_id:
                    s["choices"].append({"rank": rank, "target": tgt, "raw": raw,
                                         "status": "resolved", "score": 1.0})
                    matched_ct += 1
                else:
                    print(json.dumps({"error": f"resolution target '{tgt}' not a valid student id"}),
                          file=sys.stderr); sys.exit(2)
                continue
            raw_n = norm(raw)
            scored = sorted(((score(raw_n, t), t) for t in students if t["id"] != s["id"]),
                            key=lambda x: -x[0])
            top, second = scored[0], (scored[1] if len(scored) > 1 else (0, None))
            if top[0] >= a.match_threshold and top[0] - second[0] >= 0.04:
                s["choices"].append({"rank": rank, "target": top[1]["id"], "raw": raw,
                                     "status": "matched", "score": round(top[0], 3)})
                matched_ct += 1
            elif top[0] >= a.candidate_threshold:
                cands = [{"id": t["id"], "name": t["name"], "gan": t["gan"], "score": round(sc, 3)}
                         for sc, t in scored[:4] if sc >= a.candidate_threshold]
                ambiguous.append({"chooser": s["id"], "chooser_name": s["name"], "chooser_gan": s["gan"],
                                  "rank": rank, "raw": raw, "candidates": cands})
            else:
                unmatched.append({"chooser": s["id"], "chooser_name": s["name"], "rank": rank,
                                  "raw": raw, "reason": "no plausible roster match"})

    for s in students:
        s.pop("_n", None); s.pop("_first", None)

    pending = {x["chooser"] for x in ambiguous}
    zero_choice_kids = [{"id": s["id"], "name": s["name"], "gan": s["gan"]}
                        for s in students
                        if not s["choices"]
                        and any((c or "").strip() for c in s.get("raw_choices", []))
                        and s["id"] not in pending]
    no_form_kids = [{"id": s["id"], "name": s["name"], "gan": s["gan"]}
                    for s in students if not any((c or "").strip() for c in s.get("raw_choices", []))]

    data["reconciliation"] = {
        "matched": matched_ct, "ambiguous": ambiguous, "unmatched": unmatched,
        "zero_matched_choices": zero_choice_kids, "no_choices_on_form": no_form_kids,
    }
    json.dump(data, open(a.output, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"ok": True, "matched": matched_ct, "ambiguous": len(ambiguous),
                      "unmatched": len(unmatched),
                      "zero_matched_choices": [k["name"] for k in zero_choice_kids],
                      "no_choices_on_form": [k["name"] for k in no_form_kids]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
