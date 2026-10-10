# Design: key-milestones-to-the-initiative

## Decision 1 — the key moves to the initiative, and the priority view is derived

The correction is a keying change, not a data change. A milestone belongs to the
team initiative that owns the register row; the priority it shows against is
read-time information, computed by joining `initiative_priority`.

This is why UNIQUE becomes `(initiative_id, name)` rather than
`(priority_id, name)`: an initiative feeding two priorities would otherwise
force its milestone set to be stored twice. Storing it once and expanding at
read time keeps one row per real clause — 84 rows on both stores — and makes the
count honest rather than inflated by a join.

Correspondingly, `app/port.py` de-duplicates at read time. The expansion is a
join artefact, not a data duplicate, and the requirement in the spec delta says
so explicitly, so a future reader does not "fix" the duplication in the seed.

## Decision 2 — the seed's INSERT order is part of the contract

**This is the non-obvious part, and it cost a debugging cycle.**

Both stores order a priority's milestones by an integer id:

- SQLite: `ORDER BY p.Code, m.SortOrder, m.MilestoneID`
- Rev2: `ORDER BY ap.priority_code, m.sort_order, m.milestone_id`

Neither id means anything to the other store, and **neither is derived from the
data**. SQLite's `MilestoneID` is a rowid following the register's clause order;
Rev2's `milestone_id` is an `INT IDENTITY(1,1)`, so its value is assigned by the
seed's `INSERT` order. Two locally-assigned ids order the same rows however they
happen to be assigned.

Applied to the live store, the migration and seed both succeeded — and the two
parity tests still failed on P01 with **15 rows on each side, the same names and
the same statuses, in a different sequence**. SQLite had
`7,10,38,40,70`; Rev2 had `33,48,51,95,97`, for the same five milestones. The
data was never wrong and the migration was never wrong.

The diagnostic that settled it in one step: dump `(id, sort_order, name)` for
the failing group from **both** stores and diff the two sequences. Seeing the
same five names in a different order isolated the defect to the `ORDER BY`'s
tie-break before any data or migration was touched.

**Consequence for the seed:** it must insert in `m.MilestoneID` order, which
makes the IDENTITY assignment follow the register clause order so the two
`ORDER BY`s coincide. The seed previously traversed `(MIId, SortOrder,
MilestoneID)`, which grouped by initiative and reordered every tie.

One trap worth recording: the idempotent `IF NOT EXISTS` guards mean **re-running
the seed does not reorder anything**. The rows had to be deleted and re-inserted
for the new order to take. (`dbo.milestone` has no inbound FKs, verified first.)

A second trap: `app/port.py` carries a comment saying mssql "returns the
generated string id", which reads as `milestone_id` being VARCHAR. The DDL in
`008` says `INT IDENTITY`. The comment is wrong about the shape; the divergence
was in the *sequence*, not the type.

## Decision 3 — the migration order is constrained

`011` must run **after `008` and after anything that reads
`milestone.priority_id`**, because it drops that key. It is therefore last in
`db/mssql/apply.py`'s `ORDER`, and the comment there records why. `011` is
idempotent (`COL_LENGTH` / `sys.*`-guarded), so re-running the whole list is
safe.

## Decision 4 — the migration deletes rather than re-parents

Re-parenting the 18 mock rows requires choosing an initiative for each, and a
priority being fed by many initiatives means the data supplies no answer. They
are `dataset_provenance='mock'` wireframe rows; deleting them and re-emitting the
84 real clauses from register column F is the defensible move, and it is what
makes the row count honest on both stores.

## Risks

- **A future regeneration that sorts the seed differently breaks parity with
  identical data on both stores**, which reads as a migration defect. The
  constraint is documented in `db/build_rev2_seed.py` next to the `ORDER BY` and
  in `db/mssql/DEVIATIONS.md`.
- **Rev2 is not the production source yet** (`DB_PROVIDER=sqlite` in
  production), so this is a parallel-store correction. Nothing here reaches
  production until Rev2 is promoted, which is a separate decision.
