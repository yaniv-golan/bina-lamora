# Hebrew name matching — what the normalizer does and doesn't catch

reconcile_names.py normalizes before comparing:

- Final letters folded: ך→כ, ם→מ, ן→נ, ף→פ, ץ→צ (so "חן" matches "חנ...")
- Nikud and te'amim stripped (U+0591–U+05C7)
- Geresh/gershayim/quotes removed (so "יעקב" ≈ 'יעקב', צ'רלי ≈ צרלי)
- Punctuation → space, whitespace collapsed, Latin lowercased
- First-name-only picks compared against roster first names (slight penalty)
- Reversed word order tried ("כהן נועה" ≈ "נועה כהן")

Caught automatically (score ≥ 0.93): minor typos (יוסי/יossi, אביגיל/אביגייל),
missing/extra final letter, partial surnames.

Goes to **ambiguous** (human decides):
- Two kids sharing a first name when the pick is first-name-only ("נועה" → נועה כהן /
  נועה לוי). Show the chooser's gan — kids usually pick friends from their own gan,
  which is a strong hint, but let the human confirm.
- If you're ever forced to resolve without the human (batch mode), rank candidates by:
  same gan first, then gender-consistency of the *written form* (ליבי is a girl's name;
  matching it to לביא, a boy, is almost certainly wrong even if the letters are close),
  then score. And still log every such decision for review.
- ktiv male/haser far apart (שרה/שרהלה, מיכל/מיכאלה) — similarity may be mid-range.
- Nicknames with no letter overlap (אלכס↔אלכסנדר scores fine, but יוסי↔יוסף scores
  ~0.7 → lands in ambiguous, good; צחי↔יצחק may score <0.6 → lands in unmatched!).

Goes to **unmatched** (dropped, but review the list before accepting):
- Kids going to a different school — correct behavior, drop.
- Radical nicknames (see above). Scan the unmatched list; if a "no plausible match"
  entry looks like a nickname of a roster kid, add a resolution manually instead of
  letting it drop. This is the main silent-failure risk of the whole pipeline.

Duplicate full names in the roster get " (2)" suffixes at parse time — before
reconciling, ask the user to tell the two apart (usually by gan) and note it, because
every choice pointing at that name becomes ambiguous by design.
