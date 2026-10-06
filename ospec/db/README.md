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
