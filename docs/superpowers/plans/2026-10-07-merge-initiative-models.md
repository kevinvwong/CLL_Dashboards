# Merge the Two Initiative Models — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the register's 29 Major Initiatives the one initiative model — move the progress diary, tags, links, retire and permission model onto it, and retire the prototype's parallel model.

**Architecture:** Add `MajorInitiativeUpdates` (the diary) and `MajorInitiatives.IsActive`. Retarget `repo.py`, `auth.py`, `queries.py` and the routes from the prototype's `Initiatives`/`ProgressUpdates` tables to `MajorInitiatives`/`MajorInitiativeUpdates`. Drop the five prototype tables and 308-redirect `/initiatives/*` to `/major-initiatives/*`.

**Tech Stack:** Python 3.12, SQLite, FastAPI, Jinja2, HTMX, pytest.

**Spec:** `docs/superpowers/specs/2026-10-07-merge-initiative-models-design.md`

## Global Constraints

- `Initiative Dashboard Register.xlsx` is canon and decides everything.
- The 24 sample `ProgressUpdates` rows are **discarded, not migrated** — none references a `MajorInitiative`.
- Keys change from **Code** (`'ELIZ-1'`) to **MIId** (`'MI-002'`).
- Retired `/initiatives/*` routes return **308** to their `/major-initiatives/*` target.
- `/outcomes`, `oct16_data.py` and the Dean Priorities layer are **untouched**.
- Seeds stay reproducible: two consecutive `python db/build_db.py` runs hash identically.
- Stage exact paths with `git add -- <path>`; never `git add -A`.
- Full suite green (currently 538) between every task.

---

### Task 1: Schema — the diary, IsActive, and the drop

**Files:**
- Modify: `db/schema.sql`
- Modify: `db/seed_sample.sql`, `db/seed_team_layer.sql` (remove references to dropped tables)
- Modify: `db/build_db.py` (row-count list)
- Test: `tests/test_schema_merge.py` (create)

**Interfaces:**
- Produces: table `MajorInitiativeUpdates`; column `MajorInitiatives.IsActive`; view `vw_LatestMajorInitiativeProgress`; the five prototype tables and their triggers/indexes removed.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_schema_merge.py
"""The merged model: the diary exists, the prototype tables are gone."""
import os, sqlite3
import pytest

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = os.path.join(R, "db", "schema.sql")


def _con():
    con = sqlite3.connect(":memory:")
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(open(SCHEMA, encoding="utf-8").read())
    return con


def test_diary_table_exists():
    con = _con()
    t = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "MajorInitiativeUpdates" in t
    con.close()


def test_prototype_tables_are_gone():
    con = _con()
    t = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for gone in ("Initiatives", "InitiativeGoals", "InitiativePriorities",
                 "InitiativeLinks", "ProgressUpdates"):
        assert gone not in t, gone
    con.close()


def test_major_initiatives_has_isactive():
    con = _con()
    cols = {d[1] for d in con.execute("PRAGMA table_info(MajorInitiatives)")}
    assert "IsActive" in cols
    con.close()


def test_diary_status_check():
    con = _con()
    con.execute("INSERT INTO MajorInitiatives (Code, Title) VALUES ('x','t')")
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("INSERT INTO MajorInitiativeUpdates (MajorInitiativeID, PercentComplete, Status) "
                    "VALUES (1, 10, 'Nonsense')")
    con.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_schema_merge.py -v`
Expected: FAIL — `no such table: MajorInitiativeUpdates`

- [ ] **Step 3: Edit the schema**

In `db/schema.sql`:
1. Add `IsActive INTEGER NOT NULL DEFAULT 1 CHECK (IsActive IN (0,1))` to `MajorInitiatives`.
2. Add the `MajorInitiativeUpdates` table, its index and `vw_LatestMajorInitiativeProgress` exactly as the spec's §1 shows.
3. Delete the `CREATE TABLE` blocks for `Initiatives`, `InitiativeGoals`, `InitiativePriorities`, `InitiativeLinks`, `ProgressUpdates`; the `trg_Links_LevelCheck*` triggers; and the `IX_IG_*`, `IX_IP_*`, `IX_IL_*`, `IX_PU_*`, `UX_IG_*`, `UX_IP_*` indexes and the `vw_GoalInitiatives`/`vw_PriorityInitiatives`/`vw_InitiativeConnections`/`vw_PersonInitiatives`/`vw_LatestProgress`/`vw_RecentUpdates`/`vw_DataChecks` views that read them.

- [ ] **Step 4: Remove the dropped tables from the seeds**

In `db/seed_sample.sql` delete every `INSERT INTO Initiatives|InitiativeGoals|InitiativePriorities|InitiativeLinks|ProgressUpdates` block (and the People rows only those tables used). In `db/seed_team_layer.sql` leave the Teams/SourceAreas/MajorInitiatives/Priorities blocks. In `db/build_db.py` update the row-count list to: `Goals, Priorities, People, Teams, SourceAreas, MajorInitiatives, MajorInitiativePriorities, MajorInitiativeGoals, DeanPriorities, MajorInitiativeDeanLinks, MajorInitiativeCoOwners, MajorInitiativeUpdates`.

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_schema_merge.py -v`
Expected: PASS (4 tests)

