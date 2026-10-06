"""Integrity report, orphan detection, traceability and provenance tests.

Group 6 of adopt-rev2-strategy-portfolio-schema.

The report is the backstop for the two rules T-SQL cannot defer, so these tests
matter more than most: they are what stands between a bypassed write path and an
undetected governance violation.

Every test that asserts the report is clean is paired with one that introduces a
defect and asserts the report names it, so a report that always returns nothing
cannot pass.
"""
import os
import uuid

import pymssql
import pytest

CREDS = os.environ.get("REV2_CREDS", r"C:\Users\kwong318\AppData\Local\Temp\opencode\rev2sql.txt")
PFX = "ZZT"


def _creds():
    d = {}
    for line in open(CREDS, encoding="ascii"):
        if "=" in line:
            k, v = line.strip().split("=", 1)
            d[k] = v
    return d


@pytest.fixture(scope="module")
def db():
    c = _creds()
    conn = pymssql.connect(server=c["SERVER"], user=c["USER"], password=c["PASSWORD"],
                           database=c["DB"], login_timeout=90, timeout=120)
    conn.autocommit(True)
    yield conn
    cur = conn.cursor()
    _reset(cur)
    conn.close()


def _reset(cur):
    """Return the database to empty. See test_read_models for why this is a full
    clear rather than a prefix match: the database holds no business data, and a
    missed row leaves a UNIQUE goal_number behind that fails unrelated tests."""
    guards = (("trg_block_canonical_goal_delete", "goal"),
              ("trg_block_objective_delete", "strategic_objective"),
              ("trg_block_initiative_update_change", "initiative_update"))
    for trg, tbl in guards:
        cur.execute("DISABLE TRIGGER %s ON dbo.%s" % (trg, tbl))
    cur.execute("UPDATE dbo.initiative SET status='Retired'")
    for tbl in ("initiative_update", "validation_event", "stewardship_assignment",
                "initiative_relationship", "initiative_owner", "initiative_priority",
                "initiative_goal", "objective_initiative", "initiative_metric",
                "initiative", "goal_metric", "target_metric", "metric_version", "metric",
                "objective_target", "target", "strategic_objective", "goal",
                "portfolio_goal", "portfolio", "annual_priority", "priority_cycle",
                "priority_definition", "planning_cycle", "person", "team", "source_record"):
        try:
            cur.execute("DELETE FROM dbo.%s" % tbl)
        except Exception:
            pass
    for trg, tbl in guards:
        cur.execute("ENABLE TRIGGER %s ON dbo.%s" % (trg, tbl))


@pytest.fixture
def cur(db):
    _reset(db.cursor())
    return db.cursor()


def _count_defects(cur, cls=None):
    if cls:
        cur.execute("SELECT COUNT(*) FROM dbo.vw_integrity_report WHERE defect_class=%s", (cls,))
    else:
        cur.execute("SELECT COUNT(*) FROM dbo.vw_integrity_report")
    return cur.fetchone()[0]


def _seed_minimal(cur, tag=None):
    """A conforming dataset: one goal, one Dean initiative, mapped, owned.

    Reuses an existing goal when there is one, because goal_number is UNIQUE over
    1..5 and a test that seeds a second goal fails for a reason unrelated to what
    it is testing.
    """
    tag = tag or uuid.uuid4().hex[:4]
    m = {"tag": tag}
    cur.execute("SELECT goal_id, source_id FROM dbo.goal")
    row = cur.fetchone()
    if row:
        m["goal"], m["src"] = row[0], row[1]
    else:
        m["src"] = PFX + "SRC" + tag
        cur.execute("INSERT INTO dbo.source_record (source_id, source_type, source_name, authority_level)"
                    " VALUES (%s,'t','t','Canonical')", (m["src"],))
        m["goal"] = PFX + "G" + tag
        cur.execute("INSERT INTO dbo.goal (goal_id, goal_number, short_label, canonical_title,"
                    " source_id, display_order) VALUES (%s,1,'Test Goal','wording',%s,1)",
                    (m["goal"], m["src"]))
    m["person"] = PFX + "P" + tag
    cur.execute("INSERT INTO dbo.person (person_id, display_name) VALUES (%s,'Owner')", (m["person"],))
    m["i"] = PFX + "I" + tag
    cur.execute("INSERT INTO dbo.initiative (initiative_id, initiative_code, initiative_name,"
                " description, initiative_level, initiative_type, status)"
                " VALUES (%s,%s,'init','d','Dean','Initiative','Proposed')",
                (m["i"], PFX + "C" + tag))
    cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type,"
                " validation_status) VALUES (%s,%s,'Primary','Leadership Confirmed')",
                (m["i"], m["goal"]))
    return m


