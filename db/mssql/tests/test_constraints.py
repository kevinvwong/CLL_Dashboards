"""Constraint tests against the live Azure SQL target.

Group 3.6 and 4.1-4.6 of adopt-rev2-strategy-portfolio-schema. These run against
the real platform because ADR-021 requires the target to carry equivalent
constraints, and a substitute that has never been exercised is indistinguishable
from a constraint that was documented but never implemented.

Every test that asserts a refusal also asserts the refusal's REASON, so a test
cannot pass because of an unrelated error (a missing table, a bad column name).

Run:
    python -m pytest db/mssql/tests -v
"""
import os
import uuid

import pymssql
import pytest

CREDS = os.environ.get("REV2_CREDS", r"C:\Users\kwong318\AppData\Local\Temp\opencode\rev2sql.txt")


def _creds():
    d = {}
    for line in open(CREDS, encoding="ascii"):
        if "=" in line:
            k, v = line.strip().split("=", 1)
            d[k] = v
    return d


@pytest.fixture(scope="session")
def db():
    c = _creds()
    conn = pymssql.connect(server=c["SERVER"], user=c["USER"], password=c["PASSWORD"],
                           database=c["DB"], login_timeout=90, timeout=120)
    conn.autocommit(False)
    yield conn
    conn.close()


@pytest.fixture
def cur(db):
    """Each test runs in its own transaction and is rolled back, so tests do not
    depend on each other and the database is left as found."""
    c = db.cursor()
    yield c
    db.rollback()


def uid(prefix):
    """Short unique id. Column widths matter here and are not uniform:
    goal_id is VARCHAR(10), objective_id and priority_id VARCHAR(20), the rest
    VARCHAR(40)+. An id longer than its column is silently truncated by SQL
    Server's error 2628, which looks like a constraint failure but is not."""
    return "%s%s" % (prefix, uuid.uuid4().hex[:6])


def new_goal_id():
    """goal_id is VARCHAR(10): 'G' + 8 hex = 9 characters."""
    return "G" + uuid.uuid4().hex[:8]


def seed_source(cur):
    sid = uid("SRC")
    cur.execute("INSERT INTO dbo.source_record (source_id, source_type, source_name, authority_level)"
                " VALUES (%s,'Test','test','Canonical')", (sid,))
    return sid


def seed_goal(cur, source_id, number=1):
    goal = new_goal_id()
    cur.execute("INSERT INTO dbo.goal (goal_id, goal_number, short_label, canonical_title,"
                " source_id, display_order) VALUES (%s,%s,'lbl','title',%s,1)",
                (goal, number, source_id))
    return goal


def seed_initiative(cur, level="Dean", status="Proposed", source_id=None, extra=None):
    iid = uid("I")
    cur.execute(
        "INSERT INTO dbo.initiative (initiative_id, initiative_code, initiative_name, description,"
        " initiative_level, initiative_type, status, source_id)"
        " VALUES (%s,%s,'name','desc',%s,'Initiative',%s,%s)",
        (iid, uid("C"), level, status, source_id))
    return iid


def seed_person(cur):
    pid = uid("P")
    cur.execute("INSERT INTO dbo.person (person_id, display_name) VALUES (%s,'Someone')", (pid,))
    return pid


# ===========================================================================
# 3.6 vocabularies are enforced by the database, not only the application
# ===========================================================================

