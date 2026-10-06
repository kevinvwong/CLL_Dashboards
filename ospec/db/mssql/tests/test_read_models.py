"""Read-model tests (group 5) against the live Azure SQL target.

These check the read models' behaviour: that a goal list and a priority list
return the same record, that current state follows the latest update rather than
the cached column, and that no view invents a rolled-up progress figure.

A note on test data. Everything this module creates is tagged with a single
prefix so cleanup can find it exactly rather than by guesswork. An earlier version
used `LIKE 'I%'` for initiatives while creating ids like `DA...`, so the purge
silently missed the rows blocking it and one stale UNIQUE goal_number row then
failed 35 tests. Cleanup runs at setup as well as teardown, because setup can
raise and when it does teardown never runs.
"""
import os
import uuid

import pymssql
import pytest

CREDS = os.environ.get("REV2_CREDS", r"C:\Users\kwong318\AppData\Local\Temp\opencode\rev2sql.txt")

# Every row this module creates uses this prefix, on every table. Cleanup is a
# prefix match on this and nothing else, so it can never miss or overreach.
PFX = "ZZT"


def _creds():
    d = {}
    for line in open(CREDS, encoding="ascii"):
        if "=" in line:
            k, v = line.strip().split("=", 1)
            d[k] = v
    return d


def _purge(cur):
    """Remove this module's test rows, in an order the guards permit.

    Order matters and is not arbitrary:
      1. disable the three guards that refuse DELETE on principle
      2. retire initiatives, so the goal and dean-link guards stop objecting to
         unlinking them (they only protect ACTIVE rows)
      3. delete children before parents
      4. re-enable the guards
    `validation_event` is append-only by intent but has no guard, so it deletes
    normally.
    """
    guards = (
        ("trg_block_canonical_goal_delete", "goal"),
        ("trg_block_objective_delete", "strategic_objective"),
        ("trg_block_initiative_update_change", "initiative_update"),
    )
    for trg, tbl in guards:
        cur.execute("DISABLE TRIGGER %s ON dbo.%s" % (trg, tbl))

    # Retire first: the goal and Dean-link guards protect ACTIVE initiatives and
    # refuse unlinking one, so rows must be parked before their links go.
    cur.execute("UPDATE dbo.initiative SET status='Retired'")

    # This database was provisioned solely for this change and holds no business
    # data - the package ships canonical strategy and ZERO operational rows (see
    # ../rev2/inventory-absent.md). So the cleanup clears these tables outright
    # rather than pattern-matching test ids. An earlier prefix-matching version
    # was wrong twice: it missed rows it had created under a different naming
    # scheme, and each miss left a UNIQUE goal_number behind that then failed
    # every other test in the suite.
    for tbl in ("initiative_update", "validation_event", "stewardship_assignment",
                "initiative_relationship", "initiative_owner", "initiative_priority",
                "initiative_goal", "objective_initiative", "initiative_metric",
                "initiative", "goal_metric", "target_metric", "metric_version",
                "metric", "objective_target", "target", "strategic_objective",
                "goal", "portfolio_goal", "portfolio", "annual_priority",
                "priority_cycle", "priority_definition", "planning_cycle", "person", "team",
                "source_record"):
        try:
            cur.execute("DELETE FROM dbo.%s" % tbl)
        except Exception:
            # a table that does not exist yet, or a guard we have not disabled,
            # must not abort the whole cleanup
            pass

    for trg, tbl in guards:
        cur.execute("ENABLE TRIGGER %s ON dbo.%s" % (trg, tbl))