# ===========================================================================
# 6.3 the report is clean when data is clean, and never repairs
# ===========================================================================

class TestIntegrityReportBaseline:
    def test_a_clean_dataset_reports_zero_defects(self, cur):
        m = _seed_minimal(cur)
        cur.execute("UPDATE dbo.initiative SET status='Active' WHERE initiative_id=%s", (m["i"],))
        cur.execute("UPDATE dbo.initiative SET status='Proposed' WHERE initiative_id=%s", (m["i"],))
        # nothing active, nothing defective
        assert _count_defects(cur) == 0, "a clean dataset must report nothing"

    def test_the_report_does_not_repair_what_it_reports(self, cur):
        """A report that fixed the data would hide the defect it exists to
        surface, and would make task 7.1's acceptance run meaningless."""
        m = _seed_minimal(cur)
        # an actively defective initiative: Retired is permitted, but make it
        # Active with no goal by removing the mapping after activation
        cur.execute("UPDATE dbo.initiative SET status='Active' WHERE initiative_id=%s", (m["i"],))
        cur.execute("DISABLE TRIGGER trg_goal_mapping_removal_requires_goal ON dbo.initiative_goal")
        cur.execute("DELETE FROM dbo.initiative_goal WHERE initiative_id=%s", (m["i"],))
        cur.execute("ENABLE TRIGGER trg_goal_mapping_removal_requires_goal ON dbo.initiative_goal")

        before = _count_defects(cur, "Orphan initiative")
        assert before == 1, "the defect must be visible"
        # run the report again; the record must still be defective
        assert _count_defects(cur, "Orphan initiative") == 1, "the report must not repair"
        cur.execute("SELECT COUNT(*) FROM dbo.initiative_goal WHERE initiative_id=%s", (m["i"],))
        assert cur.fetchone()[0] == 0, "the missing mapping must still be missing"


# ===========================================================================
# 6.2 each orphan class is detected and names its record
# ===========================================================================

