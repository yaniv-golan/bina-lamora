#!/usr/bin/env python3
"""Assign students to classes. CP-SAT (OR-Tools) with pure-Python fallback.

Usage:
  python solve.py reconciled.json --config config.json -o solution.json
                  [--board-state board_state.json] [--engine cpsat|local] [--time-limit 30]

Hard constraints: one class per student; class size bounds; mishalevet spread
(exactly/at-most one per class); >=1 satisfied choice per student who has matched
choices; locks / apart / together pairs; gan_class_restrictions (gan → allowed
classes; never auto-relaxed; unresolvable names are a hard error).

Board-state lock semantics: exports carrying a fingerprint/version REPLACE config
locks (the board pre-locks anchors, so a deliberately-unlocked anchor stays
unlocked); legacy exports without a fingerprint merge over config locks.
Soft (objective): rank-weighted satisfied choices, gan spread, gender balance.

Relaxation ladder (applied automatically on infeasibility, recorded in output):
  R1 gan spread: hard bounds -> heavy penalty
  R2 friend guarantee -> heavy penalty (reports which kids lost it)
  R3 size bounds widened by 2
  R4 mishalevet 'exactly one' -> 'at most one'
See references/solver-notes.md.
"""
import argparse, json, math, random, sys
from collections import defaultdict

BIG = 1000  # penalty per child without a satisfied choice under relaxation
DEFAULT_WEIGHTS = {"rank1": 5, "rank2": 3, "rank3": 2, "gan_dev": 8, "gender_dev": 1}


def load(path):
    return json.load(open(path, encoding="utf-8"))


