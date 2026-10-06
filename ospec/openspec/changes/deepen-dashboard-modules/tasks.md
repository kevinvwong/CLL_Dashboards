# Tasks

## 1. Give the connection one interface and one default (spec: `data-connection`)

- [x] 1.1 Confirm no caller outside `app/`, `tests/`, and `scripts/` uses `db.query`, `db.DEFAULT_DB_PATH`, `Config.is_local`, or `as_dict`; record the grep and its (empty) result. *Verify: the recorded grep shows no callers, so the deletions below are safe.*
  - Grepped `get_connection|db\.query|DEFAULT_DB_PATH|is_local|as_dict` across `app/`, `tests/`, `scripts/`. Result: `db.query` and `as_dict` and `is_local` have **no callers**; `DEFAULT_DB_PATH` is referenced only inside `db.py` itself (lines 6, 16); `get_connection` is called only at auth.py:47, queries.py:13, repo.py:41. Safe to delete.
- [x] 1.2 Delete `db.query`, `db.DEFAULT_DB_PATH`, and `Config.is_local`/`as_dict`; make `get_connection()` require the path and take it from `Config`. *Verify: the app starts and every route that reads or writes still works — `python -m pytest tests -q` green.*
- [x] 1.3 Collapse the three `_conn` helpers so all reads go through one interface and only `repo` adds `BEGIN IMMEDIATE`. *Verify: a test opens a write and a read in one request and both see the same file; the suite is green.*
  - `db.get_connection(path)` became `db.connect(write=False)`, which reads `Config.DB_PATH` itself — the path is now named in exactly one place. `auth._conn` and `queries._conn` call `connect()`; `repo._conn` calls `connect(write=True)`. The three helpers remain as one-liners so call sites are unchanged, but they now delegate to the one interface.
- [x] 1.4 Add a test asserting no second database path exists in the tree. *Verify: the test fails if `DEFAULT_DB_PATH` or a literal `cll_initiatives.db` default is reintroduced.*
  - `tests/test_connection.py` (5 tests): no `DEFAULT_DB_PATH`, the default filename only in `config.py`, no `sqlite3.connect` outside `db.py`, `BEGIN IMMEDIATE` only in `db.connect(write=True)`, and a read+write in one request see the same file. Red-proof: reintroducing a second default and a stray `sqlite3.connect` fails 2 of the 5; restoring passes all 5.
  - **Defect found in the guard itself:** the scan flagged the *comment* in `repo.py` that explains the rule. Fixed by stripping comments before matching (`_code_lines`) — a gate that fires on its own documentation gets switched off.
- [x] 1.5 **Group check:** build the deploy archive and confirm it still carries exactly one database entry. *Verify: `test_deploy_zip.py` passes (4 tests), proving the stray-DB failure cannot recur.*
  - 4 passed. Full suite: 262 passed.

## 2. Deepen the write path (spec: `initiative-write-path`)

- [x] 2.1 Add a `write(body)` seam in `repo.py` that owns BEGIN IMMEDIATE, commit, rollback, `_friendly` mapping, and close. *Verify: a unit test drives a body that raises and asserts nothing was written and the connection closed.*
- [x] 2.2 Move `add_progress_update` onto the seam, keeping its validation and messages. *Verify: `test_updates.py` passes unchanged.*
- [x] 2.3 Move `update_initiative_details`, `replace_tags`, `replace_links` onto the seam. *Verify: `test_admin.py` passes unchanged.*
- [x] 2.4 Move `create_initiative`, `retire_initiative`, `update_entry_description` onto the seam; fold `create_initiative`'s inline error map into the shared mapping. *Verify: the duplicate-code and unknown-owner messages still appear, asserted by `test_admin.py`.*
  - **Defect fixed, not merely moved.** `create_initiative`'s unknown-owner branch tested for the literal text `"OwnerID"`, which SQLite never emits (it returns a bare `FOREIGN KEY constraint failed` with no column name). The branch was dead and the case fell through to the generic message, which does not name what to change — contrary to the `initiative-write-path` spec. `Initiatives` has exactly one foreign key on this INSERT (`OwnerID → People`), so a foreign-key failure there is unambiguously the owner; the branch now tests for that and the message names the directory. Red-proof: restoring the dead branch fails `test_unknown_owner_is_a_message_not_a_driver_error`.
- [x] 2.5 Add tests for the spec's refusal cases — percent out of range, unknown status, duplicate code — asserting a message, never a driver error. *Verify: each new test fails if the seam lets an `IntegrityError` escape.*
  - `tests/test_write_path.py` (9 tests): atomicity (refused write, mid-write raise, successful commit as a single change), refusal messages (percent, status, duplicate code, unknown owner), append-only, and "the skeleton exists once".
  - Red-proof: a seam that commits on a failing body fails the atomicity test. A first attempt that merely removed the explicit `rollback()` proved nothing — SQLite rolls back an uncommitted transaction at connection close, so behaviour was unchanged and the test correctly still passed; the mutation had to change the outcome, not the code text.
