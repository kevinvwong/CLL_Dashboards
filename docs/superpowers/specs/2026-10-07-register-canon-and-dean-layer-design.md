# Design: Register as canon, and the Dean Priorities layer

Date: 2026-10-07
Status: approved (sectioned review §1-§5, 2026-10-07)
Source: `C:\Users\kwong318\Downloads\Initiative Dashboard Register.xlsx`

## Problem

A new workbook, **`Initiative Dashboard Register.xlsx`** (sheet "Team KPI
Register", 40 data rows), has been supplied as the current authority for the
Major Initiatives. Provenance check: `docProps/core.xml` names
`Smith, Elizabeth C` as last author and `app.xml` names `Microsoft Excel
Online` — it is a genuine, human-authored register, not a generated artifact.
It was supplied by the user with the instruction **"register is canon and
overwrites"**.

It agrees with what we store on 24 of 29 team-initiatives' titles, and it
disagrees on:

- **Team assignment** — 4 rows move to *Learning Ecosystems*:
  Growth Engine Readiness, Strategic Partnership & Revenue Growth, Geographic
  Expansion (from Learning Experiences) and Asset Utilization (from Learning
  Infrastructure). Team counts reconcile exactly: Learning Experiences 13→10,
  Learning Infrastructure 8→7, Learning Ecosystems 2→6 (still 29 in total).
- **Title wording** — 5 rows reworded: MI-024, MI-025, MI-026, MI-027, MI-029.

It also carries material we do not hold at all:

- **Named Owner** — real names: Mario Herane (Learning Ecosystems), Tim Jacobbe
  (Learning Experiences), Meltem Alemdar (Learning Futures — a person new to
  the repo), Elizabeth Smith (Learning Infrastructure), Bill Gaudelli (Dean).
  Our `People` table holds five *placeholders* (`Bill`, `Elizabeth`, `Tim`,
  `Mario`, `Kevin`); none of the full names appear anywhere in the repo.
- **Description** per row.
- A **Goals 1-5** alignment matrix (58 edges across the 29 team rows).
- A **Dean KPI 27** linkage matrix (61 edges across the 29 team rows) naming the
  8 FY27 items a team initiative contributes to.
- A distinct **Dean layer of 11 rows**: *Dean KPI 26* (3 rows, all complete) and
  *Dean KPI 27* (8 rows), owned by Bill Gaudelli, carrying **0-1 completion
  values** (rendered as percent), a Description, a Goal alignment, and a primary
  priority.

## Terminology (settled)

The app keeps **Major Initiative** for the 29 team rows (the earlier rename
stands). **KPI** is not adopted as a row label. The 11 Dean rows are presented
as **"Dean Priorities"**, split **FY26** (complete) and **FY27** (in flight).
The register's own "Team KPI" / "Dean KPI 26/27" headers are working-spreadsheet
wording, not app vocabulary.

## Approaches considered

- **A (chosen)** — new `DeanPriorities` layer as its own tables; extend
  `MajorInitiatives` and `People`; re-seed all of it from the register.
- **B (rejected)** — fold the Dean 11 into the superseded prototype `Initiatives`
  table (`Level='Dean'`). Rejected: that table is the retired prototype model,
  entangled with `vw_*` views, level-check triggers and `ProgressUpdates`;
  reusing it resurrects the layer we deliberately replaced, and makes "Major
  Initiative" and "Dean initiative" share a table while meaning different things.
- **C (rejected)** — store the Dean links only, no Dean UI. Rejected by the user,
  who chose to display the layer.

## §1 Data model

### New tables

```sql
CREATE TABLE DeanPriorities (
    DeanPriorityID  INTEGER PRIMARY KEY,
    FiscalYear      INTEGER NOT NULL CHECK (FiscalYear IN (26,27)),
    Code            TEXT    NOT NULL UNIQUE,   -- 'D26-1'..'D26-3', 'D27-1'..'D27-8'
    Title           TEXT    NOT NULL,
    Description     TEXT,
    PriorityID      INTEGER REFERENCES Priorities(PriorityID),  -- its primary annual priority
    PercentComplete INTEGER NOT NULL DEFAULT 0 CHECK (PercentComplete BETWEEN 0 AND 100),
    Note            TEXT
);

-- The X-matrix: which team Major Initiative contributes to which FY27 Dean item.
CREATE TABLE MajorInitiativeDeanLinks (
    MajorInitiativeID INTEGER NOT NULL REFERENCES MajorInitiatives(MajorInitiativeID),
    DeanPriorityID    INTEGER NOT NULL REFERENCES DeanPriorities(DeanPriorityID),
    PRIMARY KEY (MajorInitiativeID, DeanPriorityID)
);
```

### Extensions to existing tables

- `MajorInitiatives` gains `Description TEXT` and `OwnerID INTEGER REFERENCES
  People(PersonID)`.
- `MajorInitiativePriorities` gains `IsPrimary INTEGER NOT NULL DEFAULT 0 CHECK
  (IsPrimary IN (0,1))`, with a partial unique index for one primary per MI,
  mirroring the prototype's `UX_IP_OnePrimary` convention. The register states a
  **primary** and a **secondary** priority for each team row.
- `People` gains `TeamID INTEGER REFERENCES Teams(TeamID)` (nullable; the Dean
  leads none).

One owner per initiative (not Revision 2's effective-dated multi-role model).

### Field provenance

`MIId` and `SourceArea` are **not** in the register; they still come from the
canon workbook `CLL_FY2027_Goals_Priorities_Initiatives_and_People.xlsx` via
`db/build_canon_links.py`, which stays responsible for those two fields only.

## §2 People

`People` is replaced by the register's named owners, each tied to their team:

| PersonID | Name           | Title | TeamID | Note |
|----------|----------------|-------|--------|------|
| 1 | Bill Gaudelli  | Dean  | NULL | replaces placeholder "Bill" |
| 2 | Mario Herane   | NULL  | Learning Ecosystems | replaces "Mario" |
| 3 | Tim Jacobbe    | NULL  | Learning Experiences | replaces "Tim" |
| 4 | Meltem Alemdar | NULL  | Learning Futures | **new person** |
| 5 | Elizabeth Smith| NULL  | Learning Infrastructure | replaces "Elizabeth" |
| 6 | Kevin          | Associate Director, Strategic Operations | NULL | dashboard admin, unchanged |

## §3 Seed pipeline

New generator `db/build_register_seed.py`, reading the register workbook
directly (not retyped) and emitting `db/seed_register.sql`. It follows the
existing `build_canon_links.py` pattern and its hard-won rules:

- **Join by normalized title, not position.** The canon reorder previously
  paired 8 rows with the wrong target; a positional join is the failure mode. A
  `RENAMED`-style map carries the 5 reworded titles.
- **Fail loudly on any unmatched row** — no positional fallback (exit non-zero,
  name the row).
- **Reproducible** — every timestamped column set from the seed itself, so two
  builds hash identically. Asserted by building twice and comparing hashes.
- **`--check` mode** so `build_db.py`/CI can assert the seed is current.

Load order in `build_db.py`: after `seed_canon_links.sql` (the register seed
updates MI rows by Code and adds the Dean layer).

The register's 0-1 completion values are scaled ×100 into `PercentComplete`
(1 → 100, 0.05 → 5, 0 and blank → 0). Register `Status` text maps to our
vocabulary (`Not started` / `On track` / `At risk` / `Off track` / `Complete`);
the 29 team rows are all `Not started`.

The register seed writes all three edge sets:

1. **MI→Goal** (58 edges) from the register's Goals 1-5 columns, replacing the
   alignment-string parse in `build_canon_links.py`.
2. **MI→Priority** (primary + secondary per team row), writing `IsPrimary`.
3. **MI→Dean** (61 edges) from the register's eight Dean KPI 27 columns into
   `MajorInitiativeDeanLinks`.

### Register expansion

The register is the source of record. Where a field the app needs is absent
from the register, the **register itself is expanded** (a new column), not
invented in the database. This pass needs no expansion: every field in §1 is
present in the register.

## §4 Read models and UI

- New view `vw_DeanPriorities` (Dean rows with their priority).
- New view `vw_MajorInitiativeDeanLinks` (one row per team-initiative → Dean-FY27
  link).
- **Home page**: a new "Dean Priorities — FY26 / FY27" section, percent bars
  using the Hive status tokens; FY26 grouped and marked complete.
- **Major Initiative card**: gains its `Description` and "contributes to →"
  chips from the Dean-link matrix.
- Team reassignments flow automatically through `vw_TeamSummary` and the team
  pages.

The 4 reassigned rows move immediately; the move is recorded in
`docs/ops/LAUNCH_RECORD.md` as a before/after note.

## §5 Testing

- `tests/test_register_seed.py` — asserts counts (29 Major Initiatives, 11 Dean
  Priorities, 8 FY27 items, 61 MI→Dean links, 58 MI→Goal edges), name-join
  integrity, and byte-reproducibility of the built db.
- `tests/test_dean_layer.py` — percent scaling (0.05→5, 1→100), FY26/FY27
  grouping, and that the Dean-link matrix resolves to real rows.
- Full suite must stay green (currently 510 passing).

## Counts asserted from the register

| Quantity | Value |
|----------|-------|
| Team Major Initiatives | 29 |
| Dean Priorities | 11 (FY26: 3, FY27: 8) |
| Team MI → Goal edges | 58 |
| Team MI → Dean FY27 edges | 61 |
| Dean rows → Goal edges | 27 |
| Primary priorities used (team rows) | 6 |

## Out of scope

- No change to the 6 Annual Priorities' definitions.
- No Revision 2 adoption; the prototype schema remains the model.
- No deployment; the live site stays on the pre-Hive build.