def prepare(data, config, board_state):
    students = data["students"]
    idx = {s["id"]: i for i, s in enumerate(students)}
    n = len(students)
    k = config["num_classes"]
    edges = []  # (chooser_idx, target_idx, rank)
    for s in students:
        for c in s.get("choices", []):
            if c["target"] in idx:
                edges.append((idx[s["id"]], idx[c["target"]], c["rank"]))
    has_edge = {i for i, _, _ in edges}

    base_min = max(0, math.floor(n / k) - 2)
    base_max = math.ceil(n / k) + 2
    size_min = config.get("min_size") or base_min
    size_max = config.get("max_size") or base_max

    def die(msg, **extra):
        print(json.dumps({"error": msg, **extra}, ensure_ascii=False), file=sys.stderr)
        sys.exit(2)

    locks = {}
    for sid, cls in (config.get("locks") or {}).items():
        if sid not in idx:
            die(f"locks: student id '{sid}' not in roster — the roster may have been "
                f"re-parsed since this config was written; rebuild the locks",
                roster_size=n)
        cls = int(cls)
        if not (0 <= cls < k):
            die(f"locks: class index {cls} for '{students[idx[sid]]['name']}' out of range "
                f"(valid: 0..{k-1}; indices are 0-based — 'א1' is 0)")
        locks[idx[sid]] = cls
    board_locked = set()  # student indices locked via a FINGERPRINTED export (counselor decisions)
    if board_state:
        # A board export carrying a fingerprint/version was generated from a board that
        # already knew the config anchors (it pre-locks them). Its lock set is therefore
        # authoritative: REPLACE config locks, so an anchor the counselor deliberately
        # unlocked stays unlocked. Legacy exports (no fingerprint) keep merge behavior.
        fingerprinted = bool(board_state.get("fingerprint") or board_state.get("version"))
        stale = [sid for sid in board_state.get("locks", []) if sid not in idx]
        if fingerprinted and stale:
            die("board-state export references student ids not in this roster — the board "
                "was built from a different/older roster; regenerate the board and redo "
                "the manual edits", unknown_ids=stale)
        if fingerprinted:
            locks = {}
        for sid in board_state.get("locks", []):
            if sid in idx and sid in board_state.get("assignment", {}):
                c = int(board_state["assignment"][sid])
                if 0 <= c < k:
                    locks[idx[sid]] = c
                    if fingerprinted:
                        board_locked.add(idx[sid])
                elif fingerprinted:
                    die(f"board-state lock for '{students[idx[sid]]['name']}' has class index "
                        f"{c} out of range 0..{k-1} — was the board built with a different "
                        f"number of classes?")

    # gan → allowed class indices ("סיגלון רק בא1 וא3"). Administrative decree:
    # applied as hard domain restrictions, never auto-relaxed, and unresolvable
    # names are a loud error — this must never become a silent no-op.
    class_names = config.get("class_names") or [f"כיתה א'{i+1}" for i in range(k)]
    cname_idx = {str(cn).strip(): i for i, cn in enumerate(class_names)}
    student_gans = {s["gan"] for s in students}
    restrict = {}  # student_idx -> set(allowed class indices)
    for gan, allowed in (config.get("gan_class_restrictions") or {}).items():
        if gan not in student_gans:
            print(json.dumps({"error": f"gan_class_restrictions: gan '{gan}' not in roster",
                              "roster_gans": sorted(student_gans)}, ensure_ascii=False),
                  file=sys.stderr); sys.exit(2)
        allowed_idx = set()
        for cn in allowed:
            if str(cn).strip() not in cname_idx:
                print(json.dumps({"error": f"gan_class_restrictions: class '{cn}' not in class_names",
                                  "class_names": class_names}, ensure_ascii=False),
                      file=sys.stderr); sys.exit(2)
            allowed_idx.add(cname_idx[str(cn).strip()])
        for i, s in enumerate(students):
            if s["gan"] == gan:
                restrict[i] = allowed_idx
    # Lock vs gan-restriction conflicts: a lock made ON THE BOARD (fingerprinted export
    # = the counselor's explicit decision) OVERRIDES the restriction for that child only
    # — the rule stays intact for everyone else. A conflicting CONFIG lock is
    # assistant-authored and keeps failing loudly (a typo must not become legal).
    override_warnings = []
    for i, c in locks.items():
        if i in restrict and c not in restrict[i]:
            if i in board_locked:
                del restrict[i]
                override_warnings.append(
                    f"board lock overrides gan restriction for '{students[i]['name']}' "
                    f"(gan '{students[i]['gan']}', class {c}) — rule still applies to the rest of the gan")
            else:
                die(f"lock for '{students[i]['name']}' (class {c}) conflicts with gan_class_restrictions")

    def pairs(key):
        # unresolvable ids in apart/together are as dangerous silently dropped as a
        # bad gan restriction — same loud-error discipline (these are 'keep these two
        # children separated' directives; a typo must not become a no-op)
        out = []
        for a, b in (config.get(key) or []):
            missing = [x for x in (a, b) if x not in idx]
            if missing:
                die(f"{key}: pair [{a}, {b}] references unknown student id(s) {missing} — "
                    f"the roster may have changed since this config was written")
            out.append((idx[a], idx[b]))
        return out
    weights = {**DEFAULT_WEIGHTS, **(config.get("weights") or {})}
    hint = None
    if board_state and board_state.get("assignment"):
        hint = {idx[sid]: int(c) for sid, c in board_state["assignment"].items()
                if sid in idx and 0 <= int(c) < k}

    apart_p, together_p = pairs("apart"), pairs("together")
    # Cheap deterministic pre-checks: contradictory locks must fail IMMEDIATELY with
    # names, not after burning the full relaxation ladder. These are backstops against
    # assistant error — SKILL.md Stage 5 reconciles counselor decisions BEFORE solving.
    for a, b in apart_p:
        if a in locks and b in locks and locks[a] == locks[b]:
            die(f"apart pair locked into the same class: '{students[a]['name']}' + "
                f"'{students[b]['name']}' (class {locks[a]}) — if the counselor chose this "
                f"deliberately, remove the apart pair from config.json before solving")
    for a, b in together_p:
        if a in locks and b in locks and locks[a] != locks[b]:
            die(f"together pair locked into different classes: '{students[a]['name']}' "
                f"(class {locks[a]}) + '{students[b]['name']}' (class {locks[b]}) — if "
                f"deliberate, remove the together pair from config.json before solving")

    return dict(students=students, n=n, k=k, edges=edges, has_edge=has_edge,
                size_min=size_min, size_max=size_max, locks=locks, restrict=restrict,
                apart=apart_p, together=together_p, override_warnings=override_warnings,
                weights=weights, gan_tol=int(config.get("gan_tolerance", 1)), hint=hint,
                mish=[i for i, s in enumerate(students) if s.get("mishalevet")])


def rank_w(weights, rank):
    return weights.get(f"rank{rank}", 1)


# ---------------- CP-SAT engine ----------------

