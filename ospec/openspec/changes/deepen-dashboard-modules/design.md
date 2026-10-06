# Design

## Context

See `proposal.md` → Why for the measured friction. This document records how the six deep modules are shaped and what their interfaces expose.

Constraints that shape the approach:

- **The schema is the source of truth and is not changed by this change.** `db/schema.sql` owns the status vocabulary, the percents, the levels, and the link rule. Python reads these; it must not become a second place they are written.
- **Writes are append-only and single-transaction** by prior decision (the prototype change's design.md D4). This change keeps that contract and moves where it is stated.
- **The live service is on F1 and stopped on an hourly quota.** The refactor must be deployable in one archive and must not change routes, so the deploy runbook is untouched.
- **The suite runs 238 test functions; 9 files open SQLite directly.** Any change to a seam must keep those tests meaningful, so the refactor re-points them rather than deleting them.

## Goals / Non-Goals

**Goals:**

- Each of the six modules presents a smaller interface than it does today, with the behaviour it hides unchanged except the three stated corrections.
- Callers and tests cross the same seam, so a test can assert behaviour without opening the database itself.
- The invariants in the specs are stated once, in the module that owns them.

**Non-Goals:**

- No route is added, removed, or renamed; the routes table in the prototype's `design.md` stands.
- No change to `db/schema.sql`, the sample data, or the access model.
- No attempt to make the modules deep by adding layers; each deepening removes duplication rather than wrapping it.
- Not a step toward Azure SQL. The T-SQL port is a separate change; this one keeps SQLite.

## Decisions

### D1 — One `write()` seam in `repo.py`, not a base class or a decorator

A single function that takes the write body, opens a write connection, runs the body, commits, rolls back on failure, and maps a constraint error to a message. The eight current write functions become bodies passed to it.

- **Why not a decorator:** a decorator hides the transaction from the body's own reads (the existence check must run inside the same transaction), so the body would need the connection anyway.
- **Why not a base class:** there is one implementation and no variation across a seam; a class would be a hypothetical seam.
- **Depth gained:** the interface becomes `write(body)` plus the eight names; the transaction discipline leaves the interface. `create_initiative`'s duplicate inline error map folds into the shared mapping.

### D2 — A request dependency resolves person, target, and permission; routes declare what they require

FastAPI dependencies resolve, in order: the signed-in person (already gated), the target initiative (404 if absent), and the caller's permission for the declared action (403 if absent). The handler receives the resolved record.

- **Why a dependency rather than middleware:** permission depends on the route's action and the target code, which middleware does not know. A dependency is declared per route, so admin-only routes declare it and stop repeating the check.
- **Ordering:** existence-before-permission is enforced inside the dependency, which is why the spec puts that rule there rather than in each handler.
- **Alternative considered:** a decorator on each handler. Rejected: it hides the resolution from the signature, so the handler's parameters no longer say what it needs.

### D3 — `db.py` owns connection and path; `Config` supplies the path; `repo` adds write mode at the same seam

`get_connection()` keeps its pragmas and takes the path from `Config`. The second default (`db.DEFAULT_DB_PATH`), the dead `query()`, and `Config.is_local`/`as_dict` are deleted. `repo`'s write connection is the same interface plus `BEGIN IMMEDIATE`.

- **Why delete rather than keep both defaults:** two defaults for one concept is what allowed an empty database to be packaged beside the real one (commit `35fc22e`). The spec states "no second default path" precisely to make that failure unrepeatable.
- **Alternative considered:** make `db.query` the shared reader. Rejected: it hardwires the wrong path and no caller wants it.

### D4 — A `status` module states the vocabulary, the slug, and the colour; CSS defines a colour for every class emitted

The vocabulary is read from the schema's `CHECK` at build time (or asserted against it in a test), so the schema remains the source of truth. The module exposes the slug function and the class name; templates call it and stop transforming. `style.css` gains a colour rule for every class the templates emit, including the milestone `m-*` classes.

- **Why a module and not a Jinja filter:** a filter is registered once but the vocabulary and the class list still need a home; the module is that home, and the filter becomes a thin adapter over it.
- **Correction this makes:** status badges outside a bar currently render uncoloured, and `m-*` classes are emitted with no rule. Both are observable and are fixed here, not left as cosmetic.

### D5 — `oct16_data` exposes `percent(outcome)` and reuses `owner_label` for every owner state

The module already documents the bar as *derived* and already owns `owner_label`. The template calls both instead of computing `(100 * reached / planned)` and re-spelling the no-owner string.

- **Why the generator changes, not the module by hand:** `oct16_data.py` is generated by `scripts/build_oct16_data.py`; a hand edit is overwritten on rebuild. Any new helper is emitted by the generator.
- **Why not store a percent constant:** the percent is a function of reached and planned; storing it invites the two to drift.

### D6 — Reads are shaped to the screen; the single-table readers move behind them and are deleted

`initiative_card` is the model to follow. The edit screens gain one read each; the six pass-through readers (`all_goals`, `all_priorities`, `active_dean_initiatives`, `current_goal_tags`, `current_priority_tags`, `current_links`) are deleted once their callers move.

- **Deletion test:** removing them concentrates the SQL into one read per screen; the complexity does not reappear across callers.
- **Note:** `current_*` readers are also read inline inside `initiative_card` (queries.py:171–188). The screen-shaped reads become the single path.

## Risks / Trade-offs

- [The refactor touches the write path the whole meeting depends on] → The suite's write tests (`test_updates.py`, `test_admin.py`) are re-pointed at the new seam before the old skeleton is deleted, so a regression fails a test rather than reaching the meeting. Rollback is the previous archive; no schema or data change means a revision rollback is sufficient.
- [Moving tests off direct SQLite access could weaken them] → A test that opened the database directly is replaced by one that asserts through the new read/write interface, which is the surface the app uses; where a test genuinely needs to seed state, it seeds through the write module rather than raw SQL.
- [Reading the vocabulary from the schema adds a build-time dependency] → A test asserts the module's vocabulary equals the schema's `CHECK` values, so a schema change fails a test naming the drift rather than rendering an unknown status.
- [Deleting the second default could break a caller outside the searched roots] → The grep for callers covered `app/`, `tests/`, and `scripts/`; the task states the deletion is gated on that grep being empty at implementation time.

## Migration Plan

This is an in-place refactor with no schema or data migration.

1. **Land in the order the tasks give**, one module per group, each group ending green on the full suite, so a regression is attributed to one module.
2. **Deploy** as a single archive with the existing runbook (`ospec/docs/DEPLOY.md`); the marker and `/healthz` check are unchanged.
3. **Rollback** is the previous revision — no data half is needed, because nothing in this change writes to the database differently, only through a different seam. Note the F1 stop-request quota: space deploys out (see the runbook's quota section).

## Open Questions

- Whether the milestone-status vocabulary (`Met`, `In progress`, `Due Dec`, `Confirm`) should also be declared formally. It is not in the schema's constraint today, so the spec only requires that every emitted class have a defined appearance; a decision to formalise it can come later without changing this design.
