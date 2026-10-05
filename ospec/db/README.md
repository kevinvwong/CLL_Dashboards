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

Each table becomes a SharePoint List or Dataverse table; each REFERENCES column becomes a Lookup.
Rules that SQLite enforces (one primary tag, D-1 -> Dean links, percent 0-100) need to be
rebuilt as column validation or Power Automate checks, and vw_DataChecks becomes a Power BI page.
For Azure SQL, the earlier T-SQL file (v2) is the starting point.
