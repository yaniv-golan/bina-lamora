<div dir="rtl">

# קלוד-למורה 👩‍🏫

**כלים של Claude למורות, למורים ולצוותי חינוך בישראל.** עברית תחילה, בלי ז'רגון,
בנוי לעבודה אמיתית בבית ספר.

הכלי הראשון כאן: **המשבץ** — שיבוץ שכבה לכיתות מאוזנות.

> אין צורך לדעת לתכנת, ואין מה להתקין במחשב. הכל קורה בתוך Claude שבדפדפן.
> אם את/ה יודע/ת לפתוח קובץ אקסל ולשלוח הודעה — זה מספיק. המדריך מלווה צעד-אחר-צעד.

---

## מה זה עושה?

מחליף את טקס הפתקים על הקיר. שולחים ל-Claude את קובץ האקסל של בחירות החברים
(מטופס Google, או קובץ שהיועצת הכינה), ומקבלים חלוקה לכיתות שבה:

- **לכל ילד יש לפחות חבר אחד שהוא בחר** בכיתה.
- הכיתות מאוזנות בגודל, במגדר ובגני המוצא.
- **לוח גרירה בעברית** — קובץ אחד שנפתח בכל דפדפן (גם במחשב בית-ספרי בלי אינטרנט),
  שבו גוררים ילדים בין כיתות ורואים מיד למי יש חבר ולמי לא.
- **קובץ אקסל סופי** — גיליון לכל כיתה, סיכום, ורשימת "לתשומת לב".

הכל בשיחה אחת, בעברית, כשהמערכת שואלת אותך שאלות פשוטות ואת/ה עונה במילים שלך.

---

## מה צריך כדי להתחיל

- **מנוי Claude בתשלום** — כל מנוי מתאים (Pro, Max, Team או Enterprise).
- **דפדפן** — נכנסים ל-**claude.ai** ומתחברים. אפשר גם באפליקציית Claude למחשב או בנייד;
  זה אותו חשבון, ואותם צעדים בדיוק.

> אין צורך להוריד או להתקין תוכנה. "המשבץ" מותקן בתוך Claude עצמו (בבחירת "Plugins"),
> ורץ שם.

---

## שלב 1 — הוספת "המשבץ" ל-Claude (פעם אחת, דקה)

עושים את זה **פעם אחת בלבד**. אחרי זה המשבץ תמיד שם.

1. נכנסים ל-**claude.ai** ומתחברים.
2. בתפריט הצד לוחצים על **Customize** (התאמה אישית).
   > עובד/ת דרך **Cowork**? פותחים קודם את לשונית **Cowork**, ואז **Customize** — משם
   > הצעדים זהים.
3. במסך שנפתח, לוחצים בצד על **Plugins** (פלאגינים).
4. למעלה מימין לוחצים על **Add ▾** ובוחרים **Add marketplace** (הוספת מרקטפלייס).
5. בשדה הכתובת מקלידים:

   <div dir="ltr">

   ```
   yaniv-golan/claude-lamora
   ```

   </div>

   ובוחרים את **claude-lamora / yaniv-golan** שקופץ ברשימה.
6. לוחצים על **Sync** (סנכרון). נפתח חלון שבו מופיע הכרטיס **המשבץ**.
7. לוחצים על כפתור ה־**+** שעל כרטיס המשבץ. תופיע הודעה קטנה למעלה:
   *"המשבץ is installed and ready to use"* — זהו, מותקן. 🎉

אפשר לסגור את החלון. לא צריך לחזור על השלב הזה שוב.

**ככה זה נראה, צעד-אחר-צעד** (עקבו אחרי המספרים בעיגולים הכתומים):

<div align="center">

<img src="docs/images/frame1-add-marketplace.png" width="760" alt="לשונית Plugins — פתיחת התפריט Add ובחירת Add marketplace">

<sub>① לוחצים **Add**, ② בוחרים **Add marketplace**.</sub>

<img src="docs/images/frame2-sync.png" width="760" alt="חלון Add marketplace — הקלדת yaniv-golan/claude-lamora ולחיצה על Sync">

<sub>③ מקלידים <code>yaniv-golan/claude-lamora</code>, ④ לוחצים **Sync**.</sub>

<img src="docs/images/frame3-install.png" width="760" alt="חלון Directory — כרטיס המשבץ עם כפתור הפלוס להתקנה">

<sub>⑤ לוחצים על **+** בכרטיס **המשבץ**.</sub>

<img src="docs/images/frame4-installed.png" width="760" alt="הודעת אישור: המשבץ הותקן ומוכן לשימוש">

<sub>✓ מופיעה הודעת האישור — המשבץ מותקן ומוכן.</sub>

</div>

---

## שלב 2 — שיבוץ כיתות (בכל פעם מחדש)

1. **פותחים שיחה חדשה** ב-Claude.
2. **מצרפים את קובץ האקסל** של בחירות החברים (גוררים אותו לתוך השיחה, או בכפתור
   ה-**+** / המהדק 📎).
3. **כותבים בעברית**, למשל:

   > *"יש לי קובץ בחירות חברים של כיתות א', תעזור לי לשבץ אותם לכיתות."*

   Claude יזהה לבד שצריך להפעיל את המשבץ — לא צריך פקודות מיוחדות.
