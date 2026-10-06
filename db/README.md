# CLL Strategic Initiatives Database (local dev)

SQLite version for development. No server needed; the whole database is one file.

## Build it

    python3 db/build_db.py           # schema + sample data -> ./cll_initiatives.db
    python3 db/build_db.py --empty   # schema only

Open `cll_initiatives.db` with DB Browser for SQLite (free) or the SQLite extension in VS Code.
Always run `PRAGMA foreign_keys = ON;` when connecting, or the links aren't enforced.

## Files

- `schema.sql` – tables, rules, and the views behind each card
- `seed_sample.sql` – FAKE data for testing; replace with live intake data
- `build_db.py` – rebuilds the database from the two SQL files
- `canonical_goals.py` – the five Strategy 2035 goals, generated from the deck

## The five goals are canonical, and were corrected

**What was wrong.** The seed carried goals 3 and 4 transposed against the
canonical Strategy 2035 deck, goal 1 as a truncated paraphrase, and no title at all
for goals 2 to 5. The prototype's `/goals/3` therefore served the Research goal
where the deck has Learner at 3.

**The source.** `CLL-strategy-2035-presentation.pptx`, slide 7, "College Goals: How
We Will Advance Our Vision". Both the enterprise package and the wireframes name
this deck as the authority, and the package matches it word for word.

**Corrected by re-seeding, not by editing.** A goal's number is its identity:
`InitiativeGoals` references `GoalID`, and the seed joins tags by `ShortName`. So
editing a goal's number in place would have left the initiatives attached to a
record whose meaning had changed, and renaming a tag would have moved those
initiatives to a different goal. The correction instead:

1. generates `canonical_goals.py` from the deck (`scripts/extract_canonical_goals.py`)
2. rewrites the `Goals` rows from it
3. renames only the tag references that name a goal which no longer exists
   (`'Learner impact'` → `'Learner'`; the Research tags needed no change, because
   the Research goal is still called Research and simply moved to number 4)
4. rebuilds the database

The verification is that **every initiative stayed attached to the same goal
entity**. Eight tag rows changed *number*; none changed *goal*.

**Two latent bugs this surfaced**, both now fixed and both worth knowing:

- `build_db.py` read the SQL with no `encoding`, so on Windows Python decoded it
  as cp1252. The canonical wording contains a curly apostrophe (goal 1) and an en
  dash (goal 3), and both were written into the database as mojibake — `worldâ€™s`.
  The file was right and the database was wrong.
- A comment line in `seed_sample.sql` had lost its `--` prefix, so the seed failed
  to load at all with `near "no": syntax error`.

**Regenerating if the deck changes:**

    python scripts/extract_canonical_goals.py    # rewrites db/canonical_goals.py

Then reconcile `seed_sample.sql` against it and rebuild. The goal tests read their
expectations from `canonical_goals.py` rather than duplicating the wording, so a
drift between the source and the data fails them.

## Views (one per screen)

| View | Used for |
|---|---|
| vw_GoalInitiatives | Goal list and goal card (Dean rows first, then D-1) |
| vw_PriorityInitiatives | Priority list and priority card |
| vw_InitiativeConnections | Initiative card: what it feeds / what feeds it |
| vw_PersonInitiatives | Person card |
| vw_LatestProgress | Progress bars (latest diary entry) |
| vw_DataChecks | Cleanup list: missing links, missing tags, misaligned goals |

## Migrating to Microsoft tools later

Target is **Azure SQL (T-SQL)**. The T-SQL mirror of this schema is `schema.mssql.sql`, kept in this
directory so the two can be diffed together. It has been verified against `schema.sql`
table-for-table and view-for-view: 9 tables, 7 views, every column matched.

- SQLite rules that SQLite enforced with pragmas and triggers become declarative in T-SQL: one
  primary tag -> filtered unique index (`WHERE IsPrimary = 1`); D-1 -> Dean links ->
  `trg_Links_LevelCheck`; percent 0-100 -> `CHECK (PercentComplete BETWEEN 0 AND 100)`.
- Because the views are the contract (design.md decision 3), they survive the move unchanged. That
  is the reason Azure SQL was chosen over a Dataverse/SharePoint target: Dataverse has no SQL
  views, and every SQLite-enforced rule would have to be rebuilt as a Power Automate check.
- Keep both schema files in sync. A change present in one and not the other is a build failure.
- `vw_DataChecks` becomes the first Power BI page.

Still missing: a T-SQL equivalent of `seed_sample.sql`, so the views cannot yet be verified
against real rows.

Superseded 2026-10-05: this section previously named SharePoint/Dataverse as the migration target.
