# Deviations from the PostgreSQL reference

ADR-021 requires the target platform to carry equivalent constraints and every
semantic deviation to be documented. This is that record. Each entry names the
reference mechanism, the substitute, the residual risk, and the test that
evidences it.

The T-SQL port is `001`–`004` in this directory. The reference is
`../rev2/package_04_baseline.sql` and `../rev2/package_09_rev2_migration.sql`.

## Summary

| # | Reference mechanism | T-SQL substitute | Equivalent? |
|---|---|---|---|
| 1 | Partial unique index | Filtered unique index | **Yes, native** |
| 2 | `BEFORE INSERT` trigger | `AFTER INSERT` + rollback | Yes, for one statement |
| 3 | Recursive CTE in a trigger | Iterative walk, depth-bounded | Yes |
| 4 | `DEFERRABLE INITIALLY DEFERRED` constraint | Immediate trigger + integrity report | **No — weaker** |
| 5 | `EXCLUDE USING gist` period non-overlap | Trigger + `sp_getapplock` | **No — weaker** |
| 6 | `NULL` distinct in a unique column | Filtered unique index | Yes, after fix |

Entries 4 and 5 are the ones that matter. Neither is claimed equivalent.

---

## 1. Partial unique index — native

**Reference:** `create unique index ... where primary_flag = true and
ownership_role = 'Reporting Owner' and effective_end is null`

**Substitute:** `CREATE UNIQUE INDEX ... WHERE ...` (filtered index).

**Measured on the target:** refuses a duplicate inside the filter, and permits
multiple rows where the filter is false. The `effective_end IS NULL` slot
therefore frees when an incumbent is end-dated, which is what makes ownership
transferable. `TestPrimaryOwner::test_a_closed_primary_permits_a_new_one`
proves that half specifically.

## 2. BEFORE trigger — equivalent for a single statement

**Reference:** `before insert or update` plpgsql trigger.

**Substitute:** `AFTER INSERT, UPDATE` trigger that rolls the statement back.

T-SQL has no `BEFORE` trigger on a table. The row is briefly visible inside the
transaction before the rollback; nothing is ever committed. For a single
statement the observable behaviour is the same, and the refusal message names
the attempted direction exactly as the reference does.

## 3. Recursive CTE in a trigger — equivalent

**Reference:** a recursive CTE starting from the destination and following
hierarchical links, to detect whether an insert would close a cycle.

**Substitute:** an iterative walk over a materialised edge list, bounded at 64
hops.

A recursive CTE cannot reference the mutating table inside a T-SQL trigger. The
depth bound is a termination guard, not a limit on correctness: any cycle is
found within a number of hops equal to its length, and the bound exceeds the
largest possible chain here by a wide margin. A pre-existing cycle in the data
also terminates rather than looping, because visited nodes are tracked.

Proven by `TestCycles` for a 3-node and a 5-node cycle, and by a non-cyclic
chain that must be accepted.

## 4. Deferred constraint — WEAKER

**Reference:** `DEFERRABLE INITIALLY DEFERRED` constraint trigger, so a
transaction may insert an initiative, map it, and activate it, with the
cardinality rule checked at `COMMIT`.

**Substitute:** immediate triggers on both the initiative and the mapping
tables, plus the standing integrity report (`007_integrity_report.sql`).

**Residual risk, stated plainly:** a transaction can no longer briefly hold a
violating state and repair it before committing. Concretely: you cannot
`INSERT` an Active initiative and then map it in the same transaction — the
insert is refused first. The workaround is to insert the mapping before
activating, which is the same order the reference's own example transaction
uses. Code that writes around the triggers leaves a violation for the report to
catch.

**Evidence:** `TestCardinalityMinimums`, including the case where a D-1
satisfies the goal rule but not the Dean rule and is still refused — proving the
two rules are independent, as the reference's separate `assert_` functions are.

## 5. `EXCLUDE USING gist` — WEAKER