4. **עונים על השאלות.** המשבץ ישאל אותך דברים פשוטים, אחד-אחד, בעברית:
   - כמה כיתות? ואיך קוראים להן (למשל א1, א2, א3)?
   - יש ילדי שילוב? מי הם? (אפשר פשוט להקליד רשימת שמות.)
   - יש ילדים שחייבים / אסור להם להיות ביחד, או ילדים שכבר סגורים לכיתה מסוימת?
5. **מקבלים "טיוטת לוח"** — קובץ אחד שאפשר לפתוח ולראות איך החלוקה נראית, עוד לפני
   שנכנסים לכל הפרטים הקטנים.
6. המשבץ יעבור איתך על **שמות** שההורים כתבו בטעות ("מי זו 'נועה' — נועה כהן או נועה
   לוי?") ועל **הערות** מהעמודה (לא-עם / עדיפות-עם / כוכב / שילוב). כלום לא נכנס
   לשיבוץ בלי שאישרת.
7. **מקבלים את הלוח הסופי** — פותחים אותו בדפדפן, גוררים ילדים בין כיתות אם רוצים
   (כל גרירה ננעלת אוטומטית), ובלחיצה רואים למי כל ילד בחר ומי בחר אותו.
8. **מקבלים קובץ אקסל** מוכן — גיליון לכל כיתה. זה הפלט שאפשר להדפיס ולהגיש.

עשית שינוי ידני בלוח ורוצה שהמערכת תאזן מחדש סביבו? שומרים את הלוח לקובץ, מחזירים אותו
לשיחה וכותבים "תמשיך מכאן" — והמשבץ ממשיך מאיפה שהיית.

---

## פרטיות — חשוב 🔒

הכלי בנוי סביב עיקרון אחד: **מידע על קטינים לא עוזב את הסביבה שלך.**

- אין חיפוש שמות באינטרנט.
- אין שליחת רשימת הילדים לשום שירות חיצוני.
- לוח הסקירה הוא קובץ עצמאי — נפתח גם במחשב בית-ספרי בלי חיבור לאינטרנט.

הקבצים הסופיים מכילים שמות של ילדים — לשמור עליהם כמו על כל מסמך רגיש בבית הספר.

---

## אם משהו לא עובד 🛠️

- **לא מוצא/ת את Customize או את Plugins** — ודא/י שאת/ה מחובר/ת לחשבון Claude בתשלום.
  הפלאגינים זמינים במנויי Pro / Max / Team / Enterprise.
- **המשבץ לא "תופס" בשיחה** — פתח/י שיחה חדשה אחרי ההתקנה ונסה/י שוב.
- **הקובץ לא נקרא כמו שצריך** — פשוט ספר/י למשבץ בשיחה מה יש בקובץ ("יש כמה גיליונות",
  "שמות הגנים לא אחידים") — הוא בנוי להתמודד עם זה ולשאול אותך מה שחסר.
- נתקעת? פשוט כתוב/י בשיחה מה קרה — Claude יסביר וימשיך משם.

---

## דרישות טכניות (למי שסקרן/ית)

- הכל רץ בתוך Claude — Python מגיע מובנה, לא צריך להתקין כלום במחשב שלך.
- לאופטימיזציה המתמטית המלאה מומלצת ספריית `ortools` — המשבץ מתקין אותה לבד כשיש רשת,
  ועובד מצוין גם בלעדיה (יש לו מנוע גיבוי מובנה שרץ בלי אינטרנט).

</div>

---

<div dir="ltr">

## English

**claude-lamora** ("Claude for the Teacher", קלוד-למורה) is a Claude plugin marketplace
for Israeli educators, built for **Claude Cowork**. Its first skill, **hameshabetz**
(המשבץ, "The Placer"), turns a Google Forms friend-choice export into a balanced class
assignment: Hebrew-aware name reconciliation, hard/soft constraints (apart/together
pairs, anchors, special-ed spread, kindergarten and gender balance, per-gan class
restrictions), CP-SAT optimization with an offline fallback engine, a self-contained
RTL drag-and-drop review board, and final Excel rosters. Built for **non-technical
school counselors** — all children's data is processed locally and never sent to
external services.

### Install (one time)

No downloads. Everything runs inside Claude, on any paid plan (Pro / Max / Team /
Enterprise), from the browser at **claude.ai**, the desktop app, or mobile.

1. Go to **claude.ai** and sign in.
2. In the sidebar, open **Customize**. *(Using **Cowork**? Open the **Cowork** tab
   first, then **Customize** — the steps are the same.)*
3. Select the **Plugins** tab.
4. Click **Add ▾** → **Add marketplace**.
5. Enter `yaniv-golan/claude-lamora` and pick it from the list.
6. Click **Sync**, then click **+** on the **המשבץ** card. You'll see
   *"המשבץ is installed and ready to use."*

Then start a new conversation, attach your friend-choice spreadsheet, and write
(in Hebrew or English): *"help me split this grade into balanced classes."* Claude
invokes the skill automatically.

### For maintainers

- `python3 tools/validate.py` — validate the marketplace, plugin manifest, and skills.
- `python3 tools/bump-version.py . X.Y.Z` — bump the version everywhere (see
  [VERSIONING.md](VERSIONING.md)).
- CI validates every push/PR; pushing a `vX.Y.Z` tag publishes a GitHub Release.

### License

MIT — see [LICENSE](LICENSE).

</div>
