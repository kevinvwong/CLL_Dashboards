# Proposal: Key milestones to the initiative, not the priority

## Why

`008_app_layer.sql` created `dbo.milestone` keyed to `annual_priority` via
`priority_id`. That put milestones **one level too high** in the cascade:
column F of the source register ("FY2027 Target / Achievement Marks") lives on
the register ROW, which maps to a Team Initiative, not to an annual priority.

The cost was not cosmetic. A priority is fed by *many* initiatives, so
priority-scoped milestones had to be duplicated once per feeding priority to be
counted, and the attainment rollup could not attribute a milestone to the work
that owns it. SQLite was corrected first (`460b827`); Rev2 kept the old keying,
so the two stores disagreed on milestones alone while agreeing on everything
else — exactly the drift the parity tests exist to catch.
`build_rev2_seed.py` refused to seed milestones at all until this existed.

**This change records work that is already implemented and verified.** The
migration `011` is written and has been applied to the live `cllrev2`; the seed
is re-keyed and re-applied; both parity tests are green. It exists so the spec
catalogue states the contract that is now true, rather than the one `008` left
behind.

## What changes

- **`db/mssql/011_milestone_initiative.sql`** — the Rev2 half of the
  correction:
  - adds `initiative_id` (nullable, then `NOT NULL` once the old rows are gone)
    and FKs it to `dbo.initiative`
  - adds the weight columns the rollup reads — `weight`, `weight_basis`,
    `weight_source`, `needs_rewrite` — with the same CHECKs the SQLite schema
    enforces, so both stores carry identical rollup inputs
  - moves UNIQUE from `(priority_id, name)` to `(initiative_id, name)`, because
    an initiative feeds two priorities and its milestone set belongs to it, not
    to either priority
  - drops `priority_id`, its FK and its default **last**, so the table is never
    left with neither parent
- **Seed re-keyed** in `db/build_rev2_seed.py`: the 84 register clauses are
  emitted against the initiative (`INI-<MIId>`), once per initiative, carrying
  the weight columns.
- **`app/port.py`** — the three mssql branches that read milestones
  (`milestones_for_year`, `priority_outcomes`, `telemetry`) join through
  `initiative_priority`, de-duplicated at read time. `telemetry` also gained the
  `NeedsRewrite` count it was missing.
- **`db/mssql/apply.py`** registers `011` **last**: it drops the key `008`
  created, so anything earlier that still reads `milestone.priority_id` would
  fail if it ran afterwards.
- **Ordering invariant discovered while applying it** — see design.md. The seed
  must insert milestones in the app's `MilestoneID` order, or the two stores
  return the same rows in a different sequence and parity fails with *identical
  data*.

## Non-goals

- **Not re-parenting the 18 old rows.** They are the mock/Wireframe set and
  "which initiative owns this mock milestone" has no answer the data supplies.
  They are deleted and the corrected seed re-emits the 84 real clauses.
- **No UI change.** Surfaces read through the existing port functions.
- **Not promoting Rev2 to the authoritative production source.** That remains a
  separate business-validation decision (`docs/ops/DEPLOY.md`); no approved
  inventory exists yet.

## Success

`cllrev2` holds the 84 clauses keyed to their initiative; `priority_id` is
gone from `dbo.milestone`; the app's milestone, priority-outcome and telemetry
reads return the same names, statuses and **sequence** on both stores; and
`vw_integrity_report` stays clean. `db/seed_rev2.sql` is reproducible
(`build_rev2_seed.py --check` clean) and the full suite passes.