@pytest.fixture(scope="module")
def seeded():
    """A small conforming dataset, committed, torn down at the end of the module.

    Committed rather than rolled back because the read models are views over
    tables and the assertions are about what they return, not about refusals.
    """
    c = _creds()
    conn = pymssql.connect(server=c["SERVER"], user=c["USER"], password=c["PASSWORD"],
                           database=c["DB"], login_timeout=90, timeout=120)
    conn.autocommit(True)
    cur = conn.cursor()

    _purge(cur)                       # idempotent: setup may have crashed last time

    tag = uuid.uuid4().hex[:4]
    m = {"tag": tag}

    m["src"] = PFX + "SRC" + tag
    cur.execute("INSERT INTO dbo.source_record (source_id, source_type, source_name, authority_level)"
                " VALUES (%s,'t','t','Canonical')", (m["src"],))

    # goal_number must be 1..5 and UNIQUE. Only one test goal exists at a time
    # because _purge clears the previous one first.
    m["goal"] = PFX + "G" + tag
    cur.execute("INSERT INTO dbo.goal (goal_id, goal_number, short_label, canonical_title,"
                " source_id, display_order) VALUES (%s,1,'Test Goal','test wording',%s,1)",
                (m["goal"], m["src"]))

    m["prio"] = PFX + "P" + tag
    cur.execute("INSERT INTO dbo.annual_priority (priority_id, priority_code, priority_name,"
                " planning_period, display_order) VALUES (%s,%s,'Data','FY2027',1)",
                (m["prio"], PFX + "PC" + tag))

    m["owner"] = PFX + "PERO" + tag
    m["steward"] = PFX + "PERS" + tag
    cur.execute("INSERT INTO dbo.person (person_id, display_name) VALUES (%s,'Owner Person')", (m["owner"],))
    cur.execute("INSERT INTO dbo.person (person_id, display_name) VALUES (%s,'Steward Person')", (m["steward"],))

    # ORDER: proposed -> map -> link -> owner -> activate.
    # The reference defers the cardinality check to COMMIT so it can insert an
    # Active initiative first; T-SQL has no deferred constraint (DEVIATIONS.md #4),
    # so prerequisites come first here.
    m["d1"] = PFX + "I" + tag
    cur.execute("INSERT INTO dbo.initiative (initiative_id, initiative_code, initiative_name,"
                " description, initiative_level, initiative_type, status, source_id)"
                " VALUES (%s,%s,'D-1 initiative','desc','D-1','Initiative','Proposed',%s)",
                (m["d1"], PFX + "C" + tag, m["src"]))
    cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type)"
                " VALUES (%s,%s,'Primary')", (m["d1"], m["goal"]))
    cur.execute("INSERT INTO dbo.initiative_priority (initiative_id, priority_id, relationship_type)"
                " VALUES (%s,%s,'Primary')", (m["d1"], m["prio"]))

    m["deans"] = []
    for i in (1, 2):
        code = PFX + "D" + str(i) + tag
        cur.execute("INSERT INTO dbo.initiative (initiative_id, initiative_code, initiative_name,"
                    " description, initiative_level, initiative_type, status, source_id)"
                    " VALUES (%s,%s,%s,'desc','Dean','Initiative','Proposed',%s)",
                    (code, code, "Dean initiative %d" % i, m["src"]))
        cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type)"
                    " VALUES (%s,%s,'Primary')", (code, m["goal"]))
        m["deans"].append(code)

    for code in m["deans"]:
        cur.execute("INSERT INTO dbo.initiative_relationship (from_initiative_id, to_initiative_id,"
                    " relationship_type) VALUES (%s,%s,'Supports')", (m["d1"], code))

    cur.execute("INSERT INTO dbo.initiative_owner (initiative_id, person_id, ownership_role,"
                " primary_flag, effective_start) VALUES (%s,%s,'Reporting Owner',1,'2026-01-01')",
                (m["d1"], m["owner"]))

    for t in (m["d1"],) + tuple(m["deans"]):
        cur.execute("UPDATE dbo.initiative SET status='Active' WHERE initiative_id=%s", (t,))

    # An update saying 40% while the cached column says something else, so the
    # read model can be shown to prefer the history.
    #
    # NOTE: initiative.status and initiative_update.status_at_update are TWO
    # DIFFERENT VOCABULARIES and the schema correctly refuses to mix them.
    #   initiative.status            -> Proposed, Active, On Hold, Completed, Retired
    #   update.status_at_update      -> a progress report: "On track", "At risk", ...
    # Writing 'On track' into initiative.status is refused by ck_initiative_status.
    # The cached column below therefore holds only a stale PERCENT, which is the
    # part a naive implementation would actually get wrong.
    m["u1"] = PFX + "U1" + tag
    cur.execute("INSERT INTO dbo.initiative_update (update_id, initiative_id, updated_by_person_id,"
                " narrative, progress_value, status_at_update)"
                " VALUES (%s,%s,%s,'latest word',40,'At risk')", (m["u1"], m["d1"], m["owner"]))
    cur.execute("UPDATE dbo.initiative SET progress_value=99 WHERE initiative_id=%s",
                (m["d1"],))

    m["st"] = PFX + "ST" + tag
    cur.execute("INSERT INTO dbo.stewardship_assignment (stewardship_id, entity_type, entity_id,"
                " person_id, stewardship_role, effective_start)"
                " VALUES (%s,'Initiative',%s,%s,'Data Steward','2026-01-01')",
                (m["st"], m["d1"], m["steward"]))

    yield conn, m

    _purge(cur)
    conn.close()


def _delete_update(cur, update_id):
    """Remove a test update with the append-only guard briefly disabled.

    initiative_update is immutable by design (ADR-010), so its guard refuses
    DELETE. That is the guard working, not a bug: only test cleanup may bypass it,
    and only here.
    """
    cur.execute("DISABLE TRIGGER trg_block_initiative_update_change ON dbo.initiative_update")
    cur.execute("DELETE FROM dbo.initiative_update WHERE update_id=%s", (update_id,))
    cur.execute("ENABLE TRIGGER trg_block_initiative_update_change ON dbo.initiative_update")


