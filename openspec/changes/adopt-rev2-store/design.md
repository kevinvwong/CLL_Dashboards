# Design: port reads and writes to the Rev2 store

## Context

`app/db.py connect()` selects an engine by `DB_PROVIDER`. The two engines do not
share a schema:

| Concern | SQLite app model | Rev2 (Azure SQL) |
|---|---|---|
| Initiative | `TeamInitiatives` (one tier) | `initiative` + `initiative_level/type`; D-1 vs Dean distinguished by level/type, with `initiative_relationship` for contributes-to |
| Progress | `TeamInitiativeUpdates` (diary) + `vw_LatestTeamInitiativeProgress` | `initiative_update` + `vw_latest_update` / `vw_initiative_current` |
| Goal link | `TeamInitiativeGoals` | `initiative_goal` (+ `relationship_type`) |
| Priority link | `TeamInitiativePriorities` (+`IsPrimary`) | `initiative_priority` (+ `relationship_type`) |
| Owner | `TeamInitiatives.OwnerID` (single FK) | `initiative_owner` (role + `primary_flag` + effective dates); `vw_primary_reporting_owner` |
| Dean contributes-to | `TeamInitiativeDeanLinks` | `initiative_relationship` (from=D-1, to=Dean) |
| Person | `People` | `person` (plus `vw_person_portfolio`) |
| Milestones | `Milestones` + `vw_PriorityMilestoneProgress` | (no Rev2 table — see Open issues) |
| Governance fields | `Priorities.Measure/Target/Cadence/OwnerLabel/Colour` | `annual_priority` columns |
| AppMeta | `AppMeta` key/value | (no Rev2 table — see Open issues) |
| AuditTrail | `AuditLog` | (no Rev2 table — see Open issues) |

The app's screens already have per-screen read shapes, and Rev2 ships read
models (`db/mssql/006_read_models.sql`) that exist to serve exactly those cards.
The design intent is: **the screen's data source is a named read model where one
exists, and explicit translated SQL where it does not.**

## Decisions

### D1 — Engine dispatch lives in exactly one place per read/write

The seam is the function, not a scattered branch. Each ported function keeps its
public signature and return key-set; internally it asks `connect()` for the
engine tag and chooses a formulation. Two formulations are allowed only because
the parameter placeholder differs (`?` vs `%s`) and dialect SQL differs
(`date('now')` vs T-SQL date functions). The route handlers in `app/main.py` and
the templates are untouched — they cannot tell which engine answered.

A helper on the connection (`engine` attribute: `"sqlite"` or `"mssql"`) is the
single source of the tag, so no module re-reads `Config().DB_PROVIDER` and the
choice cannot drift per call.

### D2 — Prefer Rev2 read models where the card's shape matches

`vw_goal_initiatives`, `vw_priority_initiatives` and `vw_person_portfolio` exist
to serve the goal/priority/person cards identically field-for-field (task 5.1 in
`006_read_models.sql`). The port uses them rather than re-deriving the latest
update and owner inline, so the mssql path and the documented Rev2 contract agree
by construction. Where the SQLite view's key names differ from the Rev2 view's,
the port **aliases on select** so the template's keys are unchanged.

### D3 — Current progress is derived, never the cache

Rev2 D2 (`006_read_models.sql` header): `initiative.progress_value` /
`.status` are a cache and must not be read for current state. The port reads
current progress from `vw_initiative_current` / `vw_latest_update` only — same
rule as the SQLite side reads `vw_LatestTeamInitiativeProgress`, never a stored
column.

### D4 — Ownership: Reporting Owner + primary

The SQLite model has a single `OwnerID`. Rev2 has many owners per initiative
with roles and effective dates. The port reads the owner through
`vw_primary_reporting_owner` (`ownership_role='Reporting Owner' AND
primary_flag=1 AND effective_end IS NULL`) — the documented current-owner read.
Writes that set or change an owner insert/update an `initiative_owner` row in
that role (out of the current write surface; the SQLite write surface has no
owner-edit, so this is read-only in this change).

### D5 — Writes stay append-only and audited

The write surface (`repo.py`) keeps its shape and its `RuleError` contract.
Translated per engine:

- **add progress update** → `INSERT initiative_update` (+ the initiative id from
  `initiative_code`, the public `MI-###` key).
- **create / rename / retire / restore initiative** → `INSERT/UPDATE initiative`
  (`active_flag` for retire/restore).
- **replace tags** → replace rows in `initiative_goal` and `initiative_priority`.
- **replace contributes-to links** → replace `initiative_relationship` rows
  (from D-1 to Dean).
- **edit goal/priority description** → `UPDATE goal` / `UPDATE annual_priority`.

Each write is one transaction and records its change-management row (AuditLog
equivalent — see Open issues below).

### D6 — Integrity errors still map to actionable messages

`repo.write` catches `sqlite3.IntegrityError` and maps it via `_friendly`. On
mssql the driver raises `pymssql` exceptions; the port wraps them into the same
`RuleError` messages so a route keeps surfacing "Percent must be between 0 and
100", not a driver string. The mapping is engine-aware at the single write seam.

## Open issues (recorded, not silently decided)

These are genuine gaps between the SQLite model and Rev2 as applied. Each item
is named, given an interim behaviour, and flagged for a follow-up rather than
guessed at here:

1. **Milestones** — the SQLite `Milestones` table and
   `vw_PriorityMilestoneProgress` feed the priorities screen (`priority_outcomes`)
   and the meeting view. Rev2 001..007 has no milestone table. *Interim:* keep
   `priority_outcomes` on sqlite only; do not port it in this change. *Flagged
   for follow-up:* either add a milestone table to Rev2 (a separate schema
   change) or accept the priorities screen is sqlite-backed until then.
2. **AppMeta** — `current_plan_year` and `dataset_provenance` are read from a
   key/value table. Rev2 has no equivalent. *Interim:* these two small reads stay
   sqlite-backed regardless of `DB_PROVIDER` (they are engine-agnostic config).
   *Flagged:* decide whether an `app_meta` table belongs in Rev2.
3. **AuditLog** — the change-management record. Rev2 001..007 has no audit
   table. *Interim:* writes raise a clear error on mssql until the audit target
   is decided, so the port never silently drops an audit row. *Flagged:* add an
   audit table to Rev2, or confirm the existing table list already covers it.
4. **Meeting view** — the meeting surface is ICED (`MEETING_ENABLED=0`,
   404'd). Its reads (`meeting_updates`, `update_deltas`, `attention_list`) are
   ported only if they share a read model already ported for another screen;
   otherwise they are out of scope while the surface is disabled.

## Risks

- **Schema drift.** `cllrev2` as applied must match `db/mssql/001..007`. The
  first task verifies the live schema equals the committed files before any port
  is built on it (integrity report `007_integrity_report.sql` and the read-model
  definitions).
- **Partial coherence.** Reads + writes together means the app is only coherent
  when the whole surface is ported. Mitigation: the sqlite suite runs on every
  commit and stays green; the port lands screen-by-screen, each commit leaving
  `DB_PROVIDER=sqlite` fully working.
- **The "Rev2 is seeded from the app" caveat.** The read parity tests compare two
  stores that were deliberately seeded to agree. They prove the *translation* is
  faithful; they do not prove Rev2 holds authoritative institutional data (it
  does not — see Non-goals).