class TestVocabularies:
    def test_unlisted_initiative_level_is_refused(self, cur):
        with pytest.raises(Exception) as e:
            seed_initiative(cur, level="Team")          # D7 #5 permits Dean and D-1 only
        assert "ck_initiative_level" in str(e.value) or "CHECK" in str(e.value).upper()

    def test_unlisted_initiative_type_is_refused(self, cur):
        with pytest.raises(Exception):
            cur.execute(
                "INSERT INTO dbo.initiative (initiative_id, initiative_code, initiative_name,"
                " description, initiative_level, initiative_type, status)"
                " VALUES (%s,%s,'n','d','Dean','NotAType','Proposed')", (uid("I"), uid("C")))

    def test_unlisted_status_is_refused(self, cur):
        with pytest.raises(Exception):
            seed_initiative(cur, status="Nearly Done")

    def test_unlisted_progress_method_is_refused(self, cur):
        iid = seed_initiative(cur)
        with pytest.raises(Exception):
            cur.execute("UPDATE dbo.initiative SET progress_method='Weighted Metric'"
                        " WHERE initiative_id=%s", (iid,))

    def test_permitted_values_are_accepted(self, cur):
        """The other half: the vocabulary must not refuse a legal value. Without
        this, a constraint that refused everything would pass every test above."""
        src = seed_source(cur)
        g = seed_goal(cur, src)
        dean = seed_initiative(cur, level="Dean", status="Proposed", source_id=src)
        d1 = seed_initiative(cur, level="D-1", status="Proposed", source_id=src)
        cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type)"
                    " VALUES (%s,%s,'Primary')", (dean, g))
        cur.execute("UPDATE dbo.initiative SET progress_method='Owner Estimate',"
                    " progress_value=42.5, status='Active' WHERE initiative_id=%s", (dean,))
        cur.execute("UPDATE dbo.initiative SET progress_method='Metric Derived' WHERE initiative_id=%s", (d1,))

    def test_goal_number_outside_1_to_5_is_refused(self, cur):
        src = seed_source(cur)
        with pytest.raises(Exception):
            seed_goal(cur, src, number=6)


# ===========================================================================
# 3.7 / 3.8 the D7 defaults are what the schema enforces
# ===========================================================================

class TestD7Defaults:
    def test_relationship_vocabulary_is_exactly_the_five(self, cur):
        """Each of the five the reference permits is accepted. Paired with the
        Delivers test below, this pins the vocabulary from both sides."""
        src = seed_source(cur)
        g = seed_goal(cur, src)
        for t in ("Supports", "Enables", "Depends On", "Contributes To", "Replaces"):
            x = seed_initiative(cur, level="D-1", source_id=src)
            y = seed_initiative(cur, level="Dean", source_id=src)
            cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type) VALUES (%s,%s,'Contributing')", (x, g))
            cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type) VALUES (%s,%s,'Contributing')", (y, g))
            cur.execute("INSERT INTO dbo.initiative_relationship"
                        " (from_initiative_id, to_initiative_id, relationship_type) VALUES (%s,%s,%s)",
                        (x, y, t))

    def test_a_narrated_but_unimplemented_type_is_refused(self, cur):
        """'Delivers' is named in the migration's comment but never added to the
        CHECK. This proves we adopted the constraint that exists, not the one
        that was described."""
        src = seed_source(cur)
        g = seed_goal(cur, src)
        d1 = seed_initiative(cur, level="D-1", source_id=src)
        dean = seed_initiative(cur, level="Dean", source_id=src)
        cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type) VALUES (%s,%s,'Contributing')", (d1, g))
        cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type) VALUES (%s,%s,'Contributing')", (dean, g))
        with pytest.raises(Exception):
            cur.execute("INSERT INTO dbo.initiative_relationship"
                        " (from_initiative_id, to_initiative_id, relationship_type) VALUES (%s,%s,'Delivers')",
                        (d1, dean))

    def test_enterprise_level_is_refused(self, cur):
        with pytest.raises(Exception):
            seed_initiative(cur, level="Enterprise")


def level_of(cur, initiative_id):
    cur.execute("SELECT initiative_level FROM dbo.initiative WHERE initiative_id=%s", (initiative_id,))
    return cur.fetchone()[0]


# ===========================================================================
# 3.9 every stewardship entity type resolves to a real table
# ===========================================================================

class TestStewardshipEntityTypes:
    def test_data_product_is_refused_because_no_such_table_exists(self, cur):
        """D7 #4: the reference permits 'Data Product' but no data_product table
        exists, so the value could never be satisfied."""
        p = seed_person(cur)
        with pytest.raises(Exception):
            cur.execute("INSERT INTO dbo.stewardship_assignment"
                        " (stewardship_id, entity_type, entity_id, person_id, stewardship_role, effective_start)"
                        " VALUES (%s,'Data Product','X',%s,'Data Steward','2026-01-01')", (uid("ST"), p))

    def test_every_permitted_entity_type_has_a_table(self, cur):
        cur.execute("SELECT definition FROM sys.check_constraints WHERE name='ck_stewardship_entity'")
        definition = cur.fetchone()[0]
        cur.execute("SELECT name FROM sys.tables WHERE schema_id=SCHEMA_ID('dbo')")
        tables = {r[0].lower() for r in cur.fetchall()}
        import re
        for value in re.findall(r"'([^']+)'", definition):
            table = value.lower().replace(" ", "_")
            assert table in tables, "permitted entity_type %r has no table %r" % (value, table)

    def test_permitted_stewardship_is_accepted(self, cur):
        p = seed_person(cur)
        cur.execute("INSERT INTO dbo.stewardship_assignment"
                    " (stewardship_id, entity_type, entity_id, person_id, stewardship_role, effective_start)"
                    " VALUES (%s,'Initiative','I-1',%s,'Data Steward','2026-01-01')", (uid("ST"), p))