class _Session:
    """A cursor plus the fixture's metadata.

    pymssql's Cursor refuses arbitrary attribute assignment (__slots__), so the
    test data cannot simply be hung off it.
    """

    def __init__(self, conn, m):
        self.cur = conn.cursor()
        self.m = m

    def execute(self, *a, **kw):
        return self.cur.execute(*a, **kw)

    def fetchone(self, *a, **kw):
        return self.cur.fetchone(*a, **kw)

    def fetchall(self, *a, **kw):
        return self.cur.fetchall(*a, **kw)


@pytest.fixture
def cur(seeded):
    conn, m = seeded
    return _Session(conn, m)


def _make_extra(cur, m, suffix, level="Dean", status="Proposed"):
    iid = PFX + 'X' + suffix + m['tag']
    cur.execute("INSERT INTO dbo.initiative (initiative_id, initiative_code, initiative_name,"
                " description, initiative_level, initiative_type, status)"
                " VALUES (%s,%s,'extra','d',%s,'Initiative',%s)",
                (iid, iid, level, status))
    return iid


# ===========================================================================
# 5.1 a goal list and a priority list return the same underlying records
# ===========================================================================

class TestGoalAndPriorityAgree:
    def test_the_same_initiative_is_reachable_from_both(self, cur):
        m = cur.m
        cur.execute("SELECT initiative_code, initiative_name, status_current, progress_current,"
                    " owner_name FROM dbo.vw_goal_initiatives WHERE goal_id=%s"
                    " AND initiative_id=%s", (m["goal"], m["d1"]))
        via_goal = cur.fetchone()
        cur.execute("SELECT initiative_code, initiative_name, status_current, progress_current,"
                    " owner_name FROM dbo.vw_priority_initiatives WHERE priority_id=%s"
                    " AND initiative_id=%s", (m["prio"], m["d1"]))
        via_prio = cur.fetchone()
        assert via_goal is not None, "the goal list must return the initiative"
        assert via_prio is not None, "the priority list must return the initiative"
        assert via_goal == via_prio, "both lists must return an identical record"

    def test_a_priority_is_reachable_without_any_goal(self, cur):
        m = cur.m
        i = _make_extra(cur, m, "PO")
        cur.execute("INSERT INTO dbo.initiative_priority (initiative_id, priority_id, relationship_type)"
                    " VALUES (%s,%s,'Supporting')", (i, m["prio"]))
        # No activation: rule K1 forbids an Active initiative with no goal, and the
        # point of this test is that the priority lens works without a goal. The
        # read models filter on active_flag, not status, so the initiative is
        # visible either way.
        cur.execute("SELECT COUNT(*) FROM dbo.vw_priority_initiatives WHERE initiative_id=%s", (i,))
        assert cur.fetchone()[0] == 1, "a priority-only initiative appears in the priority list"
        cur.execute("SELECT COUNT(*) FROM dbo.vw_goal_initiatives WHERE initiative_id=%s", (i,))
        assert cur.fetchone()[0] == 0, "and in no goal list"


# ===========================================================================
# 5.2 current state is derived from the latest update
# ===========================================================================

class TestCurrentStateIsDerived:
    def test_the_view_reports_the_update_not_the_cached_column(self, cur):
        m = cur.m
        cur.execute("SELECT progress_current, status_current, no_update_yet"
                    " FROM dbo.vw_initiative_current WHERE initiative_id=%s", (m["d1"],))
        progress, status, no_update = cur.fetchone()
        assert progress == 40, "must follow the update (40), not the cached column (99)"
        assert status == "At risk"
        assert no_update == 0

    def test_posting_an_update_moves_the_derived_value(self, cur):
        m = cur.m
        u = PFX + "U2" + m["tag"]
        cur.execute("INSERT INTO dbo.initiative_update (update_id, initiative_id, updated_by_person_id,"
                    " narrative, progress_value, status_at_update, update_date)"
                    " VALUES (%s,%s,%s,'newer',75,'On track',DATEADD(day,1,SYSDATETIME()))",
                    (u, m["d1"], m["owner"]))
        cur.execute("SELECT progress_current, status_current FROM dbo.vw_initiative_current"
                    " WHERE initiative_id=%s", (m["d1"],))
        progress, status = cur.fetchone()
        assert progress == 75 and status == "On track"
        _delete_update(cur, u)

    def test_no_update_yet_is_flagged_and_not_reported_as_zero(self, cur):
        """The spec case the seed data cannot exercise: an initiative with no
        update must be distinguishable from one reported as zero."""
        m = cur.m
        i = _make_extra(cur, m, "NU")
        cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type)"
                    " VALUES (%s,%s,'Primary')", (i, m["goal"]))
        cur.execute("SELECT progress_current, no_update_yet FROM dbo.vw_initiative_current"
                    " WHERE initiative_id=%s", (i,))
        progress, no_update = cur.fetchone()
        assert no_update == 1, "the absence of an update must be visible"
        assert progress is None, "and must not be shown as zero"


