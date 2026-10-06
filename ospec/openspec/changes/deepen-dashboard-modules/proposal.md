# Proposal

## Why

The prototype's modules are shallow: their interfaces are nearly as wide as their implementations, so callers and tests must know things the modules should be hiding. Four symptoms were measured in the architecture review (`architecture-review-20261006T165950Z.html`):

- `repo.py`'s eight write functions each restate the same transaction/rollback/error-map skeleton, so its interface is as wide as its body.
- `main.py`'s 27 handlers repeat the same guard preamble — `initiative_card(code) is None` ×6, `is_admin_request(request)` ×9, `status_code=422` ×7 — so the 404-before-403 invariant lives at 27 call sites.
- Four `_conn` helpers obtain a connection in four files, and `db.py` carries a **second, conflicting default database path** that already shipped an empty database into a deploy archive (commit `35fc22e`).
- One status concept crosses the schema, Python, and **six** templates; the colours are scoped `.bar-fill.status-*`, so a status badge outside a bar renders uncoloured, and the milestone classes `m-*` have no CSS rule at all.

The test suite cannot see most of this: 9 of 16 test files open SQLite directly, and two re-implement production queries rather than importing them.

## What Changes

Deepen six modules so that behaviour sits behind smaller interfaces. Each refactor **preserves observable behaviour** except where listed as a correction; the spec deltas either pin the invariant the refactor must hold, or state an observable requirement that was previously implicit.

- **Deepen the write path.** One `write()` seam owns `BEGIN IMMEDIATE` / commit / rollback / constraint-to-message mapping; the eight writes become bodies inside it. Removes a duplicate inline error map in `create_initiative`.
- **Collapse the route guard chain.** A dependency resolves *person, target initiative, and permission* once, before the handler body. The existence-before-permission ordering becomes one rule in one place, not a per-route comment.
- **Give the connection one interface and one default.** One module owns how a connection is obtained and to which path; `repo` adds write mode at the same seam. Delete `db.query` (no callers), `Config.is_local`, `as_dict`, and the second default path.
- **Single-source the status vocabulary, slug, and colour.** A status module derives the vocabulary from the schema's own `CHECK`, exposes the slug and the badge colour; templates stop re-deriving all three. **Correction:** status badges currently render uncoloured and `m-*` classes are dead; both are fixed by this change.
- **Let `oct16_data` state what the page derives.** The module exposes the milestone percent and the owner label it already documents; the template renders values instead of computing `(100 * reached / planned)` and re-spelling the owner-none string.
- **Screen-shaped reads.** The six single-`SELECT` pass-through readers collapse into reads shaped to the screen that consumes them, as `initiative_card` already is.

**Out of scope.** No new screens, routes, or data fields. No change to the access model (passcode + picker), the schema's tables, or the sample data. No migration to Azure SQL — the schema stays SQLite for this change. The live deploy is governed by `launch-initiatives-dashboard-live` and is not touched here. The `.m-*` colour values, once defined, are cosmetic and not specified.

## Capabilities

### New Capabilities

- `initiative-write-path`: how every write runs — one transaction, one error-to-message mapping, append-only progress — stated so the refactor cannot silently change it.
- `request-guards`: how a request resolves its target and the caller's permission — existence before permission, admin gate from the server, resolved once per request.
- `data-connection`: how the application obtains a database connection and which file it names — one interface, one configured path.
- `status-presentation`: how an initiative status is shown — a single vocabulary, a single slug transform, a colour wherever the status appears.
- `oct16-deliverable`: what the October 16 page shows and where each shown value comes from, including that the illustrative/confirmed marker is derived from the data.
- `screen-reads`: the read interface each screen uses — one named read per screen, shaped to what that screen renders.

### Modified Capabilities

None. `openspec/specs/` holds no archived main specs yet (the prototype change is still open), so every delta is `ADDED`. These capabilities pin invariants that were previously implicit in code, plus the three observable corrections noted above.

## Impact

- **Code:** `app/repo.py`, `app/main.py`, `app/db.py`, `app/config.py`, `app/auth.py`, `app/queries.py`, `app/static/style.css`, `app/templates/*.html`, `app/oct16_data.py` and its generator `scripts/build_oct16_data.py`.
- **Tests:** the 9 files that open SQLite directly move behind the new seams; two that re-implement production SQL (`test_updates.py` diary, `test_home.py` counts) are re-pointed at the importing form.
- **No change to:** `db/schema.sql` (the vocabulary is *read* from it, not altered), the routes table in `design.md`, or the live deployment.