- [x] 2.6 **Group check:** the full suite is green and every write route still behaves as its spec describes. *Verify: `python -m pytest tests -q` green; no write function retains its own transaction skeleton (grep for `BEGIN IMMEDIATE` finds exactly one site).*
  - 271 passed. `BEGIN IMMEDIATE` appears in exactly one place (`db.connect`); each of the eight writes delegates to `repo.write`.

## 3. Collapse the route guard chain (spec: `request-guards`)

- [x] 3.1 Add a request dependency that resolves the signed-in person, then the target initiative (404), then the declared permission (403), in that order. *Verify: a test asserts an unknown code returns 404 even for a caller who would be forbidden on a real one.*
- [x] 3.2 Move the two owner-permission routes (`/updates`, `/edit/details`) onto the dependency. *Verify: `test_access.py` and `test_updates.py` pass; a direct non-owner POST is still 403.*
- [x] 3.3 Move the admin-only routes (create, retire, tags, links, entry descriptions) onto the dependency. *Verify: `test_admin.py` passes; a direct non-admin POST is still 403.*
- [x] 3.4 Remove the now-dead per-route guard clauses and the `person["PersonID"]` index asserts they required. *Verify: grep finds no `is_admin_request(request)` guard left in a route body; the suite is green.*
  - `app/guards.py` holds `may_update`, `may_edit_details`, `admin_only`, `admin_for`, `known_target`. `auth.current_person` now caches on `request.state`, so the guard, the template context, and the permission check read the person once. The three surviving `is_admin_request` calls are `may_admin` **presentation flags** in `_ctx`/`_edit_ctx` and the card render, not guards.
- [x] 3.5 **Group check:** every route's 404/403 behaviour matches its spec, checked by walking the routes table against `design.md`. *Verify: `test_access.py`, `test_admin.py`, and `test_flows.py` green; the routes table in `design.md` still lists the same routes.*
  - 278 passed. `tests/test_guards.py` (7 tests): unknown code is 404 even for an admin; known-but-forbidden is 403; direct POST without permission is 403; a non-admin cannot edit tags; the person is read once per request; no route re-inlines the admin guard or the 404-then-403 pair. Red-proof: removing the person cache fails the once-per-request test.
  - Note: the two `is_admin_request` calls in `_ctx`/`_edit_ctx` are template flags, not guards, and the card route keeps them; that is why the "no per-route admin guard" test matches the `if not auth.…` form, not the bare call.

## 4. Single-source the status vocabulary, slug, and colour (spec: `status-presentation`)

- [x] 4.1 Add a status module that exposes the vocabulary, the slug transform, and the class name, reading the vocabulary from the schema's `CHECK`. *Verify: a test asserts the module's vocabulary equals the values parsed from `db/schema.sql`.*
- [x] 4.2 Register the slug as a Jinja filter that delegates to the module. *Verify: a test renders a status with a space and asserts the same class the module produces.*
- [x] 4.3 Replace the six in-template slug transforms with the filter. *Verify: grep finds no `lower | replace(' ', '-')` left in `app/templates/`.*
- [x] 4.4 Add a CSS rule for every emitted status and milestone class, including `m-*`. *Verify: a test collects every class a template emits and asserts each has a rule in `style.css` — the check that would have caught the dead `m-*` classes.*
  - `app/status.py` (vocabulary read from the schema's CHECK, `slug`, `status_class`, `milestone_class`, `availability_class`); filters registered in `main.py`; six templates now call the filter.
  - **A second dead-class defect found while writing the test:** three availability values (`Build`, `Derived`, `Have it`) were emitted with no CSS rule, exactly like `m-*`. The test derives both the milestone and availability values from `oct16_data`, so a new value cannot be emitted unstyled. Fixed by adding rules for all five availability values.
- [x] 4.5 Colour a status shown as a badge, not only inside a bar. *Verify: a test asserts a status badge carries its status class, and `design-audit`-style visual check shows the colour.*
  - Added `.badge.status-*` rules (the old colours were scoped `.bar-fill.status-*` only) and `.connection-status.status-*` / `.count.status-*`. Rendered `/oct16` confirms `status-on-track`, `status-at-risk` on badges and no old-style uppercase slug.
- [x] 4.6 **Group check:** the same status renders identically on every screen. *Verify: a test renders one status across list, person, card, and oct16 and asserts the same class string from each.*
  - 286 passed. `tests/test_status_presentation.py` (8 tests). Red-proofs: removing the `m-*` rules fails the milestone test; removing the three availability rules fails the availability test.

## 5. Let `oct16_data` state what the page derives (spec: `oct16-deliverable`)

- [x] 5.1 Emit `percent(outcome)` from `scripts/build_oct16_data.py`, regenerate `app/oct16_data.py`, and call it from `oct16.html` in place of the inline formula. *Verify: a test asserts the rendered bar width equals `percent()`; grep finds no `100 * o.reached` in the template.*
  - `percent()` floors (`(100 * reached) // planned`), so a 1-of-3 bar reads 33%, not 34% — a bar must not overstate progress. It also guards `planned == 0`.
- [x] 5.2 Use `owner_label` for every owner state in the template, removing the second spelling of the no-owner string. *Verify: a test asserts the rendered no-owner text equals `OWNER_NONE`.*
- [x] 5.3 Add tests for the confirmed-marker rules: illustrative, confirmed, partial, and a no-name file refused as confirmation. *Verify: `test_confirmed_data.py` covers all four; each fails against the un-fixed generator (red-proof).*
  - `tests/test_oct16_module.py` (11 tests): percent is a module function, floors, guards zero; the template computes nothing and re-spells nothing; illustrative / partial / confirmed marker states; the three owner states.
  - Red-proof: restoring the inline formula to the template fails `test_the_template_does_not_compute_the_percent`.
- [x] 5.4 **Group check:** regenerate from the generator and confirm the module still imports, renders, and clears the marker by itself. *Verify: `test_oct16.py` and `test_oct16_swap.py` green; `build_oct16_data.py` run without `--owners` leaves the page illustrative.*
  - 297 passed. The regenerated module keeps `CONFIRMED = False` and the illustrative marker; `percent` returns 25/40/25/0/50/33 for P01–P06.

## 6. Screen-shaped reads (spec: `screen-reads`)

- [x] 6.1 Add one read per edit screen returning its options and current values in a single call. *Verify: `test_admin.py` passes with the edit routes reading through the new call.*
  - `queries.tag_edit_options(initiative_id)` and `queries.link_edit_options(initiative_id)`, each returning the options and the chosen values in one call.
- [x] 6.2 Move the `current_*` callers onto the screen-shaped reads and delete the six pass-through readers. *Verify: grep finds no caller of `all_goals`, `all_priorities`, `active_dean_initiatives`, `current_goal_tags`, `current_priority_tags`, `current_links`.*
  - The six are deleted; only an explanatory comment names them. `test_admin.py`'s three link tests were re-pointed at `link_edit_options` (task 6.3's work, done here because the deletion forced it).
