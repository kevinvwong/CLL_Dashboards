# Design: Merge the two initiative models (register-driven)

Date: 2026-10-07
Status: approved (sectioned review §1–§5, 2026-10-07)
Supersedes: nothing; completes the `register-canon-and-dean-layer` change.

## Problem

The database holds **two organizational models**, and the home page now shows
both at once — "22 initiatives tracked" beside "29 Team Initiatives" — which
reads as a contradiction to anyone looking at it.

| | Prototype model | Register model |
|---|---|---|
| Table | `Initiatives` (22 rows) | `TeamInitiatives` (29 rows) |
| Contents | **all named `(sample)`** | the canon (`MI-001..MI-029`) |
| Levels | 16 D-1 + 6 Dean | 29, grouped by 4 teams |
| Owner / team / description | via joins | on the row |
| Goal / priority edges | `InitiativeGoals`, `InitiativePriorities` | `TeamInitiativeGoals`, `TeamInitiativePriorities` |
| Dean link | `InitiativeLinks` (D-1 → Dean) | `TeamInitiativeDeanLinks` |
| **Progress diary** | `ProgressUpdates` (24 rows) | **absent** |
| **Write path** | `repo.py` (update, tags, links, create, retire) | seeds only |
| Routes | ~22 | ~4 |

`Initiative Dashboard Register.xlsx` is canon and decides everything. The
register model already carries owner, team, description, goal, priority and
Dean-link edges. What it lacks is the **write half**: the progress diary, the
tags/links/retire write paths, and the permission model. The prototype model has
those but is not canon.

**The 24 existing diary rows are discarded, not migrated.** Every one is about a
sample initiative (`D-A (sample): Transparent ROI reporting`, `ELIZ-1 …`) and
none names a real Team Initiative. Verified: no `ProgressUpdates` row references
a row in `TeamInitiatives`. The register's initiatives start with a clean diary.

## Approaches considered

- **A (chosen)** — register-driven: add the diary and write paths to the
  `TeamInitiatives` layer; rewrite `repo.py`, `auth.py`, the queries and the
  routes against it; drop the five prototype tables.
- **B (rejected)** — same end state with compatibility `VIEW`s over the retired
  table names during a transition. Rejected: an alias layer invites exactly the
  two-headed state being fixed, and a view over a different grain of table
  re-creates the 22-vs-29 confusion.
- **C (rejected)** — migrate the register's 29 *into* the prototype's `Initiatives`
  table (which already has the diary and write path). Rejected: it makes the
  non-canon table the survivor and inverts the "register is canon" decision.

## §1 — Schema

**Add to `TeamInitiatives`:** `IsActive INTEGER NOT NULL DEFAULT 1 CHECK
(IsActive IN (0,1))`, so retire-not-delete works as it did on the prototype.

**Add the diary, on the 29:**

```sql
CREATE TABLE TeamInitiativeUpdates (
    UpdateID          INTEGER PRIMARY KEY,
    TeamInitiativeID INTEGER NOT NULL REFERENCES TeamInitiatives(TeamInitiativeID),
    UpdateDate        TEXT    NOT NULL DEFAULT (date('now')),
    PercentComplete   INTEGER NOT NULL CHECK (PercentComplete BETWEEN 0 AND 100),
    Status            TEXT    NOT NULL DEFAULT 'Not started'
                      CHECK (Status IN ('Not started','On track','At risk',
                                        'Off track','Complete','Paused')),
    Note              TEXT,
    EnteredByID       INTEGER REFERENCES People(PersonID),
    CreatedAt         TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IX_MIU_MI_Date ON TeamInitiativeUpdates(TeamInitiativeID, UpdateDate);
CREATE VIEW vw_LatestTeamInitiativeProgress AS
SELECT TeamInitiativeID, UpdateDate, PercentComplete, Status, Note FROM (
    SELECT u.*, ROW_NUMBER() OVER (PARTITION BY TeamInitiativeID
                                   ORDER BY UpdateDate DESC, UpdateID DESC) AS rn
    FROM TeamInitiativeUpdates u)
WHERE rn = 1;
```