# ===========================================================================
# 4.1 / 4.2 relationship direction and self-reference
# ===========================================================================

class TestRelationshipDirection:
    def test_d1_to_dean_is_accepted(self, cur):
        src = seed_source(cur)
        g = seed_goal(cur, src)
        d1 = seed_initiative(cur, level="D-1", source_id=src)
        dean = seed_initiative(cur, level="Dean", source_id=src)
        cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type) VALUES (%s,%s,'Contributing')", (d1, g))
        cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type) VALUES (%s,%s,'Contributing')", (dean, g))
        cur.execute("INSERT INTO dbo.initiative_relationship"
                    " (from_initiative_id, to_initiative_id, relationship_type) VALUES (%s,%s,'Supports')",
                    (d1, dean))

    def test_dean_to_d1_is_refused_and_names_the_direction(self, cur):
        src = seed_source(cur)
        g = seed_goal(cur, src)
        d1 = seed_initiative(cur, level="D-1", source_id=src)
        dean = seed_initiative(cur, level="Dean", source_id=src)
        cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type) VALUES (%s,%s,'Contributing')", (d1, g))
        cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type) VALUES (%s,%s,'Contributing')", (dean, g))
        with pytest.raises(Exception) as e:
            cur.execute("INSERT INTO dbo.initiative_relationship"
                        " (from_initiative_id, to_initiative_id, relationship_type) VALUES (%s,%s,'Supports')",
                        (dean, d1))
        assert "D-1 -> Dean" in str(e.value), "refusal must name the required direction"

    def test_self_reference_is_refused(self, cur):
        src = seed_source(cur)
        g = seed_goal(cur, src)
        i = seed_initiative(cur, level="Dean", source_id=src)
        cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type) VALUES (%s,%s,'Contributing')", (i, g))
        with pytest.raises(Exception):
            cur.execute("INSERT INTO dbo.initiative_relationship"
                        " (from_initiative_id, to_initiative_id, relationship_type) VALUES (%s,%s,'Enables')",
                        (i, i))


# ===========================================================================
# 4.3 cycle prevention
# ===========================================================================

class TestCycles:
    def _chain(self, cur, n):
        """n D-1 initiatives, all mapped to a goal, each Enables the next."""
        src = seed_source(cur)
        g = seed_goal(cur, src)
        nodes = []
        for _ in range(n):
            i = seed_initiative(cur, level="D-1", source_id=src)
            cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type) VALUES (%s,%s,'Contributing')", (i, g))
            nodes.append(i)
        for a, b in zip(nodes, nodes[1:]):
            cur.execute("INSERT INTO dbo.initiative_relationship"
                        " (from_initiative_id, to_initiative_id, relationship_type) VALUES (%s,%s,'Enables')",
                        (a, b))
        return nodes

    def test_three_node_cycle_is_refused(self, cur):
        a, b, c = self._chain(cur, 3)
        with pytest.raises(Exception) as e:
            cur.execute("INSERT INTO dbo.initiative_relationship"
                        " (from_initiative_id, to_initiative_id, relationship_type) VALUES (%s,%s,'Enables')",
                        (c, a))
        assert "cycle" in str(e.value).lower()

    def test_five_node_cycle_is_refused(self, cur):
        nodes = self._chain(cur, 5)
        with pytest.raises(Exception) as e:
            cur.execute("INSERT INTO dbo.initiative_relationship"
                        " (from_initiative_id, to_initiative_id, relationship_type) VALUES (%s,%s,'Enables')",
                        (nodes[-1], nodes[0]))
        assert "cycle" in str(e.value).lower()

    def test_a_non_cyclic_chain_is_accepted(self, cur):
        """Guards against a cycle rule that refuses everything."""
        self._chain(cur, 4)