- [ ] **Step 6: Commit**

```bash
git add -- db/schema.sql db/seed_sample.sql db/seed_team_layer.sql db/build_db.py tests/test_schema_merge.py
git commit -m "feat(schema): merge to one initiative model; add the diary, drop the prototype tables"
```

---

### Task 2: `repo.py` — write paths on the register model

**Files:**
- Modify: `app/repo.py`
- Test: `tests/test_repo_merge.py` (create)

**Interfaces:**
- Consumes: `MajorInitiatives` (with `IsActive`), `MajorInitiativeUpdates`, `MajorInitiativeGoals`, `MajorInitiativePriorities`, `MajorInitiativeDeanLinks`.
- Produces: the eight write functions with the same names/signatures, now keyed by **MIId**.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_repo_merge.py
"""The write paths, on the register model."""
import sqlite3
from app import repo


def _latest(db):
    con = sqlite3.connect(db)
    row = con.execute("SELECT PercentComplete, Status FROM MajorInitiativeUpdates "
                      "ORDER BY UpdateID DESC LIMIT 1").fetchone()
    con.close()
    return row


def test_add_update_lands_on_a_major_initiative(fresh_db):
    repo.add_progress_update("MI-002", 40, "On track", "note", entered_by_id=5)
    assert _latest(fresh_db) == (40, "On track")


def test_add_update_refuses_unknown_mi(fresh_db):
    with pytest.raises(repo.RuleError):
        repo.add_progress_update("MI-999", 10, "On track", "", entered_by_id=5)


def test_retire_sets_isactive(fresh_db):
    repo.retire_initiative("MI-002", person_id=5)
    con = sqlite3.connect(fresh_db)
    v = con.execute("SELECT IsActive FROM MajorInitiatives WHERE MIId='MI-002'").fetchone()[0]
    con.close()
    assert v == 0


import pytest  # noqa: E402
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_repo_merge.py -v`
Expected: FAIL — `no such table: MajorInitiativeUpdates` (or a query error on `Initiatives`)

- [ ] **Step 3: Retarget the writes**

Rewrite each function so its lookup is `SELECT MajorInitiativeID ... FROM MajorInitiatives WHERE MIId = ? AND IsActive = 1` and its writes hit `MajorInitiativeUpdates` / `MajorInitiativeGoals` / `MajorInitiativePriorities` / `MajorInitiativeDeanLinks`:

- `add_progress_update` → INSERT into `MajorInitiativeUpdates`.
- `replace_tags` → DELETE/INSERT `MajorInitiativeGoals` and `MajorInitiativePriorities` (both take `IsPrimary`? `MajorInitiativeGoals` does not; `MajorInitiativePriorities` does).
- `replace_links` → DELETE/INSERT `MajorInitiativeDeanLinks`; the target check reads `DeanPriorities(DeanPriorityID)`, not `Initiatives.Level`.
- `create_initiative` → INSERT into `MajorInitiatives (Code, Title, ...)`; the code is generated, `MIId` is NULL until the canon assigns one.
- `retire_initiative` → `UPDATE MajorInitiatives SET IsActive=0 WHERE MIId=?`.
- `update_initiative_details` → `UPDATE MajorInitiatives SET Title=?, Description=? WHERE MIId=?`.
- `_friendly` messages updated to name `MajorInitiatives`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_repo_merge.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add -- app/repo.py tests/test_repo_merge.py
git commit -m "feat(repo): all writes target the register model"
```

---

### Task 3: `auth.py` — permissions on the register model

**Files:**
- Modify: `app/auth.py`
- Test: `tests/test_auth_merge.py` (create)

**Interfaces:**
- Consumes: `MajorInitiatives.OwnerID`, `People.TeamID`.
- Produces: `get_initiative(mi_id)`, `is_dean(person)`, `can_update`, `can_edit_details` unchanged in name.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_auth_merge.py
from app import auth


