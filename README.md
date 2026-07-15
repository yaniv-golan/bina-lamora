<div dir="rtl">

# קלוד-למורה

**סקילים של Claude למורות, למורים ולצוותי חינוך בישראל.** עברית תחילה, בלי ז'רגון,
בנוי לעבודה אמיתית בבית ספר.

הסקיל הראשון במרקטפלייס: **המשבץ**.

## המשבץ — שיבוץ שכבה לכיתות מאוזנות

מחליף את טקס הפתקים על הקיר: שולחים ל-Claude את קובץ האקסל של בחירות החברים
(מטופס Google או קובץ שהיועצת הכינה), ומקבלים חלוקה לכיתות שבה **לכל ילד יש לפחות
חבר אחד שבחר**, הכיתות מאוזנות בגודל, במגדר ובגני המוצא — ולוח גרירה בעברית לסקירה
ולשינויים ידניים.

### מה המשבץ יודע לעשות

- קורא קבצי אקסל/CSV כפי שהם — כולל קבצים עם כמה גיליונות, שמות גנים לא אחידים,
  וטעויות הקלדה של הורים בשמות החברים (פיוס שמות בעברית: כתיב מלא/חסר, כינויים,
  אותיות סופיות).
- מבין את עמודת ההערות: "לא עם X", "עדיפות עם Y", "כוכב", "שילוב", ועמודת כיתה
  לילדי עוגן — הכל מוצג לאישור לפני שנכנס לשיבוץ. שום דבר לא מוחל בשקט.
- אילוצים: הפרדות וצירופים, נעילת ילדים לכיתה, פיזור ילדי שילוב, "גן X רק בכיתות
  Y ו-Z", איזון גודל/מגדר/גנים — עם אופטימיזציה מתמטית (CP-SAT) או מנוע גיבוי שעובד
  בלי אינטרנט.
- **לוח סקירה בעברית** — קובץ אחד שנפתח בכל דפדפן, גם במחשב בית-ספרי בלי אינטרנט:
  גוררים ילדים בין כיתות (כל גרירה ננעלת אוטומטית), רואים למי יש חבר בכיתה ולמי לא,
  מי בחר את מי, ואילו כללים נסתרים — עם ביטול פעולה, חיפוש, ושמירת שינויים לקובץ
  שמחזירים לשיחה להמשך אופטימיזציה.
- פלט סופי: חוברת אקסל בעברית (גיליון לכל כיתה, סיכום, ורשימת "לתשומת לב").

### התקנה (Claude Code / Cowork)

<div dir="ltr">

```
/plugin marketplace add yaniv-golan/claude-lamora
/plugin install hameshabetz@claude-lamora
```

</div>

ואז פשוט לכתוב לקלוד: *"יש לי קובץ בחירות חברים של כיתות א' — תעזור לי לשבץ"*,
או לצרף את הקובץ ולכתוב "שיבוץ כיתות".

### דרישות

- Python 3 (מגיע עם Claude Code/Cowork). לאופטימיזציה מלאה מומלץ `ortools` —
  הסקיל מתקין לבד כשיש רשת, ועובד מצוין גם בלעדיו (מנוע גיבוי מובנה).
- הקבצים מכילים שמות של ילדים — הכל מעובד מקומית; הסקיל לעולם לא שולח את הרשימה
  לשירותים חיצוניים.

### פרטיות

הסקיל בנוי סביב עיקרון אחד: **מידע על קטינים לא עוזב את הסביבה המקומית.** אין חיפוש
שמות ברשת, אין שליחת נתונים לשירותי צד ג', ולוח הסקירה הוא קובץ עצמאי בלי תלות
באינטרנט.

</div>

---

<div dir="ltr">

## English

**claude-lamora** ("Claude for the Teacher", קלוד-למורה) is a Claude plugin marketplace
for Israeli educators. Its first skill, **hameshabetz** (המשבץ, "The Placer"), turns a
Google Forms friend-choice export into a balanced class assignment: Hebrew-aware name
reconciliation, hard/soft constraints (apart/together pairs, anchors, special-ed
spread, kindergarten and gender balance, per-gan class restrictions), CP-SAT
optimization with an offline fallback engine, a self-contained RTL drag-and-drop
review board, and final Excel rosters. Built for non-technical school counselors; all
children's data is processed locally and never sent to external services.

### Install

```
/plugin marketplace add yaniv-golan/claude-lamora
/plugin install hameshabetz@claude-lamora
```

### License

MIT — see [LICENSE](LICENSE).

</div>