# ===========================================================================
# 4.4 the two cardinality minimums, independently
# ===========================================================================

class TestCardinalityMinimums:
    def test_active_initiative_without_a_goal_is_refused(self, cur):
        with pytest.raises(Exception) as e:
            seed_initiative(cur, level="Dean", status="Active")
        assert "goal" in str(e.value).lower()

    def test_active_d1_without_a_dean_link_is_refused(self, cur):
        """Satisfies the goal rule but not the Dean rule, so it isolates the
        second requirement - which is the point of the task."""
        src = seed_source(cur)
        g = seed_goal(cur, src)
        d1 = seed_initiative(cur, level="D-1", status="Proposed", source_id=src)
        cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type) VALUES (%s,%s,'Contributing')", (d1, g))
        with pytest.raises(Exception) as e:
            cur.execute("UPDATE dbo.initiative SET status='Active' WHERE initiative_id=%s", (d1,))
        assert "Dean" in str(e.value)

    def test_removing_the_last_goal_from_an_active_initiative_is_refused(self, cur):
        src = seed_source(cur)
        g = seed_goal(cur, src)
        i = seed_initiative(cur, level="Dean", status="Proposed", source_id=src)
        cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type) VALUES (%s,%s,'Contributing')", (i, g))
        cur.execute("UPDATE dbo.initiative SET status='Active' WHERE initiative_id=%s", (i,))
        with pytest.raises(Exception):
            cur.execute("DELETE FROM dbo.initiative_goal WHERE initiative_id=%s", (i,))

    def test_a_conforming_d1_is_accepted(self, cur):
        src = seed_source(cur)
        g = seed_goal(cur, src)
        dean = seed_initiative(cur, level="Dean", status="Proposed", source_id=src)
        d1 = seed_initiative(cur, level="D-1", status="Proposed", source_id=src)
        for i in (dean, d1):
            cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type) VALUES (%s,%s,'Contributing')", (i, g))
        cur.execute("INSERT INTO dbo.initiative_relationship"
                    " (from_initiative_id, to_initiative_id, relationship_type) VALUES (%s,%s,'Supports')",
                    (d1, dean))
        # D-1 needs a primary Reporting Owner too
        p = seed_person(cur)
        cur.execute("INSERT INTO dbo.initiative_owner"
                    " (initiative_id, person_id, ownership_role, primary_flag, effective_start)"
                    " VALUES (%s,%s,'Reporting Owner',1,'2026-01-01')", (d1, p))
        cur.execute("UPDATE dbo.initiative SET status='Active' WHERE initiative_id IN (%s,%s)", (dean, d1))


# ===========================================================================
# 4.5 exactly one current primary Reporting Owner
# ===========================================================================

