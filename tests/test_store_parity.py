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