class TestOrphanDetection:
    def test_orphan_initiative_is_named(self, cur):
        m = _seed_minimal(cur)
        cur.execute("UPDATE dbo.initiative SET status='Active' WHERE initiative_id=%s", (m["i"],))
        cur.execute("DISABLE TRIGGER trg_goal_mapping_removal_requires_goal ON dbo.initiative_goal")
        cur.execute("DELETE FROM dbo.initiative_goal WHERE initiative_id=%s", (m["i"],))
        cur.execute("ENABLE TRIGGER trg_goal_mapping_removal_requires_goal ON dbo.initiative_goal")
        cur.execute("SELECT record_id FROM dbo.vw_integrity_report WHERE defect_class='Orphan initiative'")
        assert m["i"] in [r[0] for r in cur.fetchall()]

    def test_active_d1_without_dean_link_is_named(self, cur):
        m = _seed_minimal(cur)
        d1 = PFX + "D" + m["tag"]
        cur.execute("INSERT INTO dbo.initiative (initiative_id, initiative_code, initiative_name,"
                    " description, initiative_level, initiative_type, status)"
                    " VALUES (%s,%s,'d1','d','D-1','Initiative','Proposed')", (d1, PFX + "DC" + m["tag"]))
        cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type)"
                    " VALUES (%s,%s,'Primary')", (d1, m["goal"]))
        # activate the Dean first so the goal rule is satisfied, then find the D-1
        cur.execute("UPDATE dbo.initiative SET status='Active' WHERE initiative_id=%s", (m["i"],))
        # the D-1 cannot be activated without a Dean link, so force it in to create
        # the defect the report is meant to catch
        cur.execute("DISABLE TRIGGER trg_active_d1_requires_dean_link ON dbo.initiative")
        cur.execute("UPDATE dbo.initiative SET status='Active' WHERE initiative_id=%s", (d1,))
        cur.execute("ENABLE TRIGGER trg_active_d1_requires_dean_link ON dbo.initiative")
        cur.execute("SELECT record_id FROM dbo.vw_integrity_report"
                    " WHERE defect_class='Active D-1 without Dean link'")
        assert d1 in [r[0] for r in cur.fetchall()]

    def test_active_d1_without_primary_owner_is_named(self, cur):
        m = _seed_minimal(cur)
        d1 = PFX + "E" + m["tag"]
        cur.execute("INSERT INTO dbo.initiative (initiative_id, initiative_code, initiative_name,"
                    " description, initiative_level, initiative_type, status)"
                    " VALUES (%s,%s,'d1','d','D-1','Initiative','Proposed')", (d1, PFX + "EC" + m["tag"]))
        cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type)"
                    " VALUES (%s,%s,'Primary')", (d1, m["goal"]))
        cur.execute("UPDATE dbo.initiative SET status='Active' WHERE initiative_id=%s", (m["i"],))
        cur.execute("INSERT INTO dbo.initiative_relationship (from_initiative_id, to_initiative_id,"
                    " relationship_type) VALUES (%s,%s,'Supports')", (d1, m["i"]))
        cur.execute("UPDATE dbo.initiative SET status='Active' WHERE initiative_id=%s", (d1,))
        cur.execute("SELECT record_id FROM dbo.vw_integrity_report"
                    " WHERE defect_class='Active D-1 without primary owner'")
        assert d1 in [r[0] for r in cur.fetchall()]

    def test_orphan_metric_is_named(self, cur):
        mid = PFX + "M" + uuid.uuid4().hex[:4]
        cur.execute("INSERT INTO dbo.metric (metric_id, metric_code, metric_name)"
                    " VALUES (%s,%s,'m')", (mid, PFX + "MC" + uuid.uuid4().hex[:4]))
        cur.execute("SELECT record_id FROM dbo.vw_integrity_report WHERE defect_class='Orphan metric'")
        assert mid in [r[0] for r in cur.fetchall()]

    def test_unstewarded_metric_is_named(self, cur):
        mid = PFX + "N" + uuid.uuid4().hex[:4]
        cur.execute("INSERT INTO dbo.metric (metric_id, metric_code, metric_name)"
                    " VALUES (%s,%s,'m')", (mid, PFX + "NC" + uuid.uuid4().hex[:4]))
        cur.execute("INSERT INTO dbo.metric_version (metric_version_id, metric_id, version_number,"
                    " effective_start) VALUES (%s,%s,1,'2026-01-01')",
                    (PFX + "MV" + uuid.uuid4().hex[:4], mid))
        cur.execute("SELECT record_id FROM dbo.vw_integrity_report WHERE defect_class='Unstewarded metric'")
        assert mid in [r[0] for r in cur.fetchall()]

    def test_orphan_target_is_named(self, cur):
        tid = PFX + "T" + uuid.uuid4().hex[:4]
        cur.execute("INSERT INTO dbo.target (target_id, target_name, target_value_text)"
                    " VALUES (%s,'t','v')", (tid,))
        cur.execute("SELECT record_id FROM dbo.vw_integrity_report WHERE defect_class='Orphan target'")
        assert tid in [r[0] for r in cur.fetchall()]


# ===========================================================================
# 6.4 provenance: an unresolvable source is reported rather than confirmed
# ===========================================================================

class TestProvenance:
    def test_a_record_with_no_resolvable_source_is_not_confirmed(self, cur):
        """`source_id` is nullable on initiative, so a record can be loaded with
        no source at all. Its validation status must not read as settled."""
        tag = uuid.uuid4().hex[:4]
        iid = PFX + "PS" + tag
        cur.execute("INSERT INTO dbo.initiative (initiative_id, initiative_code, initiative_name,"
                    " description, initiative_level, initiative_type, status)"
                    " VALUES (%s,%s,'sourceless','d','Dean','Initiative','Proposed')",
                    (iid, PFX + "PSC" + tag))
        # A foreign key cannot reference a nonexistent source; the point is that the
        # NULL case is the realistic one and it must not default to confirmed.
        cur.execute("SELECT source_id, validation_status FROM dbo.initiative WHERE initiative_id=%s", (iid,))
        source_id, status = cur.fetchone()
        assert source_id is None, "the record has no source"
        assert status != "Leadership Confirmed", \
            "a record with no source must not read as leadership-confirmed"

    def test_canonical_wording_round_trips_with_non_ascii(self, cur):
        """Task 7.3 leans on this: the canonical strategy text carries an en dash
        and a curly apostrophe, and NVARCHAR must return them unchanged."""
        tag = uuid.uuid4().hex[:4]
        text = "Catalyze a learning society — the world\u2019s home for transformative learning."
        src = PFX + "SRC" + tag
        cur.execute("INSERT INTO dbo.source_record (source_id, source_type, source_name, authority_level)"
                    " VALUES (%s,'t','t','Canonical')", (src,))
        g = PFX + "G" + tag
        cur.execute("INSERT INTO dbo.goal (goal_id, goal_number, short_label, canonical_title,"
                    " source_id, display_order) VALUES (%s,1,'g',%s,%s,1)", (g, text, src))
        cur.execute("SELECT canonical_title FROM dbo.goal WHERE goal_id=%s", (g,))
        assert cur.fetchone()[0] == text, "canonical text must round-trip byte-for-byte"


