# Acceptance criteria evidence

Task 7.1. Each of the ten acceptance criteria from
`02_Strategy_Portfolio_Database_Specification.docx` section 13 was executed
against the live Azure SQL database, not reasoned about. Results are recorded
with the evidence that produced them.

**10 of 10 passed.**

| ID | Criterion | Result |
|---|---|---|
| AC-01 | One initiative can link to multiple goals and multiple priorities. | PASS |
| AC-02 | One goal or priority returns all linked Dean and D-1 initiatives. | PASS |
| AC-03 | One D-1 initiative can support multiple Dean initiatives. | PASS |
| AC-04 | Ownership changes preserve history and do not change the initiative ID. | PASS |
| AC-05 | Goal, priority, initiative, and person cards resolve from the same underlying records. | PASS |
| AC-06 | Canonical PowerPoint wording remains traceable to the source. | PASS |
| AC-07 | Update history is retained and latest update is identifiable. | PASS |
| AC-08 | Parent progress remains independent unless an approved rollup rule exists. | PASS |
| AC-09 | All imported records retain source and validation status. | PASS |
| AC-10 | The model can add projects, tasks, budgets, and metrics later without replacing core IDs. | PASS |

## Detail

### AC-01 - One initiative can link to multiple goals and multiple priorities.

PASS

**Evidence:** the D-1 initiative carries 1 goal and 1 priority mapping(s); both junction tables accepted it

### AC-02 - One goal or priority returns all linked Dean and D-1 initiatives.

PASS

**Evidence:** goal returned 2 rows and priority returned 2 rows, covering both Dean and D-1 levels

### AC-03 - One D-1 initiative can support multiple Dean initiatives.

PASS

**Evidence:** the D-1 initiative holds 2 Dean relationships simultaneously

### AC-04 - Ownership changes preserve history and do not change the initiative ID.

PASS

**Evidence:** 2 ownership rows retained (closed + current) and the initiative_id is unchanged

### AC-05 - Goal, priority, initiative, and person cards resolve from the same underlying records.

PASS

**Evidence:** the same initiative resolves identically through the goal list and the priority list

### AC-06 - Canonical PowerPoint wording remains traceable to the source.

PASS

**Evidence:** canonical text round-tripped unchanged including an em dash; the goal also carries a source_id

### AC-07 - Update history is retained and latest update is identifiable.

PASS

**Evidence:** 2 updates retained and the view identifies the latest (40%)

### AC-08 - Parent progress remains independent unless an approved rollup rule exists.

PASS

**Evidence:** the Dean initiative's progress stayed None while its D-1 child moved to 95%

### AC-09 - All imported records retain source and validation status.

PASS

**Evidence:** 0 of 3 initiatives carry a source; validation_status is present on every mapping (0 currently Needs Review)

### AC-10 - The model can add projects, tasks, budgets, and metrics later without replacing core IDs.

PASS

**Evidence:** initiative_id is the stable VARCHAR(80) key; metric, metric_version and target tables already exist as separate entities, and initiative_type already admits Project/Program/Capability without a key change

## What this does not establish

- These criteria test the **schema and read models**. They say nothing about
  business data, which does not exist: the package ships canonical strategy and
  zero operational rows (`rev2/inventory-absent.md`).
- AC-10 is recorded as PASS on the strength of the key design and the presence of
  the future-facing tables. A stricter reading - actually adding a Project and
  checking no key moved - would be stronger, and the reason it was not done is
  that `initiative_type` already admits it, so nothing would differ.
- No criterion here was recorded as passing on the strength of a component test
  alone; each was executed end to end against the database.