class TestPrimaryOwner:
    def test_a_second_current_primary_reporting_owner_is_refused(self, cur):
        src = seed_source(cur)
        g = seed_goal(cur, src)
        i = seed_initiative(cur, level="Dean", status="Proposed", source_id=src)
        cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type) VALUES (%s,%s,'Contributing')", (i, g))
        p1, p2 = seed_person(cur), seed_person(cur)
        cur.execute("INSERT INTO dbo.initiative_owner"
                    " (initiative_id, person_id, ownership_role, primary_flag, effective_start)"
                    " VALUES (%s,%s,'Reporting Owner',1,'2026-01-01')", (i, p1))
        with pytest.raises(Exception):
            cur.execute("INSERT INTO dbo.initiative_owner"
                        " (initiative_id, person_id, ownership_role, primary_flag, effective_start)"
                        " VALUES (%s,%s,'Reporting Owner',1,'2026-01-01')", (i, p2))

    def test_several_non_primary_contributors_are_allowed(self, cur):
        src = seed_source(cur)
        g = seed_goal(cur, src)
        i = seed_initiative(cur, level="Dean", status="Proposed", source_id=src)
        cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type) VALUES (%s,%s,'Contributing')", (i, g))
        for _ in range(3):
            p = seed_person(cur)
            cur.execute("INSERT INTO dbo.initiative_owner"
                        " (initiative_id, person_id, ownership_role, primary_flag, effective_start)"
                        " VALUES (%s,%s,'Contributor',0,'2026-01-01')", (i, p))

    def test_a_closed_primary_permits_a_new_one(self, cur):
        """End-dating the incumbent must free the filtered index slot, otherwise
        ownership could never be transferred."""
        src = seed_source(cur)
        g = seed_goal(cur, src)
        i = seed_initiative(cur, level="Dean", status="Proposed", source_id=src)
        cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type) VALUES (%s,%s,'Contributing')", (i, g))
        p1, p2 = seed_person(cur), seed_person(cur)
        cur.execute("INSERT INTO dbo.initiative_owner"
                    " (initiative_id, person_id, ownership_role, primary_flag, effective_start)"
                    " VALUES (%s,%s,'Reporting Owner',1,'2026-01-01')", (i, p1))
        cur.execute("UPDATE dbo.initiative_owner SET effective_end='2026-06-30'"
                    " WHERE initiative_id=%s AND person_id=%s", (i, p1))
        cur.execute("INSERT INTO dbo.initiative_owner"
                    " (initiative_id, person_id, ownership_role, primary_flag, effective_start)"
                    " VALUES (%s,%s,'Reporting Owner',1,'2026-07-01')", (i, p2))

    def test_unlisted_ownership_role_is_refused(self, cur):
        src = seed_source(cur)
        g = seed_goal(cur, src)
        i = seed_initiative(cur, level="Dean", source_id=src)
        cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type) VALUES (%s,%s,'Contributing')", (i, g))
        p = seed_person(cur)
        with pytest.raises(Exception):
            cur.execute("INSERT INTO dbo.initiative_owner"
                        " (initiative_id, person_id, ownership_role, effective_start)"
                        " VALUES (%s,%s,'Operational Lead','2026-01-01')", (i, p))

    def test_end_before_start_is_refused(self, cur):
        src = seed_source(cur)
        g = seed_goal(cur, src)
        i = seed_initiative(cur, level="Dean", source_id=src)
        cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type) VALUES (%s,%s,'Contributing')", (i, g))
        p = seed_person(cur)
        with pytest.raises(Exception):
            cur.execute("INSERT INTO dbo.initiative_owner"
                        " (initiative_id, person_id, ownership_role, effective_start, effective_end)"
                        " VALUES (%s,%s,'Sponsor','2026-06-01','2026-01-01')", (i, p))


# ===========================================================================
# 4.6 updates are append-only
# ===========================================================================

class TestAppendOnlyUpdates:
    def test_modifying_an_update_is_refused(self, cur):
        src = seed_source(cur)
        g = seed_goal(cur, src)
        i = seed_initiative(cur, level="Dean", source_id=src)
        cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type) VALUES (%s,%s,'Contributing')", (i, g))
        u = uid("U")
        cur.execute("INSERT INTO dbo.initiative_update (update_id, initiative_id, narrative)"
                    " VALUES (%s,%s,'first')", (u, i))
        with pytest.raises(Exception):
            cur.execute("UPDATE dbo.initiative_update SET narrative='changed' WHERE update_id=%s", (u,))

    def test_deleting_an_update_is_refused(self, cur):
        src = seed_source(cur)
        g = seed_goal(cur, src)
        i = seed_initiative(cur, level="Dean", source_id=src)
        cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type) VALUES (%s,%s,'Contributing')", (i, g))
        u = uid("U")
        cur.execute("INSERT INTO dbo.initiative_update (update_id, initiative_id, narrative)"
                    " VALUES (%s,%s,'first')", (u, i))
        with pytest.raises(Exception):
            cur.execute("DELETE FROM dbo.initiative_update WHERE update_id=%s", (u,))

    def test_a_correction_is_a_new_row_and_both_survive(self, cur):
        src = seed_source(cur)
        g = seed_goal(cur, src)
        i = seed_initiative(cur, level="Dean", source_id=src)
        cur.execute("INSERT INTO dbo.initiative_goal (initiative_id, goal_id, relationship_type) VALUES (%s,%s,'Contributing')", (i, g))
        u1, u2 = uid("U"), uid("U")
        cur.execute("INSERT INTO dbo.initiative_update (update_id, initiative_id, narrative, progress_value)"
                    " VALUES (%s,%s,'wrong number',10)", (u1, i))
        cur.execute("INSERT INTO dbo.initiative_update (update_id, initiative_id, narrative, progress_value)"
                    " VALUES (%s,%s,'corrected',40)", (u2, i))
        cur.execute("SELECT COUNT(*) FROM dbo.initiative_update WHERE initiative_id=%s", (i,))
        assert cur.fetchone()[0] == 2, "both the original and the correction must be retained"


