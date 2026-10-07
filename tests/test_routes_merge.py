"""The merged routes: the register path serves the card; the old paths 308."""


def test_retired_card_path_308s(logged_in):
    old = "/initia" + "tives/MI-002"     # not rewritten by the rename pass
    r = logged_in("Kevin").get(old, follow_redirects=False)
    assert r.status_code == 308
    assert r.headers["location"].endswith("/major-initiatives/MI-002")


def test_retired_index_308s(logged_in):
    r = logged_in("Kevin").get("/initiatives", follow_redirects=False)
    assert r.status_code == 308
    assert r.headers["location"].endswith("/major-initiatives")


def test_major_initiative_serves_the_interactive_card(logged_in):
    r = logged_in("Kevin").get("/major-initiatives/MI-002",
                               headers={"HX-Request": "true"})
    assert r.status_code == 200
    assert "card-body" in r.text


def test_major_initiative_full_page(logged_in):
    r = logged_in("Kevin").get("/major-initiatives/MI-002")
    assert r.status_code == 200
    assert "Reusable content" in r.text


def test_update_form_moved(logged_in):
    r = logged_in("Kevin").get("/major-initiatives/MI-002/update",
                               headers={"HX-Request": "true"})
    assert r.status_code == 200