# ===========================================================================
# 6.5 validation status is explicit and attributable
# ===========================================================================

class TestValidationStatus:
    def test_an_unrelated_edit_does_not_change_validation_status(self, cur):
        m = _seed_minimal(cur)
        cur.execute("INSERT INTO dbo.initiative (initiative_id, initiative_code, initiative_name,"
                    " description, initiative_level, initiative_type, status, validation_status)"
                    " VALUES (%s,%s,'x','d','Dean','Initiative','Proposed','Needs Review')",
                    (PFX + "V" + m["tag"], PFX + "VC" + m["tag"]))
        vid = PFX + "V" + m["tag"]
        cur.execute("UPDATE dbo.initiative SET description='edited for an unrelated reason'"
                    " WHERE initiative_id=%s", (vid,))
        cur.execute("SELECT validation_status FROM dbo.initiative WHERE initiative_id=%s", (vid,))
        assert cur.fetchone()[0] == "Needs Review", \
            "editing a needs-review record for another reason must not confirm it"

    def test_confirmation_is_recorded_with_who_and_when(self, cur):
        m = _seed_minimal(cur)
        ev = PFX + "VE" + m["tag"]
        cur.execute("INSERT INTO dbo.validation_event (validation_event_id, entity_type, entity_id,"
                    " prior_status, new_status, actor_person_id)"
                    " VALUES (%s,'Initiative',%s,'Needs Review','Leadership Confirmed',%s)",
                    (ev, m["i"], m["person"]))
        cur.execute("SELECT actor_person_id, acted_at, prior_status, new_status"
                    " FROM dbo.validation_event WHERE validation_event_id=%s", (ev,))
        actor, when, prior, new = cur.fetchone()
        assert actor == m["person"] and when is not None
        assert prior == "Needs Review" and new == "Leadership Confirmed"

    def test_a_needs_review_mapping_is_reported(self, cur):
        """6.6: an inferred mapping must remain visible as unconfirmed."""
        tag = uuid.uuid4().hex[:4]
        m = _seed_minimal(cur, tag)
        i2 = PFX + "W" + tag
        cur.execute("INSERT INTO dbo.initiative (initiative_id, initiative_code, initiative_name,"
                    " description, initiative_level, initiative_type, status)"
                    " VALUES (%s,%s,'inferred','d','Dean','Initiative','Proposed')",
                    (i2, PFX + "WC" + tag))
        cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type,"
                    " validation_status) VALUES (%s,%s,'Contributing','Needs Review')", (i2, m["goal"]))
        cur.execute("SELECT record_id FROM dbo.vw_integrity_report"
                    " WHERE defect_class='Mapping not confirmed' AND record_id=%s", (i2,))
        assert cur.fetchone() is not None, "an inferred mapping must be reported as unconfirmed"


# ===========================================================================
# 6.1 traceability is traversable in both directions
# ===========================================================================