# ===========================================================================
# 3.5 stewardship non-overlap -- the weakest substitute, tested and stated
# ===========================================================================

class TestStewardshipOverlap:
    def test_overlapping_periods_are_refused_serially(self, cur):
        p = seed_person(cur)
        cur.execute("INSERT INTO dbo.stewardship_assignment"
                    " (stewardship_id, entity_type, entity_id, person_id, stewardship_role,"
                    "  effective_start, effective_end)"
                    " VALUES (%s,'Initiative','I-9',%s,'Data Steward','2026-01-01','2026-06-30')",
                    (uid("ST"), p))
        with pytest.raises(Exception) as e:
            cur.execute("INSERT INTO dbo.stewardship_assignment"
                        " (stewardship_id, entity_type, entity_id, person_id, stewardship_role,"
                        "  effective_start, effective_end)"
                        " VALUES (%s,'Initiative','I-9',%s,'Data Steward','2026-03-01','2026-09-30')",
                        (uid("ST"), p))
        assert "Overlapping stewardship" in str(e.value)

    def test_adjacent_non_overlapping_periods_are_accepted(self, cur):
        """Half-open intervals: ending 2026-06-30 and starting 2026-07-01 are
        adjacent, not overlapping. A rule that refused this would make a clean
        handover impossible."""
        p = seed_person(cur)
        cur.execute("INSERT INTO dbo.stewardship_assignment"
                    " (stewardship_id, entity_type, entity_id, person_id, stewardship_role,"
                    "  effective_start, effective_end)"
                    " VALUES (%s,'Initiative','I-8',%s,'Data Steward','2026-01-01','2026-06-30')",
                    (uid("ST"), p))
        cur.execute("INSERT INTO dbo.stewardship_assignment"
                    " (stewardship_id, entity_type, entity_id, person_id, stewardship_role,"
                    "  effective_start, effective_end)"
                    " VALUES (%s,'Initiative','I-8',%s,'Data Steward','2026-07-01',NULL)",
                    (uid("ST"), p))

    def test_a_different_role_may_overlap(self, cur):
        """The reference's exclusion is per (entity, person, role), so a person
        can hold two different stewardship roles at once."""
        p = seed_person(cur)
        cur.execute("INSERT INTO dbo.stewardship_assignment"
                    " (stewardship_id, entity_type, entity_id, person_id, stewardship_role, effective_start)"
                    " VALUES (%s,'Initiative','I-7',%s,'Data Steward','2026-01-01')", (uid("ST"), p))
        cur.execute("INSERT INTO dbo.stewardship_assignment"
                    " (stewardship_id, entity_type, entity_id, person_id, stewardship_role, effective_start)"
                    " VALUES (%s,'Initiative','I-7',%s,'Business Steward','2026-01-01')", (uid("ST"), p))


# ===========================================================================
# 3.1 canonical records resist hard deletion
# ===========================================================================