**Reference:** `exclude using gist (initiative_id with =, person_id with =,
ownership_role with =, daterange(effective_start, coalesce(effective_end,
'infinity'), '[]') with &&)`

**Substitute:** an `AFTER INSERT, UPDATE` trigger that takes an exclusive
`sp_getapplock` on the assignment key, then checks for overlap.

**Measured absent on the target:** `EXCLUDE USING gist` gives `Incorrect syntax
near 'gist'`, and `tstzrange` gives `Cannot find data type tstzrange`. Neither
construct exists in T-SQL.

**Residual risk, stated plainly:**
- Under the lock, concurrent writers on the same key are serialised, so two
  overlapping assignments cannot both pass on one server.
- A writer that does **not** take the lock — a bulk load, a manual `INSERT`
  outside the application, a `BULK INSERT` — can still create an overlap. The
  trigger is on the table, so ordinary inserts do run it; the gap is bypassing
  the application's own ordering, not the trigger.
- The reference's exclusion is enforced by the storage engine regardless of who
  writes. This substitute is enforced by a trigger, which is a weaker guarantee.

**Evidence:** `TestStewardshipOverlap` proves serial refusal, proves adjacency
(ending 06-30, starting 07-01) is accepted rather than refused, and proves a
second different role may overlap the first — matching the per-role granularity
of the reference's exclusion key.

**Not tested:** concurrent writers. The serial case is proven; a two-connection
race is not, and is recorded here rather than implied to pass. Task 3.5 asked
for whichever behaviour is observed to be recorded — this is that record.

## 6. NULL uniqueness — fixed, not just documented

**Reference:** `business_email varchar(320) unique`

PostgreSQL treats `NULL`s as distinct, so any number of people may have no
email. T-SQL's plain `UNIQUE` treats `NULL`s as equal: only **one** person in
the table could have no address.

Found by running the suite, not by reading:

```
Violation of UNIQUE KEY constraint 'uq_person_email'.
The duplicate key value is (<NULL>).
```

Fixed in `004_conformance_fixes.sql` with a filtered unique index
(`WHERE business_email IS NOT NULL`), which states the reference's actual
intent: *emails, where present, are unique*.

**Audited across the model:** `business_email` is the only nullable unique
column in the port. `initiative_code`, `goal_number`, `metric_code`,
`priority_code`, and every composite primary key are `NOT NULL`, so the
NULL-as-equal trap bites nowhere else. That audit is written into
`004_conformance_fixes.sql` so a future column addition re-checks it.

## Evidence that the suite is not vacuous

Dropping a constraint must turn the suite red, or the tests prove nothing. Measured:

`
constraint present    exit=0  1 passed
constraint dropped    exit=1  1 failed     <- removed uq_metric_current_version
constraint restored   exit=0  1 passed
`

The probe is %TEMP%\opencode\redproof.py. Run it after adding a constraint to
confirm the new test would notice if the constraint were removed.

## Applying
```powershell
python db\mssql\tests\..\..\..\..\AppData\Local\Temp\opencode\apply_schema.py
```

In order: `001_rev2_tables.sql`, `002_constraints.sql`, `003_cardinality.sql`,
`004_conformance_fixes.sql`, then `007_integrity_report.sql`. All are
idempotent.

The constraint suite runs against the live database and rolls back per test:

```powershell
cd db\mssql
python -m pytest tests -q      # 33 passed
```

Credentials come from `%TEMP%\rev2sql.txt` or `REV2_CREDS`.


## Adopted-app-layer additions (not deviations — additions)

Change `rev2-full-reconciliation` (`008_app_layer.sql`). These tables carry app
layers the Rev2 package (000..007) never modeled. They are **additions**, the
same category as D9's `validation_event`, and are recorded here for the same
reason: they are not in the reference, so a reviewer needs to know they are
deliberate, not drift.