# ===========================================================================
# 5.3 a D-1 supporting two Dean initiatives returns both
# ===========================================================================

class TestRelationships:
    def test_two_parents_are_both_returned(self, cur):
        m = cur.m
        cur.execute("SELECT related_code FROM dbo.vw_initiative_relationships"
                    " WHERE initiative_id=%s AND direction='Outgoing' AND relationship_type='Supports'"
                    " ORDER BY related_code", (m["d1"],))
        parents = [r[0] for r in cur.fetchall()]
        assert len(parents) == 2, "both Dean initiatives must appear, not just one"
        assert set(parents) == set(m["deans"])

    def test_the_parent_sees_the_child_as_incoming(self, cur):
        m = cur.m
        # Compare against related_initiative_id, not related_code: an id is
        # 'ZZTI....' and a code is 'ZZTC....', so comparing a code to m["d1"]
        # is never true.
        cur.execute("SELECT related_initiative_id, direction FROM dbo.vw_initiative_relationships"
                    " WHERE initiative_id=%s", (m["deans"][0],))
        rows = cur.fetchall()
        assert any(r[0] == m["d1"] and r[1] == "Incoming" for r in rows), \
            "the Dean initiative must see the D-1 as an incoming relationship"


# ===========================================================================
# 5.4 a person who owns nothing still resolves meaningfully
# ===========================================================================

class TestPersonPortfolio:
    def test_an_owner_sees_their_initiative(self, cur):
        m = cur.m
        cur.execute("SELECT COUNT(*) FROM dbo.vw_person_portfolio"
                    " WHERE person_id=%s AND initiative_id IS NOT NULL", (m["owner"],))
        assert cur.fetchone()[0] >= 1

    def test_a_steward_who_owns_nothing_still_returns_a_row(self, cur):
        """The Kevin case: a steward who owns no initiative and manages nobody
        must not get a blank page."""
        m = cur.m
        cur.execute("SELECT COUNT(*) FROM dbo.vw_person_portfolio WHERE person_id=%s", (m["steward"],))
        assert cur.fetchone()[0] >= 1, "the person row must exist even with no work attached"

    def test_a_steward_has_stewardship_content(self, cur):
        m = cur.m
        cur.execute("SELECT entity_id, stewardship_role FROM dbo.vw_person_stewardship"
                    " WHERE person_id=%s AND entity_id LIKE %s", (m["steward"], PFX + "%"))
        rows = cur.fetchall()
        assert rows, "a steward's page must have something to show"
        assert rows[0][0] == m["d1"]


# ===========================================================================
# 5.5 no view computes an aggregate parent progress
# ===========================================================================

class TestNoRollup:
    def test_no_view_definition_aggregates_progress(self, cur):
        """D4 / AC-08: parent progress stays independent until an approved rollup
        rule exists. An average over progress_value is the signature of a rollup,
        so its absence is asserted rather than assumed."""
        cur.execute("""
            SELECT v.name, m.definition
            FROM sys.views v
            JOIN sys.sql_modules m ON m.object_id = v.object_id
            WHERE v.schema_id = SCHEMA_ID('dbo')""")
        rows = cur.fetchall()
        assert len(rows) >= 8, "expected to inspect every view, saw %d" % len(rows)
        offenders = []
        for name, definition in rows:
            body = " ".join(definition.split()).upper()
            for token in ("AVG(", "AVG (", "SUM(", "SUM ("):
                if token in body:
                    offenders.append((name, token))
        assert not offenders, "these views compute a rollup: %s" % offenders

    def test_parent_progress_is_unaffected_by_a_child_update(self, cur):
        m = cur.m
        cur.execute("SELECT progress_current FROM dbo.vw_initiative_current WHERE initiative_id=%s",
                    (m["deans"][0],))
        before = cur.fetchone()[0]
        u = PFX + "U3" + m["tag"]
        cur.execute("INSERT INTO dbo.initiative_update (update_id, initiative_id, updated_by_person_id,"
                    " narrative, progress_value, status_at_update, update_date)"
                    " VALUES (%s,%s,%s,'child moved',90,'Complete',DATEADD(day,2,SYSDATETIME()))",
                    (u, m["d1"], m["owner"]))
        cur.execute("SELECT progress_current FROM dbo.vw_initiative_current WHERE initiative_id=%s",
                    (m["deans"][0],))
        after = cur.fetchone()[0]
        assert before == after, "a child's progress must not move the parent's"
        _delete_update(cur, u)
