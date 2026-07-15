# Solver model & infeasibility playbook

## The model (CP-SAT)

Variables: `x[s][c]` — student s in class c.

Hard constraints (strict mode):
1. Each student in exactly one class.
2. Class sizes within `[min_size, max_size]` (default even split ±2).
3. Mishalevet: if #mishalevet == #classes, exactly one per class; otherwise at most
   ⌈m/k⌉ per class (spread), with a warning.
4. Friend guarantee: every student with ≥1 *matched* choice shares a class with at
   least one of their chosen friends. Students with zero matched choices are exempt —
   name them to the user, always.
5. `locks` (fixed class), `apart` (never same class), `together` (always same class).
6. `gan_class_restrictions` (gan → allowed classes) — **outside the relaxation ladder,
   never auto-relaxed**; unresolvable gan/class names are a hard error (exit 2), never
   a silent no-op. Class names are matched leniently (geresh/space-insensitive), but
   two names that normalize identically error loudly. ONE exception: a lock arriving
   via a fingerprinted board export (= the counselor's explicit decision on the board)
   overrides the restriction for that child only, with a named warning
   (`override_warnings` in solution.json) — the rule stays intact for the rest of the
   gan. A conflicting CONFIG lock still errors (assistant-authored; typos must fail).

Deterministic pre-checks (before any solving): an apart pair locked into the same
class, or a together pair locked into different classes, dies immediately with the
children's names — never burns the relaxation ladder.

Objective (maximize): Σ satisfied choices weighted by rank (defaults 5/3/2 — every
satisfied choice counts, not just the best one) − gan-spread deviations × `gan_dev`
− gender deviations × `gender_dev`.

Gan spread: for each gan g and class c, the count must fall in
[⌊|g|/k⌋ − tol, ⌈|g|/k⌉ + tol] (hard, default tol=1). Without hard bounds the solver
happily puts zero kids from some gan in a class — friend clusters correlate with gan,
so friendship weight overwhelms a soft penalty. If hard bounds clash with the friend
guarantee, the ladder softens them first (R1) since friends matter more.

## Relaxation ladder

solve.py retries automatically, recording each step in `relaxations`:

- **R1**: gan spread hard bounds → penalty (`gan_dev`, default 8 per child of
  deviation). Check the gan matrix in validation output afterwards.
- **R2**: friend guarantee → penalty of 1000 per unsatisfied child. The solver will
  sacrifice it only when truly impossible (e.g., a child whose only friends form an
  over-constrained clique). Report *which* children by name.
- **R3**: size bounds widened by 2.
- **R4**: mishalevet "exactly one" → "spread".

If all fail, the cause is almost always contradictory locks/apart/together
(e.g., A together B, B together C, A apart C) or an over-tight gan_class_restrictions
(which never relaxes). Check those by hand and show the user the contradiction in
plain words.

**The validator is relaxation-aware:** validate_solution.py reads `relaxations` from
solution.json and downgrades the correspondingly-relaxed checks to clearly-labeled
warnings (exit 0) instead of contradicting the solver with "hard violations". An
UNLABELED solution with the same breaches still exits 2 — manual breakage stays loud.

## Explaining results to counselors

- "אופטימלי" claims apply only to the objective given the constraints. Say instead:
  "כל ילד קיבל לפחות חבר אחד; 61 קיבלו בחירה ראשונה" — concrete numbers.
- If a kid got only their 3rd choice, that's a candidate for manual attention on the
  board, not a bug.
- When the user asks "why is X not with Y" — check: was the choice matched? was there
  an apart constraint? did moving X break someone else's only satisfied choice? The
  board's click-highlight answers most of these visually.

## Performance

n≈100, k≈4, ~300 edges: CP-SAT solves in seconds; 30s time limit is generous. If the
model is much larger (multi-grade), raise `--time-limit` and expect FEASIBLE rather
than OPTIMAL — that's fine.

## Fallback engine (--engine local)

Simulated annealing over move/swap neighborhood, same cost structure, fixed seed
(reproducible). Use only when OR-Tools can't be installed. **Acceptance gate:** after
annealing, an explicit `hard_violations()` checklist (mirroring the CP-SAT hard set at
the current relaxation level) decides FEASIBLE/INFEASIBLE — an accepted solution is
GUARANTEED hard-feasible. Maintainer invariant: the gate must never be replaced by a
net-cost threshold (penalties minus friendship gain) — gain masks violations; that bug
shipped once. The engine still cannot *prove* infeasibility — if it reports INFEASIBLE,
treat it as "probably infeasible" and inspect constraints before relaxing.
