"""The October 16 module states what the page shows.

Covers the `oct16-deliverable` spec of deepen-dashboard-modules, tasks 5.1-5.3.

The values the page shows come off the module, not out of the template. These
tests assert the value, not the markup, so they survive a redesign of the page.
"""
import importlib.util
import os

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(APP, "app")
TEMPLATE = os.path.join(SRC, "templates", "oct16.html")
MODULE = os.path.join(SRC, "oct16_data.py")


def _load():
    spec = importlib.util.spec_from_file_location("oct16_mod", MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- the module states the derived values ----------------------------------


def test_percent_is_a_module_function():
    """The bar's meaning lives in the module, not the template."""
    mod = _load()
    assert hasattr(mod, "percent"), "the module does not state the milestone percent"
    for o in mod.OUTCOMES:
        p = mod.percent(o)
        assert isinstance(p, int)
        assert 0 <= p <= 100


def test_percent_floors_so_a_bar_never_overstates():
    """1 of 3 is 33%, not 34%. A bar reading 34% would claim more than happened."""
    mod = _load()
    assert mod.percent({"reached": 1, "planned": 3}) == 33
    assert mod.percent({"reached": 2, "planned": 3}) == 66
    assert mod.percent({"reached": 0, "planned": 3}) == 0
    assert mod.percent({"reached": 3, "planned": 3}) == 100


def test_percent_handles_no_planned_milestones():
    """A guard, so a planned value of zero cannot divide by zero."""
    mod = _load()
    assert mod.percent({"reached": 0, "planned": 0}) == 0


def test_the_template_does_not_compute_the_percent():
    """The formula must not be in the template."""
    text = open(TEMPLATE, encoding="utf-8").read()
    assert "100 * o.reached" not in text, "the template still computes the percent"
    assert "d.percent(o)" in text, "the template does not call the module's percent"


def test_the_template_does_not_respell_the_no_owner_string():
    """The placeholder has one spelling, in the module."""
    from app import oct16_data

    text = open(TEMPLATE, encoding="utf-8").read()
    assert "d.owner_label(o.owner)" in text
    # The literal must not be typed into the template a second time.
    assert '>no owner named<' not in text, "the template re-spells the owner-none string"


# --- the confirmed marker ---------------------------------------------------


def test_illustrative_when_built_without_owners(tmp_path):
    """The committed state: no owners, so the page says illustrative."""
    mod = _load()
    assert mod.CONFIRMED is False
    assert mod.data_status() == mod.DATA_STATUS_ILLUSTRATIVE


def test_partial_is_not_rounded_to_confirmed(monkeypatch):
    """Some owners named, some not: the page reports the partial position."""
    mod = _load()
    monkeypatch.setattr(mod, "CONFIRMED", True)
    monkeypatch.setattr(mod, "OUTCOMES", [
        {"owner": "A Person"}, {"owner": "[owner withheld]"},
        {"owner": None}, {"owner": None}, {"owner": None}, {"owner": None},
    ])
    status = mod.data_status()
    assert status != mod.DATA_STATUS_CONFIRMED
    assert "1 of 6" in status, status


def test_confirmed_only_when_every_owner_is_confirmed(monkeypatch):
    mod = _load()
    monkeypatch.setattr(mod, "CONFIRMED", True)
    monkeypatch.setattr(mod, "OUTCOMES", [{"owner": "A"} for _ in range(6)])
    assert mod.data_status() == mod.DATA_STATUS_CONFIRMED


# --- three owner states -----------------------------------------------------


def test_withheld_is_not_a_confirmed_owner():
    mod = _load()
    assert mod.owner_is_confirmed(mod.OWNER_WITHHELD) is False
    assert mod.owner_is_confirmed(None) is False
    assert mod.owner_is_confirmed("A Person") is True


def test_owner_label_gives_one_spelling_for_the_absent_state():
    mod = _load()
    assert mod.owner_label(None) == mod.OWNER_NONE
    assert mod.owner_label("A Person") == "A Person"
    assert mod.owner_label(mod.OWNER_WITHHELD) == mod.OWNER_WITHHELD


def test_missing_owner_is_stated_not_left_blank(logged_in):
    """Rendered: an outcome with no owner says so, and is visually distinct."""
    body = logged_in("Bill Gaudelli").get("/oct16").text
    assert "no owner named" in body
    assert "owner-none" in body