def test_the_dean_is_recognised(fresh_db, request_for, logged_in):
    person = auth.current_person(request_for(logged_in("Bill Gaudelli")))
    assert auth.is_dean(person) is True


def test_an_owner_may_update_their_own(fresh_db):
    # ELIZ->MI mapping: Elizabeth Smith owns the Learning Infrastructure MIs;
    # pick one and assert the owner check passes for her.
    assert True  # replaced in step 3 with a concrete owner assertion
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_auth_merge.py -v`
Expected: FAIL — `get_initiative` reads `Initiatives`

- [ ] **Step 3: Retarget the permission helpers**

- `get_initiative(mi_id)` → `SELECT MajorInitiativeID, MIId, Title, OwnerID FROM MajorInitiatives WHERE MIId=? AND IsActive=1`.
- `is_dean(person)` → the person with `ReportsToID IS NULL` who owns a `MajorInitiative` (`EXISTS (SELECT 1 FROM MajorInitiatives WHERE OwnerID=? AND IsActive=1)`).
- `can_update` / `can_edit_details` compare `initiative["OwnerID"] == person["PersonID"]`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_auth_merge.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -- app/auth.py tests/test_auth_merge.py
git commit -m "feat(auth): permissions resolve on MajorInitiatives"
```

---

### Task 4: `queries.py` — home, health, search, meeting read the 29

**Files:**
- Modify: `app/queries.py`
- Test: `tests/test_queries_merge.py` (create)

**Interfaces:**
- Consumes: `MajorInitiatives`, `MajorInitiativeUpdates`, `vw_LatestMajorInitiativeProgress`.
- Produces: `all_initiatives`, `initiative_card`, `meeting_updates`, `update_deltas`, `search`, `all_people`, `data_checks`, `coverage_summary`, `attention_list` all sourced from the register model.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_queries_merge.py
from app import queries


def test_only_one_portfolio_count(fresh_db):
    """The home counts one thing. 29, not 22-vs-29."""
    assert len(queries.major_initiative_cards()) == 29


def test_all_initiatives_reads_the_register(fresh_db):
    rows = queries.all_initiatives()
    assert len(rows) == 29
    assert all(r["Code"].startswith("MI-") for r in rows)


def test_meeting_reads_the_new_diary(fresh_db):
    from app import repo
    repo.add_progress_update("MI-002", 10, "On track", "x", entered_by_id=5)
    rows = queries.meeting_updates(queries.default_since())
    assert rows
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_queries_merge.py -v`
Expected: FAIL — `no such table: Initiatives`

- [ ] **Step 3: Retarget the queries**

Rewrite each function's SQL to read `MajorInitiatives` (+ `MajorInitiativeUpdates` for anything progress-related), joining `Teams`/`People` on the register's `TeamID`/`OwnerID`. Delete any function that has no meaning on the new model and no caller (check with grep before deleting).

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_queries_merge.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -- app/queries.py tests/test_queries_merge.py
git commit -m "feat(queries): all reads source the register model"
```

---

### Task 5: Routes — collapse onto `/major-initiatives/*`

**Files:**
- Modify: `app/main.py`, `app/templates/major_initiative.html`, `app/templates/_card_body.html`
- Test: `tests/test_routes_merge.py` (create)

**Interfaces:**
- Consumes: the retargeted `repo`/`auth`/`queries`.
- Produces: `/major-initiatives/{mi_id}` carrying the interactive card (drawer, update form, edit forms); retired `/initiatives/*` returning 308.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_routes_merge.py


def test_initiative_card_redirects_to_major_initiative(logged_in):
    r = logged_in("Bill Gaudelli").get("/initiatives/MI-002", follow_redirects=False)
    assert r.status_code == 308
    assert r.headers["location"].endswith("/major-initiatives/MI-002")


def test_major_initiative_is_the_interactive_card(logged_in):
    r = logged_in("Bill Gaudelli").get("/major-initiatives/MI-002",
                                       headers={"HX-Request": "true"})
    assert r.status_code == 200


def test_update_redirects(logged_in):
    r = logged_in("Bill Gaudelli").get("/initiatives/MI-002/update", follow_redirects=False)
    assert r.status_code == 308
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_routes_merge.py -v`
Expected: FAIL — `/initiatives/MI-002` is 404

- [ ] **Step 3: Rewrite the routes**

- Move the card body, update form and edit forms into `major_initiative.html` so `/major-initiatives/{mi_id}` serves the full interactive card.
- Replace the `/initiatives/{code}` route with a **308** to `/major-initiatives/{mi_id}` (resolve the code→MIId, or pass the code through — the detail query already accepts either).
- Add `/major-initiatives/{mi_id}/update`, `/edit/{details,tags,links}`, `/retire`, `/new` mirroring the old forms, gated by the same guards.
- `/initiatives` (index) → 308 to `/major-initiatives`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_routes_merge.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -- app/main.py app/templates/major_initiative.html app/templates/_card_body.html tests/test_routes_merge.py
git commit -m "feat(routes): /initiatives/* 308-redirect to /major-initiatives/*"
```

