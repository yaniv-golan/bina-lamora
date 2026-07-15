#!/usr/bin/env python3
"""Validate a class assignment against all constraints. Works on solver output AND
on human-edited board exports — run it after every change.

Usage:
  python validate_solution.py reconciled.json solution.json --config config.json
                              [--board-state board_state.json] [--json-only]

--board-state: when the solution came from a board round-trip, pass the same export
here. Exports carrying a fingerprint/version REPLACE config locks for validation
(a deliberately-unlocked anchor is not a violation); legacy exports merge.

Prints a Hebrew human-readable summary to stdout plus a JSON report line.
Exit codes: 0 = no hard violations (warnings allowed), 2 = hard violations present.
"""
import argparse, json, math, sys
from collections import defaultdict


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("reconciled")
    ap.add_argument("solution")
    ap.add_argument("--config", required=True)
    ap.add_argument("--board-state")
    ap.add_argument("--json-only", action="store_true")
    a = ap.parse_args()

    data = json.load(open(a.reconciled, encoding="utf-8"))
    sol = json.load(open(a.solution, encoding="utf-8"))
    config = json.load(open(a.config, encoding="utf-8"))
    board_state = json.load(open(a.board_state, encoding="utf-8")) if a.board_state else None
    students = data["students"]
    by_id = {s["id"]: s for s in students}
    assign = {sid: int(c) for sid, c in sol["assignment"].items()}
    k = config["num_classes"]
    names = sol.get("class_names") or config.get("class_names") or [f"כיתה {i+1}" for i in range(k)]
    n = len(students)
    violations, warnings = [], []

    # relaxations the solver DELIBERATELY applied (recorded in solution.json) must not
    # re-surface here as "hard violations" — the pipeline would contradict itself.
    # They stay loud, but as expected warnings the assistant explains to the user.
    relaxed = " | ".join(sol.get("relaxations") or [])
    r_friend = "friend guarantee" in relaxed
    r_size = "size bounds" in relaxed
    r_mish = "mishalevet" in relaxed

    missing = [s["name"] for s in students if s["id"] not in assign]
    if missing:
        violations.append(f"students without a class: {missing}")

    sizes = [0] * k
    gan_matrix = defaultdict(lambda: [0] * k)
    mish = [0] * k
    for s in students:
        c = assign.get(s["id"])
        if c is None or not (0 <= c < k):
            continue
        sizes[c] += 1
        gan_matrix[s["gan"]][c] += 1
        if s.get("mishalevet"):
            mish[c] += 1
    smin = config.get("min_size") or max(0, math.floor(n / k) - 2)
    smax = config.get("max_size") or math.ceil(n / k) + 2
    if r_size:  # solver applied R3: bounds were deliberately widened by 2
        smin, smax = max(0, smin - 2), smax + 2
    for c in range(k):
        if not (smin <= sizes[c] <= smax):
            violations.append(f"class '{names[c]}' size {sizes[c]} outside [{smin},{smax}]")

    gan_tol = int(config.get("gan_tolerance", 1))
    for g, cnts in gan_matrix.items():
        tot = sum(cnts)
        lo, hi = max(0, math.floor(tot / k) - gan_tol), math.ceil(tot / k) + gan_tol
        for c in range(k):
            if not (lo <= cnts[c] <= hi):
                warnings.append(f"gan '{g}' in class '{names[c]}': {cnts[c]} children (target {lo}-{hi})")

    total_mish = sum(1 for s in students if s.get("mishalevet"))
    for c in range(k):
        if total_mish == k and mish[c] != 1 and not r_mish:
            violations.append(f"class '{names[c]}' has {mish[c]} mishalevet children (expected 1)")
        elif (total_mish != k or r_mish) and mish[c] > max(1, math.ceil(total_mish / k)):
            warnings.append(f"class '{names[c]}' has {mish[c]} mishalevet children")

    # friend satisfaction
    sat_rank = {}
    for s in students:
        best = None
        for ch in s.get("choices", []):
            t = ch["target"]
            if t in assign and assign.get(s["id"]) == assign[t]:
                best = ch["rank"] if best is None else min(best, ch["rank"])
        sat_rank[s["id"]] = best
    unsatisfied = [s["name"] for s in students if s.get("choices") and sat_rank[s["id"]] is None]
    no_edges = [s["name"] for s in students if not s.get("choices")]
    if unsatisfied:
        if r_friend:  # solver applied R2: the guarantee was deliberately relaxed
            warnings.append(f"(הוקל ע\"י הפותר) children without a friend in class: {unsatisfied}")
        else:
            violations.append(f"children with matched choices but NO friend in class: {unsatisfied}")

    # apart/together: an unresolvable id is itself a hard violation, never a silent skip
    nm = lambda sid: by_id[sid]["name"] if sid in by_id else f"<unknown id {sid}>"
    for a2, b in (config.get("apart") or []):
        if a2 not in by_id or b not in by_id:
            violations.append(f"apart pair [{a2}, {b}] references unknown student id — roster changed?")
        elif a2 in assign and b in assign and assign[a2] == assign[b]:
            violations.append(f"apart pair together: {nm(a2)} + {nm(b)}")
    for a2, b in (config.get("together") or []):
        if a2 not in by_id or b not in by_id:
            violations.append(f"together pair [{a2}, {b}] references unknown student id — roster changed?")
        elif a2 in assign and b in assign and assign[a2] != assign[b]:
            violations.append(f"together pair split: {nm(a2)} + {nm(b)}")
    # locks: board-state (fingerprinted) supersedes config — see docstring
    locks = {sid: int(c) for sid, c in (config.get("locks") or {}).items()}
    board_locked_ids = set()
    if board_state:
        fingerprinted = bool(board_state.get("fingerprint") or board_state.get("version"))
        if fingerprinted:
            locks = {}
        for sid in board_state.get("locks", []):
            if sid in by_id and sid in board_state.get("assignment", {}):
                locks[sid] = int(board_state["assignment"][sid])
                if fingerprinted:
                    board_locked_ids.add(sid)
    for sid, c in locks.items():
        if sid not in by_id:
            violations.append(f"lock references unknown student id '{sid}' — roster changed?")
        elif assign.get(sid) != c:
            violations.append(f"lock violated: {nm(sid)} not in class {c}")

    # gan_class_restrictions — unresolvable names are hard errors, never silent no-ops
    for gan, allowed in (config.get("gan_class_restrictions") or {}).items():
        if gan not in gan_matrix:
            violations.append(f"gan_class_restrictions: gan '{gan}' not found in roster "
                              f"(check spelling/normalization: {sorted(gan_matrix)})")
            continue
        bad_names = [str(cn) for cn in allowed if str(cn).strip() not in [str(x).strip() for x in names]]
        if bad_names:
            violations.append(f"gan_class_restrictions: unknown class names {bad_names} "
                              f"(class_names: {names})")
            continue
        allowed_idx = {i for i, cn in enumerate(names) if str(cn).strip() in [str(x).strip() for x in allowed]}
        # a lock made on the board (fingerprinted export = counselor decision) overrides
        # the restriction for that child — mirror solve.py's exemption exactly
        for s in students:
            if s["gan"] != gan or s["id"] in board_locked_ids:
                continue
            c = assign.get(s["id"])
            if c is not None and 0 <= c < k and c not in allowed_idx:
                violations.append(f"gan restriction violated: {s['name']} from gan '{gan}' "
                                  f"in class '{names[c]}' (allowed: {list(allowed)})")

    counts = {"rank1": 0, "rank2": 0, "rank3": 0, "none": len(unsatisfied), "no_choices": len(no_edges)}
    for r in sat_rank.values():
        if r in (1, 2, 3):
            counts[f"rank{r}"] += 1

    report = {"hard_violations": violations, "warnings": warnings,
              "sizes": dict(zip(names, sizes)),
              "mishalevet_per_class": dict(zip(names, mish)),
              "gan_matrix": {g: dict(zip(names, v)) for g, v in gan_matrix.items()},
              "satisfaction": counts,
              "unsatisfied_children": unsatisfied, "children_without_choices": no_edges,
              "ok": not violations}

    if not a.json_only:
        print("=== סיכום שיבוץ ===")
        for c in range(k):
            print(f"{names[c]}: {sizes[c]} תלמידים, {mish[c]} משלבת")
        print(f"קיבלו בחירה ראשונה: {counts['rank1']}, שנייה: {counts['rank2']}, שלישית: {counts['rank3']}")
        if unsatisfied:
            print(f"⚠ ילדים ללא אף חבר שבחרו: {', '.join(unsatisfied)}")
        if no_edges:
            print(f"ℹ ילדים ללא בחירות תקפות (לטיפול ידני): {', '.join(no_edges)}")
        for v in violations:
            print(f"✗ {v}")
        for w in warnings:
            print(f"⚠ {w}")
    print(json.dumps(report, ensure_ascii=False))
    sys.exit(0 if not violations else 2)


if __name__ == "__main__":
    main()
