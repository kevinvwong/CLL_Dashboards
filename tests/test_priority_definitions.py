"""The six annual priorities' canonical descriptions.

The user supplied these definitions on 2026-10-07. P01 previously read "as one
College" in the prototype's data.js and in app/ priorities.py; the confirmed
canonical wording is "as a College", fixed at the generator so a rebuild keeps it.
"""
from app import priorities
from app.db import connect

#: code -> the canonical description (the user's wording, 2026-10-07).
CANON = {
    "P01": "Build a clear, cohesive sense of who we are as a College and "
           "consistently communicate the distinctive value of CLL.",
    "P02": "Foster experimentation, creativity, and new ways of working that "
           "advance learning, improve outcomes, and position CLL for the future.",
    "P03": "Connect programs, credentials, and learning experiences into clear, "
           "cohesive pathways that help learners navigate opportunities and "
           "achieve their goals.",
    "P04": "Deliver consistent, high-quality experiences and outcomes as we "
           "expand our reach, programs, and impact.",
    "P05": "Use data and insights to inform decisions, prioritize action, "
           "measure impact, and continuously improve.",
    "P06": "Strengthen a culture of continuous learning, collaboration, and "
           "shared accountability that brings our modeled behaviors to life and "
           "builds the capabilities needed for CLL\u2019s future.",
}


def test_database_descriptions_match_the_canon(fresh_db):
    got = {r["Code"]: r["Description"]
           for r in connect().execute("SELECT Code, Description FROM Priorities")}
    for code, want in CANON.items():
        assert got.get(code) == want, "P%s description differs" % code


def test_app_module_descriptions_match_the_canon():
    by_name = {"P01": "Identity", "P02": "Innovation", "P03": "Pathways",
               "P04": "Scale", "P05": "Data", "P06": "Culture"}
    for code, name in by_name.items():
        assert priorities.description(name) == CANON[code], \
            "app/priorities.py %s differs" % code


def test_p01_says_a_college_not_one():
    """The specific correction: 'as a College', never 'as one College'."""
    assert "as one College" not in CANON["P01"]
    assert priorities.description("Identity").startswith(
        "Build a clear, cohesive sense of who we are as a College")