- [x] 6.3 Re-point `test_updates.py`'s diary helper and `test_home.py`'s hardcoded counts at the importing form rather than re-implementing the query. *Verify: a changed seed figure fails the test that imports the read, and does not pass because a copy was updated too.*
  - `test_updates._diary` now calls `queries.initiative_card(code)["diary"]`; its one assertion moved from `EnteredByID` to the card's `EnteredBy` name. `test_home.py` now derives the expected counts from a counting query over the raw tables and compares them to the view, and imports `canonical_goals.GOALS` for the names.
  - **Consequence, recorded because it changes the task's literal wording:** the old `test_home.py` pinned a hand-maintained snapshot, and that snapshot once held the *transposed* goal numbering and had to be edited by hand. The derived form still fails on a broken view JOIN (view count ≠ raw count) — which is what the snapshot was for — but a pure seed change no longer fails it on its own. That is the intended trade: pinned expectations are what drifted.
- [x] 6.4 Add a test for the "no update vs zero percent" distinction across the screens that show it. *Verify: an initiative with no update reports absent, and one at 0% with an update reports present.*
  - `tests/test_screen_reads.py` (6 tests): the two screen-shaped reads; the six pass-throughs are gone; the card's tags have no second reader; no-update reports `HasUpdate is False`; a recorded 0% reports `HasUpdate is True` and is not stale.
  - Red-proof: forcing `HasUpdate` True fails `test_no_update_is_distinct_from_zero_percent`.
- [x] 6.5 **Group check:** every screen still renders from one read. *Verify: `test_cards.py`, `test_lists.py`, `test_meeting_checks.py`, `test_updates.py` green.*
  - 304 passed.

## 7. Integration

- [x] 7.1 Run the whole suite and both validations. *Verify: `python -m pytest tests -q` green and `openspec validate --all --strict` exits 0.*
  - 304 passed; `openspec validate --all --strict` → 4 passed, 0 failed.
- [ ] 7.2 Build the deploy archive and deploy it once, observing the marker. *Verify: `/healthz` reports the new marker; the gate walk in `ospec/docs/DEPLOY.md` passes.*
  - **BLOCKED, not attempted.** The live plan `cll-dash-proto-plan` (F1 Free) is `QuotaExceeded`: `WP stop requests 34 / 15`, `nextResetTime 2026-10-06T18:00:00Z`. The site returns 403 `This web app is stopped`, and *both* apps on the shared plan are down. A deploy now is itself a stop request and would push the reset out another hour (measured: two `webapp start` attempts moved it 17:00Z → 18:00Z and the count 16 → 34). The archive builds and the rollback is already exercised (`ospec/docs/DEPLOY.md`); only the deploy is gated on the quota. Do this after `nextResetTime`, and space it from any other deploy.
- [x] 7.3 Record the new seams for the next reader: which module owns the connection, the write transaction, the status vocabulary, and the screen reads. *Verify: `design.md` in the prototype change points to each seam, so a future explorer does not re-derive them.*
  - Added a **Module seams** table to the prototype's `design.md`, naming the module, its interface, and what it hides, for all six. Also recorded the F1 stop-request finding in `DEPLOY.md`.
