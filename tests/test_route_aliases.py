"""Old route names redirect to the current ones (rename compatibility).

The layers were renamed twice: first the prototype path `/initiatives/*` was
retired, then the intermediate name `/major-initiatives/*` (and `/dean-priorities`)
when "Major Initiative" became "Team Initiative". Each deployed round's bookmarks
must keep working, so both generations 308-redirect to the current path.
"""

import pytest

#: (old path, the current path it must redirect to)
RETIRED = [
    ("/initiatives", "/team-initiatives"),
    ("/initiatives/MI-002", "/team-initiatives/MI-002"),
    ("/initiatives/MI-002/update", "/team-initiatives/MI-002/update"),
    ("/major-initiatives", "/team-initiatives"),
    ("/major-initiatives/MI-002", "/team-initiatives/MI-002"),
    ("/major-initiatives/MI-002/edit/tags", "/team-initiatives/MI-002/edit/tags"),
    ("/dean-priorities", "/dean-initiatives"),
]


@pytest.mark.parametrize("old,new", RETIRED)
def test_a_retired_path_308s_to_the_current_one(logged_in, old, new):
    r = logged_in("Kevin").get(old, follow_redirects=False)
    assert r.status_code == 308, "%s should redirect, got %s" % (old, r.status_code)
    assert r.headers["location"].endswith(new), r.headers["location"]


@pytest.mark.parametrize("path", ["/team-initiatives", "/team-initiatives/MI-002",
                                  "/dean-initiatives"])
def test_the_current_paths_serve(logged_in, path):
    assert logged_in("Kevin").get(path).status_code == 200