def solve_cpsat(P, relax, time_limit):
    from ortools.sat.python import cp_model
    m = cp_model.CpModel()
    n, k = P["n"], P["k"]
    x = [[m.NewBoolVar(f"x{s}_{c}") for c in range(k)] for s in range(n)]
    for s in range(n):
        m.AddExactlyOne(x[s])
    smin = P["size_min"] - (2 if relax >= 3 else 0)
    smax = P["size_max"] + (2 if relax >= 3 else 0)
    for c in range(k):
        m.Add(sum(x[s][c] for s in range(n)) >= max(0, smin))
        m.Add(sum(x[s][c] for s in range(n)) <= smax)

    # mishalevet spread
    mish = P["mish"]
    exact = len(mish) == k and relax < 4
    for c in range(k):
        tot = sum(x[s][c] for s in mish)
        if mish:
            (m.Add(tot == 1) if exact else m.Add(tot <= max(1, math.ceil(len(mish) / k))))

    # locks / apart / together / gan-class restrictions
    for s, c in P["locks"].items():
        m.Add(x[s][c] == 1)
    for s, allowed in P["restrict"].items():
        for c in range(k):
            if c not in allowed:
                m.Add(x[s][c] == 0)
    for a, b in P["apart"]:
        for c in range(k):
            m.Add(x[a][c] + x[b][c] <= 1)
    for a, b in P["together"]:
        for c in range(k):
            m.Add(x[a][c] == x[b][c])

    # friendship
    obj = []
    sat_pen = []
    same_by_chooser = defaultdict(list)
    for (s, t, rank) in P["edges"]:
        # y = 1 iff s and t share a class:  y = OR_c (x[s][c] AND x[t][c])
        y = m.NewBoolVar(f"y{s}_{t}_{rank}")
        zs = []
        for c in range(k):
            z = m.NewBoolVar(f"z{s}_{t}_{rank}_{c}")
            m.Add(z <= x[s][c]); m.Add(z <= x[t][c]); m.Add(z >= x[s][c] + x[t][c] - 1)
            zs.append(z)
        m.Add(y <= sum(zs))
        for z in zs:
            m.Add(y >= z)
        obj.append(rank_w(P["weights"], rank) * y)
        same_by_chooser[s].append(y)
    for s in P["has_edge"]:
        sat = m.NewBoolVar(f"sat{s}")
        m.Add(sum(same_by_chooser[s]) >= 1).OnlyEnforceIf(sat)
        m.Add(sum(same_by_chooser[s]) == 0).OnlyEnforceIf(sat.Not())
        if relax < 2:
            m.Add(sat == 1)
        else:
            sat_pen.append(BIG * (1 - sat))

    # gan spread (hard bounds with tolerance; soft from R1)
    gans = defaultdict(list)
    for i, s in enumerate(P["students"]):
        gans[s["gan"]].append(i)
    dev_terms = []
    for g, members in gans.items():
        lo = max(0, math.floor(len(members) / k) - P["gan_tol"])
        hi = math.ceil(len(members) / k) + P["gan_tol"]
        for c in range(k):
            cnt = sum(x[s][c] for s in members)
            if relax < 1:
                m.Add(cnt >= lo)
                m.Add(cnt <= hi)
            else:
                over = m.NewIntVar(0, len(members), f"ov_{g}_{c}")
                under = m.NewIntVar(0, len(members), f"un_{g}_{c}")
                m.Add(cnt - hi <= over)
                m.Add(lo - cnt <= under)
                dev_terms.append(P["weights"]["gan_dev"] * (over + under))

    # gender balance (soft)
    genders = defaultdict(list)
    for i, s in enumerate(P["students"]):
        if s.get("gender"):
            genders[s["gender"]].append(i)
    for g, members in genders.items():
        lo, hi = math.floor(len(members) / k) - 2, math.ceil(len(members) / k) + 2
        for c in range(k):
            cnt = sum(x[s][c] for s in members)
            over = m.NewIntVar(0, len(members), f"gov_{g}_{c}")
            under = m.NewIntVar(0, len(members), f"gun_{g}_{c}")
            m.Add(cnt - hi <= over)
            m.Add(max(0, lo) - cnt <= under)
            dev_terms.append(P["weights"]["gender_dev"] * (over + under))

    m.Maximize(sum(obj) - sum(sat_pen) - sum(dev_terms))
    if P["hint"]:
        for s, c in P["hint"].items():
            if 0 <= c < k:
                m.AddHint(x[s][c], 1)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 4
    st = solver.Solve(m)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        assign = {P["students"][s]["id"]: next(c for c in range(k) if solver.Value(x[s][c]))
                  for s in range(n)}
        return assign, ("OPTIMAL" if st == cp_model.OPTIMAL else "FEASIBLE"), solver.ObjectiveValue()
    return None, "INFEASIBLE", None


# ---------------- local fallback engine ----------------