| table | why | key note |
|---|---|---|
| `app_meta` | engine-agnostic config (`current_plan_year`, `dataset_provenance`); Rev2 had no equivalent and the port fell back to SQLite | PK `[key]` |
| `audit_log` | append-only change-management record every write emits; deliberately NOT `validation_event` (design R2) | `audit_id INT IDENTITY`; `person_id` a string ref, no FK (an audit may outlive the person) |
| `role` / `person_role` | the application's role vocabulary (`Roles`/`PeopleRoles`); `People.IsAdmin` derives from these | mirrored by NAME (role_id is IDENTITY) |
| `source_area` | the five source areas the team screens carry (`SourceAreas`) | `name` UNIQUE |
| `milestone` | per-year priority milestones (`Milestones`); the priorities screen + meeting agenda | keyed to `annual_priority` `(code, period)`, ADR-0002 vocabulary preserved, `UNIQUE(priority_id, name)` |

**009 additions (team layer).** The `initiative` row gains the register's richer
columns the team screens read 29/29: `team_id` (FK `dbo.team`), `source_area_id`
(FK the 008 lookup), `strategy_align`, `initiatives_text`, `proposed_target`, and
`target_status`. `target_status` is intentionally un-CHECKed: its values are
register data and a new register year may add one, so a CHECK would block the
next year (the recurring-entity lesson). The columns are NULL-capable so an
initiative without them stays valid.

**010 addition (auth).** `person.clerk_user_id` — the Clerk identity link, so the
authentication layer can resolve a person from a verified Clerk session on Rev2.
It is an *identifier*, not a secret, so it belongs on the person row; unique where
present via a filtered index (`WHERE clerk_user_id IS NOT NULL`), the same
NULL-not-equal trap 004 fixed for the nullable business email.

**No credential column, on either store.** The shared passcode is an
environment setting, and no per-person secret is stored in Rev2 or in the local
schema. The sign-in path is identical on both: the passcode, then the name
picker.

> **Correction 2026-10-08.** This paragraph previously read "production identity
> is Clerk (ADR-0004)". That was inference from the seam being built, not a
> measured fact: Azure's app settings carry `APP_PASSCODE`/`APP_SECRET` and no
> `CLERK_*` keys, so it has always run the passcode. See ADR-0006.

**The credential column is gone entirely (2026-10-09).** This entry originally
existed to explain why Rev2 held no `People.Credential` while the local store
did — a deviation from a parity goal. The per-person PIN has now been removed
from the application, so neither store has a credential column and there is no
deviation to record. The remaining sign-in path is the shared passcode plus the
name picker, on both stores. Nothing in this file changes as a result; the entry
is retained because "no credential column" is now an invariant rather than a
deviation, and that is worth stating in one place.

None of these is claimed to be a port of a reference mechanism. They are new
tables that let the whole app surface run on Rev2. `milestone` keyed to the
annual instance preserves the 2026-10-08 multi-year fix (P01 recurs each year;
its milestones belong to one year's priority row).


## A deploy note that cost a live outage

The synthetic-label deploy (task 8.2) took the live prototype down with
database unreachable for several minutes. Cause: z webapp deploy --type zip
**replaces** /home/site/wwwroot, and nothing in the application creates the
SQLite database at startup. The first zip omitted cll_initiatives.db because it
seemed right not to ship a database, so the deploy deleted the only copy.

Two things worth keeping:

- **Ship the database, or create it at startup.** The app resolves
  DB_PATH=./cll_initiatives.db relative to wwwroot, so the file must be in the
  zip at its root. The rebuilt zip carries it plus db/schema.sql and
  db/seed_sample.sql so the database can be recreated in place.
- **The verification caught it, not the deploy.** z webapp deploy exited 0 and
  reported success. Only /healthz returning database unreachable revealed the
  outage, which is exactly why that endpoint exists outside the gate.

Also: the live-verification probe initially reported PASS while actually
reading the login page, because the credential file uses the key APP_PASSCODE
rather than PASSCODE and the login silently 401'd. A page that carries the
banner is not necessarily the page you asked for; the probe now asserts the
login form is absent and the login POST returned a redirect.
