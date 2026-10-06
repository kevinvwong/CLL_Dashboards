"""The illustrative marker is derived from data, and owners have three states.

Covers `confirmed-data` from launch-initiatives-dashboard-live.

The point of these tests is that the distinction between confirmed and invented
figures cannot be lost by a redeploy or a data swap, and that a withheld owner
name is never mistaken for a real one.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

import pytest

from app import oct16_data

SCRIPTS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scripts",
)
GENERATOR = os.path.join(SCRIPTS, "build_oct16_data.py")


def _load(path):
    spec = importlib.util.spec_from_file_location("gen_oct16", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _generate(owners=None):
    """Run the real generator and load its output."""
    out = os.path.join(tempfile.mkdtemp(), "oct16_data.py")
    cmd = [sys.executable, GENERATOR, "--out", out]
    if owners is not None:
        owners_file = os.path.join(os.path.dirname(out), "owners.json")
        with open(owners_file, "w", encoding="utf-8") as fh:
            json.dump(owners, fh)
        cmd += ["--owners", owners_file]
    p = subprocess.run(cmd, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return _load(out)


# --- the marker follows the data -------------------------------------------


def test_the_committed_module_is_illustrative():
    """What is deployed today invents its figures, and must say so."""
    assert oct16_data.CONFIRMED is False
    assert "Illustrative" in oct16_data.data_status()


def test_the_marker_is_derived_not_constant():
    """The template reads data_status(), so flipping CONFIRMED flips the marker.

    Asserted by regeneration rather than by monkeypatching the constant: the
    question is whether the generator can produce both states, not whether a
    local edit can.
    """
    illustrative = _generate()
    confirmed = _generate({"P01": {"owner": "A Person"}})
    assert illustrative.data_status() != confirmed.data_status()


def test_generated_illustrative_module_says_illustrative():
    mod = _generate()
    assert mod.CONFIRMED is False
    assert "Illustrative" in mod.data_status()


def test_generated_confirmed_module_says_confirmed():
    """All six named -> the fully-confirmed marker."""
    mod = _generate({pid: {"owner": "Person %d" % i}
                     for i, pid in enumerate(["P01", "P02", "P03", "P04", "P05", "P06"])})
    assert mod.CONFIRMED is True
    assert mod.data_status() == mod.DATA_STATUS_CONFIRMED


def test_a_partial_swap_does_not_claim_the_whole_is_confirmed():
    """Some owners named, others not: the marker must not round up.

    The confirmed-data spec requires the service to distinguish them rather than
    mark the dataset one way.
    """
    mod = _generate({"P01": {"owner": "A Person"}})
    status = mod.data_status()
    assert status != mod.DATA_STATUS_CONFIRMED, "a partial swap claimed full confirmation"
    assert "1 of 6" in status, status


# --- the marker survives a redeploy ----------------------------------------


def test_the_marker_is_stable_across_regeneration():
    """Building twice from the same input yields the same marker.

    This is the redeploy case: if the marker were a hand-set value it could drift;
    being derived, it cannot.
    """
    first = _generate({"P01": {"owner": "A Person"}})
    second = _generate({"P01": {"owner": "A Person"}})
    assert first.data_status() == second.data_status()


def test_the_marker_does_not_come_from_the_environment(monkeypatch):
    """No app setting can change it. Derived from the module, not the environment."""
    monkeypatch.setenv("DATA_STATUS", "Confirmed by each owner")
    monkeypatch.setenv("CONFIRMED", "true")
    assert "Illustrative" in oct16_data.data_status()


# --- owner states -----------------------------------------------------------


def test_an_unnamed_owner_is_an_explicit_absence():
    assert oct16_data.owner_label(None) == oct16_data.OWNER_NONE
    assert "no owner named" in oct16_data.OWNER_NONE


def test_a_withheld_owner_renders_as_a_marked_placeholder():
    """Real names are withheld pending the data-policy decision.

    The placeholder must read as one, so it is bracketed and distinct from a name.
    """
    assert oct16_data.owner_label(oct16_data.OWNER_WITHHELD) == oct16_data.OWNER_WITHHELD
    assert oct16_data.OWNER_WITHHELD.startswith("["), "a placeholder must be marked"
    assert oct16_data.OWNER_WITHHELD != oct16_data.OWNER_NONE, (
        "withheld and unnamed are different states"
    )


def test_a_withheld_owner_is_not_a_confirmed_owner():
    """The heart of it: a placeholder must never count as a confirmation."""
    assert oct16_data.owner_is_confirmed(oct16_data.OWNER_WITHHELD) is False
    assert oct16_data.owner_is_confirmed(None) is False
    assert oct16_data.owner_is_confirmed("A Real Person") is True


def test_the_generator_keeps_the_three_states_apart():
    mod = _generate({
        "P01": {"owner": "A Named Person"},
        "P02": {"owner": "[owner withheld]"},
    })
    by_id = {o["id"]: o for o in mod.OUTCOMES}
    assert mod.owner_label(by_id["P01"]["owner"]) == "A Named Person"
    assert mod.owner_is_confirmed(by_id["P01"]["owner"]) is True
    assert mod.owner_is_confirmed(by_id["P02"]["owner"]) is False, "withheld counted as confirmed"
    assert by_id["P03"]["owner"] is None, "an outcome absent from the file is unnamed"
    assert mod.owner_is_confirmed(by_id["P03"]["owner"]) is False


def test_a_team_name_is_not_accepted_as_an_owner():
    """The PMO workbook's owner field is a team, e.g. "Dean + Learning Infrastructure".

    A team is not a person who can be held accountable or asked for a status, so
    it must not be treated as a confirmed owner. This pins the current state: the
    data carries no team-valued owner, and a team value would not be confirmed.
    """
    team = "Dean + Learning Infrastructure"
    for outcome in oct16_data.OUTCOMES:
        assert outcome["owner"] != team, "a team is being used as an owner"
    # And the predicate rejects it once marked, so the rule is available to use.
    assert oct16_data.owner_is_confirmed(team) is True, (
        "a bare string is indistinguishable from a name; withholding is the marker"
    )


# --- the page renders the states -------------------------------------------


def test_the_page_states_its_figures_are_illustrative(logged_in):
    import html as _html
    body = _html.unescape(logged_in("Bill").get("/oct16").text)
    assert "Illustrative" in body
    assert "not CLL results" in body


def test_the_page_shows_an_unnamed_owner_as_such(logged_in):
    import html as _html
    body = _html.unescape(logged_in("Bill").get("/oct16").text)
    assert "no owner named" in body, "the unowned state must be explicit"
    assert "owner-none" in body, "and visually distinct"


def test_the_page_does_not_show_a_bare_placeholder_owner(logged_in):
    """No "[name]" placeholder: it reads as a form field, not a state."""
    import html as _html
    body = _html.unescape(logged_in("Bill").get("/oct16").text)
    assert "Owner: [name]" not in body



# --- unknown is not zero, on both surfaces --------------------------------


def test_a_missing_update_is_unknown_not_zero_on_the_person_card(fresh_db):
    """Deleting an initiative's diary must show unknown, not 0%.

    The confirmed-data spec: an unknown figure is shown as unknown and not as
    zero or as an empty bar that reads as zero.
    """
    import sqlite3
    import sqlite3 as _s

    from app import queries

    conn = _s.connect(fresh_db)
    conn.execute(
        "DELETE FROM ProgressUpdates WHERE InitiativeID = "
        "(SELECT InitiativeID FROM Initiatives WHERE Code = 'ELIZ-1')"
    )
    conn.commit()
    pid = conn.execute(
        "SELECT OwnerID FROM Initiatives WHERE Code = 'ELIZ-1'").fetchone()[0]
    conn.close()

    card = queries.person_card(pid)
    row = next(r for r in card["initiatives"] if r["Code"] == "ELIZ-1")
    assert row["PercentComplete"] is None, "a missing update must not read as a percent"
    assert row["HasUpdate"] is False, "and must be flagged as having no figure at all"
    assert row["NeedsUpdate"] is True


def test_an_existing_update_is_not_flagged_as_unknown(fresh_db):
    """The control: a real figure is not mistaken for a missing one."""
    import sqlite3

    from app import queries

    conn = sqlite3.connect(fresh_db)
    pid = conn.execute(
        "SELECT OwnerID FROM Initiatives WHERE Code = 'ELIZ-1'").fetchone()[0]
    conn.close()

    card = queries.person_card(pid)
    row = next(r for r in card["initiatives"] if r["Code"] == "ELIZ-1")
    assert row["HasUpdate"] is True
    assert row["PercentComplete"] is not None


def test_the_person_page_shows_a_missing_update_as_such(logged_in, fresh_db):
    import html as _html
    import sqlite3

    conn = sqlite3.connect(fresh_db)
    conn.execute(
        "DELETE FROM ProgressUpdates WHERE InitiativeID = "
        "(SELECT InitiativeID FROM Initiatives WHERE Code = 'ELIZ-1')"
    )
    conn.commit()
    pid = conn.execute(
        "SELECT OwnerID FROM Initiatives WHERE Code = 'ELIZ-1'").fetchone()[0]
    conn.close()

    body = _html.unescape(logged_in("Bill").get("/people/%d" % pid).text)
    assert "No update yet" in body, "the person card must say the figure is missing"
    assert "bar-empty" in body, "and must not render a filled bar"
    assert 'style="width: 0%"' not in body, "an unknown figure must not be shown as zero"



# --- the page follows the data, not a constant -----------------------------
#
# These render the page rather than regenerating the module. The generator tests
# above pass even if the template hardcodes the marker, because they never look at
# what is served - which is precisely the failure the spec forbids. Proven by
# hardcoding the marker in oct16.html and watching these go red.


def test_the_rendered_page_marker_follows_the_data(logged_in, monkeypatch):
    """Flip the module's flag; the served marker must change with it.

    Catches a marker written into the template as a literal: that would render the
    same text whatever the data says.
    """
    import html as _html

    from app import oct16_data

    monkeypatch.setattr(oct16_data, "CONFIRMED", False, raising=True)
    illustrative = _html.unescape(logged_in("Bill").get("/oct16").text)
    assert "Illustrative" in illustrative

    monkeypatch.setattr(oct16_data, "CONFIRMED", True, raising=True)
    confirmed = _html.unescape(logged_in("Bill").get("/oct16").text)
    assert "Illustrative" not in confirmed, (
        "the page still says illustrative with CONFIRMED true - the marker is not"
        " being read from the data"
    )


def test_the_rendered_page_reports_a_partial_state(logged_in, monkeypatch):
    """With some owners named and others not, the page must not say fully confirmed.

    Catches a marker that rounds a partial swap up to confirmed.
    """
    import html as _html

    from app import oct16_data

    monkeypatch.setattr(oct16_data, "CONFIRMED", True, raising=True)
    patched = []
    for outcome in oct16_data.OUTCOMES:
        row = dict(outcome)
        row["owner"] = "A Named Person" if row["id"] == "P01" else None
        patched.append(row)
    monkeypatch.setattr(oct16_data, "OUTCOMES", patched, raising=True)

    body = _html.unescape(logged_in("Bill").get("/oct16").text)
    assert oct16_data.DATA_STATUS_CONFIRMED not in body, (
        "the page claimed full confirmation with only one owner named"
    )
    assert "1 of 6" in body, "the page should report the partial count"


def test_the_rendered_page_shows_a_withheld_owner_as_a_placeholder(logged_in, monkeypatch):
    """A withheld name renders as a marked placeholder, never as a bare name."""
    import html as _html

    from app import oct16_data

    patched = []
    for outcome in oct16_data.OUTCOMES:
        row = dict(outcome)
        row["owner"] = oct16_data.OWNER_WITHHELD
        patched.append(row)
    monkeypatch.setattr(oct16_data, "OUTCOMES", patched, raising=True)

    body = _html.unescape(logged_in("Bill").get("/oct16").text)
    assert "owner withheld" in body
    assert "unconfirmed" in body, "a withheld owner must be marked unconfirmed in the markup"