def hard_violations(P, assign, relax):
    """Enumerate violated HARD constraints at this relaxation level — mirrors the
    CP-SAT hard-constraint set exactly. This is the local engine's acceptance gate:
    the annealing cost is a guide, but only this list decides FEASIBLE/INFEASIBLE.
    (The old gate compared net cost (penalties MINUS friendship gain) to a threshold,
    so gain could mask a genuine hard violation — never reintroduce that.)"""
    k = P["k"]
    out = []
    sizes = [0] * k
    for c in assign:
        sizes[c] += 1
    smin = max(0, P["size_min"] - (2 if relax >= 3 else 0))
    smax = P["size_max"] + (2 if relax >= 3 else 0)
    for c in range(k):
        if not (smin <= sizes[c] <= smax):
            out.append(f"size: class {c} has {sizes[c]} (allowed {smin}-{smax})")
    if P["mish"]:
        mish_ct = [0] * k
        for i in P["mish"]:
            mish_ct[assign[i]] += 1
        if len(P["mish"]) == k and relax < 4:
            out += [f"mishalevet: class {c} has {mish_ct[c]} (expected 1)"
                    for c in range(k) if mish_ct[c] != 1]
        else:
            cap = max(1, math.ceil(len(P["mish"]) / k))
            out += [f"mishalevet: class {c} has {mish_ct[c]} (cap {cap})"
                    for c in range(k) if mish_ct[c] > cap]
    for s, c in P["locks"].items():
        if assign[s] != c:
            out.append(f"lock: {P['students'][s]['name']} not in class {c}")
    for s, allowed in P["restrict"].items():
        if assign[s] not in allowed:
            out.append(f"gan restriction: {P['students'][s]['name']}")
    for a, b in P["apart"]:
        if assign[a] == assign[b]:
            out.append(f"apart together: {P['students'][a]['name']} + {P['students'][b]['name']}")
    for a, b in P["together"]:
        if assign[a] != assign[b]:
            out.append(f"together split: {P['students'][a]['name']} + {P['students'][b]['name']}")
    if relax < 2:
        sat = set()
        for (s, t, _rank) in P["edges"]:
            if assign[s] == assign[t]:
                sat.add(s)
        out += [f"no friend: {P['students'][s]['name']}" for s in P["has_edge"] if s not in sat]
    return out


def cost(P, assign, relax):
    k = P["k"]
    sizes = [0] * k
    for c in assign:
        sizes[c] += 1
    pen = 0
    smin = P["size_min"] - (2 if relax >= 3 else 0)
    smax = P["size_max"] + (2 if relax >= 3 else 0)
    for c in range(k):
        pen += 10000 * max(0, smin - sizes[c]) + 10000 * max(0, sizes[c] - smax)
    mish_ct = [0] * k
    for i in P["mish"]:
        mish_ct[assign[i]] += 1
    cap = 1 if (len(P["mish"]) == P["k"] and relax < 4) else max(1, math.ceil(len(P["mish"]) / k))
    for c in range(k):
        if len(P["mish"]) == k and relax < 4:
            pen += 10000 * abs(mish_ct[c] - 1)
        else:
            pen += 10000 * max(0, mish_ct[c] - cap)
    for s, c in P["locks"].items():
        if assign[s] != c:
            pen += 10 ** 6
    for s, allowed in P["restrict"].items():
        if assign[s] not in allowed:
            pen += 10 ** 6
    for a, b in P["apart"]:
        if assign[a] == assign[b]:
            pen += 10 ** 5
    for a, b in P["together"]:
        if assign[a] != assign[b]:
            pen += 10 ** 5
    sat = defaultdict(bool)
    gain = 0
    for (s, t, rank) in P["edges"]:
        if assign[s] == assign[t]:
            gain += rank_w(P["weights"], rank)
            sat[s] = True
    for s in P["has_edge"]:
        if not sat[s]:
            pen += BIG if relax >= 2 else 10 ** 5
    gcount = defaultdict(lambda: [0] * k)
    for i, s in enumerate(P["students"]):
        gcount[s["gan"]][assign[i]] += 1
    for g, cnts in gcount.items():
        tot = sum(cnts)
        lo = max(0, math.floor(tot / k) - P["gan_tol"]); hi = math.ceil(tot / k) + P["gan_tol"]
        w = 10 ** 5 if relax < 1 else P["weights"]["gan_dev"]
        for c in range(k):
            pen += w * (max(0, cnts[c] - hi) + max(0, lo - cnts[c]))
    return pen - gain


