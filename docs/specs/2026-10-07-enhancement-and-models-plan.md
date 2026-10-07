# Enhancement & data-model plan (2026-10-07)

> **Status: accepted 2026-10-07.** This plan turns the
> `visual-enhancement-blueprint.md` design input plus a data-model gap into a
> single sequenced body of work. It is the record of the grilling session of
> 2026-10-07; the decisions it rests on are in `docs/adr/0001`–`0003`.
>
> **Scope rule:** nothing hardcoded; never invent data; every visual reads the
> database. Mock data is allowed **only** as a seed (in the database), never as
> a literal in code, and it must be labelled by provenance (see D5).

## Why now

Three things collided:

1. The Visual Enhancement Blueprint proposed 15 visual changes.
2. Four of them (health dots, priority micro-bars, milestone rings, cascade %
   bars) read status data that **does not exist** — every initiative is
   `Not started` and the diary (`TeamInitiativeUpdates`) has 0 rows.
3. The `/outcomes` page is **hardcoded**: `app/oct16_data.py` renders the six
   cards from a hand-typed scaffold in `scripts/build_oct16_data.py:138–172`,
   under an "Illustrative" banner. `CONTEXT.md` already recorded this as a
   tension to be resolved by "a future change". This is that change.

The user's instruction is explicit: **do not cut features, improve the data to
meet the requirements.** So the work is model-first: build the data models, the
collection vehicle, then the visuals that read them.

## The five models

Built in `db/schema.sql` (+ `db/schema.mssql.sql` mirror), seeded
reproducibly, tested.

1. **Milestones** (new). A milestone hangs off a **Priority** (`P01`–`P06`),
   because the Outcomes cards are one-per-priority. Fields are taken verbatim
   from the workbook's own requirement rows A-07–A-17:
   `MilestoneID`, `PriorityCode`, `Name`, `Status`, `PlannedDate`, `DateMet`,
   `OwnerLabel`/`OwnerID`, `EvidenceURL`, `SortOrder`, `IsActive`.
   A view `vw_PriorityMilestoneProgress` supplies `(reached, planned)` per
   priority (reached = count of `Status = 'Met'`).
2. **Outcome state** on the six Priorities: `Status`, `OwnerLabel` (already
   present), `LastUpdated`. Workbook rows A-04–A-06.
3. **Goal identity** — icon + colour + order for `G1`–`G5` as **code tokens**
   (ADR-0003), not DB columns.
4. **Team identity** — colour + order for the four teams, same mechanism.
5. **Priority identity** — one code→token map used by card, chip and cascade.
   Fixes the live defect where `_mi_table.html:72` and `team_initiative.html:81`
   pass the DB hex (`#53d7e8`) into a filter that expects a code (`P01`) and
   silently fall back to `--priority-1` (navy).

## Phases

### A — Docs & collection vehicle (day 1)
- This plan; `CONTEXT.md` **Status** term, "health" rejected, tension #3 updated;
  ADR-0001–0003.
- Extend the `make_template.py` → `import_xlsx.py` pattern with two sheets:
  a **Milestones** sheet and a **Priorities** sheet (outcome owner/status/
  updated), built from the workbook's own field list, with validation dropdowns
  and all-or-nothing import. **This starts the collection clock and is the
  schedule driver** — see *Risk*.

### B — Models (days 1–3)
- Schema, seed generator (mock, provenance-tagged), views, `repo.py` read/write,
  `queries.py` projections, tests. Rebuild must stay reproducible
  (`db/build_db.py` hashes identically twice; the tracked `cll_initiatives.db`
  must not go dirty).

### C — Outcomes retrofit (days 3–4)
- `GET /outcomes` (`app/main.py:791`) and `app/templates/oct16.html` read the
  DB instead of `oct16_data.py`. The hand-typed milestone scaffold is **replaced
  now** (D3). `oct16_data.py` / `scripts/build_oct16_data.py` are demoted to
  seed inputs. Their tests are retargeted.
- The "Needs panel" (`DATA_REQUIREMENTS`, `SCOPE`, `TRADE_OFFS`) stays as the
  build memo it is; it is the honest record of what is still missing.

