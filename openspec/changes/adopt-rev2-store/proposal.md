# Proposal: Adopt the Rev2 store (port all reads and writes to Azure SQL)

## Why

The dashboard's runtime data lives in two places today:

- the app's own 17-table **SQLite file** (`cll_initiatives.db`), which serves
  every screen, and
- the **Rev2 model** — a 28-table Azure SQL database (`cllrev2` on
  `cllrev2sqlg7pmp.database.windows.net`) — which is the target production
  store: it is the model the College's strategy package ports to (`db/mssql/001..007`),
  it enforces the cardinality and vocabulary rules the SQLite schema cannot, and
  it is already seeded from the app's data (40 initiatives, 96 goal links, 62
  priority links, 61 relationships).

The seam that lets the app choose a store already exists: `app/db.py connect()`
reads `DB_PROVIDER` (`sqlite` | `mssql`) and returns a connection whose rows
support both name and index access. **But no query has been ported.** Every read
in `app/queries.py` and every write in `app/repo.py` — and the route handlers in
`app/main.py` that call them — still execute the SQLite schema's SQL. Running
with `DB_PROVIDER=mssql` today fails immediately, because the SQL names SQLite
tables that do not exist in Rev2.

Until the queries are translated onto the Rev2 read models and tables, the "seam"
is only a connection factory: the app cannot run on its production store. This
change closes that gap — **port all reads and all writes** so the same screens
render and accept input identically from either engine.

## What changes

- **Reads.** Every function in `app/queries.py` is translated to run against the
  Rev2 schema (`initiative`, `initiative_update`, `initiative_goal`,
  `initiative_priority`, `initiative_relationship`, `person`, `goal`,
  `annual_priority`, …) and its read models (`vw_goal_initiatives`,
  `vw_priority_initiatives`, `vw_person_portfolio`, `vw_latest_update`,
  `vw_initiative_summary`, …). Placeholders change from `?` to `%s`; date and
  expression SQL is translated to T-SQL.
- **Writes.** Every function in `app/repo.py` is translated: append an
  `initiative_update`; create/rename/retire/restore an `initiative`; replace
  goal/priority tags (`initiative_goal` / `initiative_priority`); replace
  contributes-to links (`initiative_relationship`); edit a goal/priority
  description; record change-management rows. Where Rev2 has no equivalent of the
  SQLite `AuditLog` table, this change records the gap explicitly (see design).
- **Dialect handling.** `app/db.py` grows the minimal translation the seam needs
  (parameter placeholder and engine-tagged dialect), so a single query body is
  not duplicated per engine wherever a shared formulation exists; where the two
  schemas genuinely differ, the port is explicit SQL per engine at a single,
  named seam — never scattered `if mssql` branches in route or query bodies.
- **Parity tests.** For each screen's read, a test asserts the mssql result
  equals the sqlite result (same keys, same values) using the live `cllrev2` via
  `MSSQL_*` from `.env`. The existing 644-test sqlite suite must stay green
  throughout — each ported query is committed screen-by-screen.

## Non-goals

- **Not a data migration.** No new data is authored into Rev2. `cllrev2` was
  seeded by `db/build_rev2_seed.py` from the app's SQLite rows; that seeding is
  this project's intermediate step, not an approved institutional inventory.
  `db/rev2/inventory-absent.md` records that the College's package carries **no
  approved** initiative/people/update inventory. Promoting Rev2 to the
  authoritative production source is a business validation decision tracked
  separately; this change makes the app *able* to run on Rev2 and does not, by
  itself, declare Rev2 authoritative.
- **No schema changes to Rev2.** The port targets `db/mssql/001..007` as applied.
  If a needed column/trigger is absent, that is a gap to record and hand back,
  not something this change alters in the live database.
- **No UI changes.** Screens, templates, grouping and filtering logic are not
  touched except where a query's returned key set changes, and those cases are
  kept to zero by projecting mssql columns into the existing key names.
- **Not changing the auth seam.** `AUTH_PROVIDER` (local/clerk) is orthogonal and
  out of scope.

## Success

Running with `DB_PROVIDER=mssql` renders every screen and accepts every write,
producing results identical to `DB_PROVIDER=sqlite` against the same logical
data; the full sqlite suite passes; the Rev2 parity tests pass; and the deploy
runbook can flip the store by changing one environment variable.