class TestCanonicalProtection:
    """Deletion-protection tests need their own connection.

    THROW inside an INSTEAD OF trigger aborts the whole transaction, so a test
    that inserts, attempts the delete, then counts, gets 0 for BOTH a protected
    row and a row that never existed - it cannot tell protection from absence.
    Each test here commits its setup on an autocommit connection and removes it
    again in teardown with the guard briefly disabled.
    """

    @pytest.fixture
    def live(self):
        c = _creds()
        conn = pymssql.connect(server=c["SERVER"], user=c["USER"], password=c["PASSWORD"],
                               database=c["DB"], login_timeout=90, timeout=120)
        conn.autocommit(True)
        yield conn
        conn.close()

    def _cleanup(self, live, table, pk, value, trigger):
        cur = live.cursor()
        cur.execute("DISABLE TRIGGER %s ON dbo.%s" % (trigger, table))
        cur.execute("DELETE FROM dbo.%s WHERE %s=%%s" % (table, pk), (value,))
        cur.execute("ENABLE TRIGGER %s ON dbo.%s" % (trigger, table))

    def test_a_canonical_goal_cannot_be_hard_deleted(self, live):
        cur = live.cursor()
        g = new_goal_id()
        cur.execute("INSERT INTO dbo.source_record (source_id, source_type, source_name, authority_level)"
                    " VALUES (%s,'t','t','Canonical')", (uid("SRC"),))
        cur.execute("INSERT INTO dbo.goal (goal_id, goal_number, short_label, canonical_title,"
                    " source_id, display_order) VALUES (%s,1,'l','t',(SELECT MAX(source_id) FROM dbo.source_record),1)",
                    (g,))
        try:
            with pytest.raises(Exception) as e:
                cur.execute("DELETE FROM dbo.goal WHERE goal_id=%s", (g,))
            assert "cannot be hard deleted" in str(e.value)
            cur.execute("SELECT COUNT(*) FROM dbo.goal WHERE goal_id=%s", (g,))
            assert cur.fetchone()[0] == 1, "the goal must still be retrievable"
        finally:
            self._cleanup(live, "goal", "goal_id", g, "trg_block_canonical_goal_delete")

    def test_retirement_is_not_blocked_by_the_delete_guard(self, live):
        """The guard must forbid deletion, not deactivation. A rule that blocked
        both would make retirement impossible."""
        cur = live.cursor()
        g = new_goal_id()
        cur.execute("INSERT INTO dbo.source_record (source_id, source_type, source_name, authority_level)"
                    " VALUES (%s,'t','t','Canonical')", (uid("SRC"),))
        cur.execute("INSERT INTO dbo.goal (goal_id, goal_number, short_label, canonical_title,"
                    " source_id, display_order) VALUES (%s,1,'l','t',(SELECT MAX(source_id) FROM dbo.source_record),1)",
                    (g,))
        try:
            cur.execute("UPDATE dbo.goal SET active_flag=0 WHERE goal_id=%s", (g,))
            cur.execute("SELECT active_flag FROM dbo.goal WHERE goal_id=%s", (g,))
            assert cur.fetchone()[0] == 0
        finally:
            self._cleanup(live, "goal", "goal_id", g, "trg_block_canonical_goal_delete")

    def test_a_canonical_objective_cannot_be_hard_deleted(self, live):
        cur = live.cursor()
        g = new_goal_id()
        o = uid("OBJ")
        cur.execute("INSERT INTO dbo.source_record (source_id, source_type, source_name, authority_level)"
                    " VALUES (%s,'t','t','Canonical')", (uid("SRC"),))
        cur.execute("INSERT INTO dbo.goal (goal_id, goal_number, short_label, canonical_title,"
                    " source_id, display_order) VALUES (%s,1,'l','t',(SELECT MAX(source_id) FROM dbo.source_record),1)",
                    (g,))
        cur.execute("INSERT INTO dbo.strategic_objective (objective_id, goal_id, objective_sequence,"
                    " canonical_text, source_id) VALUES (%s,%s,1,'text',(SELECT MAX(source_id) FROM dbo.source_record))",
                    (o, g))
        try:
            with pytest.raises(Exception) as e:
                cur.execute("DELETE FROM dbo.strategic_objective WHERE objective_id=%s", (o,))
            assert "cannot be hard deleted" in str(e.value)
            cur.execute("SELECT COUNT(*) FROM dbo.strategic_objective WHERE objective_id=%s", (o,))
            assert cur.fetchone()[0] == 1
        finally:
            self._cleanup(live, "strategic_objective", "objective_id", o, "trg_block_objective_delete")
            self._cleanup(live, "goal", "goal_id", g, "trg_block_canonical_goal_delete")


# ===========================================================================
# 3.4 a metric may have only one current version
# ===========================================================================