### D — Identity & provenance (days 3–4, overlaps B)
- D1–D4 as above. D5: **a provenance marker** — the seed writes `mock`, the
  importer writes `confirmed`; `data_status()` reads provenance, not content.
  This is required because mock rows *have* owner names, so the existing
  "named owners ⇒ confirmed" logic would mislabel a mock as real.

### E — Visuals (days 4–6)
- Nav (4) + goal (5) icons as inline SVG (`currentColor`, `aria-hidden` +
  visible text). Status chips keep Unicode glyphs.
- Stat-tile fill bars + ⚠ on the "21" tile; Dean FY timeline bar (static from
  real counts: 3 FY26 / 8 FY27); cascade connector rails (list upgrade, not a
  node diagram); milestone rings on `/outcomes`.
- Legends for all four axes — the one existing legend (`oct16.html:23–30`) is
  the pattern to generalise.

### F — Motion (days 6–7)
- All 6 moves: bars fill, rings draw, cascade node reveal, card hover lift,
  stat-tile count-up (JS), filter/sort reorder. **Every one** joins the
  `prefers-reduced-motion` block, which today covers only `.button`
  (`style.css:909–911`) and must be widened to all animated selectors.

### G — a11y, tests, smoke (days 7–8)
- `axe` suite green; target-size/contrast checks; the status/priority test
  coupling in `tests/test_status_icons.py`, `test_status_presentation.py`,
  `test_goal_labels.py`, `test_design_system.py` updated in step with markup.
- Full suite green; local smoke against `run-dashboard.cmd`.

### Freeze
- **Code freeze 2026-10-13 EOD → deploy + smoke 10-14 → buffer 10-15 → demo
  10-16.** One declared checkpoint; the prior deploy zip is the rollback.
  Deploying is a promotion the user declares — not an agent step.

## Risk (the long pole is data, not code)

The workbook `Oct16_Wireframe_Data_Lists.xlsx` supplies only the *field
requirements* (19 rows); it contains **no milestone names, dates, owners or
statuses**. Its own Summary says *"Blocking: no owners are named yet."* The
workbook's A-04/A-12/A-13 assign collection to a **confirmation session with the
four team leads**, self-reported. That session — not the code — can slip the
freeze.

Mitigation: Phase A ships the intake template first so collection runs in
parallel with B–F. If collection is incomplete at the freeze, the app shows
**honest gaps** ("owner not named"), never invented numbers.

## Auth & change management (in scope, 2026-10-07)

Requested 2026-10-07 and confirmed **inside scope**. It runs as a track parallel
to B–G and rests on ADR-0004 (auth seam) and ADR-0005 (local roles).

- **Stopgap authentication, now.** Replace the self-asserted picker with a real
  credential behind `authenticate(request) -> Principal` (ADR-0004). The picker
  is deleted or made admin-only. Identity may come from a local credential now
  or from Clerk/Entra later; the routes do not change either way.
- **Local roles, now.** `Roles` + `PeopleRoles`; `guards.py` reads them instead
  of `IsAdmin` / `Title == 'Dean'` (ADR-0005). Groups are managed **locally**,
  not in Entra.
- **Change-log extension, now-ish.** `AuditLog` grows `Reason`, `Source` and a
  `CorrelationID`; `/changes` renders them; `actor` is written from the
  authenticated principal; a soft-**restore** path is added for retired rows.
  (The log exists today — `AuditLog`, 7 write sites, admin-gated `/changes` — but
  has no reason, retention or restore.)
- **Governed intake approval workflow, post-demo.** The approval state machine
  (draft → submitted → approved/rejected) on top of the registry, with the roles
  above deciding transitions. The repo already names this gap
  (`PLANNER_RECONCILIATION_2026-10-07.md:42–47`); it is a feature with its own
  design, not part of the 10-13 freeze.

**Known constraint:** a full Entra login needs a GT-tenant app registration
which is not available (host tenant is outside GT). Clerk is a viable
third-party identity provider and can be dropped in behind the seam.