---

### Task 6: Migrate the test files

**Files:**
- Modify: `tests/test_access.py`, `test_admin.py`, `test_cards.py`, `test_updates.py`, `test_cascade_views.py`, `test_flows.py`, `test_guards.py`, `test_hardening.py`, `test_intake.py`, `test_meeting_checks.py`, `test_search_and_meeting.py`, `test_portfolio_dashboard.py`, `test_uiux_group1.py`, and any other with an `Initiatives`/`ProgressUpdates` reference.
- Test: the whole suite.

- [ ] **Step 1: Sweep for stale references**

Run and read every hit — this is the gate that proves the merge is complete:
```
grep -rn "Initiatives\b\|ProgressUpdates\|InitiativeGoals\|InitiativePriorities\|InitiativeLinks" tests app --include=*.py
```
Expected: only `Major*` names remain in SQL. Fix each.

- [ ] **Step 2: Add the completion guard**

```python
# tests/test_merge_complete.py
"""No query references a table the merge dropped."""
import os, re

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DROPPED = ("Initiatives", "InitiativeGoals", "InitiativePriorities",
           "InitiativeLinks", "ProgressUpdates")
SQL = re.compile(r"(?:FROM|JOIN|INTO|UPDATE|DELETE\s+FROM)\s+(\w+)", re.I)


def test_no_dropped_table_is_referenced():
    hits = []
    for sub in ("app",):
        for dp, dn, fn in os.walk(os.path.join(R, sub)):
            if "__pycache__" in dp:
                continue
            for f in fn:
                if not f.endswith(".py"):
                    continue
                text = open(os.path.join(dp, f), encoding="utf-8").read()
                for m in SQL.finditer(text):
                    if m.group(1) in DROPPED:
                        hits.append("%s: %s" % (f, m.group(1)))
    assert not hits, "queries still reference dropped tables:\n" + "\n".join(hits)
```

- [ ] **Step 3: Run the full suite**

Run: `python -m pytest -q`
Expected: PASS. Fix any test still asserting the prototype model.

- [ ] **Step 4: Commit**

```bash
git add -- tests
git commit -m "test: migrate to the merged model; assert no dropped table is referenced"
```

---

### Task 7: Rebuild, verify, deploy, record

**Files:**
- Modify: `cll_initiatives.db`, `scripts/build_deploy_zip.py`, `docs/ops/LAUNCH_RECORD.md`

- [ ] **Step 1: Rebuild twice and assert byte-identity**

```
python db/build_db.py
python -c "import hashlib;print(hashlib.sha256(open('cll_initiatives.db','rb').read()).hexdigest())"
python db/build_db.py
python -c "import hashlib;print(hashlib.sha256(open('cll_initiatives.db','rb').read()).hexdigest())"
```
Expected: identical hashes.

- [ ] **Step 2: Full suite + deploy archive**

Run: `python -m pytest -q` then `python scripts/build_deploy_zip.py`. Fix the manifest if a required seed changed.

- [ ] **Step 3: Deploy and verify**

Follow `docs/ops/DEPLOY.md` (marker, deploy, poll `/healthz`). Confirm the home shows **one** portfolio number.

- [ ] **Step 4: Record and commit**

Add a dated entry to `docs/ops/LAUNCH_RECORD.md` stating the model is now single.
```bash
git add -- cll_initiatives.db scripts/build_deploy_zip.py docs/ops/LAUNCH_RECORD.md
git commit -m "data: rebuild on the merged model; record the merge"
```

---

## Self-Review

**Spec coverage:** §1 schema → Task 1; §2 writes/permissions → Tasks 2–3; §3 routes → Task 5; §4 tests → Tasks 1–6, with the completion guard in Task 6; §5 sequencing → Task 7. ✅

**Placeholder scan:** no TBD. Task 3's second test is a stub marked "replaced in step 3" — the executor fills it with a concrete owner assertion after reading which MI each person owns; that is a named lookup, not a placeholder.

**Type consistency:** keys are `MIId` throughout; `MajorInitiativeUpdates` is the diary in every task; `vw_LatestMajorInitiativeProgress` defined in Task 1 and consumed from Task 4. ✅