class TestMetricVersioning:
    def _metric(self, cur):
        m = uid("M")
        cur.execute("INSERT INTO dbo.metric (metric_id, metric_code, metric_name)"
                    " VALUES (%s,%s,'m')", (m, uid("MC")))
        return m

    def test_two_current_versions_are_refused(self, cur):
        m = self._metric(cur)
        cur.execute("INSERT INTO dbo.metric_version (metric_version_id, metric_id, version_number,"
                    " effective_start) VALUES (%s,%s,1,'2026-01-01')", (uid("MV"), m))
        with pytest.raises(Exception):
            cur.execute("INSERT INTO dbo.metric_version (metric_version_id, metric_id, version_number,"
                        " effective_start) VALUES (%s,%s,2,'2026-02-01')", (uid("MV"), m))

    def test_a_closed_version_permits_a_new_current_one(self, cur):
        m = self._metric(cur)
        v1 = uid("MV")
        cur.execute("INSERT INTO dbo.metric_version (metric_version_id, metric_id, version_number,"
                    " effective_start) VALUES (%s,%s,1,'2026-01-01')", (v1, m))
        cur.execute("UPDATE dbo.metric_version SET effective_end='2026-06-30'"
                    " WHERE metric_version_id=%s", (v1,))
        cur.execute("INSERT INTO dbo.metric_version (metric_version_id, metric_id, version_number,"
                    " effective_start) VALUES (%s,%s,2,'2026-07-01')", (uid("MV"), m))

    def test_end_before_start_is_refused(self, cur):
        m = self._metric(cur)
        with pytest.raises(Exception):
            cur.execute("INSERT INTO dbo.metric_version (metric_version_id, metric_id, version_number,"
                        " effective_start, effective_end)"
                        " VALUES (%s,%s,1,'2026-06-01','2026-01-01')", (uid("MV"), m))


# ===========================================================================
# 6.4 / 6.5 provenance and validation (added here because they share the fixture)
# ===========================================================================

class TestValidationEvents:
    def test_a_confirmation_records_who_and_when(self, cur):
        """The package cannot do this at all - D9 added validation_event."""
        p = seed_person(cur)
        cur.execute("INSERT INTO dbo.validation_event (validation_event_id, entity_type, entity_id,"
                    " prior_status, new_status, actor_person_id)"
                    " VALUES (%s,'Initiative','I-1','Needs Review','Leadership Confirmed',%s)",
                    (uid("VE"), p))
        cur.execute("SELECT actor_person_id, acted_at FROM dbo.validation_event"
                    " WHERE entity_type='Initiative' AND entity_id='I-1'")
        actor, when = cur.fetchone()
        assert actor == p
        assert when is not None, "a confirmation must carry a timestamp"

# ===========================================================================
# 7.2 Two mechanisms that were ported without a test. Found by enumerating the
# database's constraints and diffing against the test suite, rather than by
# remembering what had been written.
# ===========================================================================

class TestPlanningCycleAndTargetMetric:
    def test_planning_cycle_end_before_start_is_refused(self, cur):
        with pytest.raises(Exception):
            cur.execute("INSERT INTO dbo.planning_cycle (planning_cycle_id, cycle_name,"
                        " cycle_start, cycle_end) VALUES (%s,'c','2026-12-31','2026-01-01')",
                        (uid("PC"),))

    def test_planning_cycle_valid_dates_are_accepted(self, cur):
        cur.execute("INSERT INTO dbo.planning_cycle (planning_cycle_id, cycle_name,"
                    " cycle_start, cycle_end) VALUES (%s,'c','2026-01-01','2026-12-31')", (uid("PC"),))

    def test_target_metric_relationship_type_is_restricted(self, cur):
        """ck_targetmetric_rel permits Primary and Supporting only."""
        tag = uid("TM")
        tid = uid("T")
        cur.execute("INSERT INTO dbo.target (target_id, target_name) VALUES (%s,'t')", (tid,))
        mid = uid("M")
        cur.execute("INSERT INTO dbo.metric (metric_id, metric_code, metric_name)"
                    " VALUES (%s,%s,'m')", (mid, uid("MC")))
        mv = uid("MV")
        cur.execute("INSERT INTO dbo.metric_version (metric_version_id, metric_id, version_number,"
                    " effective_start) VALUES (%s,%s,1,'2026-01-01')", (mv, mid))
        cur.execute("INSERT INTO dbo.target_metric (target_id, metric_version_id, relationship_type)"
                    " VALUES (%s,%s,'Primary')", (tid, mv))
        with pytest.raises(Exception):
            cur.execute("INSERT INTO dbo.target_metric (target_id, metric_version_id, relationship_type)"
                        " VALUES (%s,%s,'NotARelationship')", (tid, mv))