def solve_local(P, relax, time_limit):
    rng = random.Random(42)
    n, k = P["n"], P["k"]
    assign = [i % k for i in range(n)]
    if P["hint"]:
        for s, c in P["hint"].items():
            assign[s] = c
    for s, c in P["locks"].items():
        assign[s] = c
    cur = cost(P, assign, relax)
    T0, iters = 5.0, 60000
    for it in range(iters):
        T = T0 * (1 - it / iters) + 0.01
        s = rng.randrange(n)
        if s in P["locks"]:
            continue
        if rng.random() < 0.5:
            new_c = rng.randrange(k)
            old_c = assign[s]
            if new_c == old_c:
                continue
            assign[s] = new_c
            nc = cost(P, assign, relax)
            if nc <= cur or rng.random() < math.exp((cur - nc) / T):
                cur = nc
            else:
                assign[s] = old_c
        else:
            t = rng.randrange(n)
            if t == s or t in P["locks"] or assign[s] == assign[t]:
                continue
            assign[s], assign[t] = assign[t], assign[s]
            nc = cost(P, assign, relax)
            if nc <= cur or rng.random() < math.exp((cur - nc) / T):
                cur = nc
            else:
                assign[s], assign[t] = assign[t], assign[s]
    # Acceptance gate: explicit hard-constraint check (NOT the net cost — friendship
    # gain must never mask a violation). Any violated hard constraint at this relax
    # level = INFEASIBLE, so the ladder in main() escalates honestly.
    if hard_violations(P, assign, relax):
        return None, "INFEASIBLE", None
    return {P["students"][i]["id"]: assign[i] for i in range(n)}, "FEASIBLE", -cur


# ---------------- main ----------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("reconciled")
    ap.add_argument("--config", required=True)
    ap.add_argument("-o", "--output", default="solution.json")
    ap.add_argument("--board-state")
    ap.add_argument("--engine", choices=["cpsat", "local", "auto"], default="auto")
    ap.add_argument("--time-limit", type=float, default=30.0)
    a = ap.parse_args()

    data = load(a.reconciled)
    config = load(a.config)
    board_state = load(a.board_state) if a.board_state else None
    P = prepare(data, config, board_state)

    engine = a.engine
    fallback = False
    if engine in ("auto", "cpsat"):
        try:
            import ortools.sat.python.cp_model  # noqa
            engine = "cpsat"
        except ImportError:
            if a.engine == "cpsat":
                print(json.dumps({"error": "ortools not installed; pip install ortools --break-system-packages, or use --engine local"}), file=sys.stderr)
                sys.exit(1)
            engine = "local"
            fallback = True  # auto-fallback: caller MUST tell the user (see SKILL.md)

    solver = solve_cpsat if engine == "cpsat" else solve_local
    relax_notes = {0: None,
                   1: "gan spread relaxed from hard bounds to penalty — check the gan matrix",
                   2: "friend guarantee relaxed to heavy penalty — some children may have no satisfied choice",
                   3: "class size bounds widened by 2",
                   4: "mishalevet 'exactly one per class' relaxed to 'spread as evenly as possible'"}
    applied = []
    assign = status = obj = None
    for relax in range(0, 5):
        if relax_notes[relax]:
            applied.append(relax_notes[relax])
        assign, status, obj = solver(P, relax, a.time_limit)
        if assign:
            break
    if not assign:
        print(json.dumps({"error": "no solution found even after all relaxations — check locks/apart/together/gan_class_restrictions for contradictions (restrictions are never auto-relaxed)"}), file=sys.stderr)
        sys.exit(2)

    out = {"assignment": assign, "engine": engine, "status": status,
           "objective": obj, "relaxations": applied,
           "fallback": fallback, "proven_optimal": status == "OPTIMAL",
           "override_warnings": P["override_warnings"],
           "num_classes": P["k"],
           "class_names": config.get("class_names") or [f"כיתה א'{i+1}" for i in range(P["k"])]}
    json.dump(out, open(a.output, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for w in P["override_warnings"]:
        print(json.dumps({"warning": w}, ensure_ascii=False), file=sys.stderr)
    if fallback:
        print(json.dumps({"engine_warning": "OR-Tools unavailable — ran the local fallback; "
                          "result is good but NOT provably optimal. Tell the user in plain "
                          "language (see SKILL.md network section)."}), file=sys.stderr)
    print(json.dumps({"ok": True, "engine": engine, "status": status, "fallback": fallback,
                      "relaxations": applied}, ensure_ascii=False))


if __name__ == "__main__":
    main()
