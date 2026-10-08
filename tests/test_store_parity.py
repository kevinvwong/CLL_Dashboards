"""The two stores agree (change `adopt-rev2-store`, parity tests).

Each ported read is run under sqlite (the app's local file) and under mssql (the
live Rev2 store, reached with MSSQL_* from .env) and the results are compared.
These tests are skipped when the Rev2 store is not configured, so the suite runs
identically on a machine with no Azure SQL credentials.

The two stores were seeded to hold the same logical data (db/build_rev2_seed.py),
so a faithful translation returns the same rows on both. A mismatch means the
port is wrong, not that the data drifted - see the change's Risks section.
"""
import pytest

from app.config import Config


def _rev2_available() -> bool:
    cfg = Config()
    return bool(cfg.MSSQL_SERVER and cfg.MSSQL_USER and cfg.MSSQL_PASSWORD)


# Skip the whole module when Rev2 is unconfigured (a dev box without MSSQL_*).
pytestmark = pytest.mark.skipif(
    not _rev2_available(),
    reason="Rev2 store not configured (MSSQL_* empty in .env)",
)


@pytest.fixture()
def both():
    """Open one connection to each store; close both afterwards."""
    from app.db import connect

    sq = connect(provider="sqlite")
    ms = connect(provider="mssql")
    try:
        yield sq, ms
    finally:
        sq.close()
        try:
            ms.close()
        except Exception:
            pass


def test_goal_tiles_parity(both):
    from app import port

    sq, ms = both
    a = port.goal_tiles(sq)
    b = port.goal_tiles(ms)
    assert [(g["GoalNumber"], g["ShortName"], g["InitiativeCount"]) for g in a] == \
           [(g["GoalNumber"], g["ShortName"], g["InitiativeCount"]) for g in b]


def test_priority_tiles_parity(both):
    from app import port

    sq, ms = both
    a = {p["Code"]: p for p in port.priority_tiles(sq)}
    b = {p["Code"]: p for p in port.priority_tiles(ms)}
    assert a.keys() == b.keys()
    for code in a:
        assert a[code]["PriorityName"] == b[code]["PriorityName"], code
        assert a[code]["InitiativeCount"] == b[code]["InitiativeCount"], code
        assert a[code]["PlanYear"] == b[code]["PlanYear"], code


def test_plan_years_parity(both):
    from app import port

    sq, ms = both
    assert port.plan_years(sq) == port.plan_years(ms)


def test_current_plan_year_and_provenance(both):
    from app import port

    sq, ms = both
    assert port.current_plan_year(sq) == port.current_plan_year(ms)
    assert port.dataset_provenance(sq) == port.dataset_provenance(ms)


def test_goal_and_priority_lookups(both):
    from app import port

    sq, ms = both
    a = port.goal_by_number(sq, 3)
    b = port.goal_by_number(ms, 3)
    assert a is not None and b is not None
    assert a["GoalNumber"] == b["GoalNumber"]
    assert a["ShortName"] == b["ShortName"]

    a = port.priority_by_name(sq, "Data")
    b = port.priority_by_name(ms, "Data")
    assert a is not None and b is not None
    assert a["PriorityName"] == b["PriorityName"] == "Data"
    assert a["PlanYear"] == b["PlanYear"]


def test_milestones_parity(both):
    """Milestones, the biggest reconciliation lift, agree on both stores."""
    from app import port

    sq, ms = both
    year = port.current_plan_year(ms) or 2027
    a = port.milestones_for_year(sq, year)
    b = port.milestones_for_year(ms, year)
    assert a.keys() == b.keys(), "a priority has milestones on one store only"
    for code in a:
        assert [(m["Name"], m["Status"]) for m in a[code]] == \
               [(m["Name"], m["Status"]) for m in b[code]], code


def test_app_config_read_from_rev2(both):
    """app_meta lives on Rev2 now: both engines resolve the same value from
    their own store (no sqlite fallback under mssql)."""
    from app import port

    sq, ms = both
    assert port._appmeta(ms, "current_plan_year") == \
           port._appmeta(sq, "current_plan_year") == "2027"
    assert port._appmeta(ms, "dataset_provenance") == \
           port._appmeta(sq, "dataset_provenance") == "mock"


# --- group 3: cascade + index -------------------------------------------


def _key(row):
    # the public key is the canon MI-### on both stores
    return row["Code"]


def test_goal_rows_parity(both):
    from app import port

    sq, ms = both
    for gn in (1, 2, 3, 4, 5):
        a = {(_key(r), r["InitiativeName"], r["Owner"]) for r in port.goal_rows(sq, gn)}
        b = {(_key(r), r["InitiativeName"], r["Owner"]) for r in port.goal_rows(ms, gn)}
        assert a == b, f"goal {gn} differs"


def test_priority_rows_parity(both):
    from app import port

    sq, ms = both
    for name in ("Identity", "Innovation", "Pathways", "Scale", "Data", "Culture"):
        a = {(_key(r), r["InitiativeName"], r["PlanYear"]) for r in port.priority_rows(sq, name)}
        b = {(_key(r), r["InitiativeName"], r["PlanYear"]) for r in port.priority_rows(ms, name)}
        assert a == b, f"priority {name} differs"


def test_all_initiatives_parity(both):
    from app import port

    sq, ms = both
    a = port.all_initiatives(sq)
    b = port.all_initiatives(ms)
    assert len(a) == len(b) == 29
    ak = {(_key(r), r["InitiativeName"], r["Owner"], r["Status"]) for r in a}
    bk = {(_key(r), r["InitiativeName"], r["Owner"], r["Status"]) for r in b}
    assert ak == bk
    # tag collection must join identically on each engine
    ag, ap = port.initiative_tag_names(sq)
    bg, bp = port.initiative_tag_names(ms)
    aid_to_code = {r["InitiativeID"]: r["Code"] for r in a}
    bid_to_code = {r["InitiativeID"]: r["Code"] for r in b}
    agg = {aid_to_code[i]: sorted(v) for i, v in ag.items()}
    bgg = {bid_to_code[i]: sorted(v) for i, v in bg.items()}
    assert agg == bgg
    app_ = {aid_to_code[i]: sorted(v) for i, v in ap.items()}
    bpp = {bid_to_code[i]: sorted(v) for i, v in bp.items()}
    assert app_ == bpp


def test_all_people_parity(both):
    from app import port

    sq, ms = both
    a, _ = port.all_people(sq)
    b, _ = port.all_people(ms)
    an = {(p["PersonID"], p["Name"]) for p in a}
    bn = {(p["PersonID"], p["Name"]) for p in b}
    assert an == bn


def test_admin_semantics_agree(both):
    """is_admin is role-based by PlatformAdmin (auth.is_admin reads the role; the
    stored People.IsAdmin is only an honored migration fallback). The port derives
    the Rev2 bit from person_role/role. Assert the PORT's answer matches the
    role-derived answer on each store — i.e. 'has the PlatformAdmin role' agrees
    across stores."""
    from app import port

    sq, ms = both
    # sqlite's role-derived admin set, from PeopleRoles + Roles (auth's source).
    sq_admins = {r["PersonID"] for r in sq.execute(
        "SELECT DISTINCT pr.PersonID FROM PeopleRoles pr JOIN Roles r "
        " ON r.RoleID = pr.RoleID WHERE r.Name IN ('PlatformAdmin')")}
    ms_people, _ = port.all_people(ms)
    ms_admins = {p["PersonID"] for p in ms_people if p["IsAdmin"]}
    assert sq_admins == ms_admins