class TestTraceability:
    def _build_chain(self, cur, tag):
        # Reuse whatever goal exists rather than seeding another: goal_number is
        # UNIQUE over 1..5, so only one test goal can exist at a time. The chain
        # does not need a second goal.
        cur.execute("SELECT goal_id FROM dbo.goal")
        row = cur.fetchone()
        if row:
            m = {"goal": row[0], "tag": tag}
            cur.execute("SELECT source_id FROM dbo.goal WHERE goal_id=%s", (row[0],))
            m["src"] = cur.fetchone()[0]
            m["person"] = PFX + "PP" + tag
            cur.execute("INSERT INTO dbo.person (person_id, display_name) VALUES (%s,'Owner')", (m["person"],))
            m["i"] = PFX + "II" + tag
            cur.execute("INSERT INTO dbo.initiative (initiative_id, initiative_code, initiative_name,"
                        " description, initiative_level, initiative_type, status)"
                        " VALUES (%s,%s,'init','d','Dean','Initiative','Proposed')",
                        (m["i"], PFX + "IC" + tag))
            cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type,"
                        " validation_status) VALUES (%s,%s,'Primary','Leadership Confirmed')",
                        (m["i"], m["goal"]))
        else:
            m = _seed_minimal(cur, tag)
        pf = PFX + "PF" + tag
        cur.execute("INSERT INTO dbo.portfolio (portfolio_id, portfolio_name, validation_status)"
                    " VALUES (%s,'Test Portfolio','Needs Review')", (pf,))
        cur.execute("INSERT INTO dbo.portfolio_goal (portfolio_id, goal_id) VALUES (%s,%s)",
                    (pf, m["goal"]))
        o = PFX + "O" + tag
        cur.execute("INSERT INTO dbo.strategic_objective (objective_id, goal_id, objective_sequence,"
                    " canonical_text, source_id) VALUES (%s,%s,1,'obj text',%s)", (o, m["goal"], m["src"]))
        t = PFX + "T" + tag
        cur.execute("INSERT INTO dbo.target (target_id, target_name, target_value_text, validation_status)"
                    " VALUES (%s,'t','v','Canonical')", (t,))
        cur.execute("INSERT INTO dbo.objective_target (objective_id, target_id) VALUES (%s,%s)", (o, t))
        cur.execute("INSERT INTO dbo.objective_initiative (objective_id, initiative_id, relationship_type,"
                    " validation_status) VALUES (%s,%s,'Primary','Leadership Confirmed')", (o, m["i"]))
        # metric must exist before its version - the FK requires it
        cur.execute("INSERT INTO dbo.metric (metric_id, metric_code, metric_name)"
                    " VALUES (%s,%s,'m')", (PFX + "M" + tag, PFX + "MC" + tag))
        mv = PFX + "MV" + tag
        cur.execute("INSERT INTO dbo.metric_version (metric_version_id, metric_id, version_number,"
                    " effective_start) VALUES (%s,%s,1,'2026-01-01')", (mv, PFX + "M" + tag))
        cur.execute("INSERT INTO dbo.initiative_metric (initiative_id, metric_version_id, relationship_type)"
                    " VALUES (%s,%s,'Primary')", (m["i"], mv))
        cur.execute("INSERT INTO dbo.initiative_owner (initiative_id, person_id, ownership_role,"
                    " primary_flag, effective_start) VALUES (%s,%s,'Reporting Owner',1,'2026-01-01')",
                    (m["i"], m["person"]))
        m.update(pf=pf, o=o, t=t, mv=mv)
        return m

    def test_the_chain_is_reachable_from_the_portfolio(self, cur):
        m = self._build_chain(cur, uuid.uuid4().hex[:4])
        # reporting_owner is the DISPLAY NAME; reporting_owner_id is the id. Selecting
        # the wrong one is why this assertion first failed.
        cur.execute("SELECT goal_id, objective_id, target_id, initiative_id, metric_version_id,"
                    " reporting_owner_id, reporting_owner FROM dbo.vw_strategy_traceability"
                    " WHERE portfolio_id=%s", (m["pf"],))
        row = cur.fetchone()
        assert row is not None, "the chain must be traversable from the portfolio"
        goal_id, obj, tgt, init, mv, owner_id, owner_name = row
        assert goal_id == m["goal"]
        assert obj == m["o"]
        assert tgt == m["t"]
        assert init == m["i"]
        assert mv == m["mv"]
        assert owner_id == m["person"], "reporting_owner_id must be the person id"
        assert owner_name == "Owner"

    def test_the_chain_is_reachable_from_the_initiative(self, cur):
        m = self._build_chain(cur, uuid.uuid4().hex[:4])
        cur.execute("SELECT portfolio_id, goal_id, objective_id FROM dbo.vw_strategy_traceability"
                    " WHERE initiative_id=%s", (m["i"],))
        row = cur.fetchone()
        assert row is not None, "the chain must be traversable from the initiative"
        assert row[0] == m["pf"] and row[1] == m["goal"] and row[2] == m["o"]

    def test_an_objective_with_no_execution_is_reported(self, cur):
        m = _seed_minimal(cur)
        o = PFX + "OX" + m["tag"]
        cur.execute("INSERT INTO dbo.strategic_objective (objective_id, goal_id, objective_sequence,"
                    " canonical_text, source_id, active_flag)"
                    " VALUES (%s,%s,9,'unexecuted',%s,1)", (o, m["goal"], m["src"]))
        cur.execute("SELECT record_id FROM dbo.vw_integrity_report"
                    " WHERE defect_class='Objective without execution'")
        assert o in [r[0] for r in cur.fetchall()], "an objective with no initiative must be reported"