**Drop:** `Initiatives`, `InitiativeGoals`, `InitiativePriorities`,
`InitiativeLinks`, `ProgressUpdates`, and the `trg_Links_LevelCheck*` triggers and
their indexes.

**Reused unchanged:** `TeamInitiativeGoals`, `TeamInitiativePriorities`
(with `IsPrimary`), `TeamInitiativeDeanLinks`, `TeamInitiativeCoOwners`,
`DeanInitiatives`, `AuditLog`.

The D-1→Dean link is expressed by `TeamInitiativeDeanLinks` (a team initiative
contributing to a Dean FY27 item). The prototype's rigid "D-1 → Dean, level
checked by trigger" rule is replaced by the register's many-to-many matrix.

## §2 — Writes and permissions

`repo.py` — the eight write functions retarget:

| function | was | becomes |
|---|---|---|
| `add_progress_update` | `ProgressUpdates` | `TeamInitiativeUpdates` |
| `replace_tags` | `InitiativeGoals`/`InitiativePriorities` | `TeamInitiativeGoals`/`TeamInitiativePriorities` |
| `replace_links` | `InitiativeLinks` | `TeamInitiativeDeanLinks` |
| `create_initiative` | `Initiatives` | `TeamInitiatives` |
| `retire_initiative` | `Initiatives.IsActive` | `TeamInitiatives.IsActive` |
| `update_initiative_details` | `Initiatives` | `TeamInitiatives` |
| `update_entry_description` | unchanged (Goals/Priorities) | unchanged |
| `_audit` | unchanged | unchanged |

The key changes from **Code** (`'ELIZ-1'`) to **MIId** (`'MI-002'`).

`auth.py` — `get_initiative`, `is_dean`, `can_update`, `can_edit_details` read
`TeamInitiatives.OwnerID`. Ownership is the register's `OwnerID`; team-lead scope
comes from `People.TeamID`. `is_dean` is the person with no `ReportsToID` who owns
a `TeamInitiative` — the Dean (Bill Gaudelli).

## §3 — Routes

The interactive card (HTMX fragment + drawer + update/edit forms), which lived
on the prototype's `/initiatives/{code}`, moves onto the register's
`/team-initiatives/{mi_id}`. `team_initiative.html` gains the card body,
the update form and the edit forms that `card.html` / `update_form.html` /
`edit_*.html` held.

| Route | Disposition |
|---|---|
| `/initiatives/{code}` | **retire** → 308 to `/team-initiatives/{mi_id}` |
| `/initiatives` (index) | **retire** → 308 to `/team-initiatives` |
| `/initiatives/new` | re-point to create a `TeamInitiative` |
| `/initiatives/{code}/update` | re-point to `/team-initiatives/{mi_id}/update` |
| `/initiatives/{code}/edit/{details,tags,links}` | re-point under `/team-initiatives/` |
| `/initiatives/{code}/retire` | re-point under `/team-initiatives/` |
| `/people`, `/people/{id}` | read `TeamInitiatives` owners |
| `/meeting` | read `TeamInitiativeUpdates` |
| `/outcomes` | **untouched** — a static generated module, reads no table |

Retired routes return a **308 permanent redirect** to the register path, so a
bookmark keeps working and the move is visible in a request log.

## §4 — Tests

The 10 test files that reference the prototype tables move with the routes.
New tests:

- the diary write path on `TeamInitiatives` (append, latest wins, permissions);
- the retired `/initiatives/*` routes 308 to their `/team-initiatives/*` targets;
- **no query references a dropped table** — a sweep over `app/` for the five
  retired names, so a half-done merge fails loudly;
- the home counts **one** portfolio number (the 29), not two.

Full suite green between every task (currently 538).

## §5 — Sequencing

One spec (this), one plan, executed in tasks, tests green between each. The db is
rebuilt and byte-reproducible; `build_deploy_zip.py`'s manifest is updated for any
new seed. **Deploy is the last step**, after the merge is verified locally, and
the launch record states the model is now single.

## Out of scope

- `/outcomes` and `oct16_data.py` (static, no table reads).
- The Dean Initiatives layer (already on the register model).
- Revision 2 adoption.
- Any change to the six priorities' definitions.
