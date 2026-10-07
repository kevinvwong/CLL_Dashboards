import os
import re

# Stamped by the deploy step as an app setting, and echoed by /healthz, so
# "is the code I just deployed the code being served?" is answerable over
# plain HTTP without shell access to the instance.
DEPLOY_MARKER = os.getenv("DEPLOY_MARKER", "dev")


def deploy_time_from_marker(marker: str) -> str:
    """The deploy time encoded in a DEPLOY_MARKER, or "" if it has none.

    A marker is '<label>-YYYYMMDDTHHMMSSZ', and the timestamp is the deploy
    moment. Reading it here means a deploy that sets only DEPLOY_MARKER still
    gets a time in the header stamp, with no second setting to keep in step.
    """
    m = re.search(r"(\d{8})T(\d{6})Z", marker or "")
    if not m:
        return ""
    date, clock = m.groups()
    return f"{date[0:4]}-{date[4:6]}-{date[6:8]} {clock[0:2]}:{clock[2:4]} UTC"


def build_stamp_label(commit: str, when: str) -> str:
    """The one-line header stamp: the short commit, then the deploy time.

    Each part is omitted when unknown, so local dev (neither known) yields "",
    and base.html hides the element rather than showing an empty chip.
    """
    parts = []
    if commit:
        parts.append(commit[:7])
    if when:
        parts.append("deployed " + when)
    return " \u00b7 ".join(parts)


# The commit the deployed code was built from (set by the deploy step), and
# when it was built. Kept separate from DEPLOY_MARKER so the stamp can name the
# code while the marker names the deploy.
BUILD_COMMIT = os.getenv("GIT_COMMIT", "").strip()
BUILD_TIME = os.getenv("BUILD_TIME", "").strip() or deploy_time_from_marker(DEPLOY_MARKER)
BUILD_STAMP_LABEL = build_stamp_label(BUILD_COMMIT, BUILD_TIME)
"""FastAPI entry point for the initiative dashboard prototype.

Access is gated before any page renders (design.md decision 5): a shared
passcode, then a person picker. Both live in signed cookies; the passcode
itself is never stored client-side.
"""

from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import auth, guards, identity, priorities, queries, repo, status

app = FastAPI()

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# One status presentation (design D4, the `status-presentation` spec). Templates
# call these instead of re-implementing `| lower | replace(' ', '-')` six times.
templates.env.filters["status_class"] = status.status_class
templates.env.filters["status_icon"] = status.status_icon
templates.env.filters["milestone_class"] = status.milestone_class
templates.env.filters["milestone_icon"] = status.milestone_icon
templates.env.filters["availability_class"] = status.availability_class
# The per-priority key colour (blueprint-redesign 1.1/1.3). A priority keeps
# its colour across the stage, the cards and the cascade. Deliberately a
# separate scale from status, so the two can never be confused.
templates.env.filters["priority_colour"] = status.priority_colour_var
# The TOKEN (e.g. "--priority-3"), for the `var({{ ... }})` pattern the chips and
# the home card share. `priority_colour` returns the whole var() expression, so
# wrapping it in var() again produced `var(var(--priority-3))` - invalid CSS that
# left every priority chip uncoloured.
templates.env.filters["priority_colour_token"] = status.priority_colour_token
# Goal and team identity (ADR-0003): a colour token and, for a goal, an icon.
# Four axes, each keyed and legend-ed, none a status colour.
templates.env.filters["goal_colour_token"] = identity.goal_colour_token
templates.env.filters["team_colour_token"] = identity.team_colour_token
templates.env.filters["goal_icon"] = identity.goal_icon
templates.env.filters["nav_icon"] = identity.nav_icon
# The one label a priority is called by, everywhere: "P01 One Shared Identity"
# (#7). Without it a priority read three ways across the app.
templates.env.filters["priority_label"] = priorities.label
templates.env.filters["priority_number"] = priorities.number
templates.env.filters["priority_code"] = priorities.code
# The full title WITHOUT the code, for a chip that already shows the code beside
# it (otherwise the code is printed twice: "P03 P03 Integrated…", #N3).
templates.env.filters["priority_title"] = priorities.title

# htmx is vendored (design.md decision 1) so the app works with no CDN access.
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")


def _is_exempt(path: str) -> bool:
    if path in auth.EXEMPT_PATHS:
        return True
    return path.startswith("/static/")


def _ctx(request: Request, **extra) -> dict:
    """Common template context. `person` is the signed-in person, or None
    before the picker has been completed."""
    path = request.url.path
    # The nav's active section (blueprint-redesign 5.1). Derived from the path
    # so every page gets it without each route remembering to pass it.
    section = "home"
    for prefix, name in (("/initiatives", "initiatives"), ("/people", "people"),
                         ("/goals", "initiatives"), ("/priorities", "initiatives"),
                         ("/teams", "initiatives"), ("/team-initiatives", "initiatives"),
                         ("/dean-initiatives", "initiatives"),
                         ("/checks", "checks"),
                         ("/changes", "changes"),
                         ("/meeting", "meeting"), ("/outcomes", "outcomes")):
        if path == prefix or path.startswith(prefix + "/"):
            section = name
            break
    return {
        "person": auth.current_person(request),
        "app_env": auth.settings().APP_ENV,
        # The meeting surface is ICED (2026-10-06): the nav hides it and the
        # route 404s unless MEETING_ENABLED is set. Read here so every page
        # agrees with the route.
        "meeting_enabled": auth.settings().MEETING_ENABLED,
        # Every page needs to know whether to offer admin-only entry points
        # (new initiative, edit description). Task 8.4 built the routes but
        # nothing linked to them.
        "may_admin": auth.is_admin_request(request),
        # (The sample-data banner was removed 2026-10-07 with the approval of the
        # register, so there is no banner_dismissed context any more.)
        "section": section,
        # The failing-check count for the admin nav badge (5.4). Zero renders
        # no badge. Wrapped because a broken read must not break every page.
        "failing_checks": _failing_check_count(),
        # The discreet header stamp: last push (short commit) and deploy time.
        # Empty in local dev, where base.html omits the element.
        "build_stamp": BUILD_STAMP_LABEL,
        **extra,
    }


def _failing_check_count() -> int:
    """How many data checks are currently failing. 0 when the read fails."""
    try:
        return len(queries.data_checks())
    except Exception:
        return 0


def _edit_ctx(request: Request, code: str) -> dict:
    """The capability flags every card render needs."""
    return {
        "may_update": auth.can_update(request, code),
        "may_edit_details": auth.can_edit_details(request, code),
        "may_admin": auth.is_admin_request(request),
    }


def _wants_fragment(request: Request) -> bool:
    """True when the response is being swapped into a page, not loaded directly.

    HTMX sets HX-Request. The edit forms are opened with hx-get into
    #card-modal, so their GET must return a fragment; a direct navigation must
    return the full layout. Serving the full layout to the modal is what nested
    the whole site inside the dialog (the Partial Responses requirement in
    `initiative-detail`).
    """
    return bool(request.headers.get("HX-Request"))


def _fragment_or_full(request: Request, fragment: str, full: str, context: dict):
    """Render `fragment` for a partial request, `full` for a direct load."""
    return templates.TemplateResponse(
        request, fragment if _wants_fragment(request) else full, context
    )


def _edit_result(request: Request, code: str):
    """What to return after a successful edit.

    The edit forms submit over HTMX into the modal, so the card fragment is
    the right answer there. Without JavaScript the same POST is a normal page
    load, and returning the bare fragment would replace the whole page with a
    `<div class="card-body">` and no header or nav - so send that case to the
    card's own full page instead.
    """
    card = queries.initiative_card(code)
    context = _ctx(request, card=card, **_edit_ctx(request, code))
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request, "card.html", context)
    return RedirectResponse(url=f"/team-initiatives/{code}", status_code=303)


@app.middleware("http")
async def access_gate(request: Request, call_next):
    """Send anyone without a passcode to /login, and anyone without a person
    to /whoami. Static files and /healthz stay outside the gate."""
    path = request.url.path

    def _redirect(url: str) -> RedirectResponse:
        # The noindex header is set here as well as on the normal path below.
        # Returning early used to skip it, so the gate's own redirects went out
        # without X-Robots-Tag - and those are precisely the responses a crawler
        # that has never authenticated will see. Found by probing the live site:
        # GET / returned 303 to /login with no X-Robots-Tag, while the local test
        # only ever checked a 200.
        response = RedirectResponse(url=url, status_code=303)
        response.headers["X-Robots-Tag"] = "noindex"
        return response

    if not _is_exempt(path):
        if not auth.has_passcode(request):
            return _redirect("/login")
        if auth.current_person(request) is None:
            return _redirect("/whoami")
    response = await call_next(request)
    # Task 9.2: noindex on every response, so nothing here reaches a search
    # engine even before robots.txt is fetched.
    response.headers["X-Robots-Tag"] = "noindex"
    return response


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt():
    """Disallow all (task 9.2). Served outside the passcode gate."""
    return PlainTextResponse("User-agent: *\nDisallow: /\n")


# --- styled error pages (the Styled Error Pages requirement) -----------------
#
# FastAPI's defaults answer with a JSON body, which reads as a broken API rather
# than a wrong turn: /initiatives returned {"detail":"Method Not Allowed"} and
# /people {"detail":"Not Found"}. A browser request gets a styled page; a
# non-browser request (one that does not accept HTML) keeps the JSON, so a
# script or a health probe is not handed a full HTML document.


def _wants_html(request: Request) -> bool:
    return "text/html" in (request.headers.get("accept") or "")


def _error_page(request: Request, status_code: int, heading: str, message: str):
    context = _ctx(request, status_code=status_code, heading=heading, message=message)
    if _wants_html(request):
        return templates.TemplateResponse(
            request, "error.html", context, status_code=status_code
        )
    return JSONResponse(context, status_code=status_code)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "That request could not be served."
    headings = {
        403: "Not allowed",
        404: "Page not found",
        405: "Method not allowed",
    }
    heading = headings.get(exc.status_code, "Something went wrong")
    return _error_page(request, exc.status_code, heading, detail)


@app.get("/healthz", response_class=PlainTextResponse)
async def healthz():
    """Outside the passcode gate. Returns no initiative data."""
    if not auth.database_reachable():
        return PlainTextResponse("database unreachable", status_code=503)
    return PlainTextResponse(f"ok DEPLOY_MARKER={DEPLOY_MARKER}")


@app.get("/login")
async def login_form(request: Request):
    locked = auth.too_many_attempts(auth.client_ip(request))
    return templates.TemplateResponse(
        request,
        "login.html",
        _ctx(
            request,
            error="Too many attempts. Try again in 15 minutes." if locked else None,
        ),
    )


@app.post("/login")
async def login_submit(request: Request):
    ip = auth.client_ip(request)
    # Checked before verifying the passcode: the spec requires the 11th
    # attempt to be refused *even if the passcode is correct*.
    if auth.too_many_attempts(ip):
        return templates.TemplateResponse(
            request,
            "login.html",
            _ctx(request, error="Too many attempts. Try again in 15 minutes."),
            status_code=429,
        )
    form = await request.form()
    if auth.passcode_matches(str(form.get("passcode", ""))):
        auth.clear_failures(ip)
        response = RedirectResponse(url="/whoami", status_code=303)
        return auth.set_passcode_cookie(response, request)
    auth.record_failure(ip)
    return templates.TemplateResponse(
        request, "login.html", _ctx(request, error="That passcode is not right."), status_code=401
    )


@app.get("/whoami")
async def whoami_form(request: Request):
    if not auth.has_passcode(request):
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        request, "whoami.html", _ctx(request, people=auth.active_people(), error=None)
    )


@app.post("/whoami")
async def whoami_submit(request: Request):
    if not auth.has_passcode(request):
        return RedirectResponse(url="/login", status_code=303)
    form = await request.form()
    person_id = str(form.get("person_id", ""))
    pin = str(form.get("pin", ""))
    if not auth.person_exists(person_id):
        return templates.TemplateResponse(
            request,
            "whoami.html",
            _ctx(request, people=auth.active_people(), error="Pick who you are."),
            status_code=400,
        )
    # The stopgap (auth hardening, 2026-10-07): once a person has a PIN, BECOMING
    # them requires it - the passcode alone no longer lets anyone assert any
    # identity, which was the real escalation vector. A person with no PIN set
    # still falls back to the passcode-held picker, so nothing breaks before PINs
    # are provisioned.
    if auth.person_credential(person_id):
        if not auth.verify_person_pin(person_id, pin):
            return templates.TemplateResponse(
                request,
                "whoami.html",
                _ctx(request, people=auth.active_people(),
                     error="That PIN is not right."),
                status_code=401,
            )
    response = RedirectResponse(url="/", status_code=303)
    return auth.set_person_cookie(response, request, int(person_id))


@app.post("/people/{person_id}/set-pin")
async def set_pin(request: Request, person_id: int, _=Depends(guards.admin_only)):
    """An admin sets a person's PIN, closing self-assertion for them."""
    form = await request.form()
    pin = str(form.get("pin", "")).strip()
    if len(pin) < 4 or not pin.isdigit():
        raise HTTPException(status_code=400, detail="A PIN must be at least 4 digits.")
    auth.set_person_pin(person_id, pin)
    return RedirectResponse(url="/people", status_code=303)


@app.get("/goals/{goal_number}")
async def goal_list(request: Request, goal_number: int, group: str | None = None):
    goal = queries.goal_by_number(goal_number)
    if goal is None:
        raise HTTPException(status_code=404, detail="No such goal")
    rows = queries.goal_rows(goal_number)
    dean_rows, d1_groups = queries.split_for_list(rows)
    counts = queries.status_counts(rows)
    return templates.TemplateResponse(
        request,
        "list.html",
        _ctx(
            request,
            heading=goal["ShortName"],
            description=goal["FullName"] or goal["Description"],
            entry_kind="goal",
            entry_key=goal["GoalNumber"],
            crumbs=[("Goals", "/#goals"), ("G%d" % goal["GoalNumber"], None)],
            dean_rows=dean_rows,
            d1_groups=d1_groups,
            grouped=queries.group_rows(rows, group) if group else [],
            group_by=group if group in queries.GROUPINGS else None,
            groupings={k: v.capitalize() for k, v in queries.GROUPINGS.items()},
            counts=counts,
            rollup=queries.rollup_label(len(rows), counts),
            # The Team Initiatives aligned to this goal (interconnection-
            # redesign 3.1): the new edge, shown from the goal side.
            team_initiatives=queries.goal_team_initiatives(goal_number),
        ),
    )


@app.get("/priorities/{priority_name}")
async def priority_list(request: Request, priority_name: str, group: str | None = None):
    priority = queries.priority_detail(priority_name)
    if priority is None:
        raise HTTPException(status_code=404, detail="No such priority")
    rows = queries.priority_rows(priority_name)
    dean_rows, d1_groups = queries.split_for_list(rows)
    counts = queries.status_counts(rows)
    return templates.TemplateResponse(
        request,
        "list.html",
        _ctx(
            request,
            heading=f"{priorities.label(priority['PriorityName'])} ({priority['PlanYear']})",
            description=priority["Description"],
            entry_kind="priority",
            crumbs=[("Priorities", "/#priorities"), (priorities.label(priority["PriorityName"]), None)],
            entry_key=priority["PriorityName"],
            plan_year=priority["PlanYear"],
            # The governed fields live on the priority page (interconnection-
            # redesign 5: the overview card is compact and links here).
            governed=priority,
            dean_rows=dean_rows,
            d1_groups=d1_groups,
            grouped=queries.group_rows(rows, group) if group else [],
            group_by=group if group in queries.GROUPINGS else None,
            groupings={k: v.capitalize() for k, v in queries.GROUPINGS.items()},
            counts=counts,
            rollup=queries.rollup_label(len(rows), counts),
        ),
    )


@app.get("/teams")
async def teams_index(request: Request):
    """The four teams, as an index. The breadcrumb on a team page links here, and
    before this existed that link 404'd."""
    teams = queries.team_overview()
    return templates.TemplateResponse(
        request, "teams.html",
        _ctx(request, teams=teams, crumbs=[("Teams", None)]),
    )


@app.get("/teams/{team_id}")
async def team_page(request: Request, team_id: int):
    """One team, with its Team Initiatives (interconnection-redesign 3.2).

    Closes the dead end: the four teams existed only inside the home table.
    """
    team = queries.team_detail(team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="No such team")
    return templates.TemplateResponse(
        request,
        "team.html",
        _ctx(request, team=team,
             crumbs=[("Teams", "/teams"), (team["Name"], None)]),
    )


# Declared before /team-initiatives/{mi_id}: otherwise "new" is captured as an
# mi_id and the create form 404s.
@app.get("/team-initiatives/new")
async def create_form(request: Request, _: guards.Target = Depends(guards.admin_only)):
    return templates.TemplateResponse(
        request, "edit_create.html",
        _ctx(request, people=auth.active_people(), error=None),
    )


@app.get("/team-initiatives/{mi_id}")
async def team_initiative_page(request: Request, mi_id: str,
                                target: guards.Target = Depends(guards.known_target)):
    """One Team Initiative: the interactive card, on the register path.

    Before the 2026-10-07 merge this was a read-only page and the interactive
    card lived on /initiatives/{code}. They are one surface now: an HTMX request
    gets the bare fragment for the drawer, a direct navigation gets the full page
    (plus the register's edges: team, source area, goals, priorities, and the Dean
    Priorities it contributes to).
    """
    mi = queries.team_initiative_detail(mi_id)
    if mi is None:
        raise HTTPException(status_code=404, detail="No such Team Initiative")
    context = _ctx(
        request,
        mi=mi,
        card=target.card,
        dean_links=queries.team_initiative_dean_links(mi["MIId"] or mi_id),
        crumbs=[("Team Initiatives", "/team-initiatives"), (mi["MIId"] or mi_id, None)],
        may_update=auth.can_update(request, mi_id),
        may_edit_details=auth.can_edit_details(request, mi_id),
        may_admin=auth.is_admin_request(request),
    )
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request, "card.html", context)
    return templates.TemplateResponse(request, "team_initiative.html", context)


# --- The interactive card, on the register path (2026-10-07 merge) ----------
#
# The prototype's /initiatives/{code} card (drawer, update form, edit forms)
# moves onto /team-initiatives/{mi_id}. Everything is keyed by the canon's
# MIId; the old /initiatives/* paths 308-redirect here so bookmarks keep working.

@app.get("/team-initiatives/{mi_id}/update")
async def update_form(request: Request, mi_id: str,
                      target: guards.Target = Depends(guards.may_update)):
    """The update form. 403 for anyone who may not update."""
    return _fragment_or_full(
        request, "update_form.html", "update_form_full.html",
        _ctx(request, card=target.card, statuses=repo.STATUSES, note_max=repo.NOTE_MAX),
    )


@app.post("/team-initiatives/{mi_id}/updates")
async def submit_update(request: Request, mi_id: str,
                        target: guards.Target = Depends(guards.may_update)):
    """Append a progress update, then re-render the card.

    The permission check is in the guard, on the server, not only on the button:
    the progress-updates spec requires a 403 for a non-owner posting directly.
    The guard also enforces existence before permission.
    """
    form = await request.form()
    try:
        repo.add_progress_update(
            mi_id=mi_id,
            percent=str(form.get("percent", 0)),
            status=str(form.get("status", "")),
            note=str(form.get("note", "")),
            entered_by_id=target.person_id,
        )
    except repo.RuleError as exc:
        return templates.TemplateResponse(
            request, "update_form.html",
            _ctx(request, card=queries.initiative_card(mi_id),
                 statuses=repo.STATUSES, note_max=repo.NOTE_MAX, error=exc.message),
            status_code=422,
        )

    card = queries.initiative_card(mi_id)
    response = templates.TemplateResponse(request, "card.html", _ctx(request, card=card))
    # Tells a list screen behind the modal that its row is now stale.
    response.headers["HX-Trigger"] = f'{{"initiativeUpdated": "{mi_id}"}}'
    return response


@app.get("/team-initiatives/{mi_id}/edit/details")
async def edit_details_form(request: Request, mi_id: str,
                            target: guards.Target = Depends(guards.may_edit_details)):
    return _fragment_or_full(
        request, "edit_details.html", "edit_details_full.html",
        _ctx(request, card=target.card),
    )


@app.post("/team-initiatives/{mi_id}/edit/details")
async def edit_details_submit(request: Request, mi_id: str,
                              target: guards.Target = Depends(guards.may_edit_details)):
    form = await request.form()
    try:
        repo.update_initiative_details(
            mi_id=mi_id,
            name=str(form.get("name", "")),
            description=str(form.get("description", "")),
            person_id=target.person_id,
        )
    except repo.RuleError as exc:
        return templates.TemplateResponse(
            request, "edit_details.html",
            _ctx(request, card=queries.initiative_card(mi_id), error=exc.message),
            status_code=422,
        )
    return _edit_result(request, mi_id)


@app.get("/team-initiatives/{mi_id}/edit/tags")
async def edit_tags_form(request: Request, mi_id: str,
                         target: guards.Target = Depends(guards.admin_for)):
    options = queries.tag_edit_options(target.card_id)
    return _fragment_or_full(
        request, "edit_tags.html", "edit_tags_full.html",
        _ctx(request, card=target.card, error=None, **options),
    )


@app.post("/team-initiatives/{mi_id}/edit/tags")
async def edit_tags_submit(request: Request, mi_id: str,
                           target: guards.Target = Depends(guards.admin_for)):
    form = await request.form()

    def collect(primary_field):
        """Build the tag list from the submitted form.

        The form uses a radio per list, so a browser sends exactly one primary.
        This still reads every `*_primary` value rather than just the first: a
        hand-crafted POST carrying two primaries must be rejected by
        repo.replace_tags with the spec's message, not silently reduced to one.
        """
        chosen = form.getlist(primary_field.replace("_primary", ""))
        primaries = {str(p) for p in form.getlist(primary_field)}
        out = []
        for raw in chosen:
            try:
                value = int(str(raw))
            except (TypeError, ValueError):
                continue
            out.append({"id": value, "primary": str(raw) in primaries})
        return out

    try:
        repo.replace_tags(
            mi_id=mi_id,
            goal_tags=collect("goal_primary"),
            priority_tags=collect("priority_primary"),
            person_id=target.person_id,
        )
    except repo.RuleError as exc:
        return templates.TemplateResponse(
            request, "edit_tags.html",
            _ctx(request, card=queries.initiative_card(mi_id),
                 goals=[], priorities=[], chosen_goals=set(), chosen_priorities=set(),
                 error=exc.message),
            status_code=422,
        )
    return _edit_result(request, mi_id)


@app.get("/team-initiatives/{mi_id}/edit/links")
async def edit_links_form(request: Request, mi_id: str,
                          target: guards.Target = Depends(guards.admin_for)):
    options = queries.link_edit_options(target.card_id)
    return _fragment_or_full(
        request, "edit_links.html", "edit_links_full.html",
        _ctx(request, card=target.card, error=None, **options),
    )


@app.post("/team-initiatives/{mi_id}/edit/links")
async def edit_links_submit(request: Request, mi_id: str,
                            target: guards.Target = Depends(guards.admin_for)):
    form = await request.form()
    ids = []
    for raw in form.getlist("dean_initiative_id"):
        try:
            ids.append(int(str(raw)))
        except (TypeError, ValueError):
            continue
    try:
        repo.replace_links(mi_id=mi_id, dean_initiative_ids=ids, person_id=target.person_id)
    except repo.RuleError as exc:
        return templates.TemplateResponse(
            request, "edit_links.html",
            _ctx(request, card=queries.initiative_card(mi_id),
                 deans=queries.link_edit_options(target.card_id)["deans"],
                 chosen=set(ids), error=exc.message),
            status_code=422,
        )
    return _edit_result(request, mi_id)


@app.post("/team-initiatives/{mi_id}/retire")
async def retire_submit(request: Request, mi_id: str,
                        target: guards.Target = Depends(guards.admin_for)):
    try:
        repo.retire_initiative(mi_id=mi_id, person_id=target.person_id)
    except repo.RuleError as exc:
        raise HTTPException(status_code=422, detail=exc.message)
    return RedirectResponse(url="/checks", status_code=303)


@app.post("/team-initiatives")
async def create_submit(request: Request,
                        target: guards.Target = Depends(guards.admin_only)):
    form = await request.form()
    try:
        repo.create_initiative(
            code=str(form.get("code", "")),
            name=str(form.get("name", "")),
            owner_id=int(str(form.get("owner_id") or 0)),
            description=str(form.get("description", "")),
            person_id=target.person_id,
        )
    except (repo.RuleError, ValueError) as exc:
        message = exc.message if isinstance(exc, repo.RuleError) else "Pick an owner."
        return templates.TemplateResponse(
            request, "edit_create.html",
            _ctx(request, people=auth.active_people(), error=message),
            status_code=422,
        )
    return RedirectResponse(url="/checks", status_code=303)


# --- Retired paths: 308 to the register path (the merge, 2026-10-07) ---------


@app.get("/initiatives/{code}")
async def initiative_retired(code: str):
    """The prototype card path retires to the register path."""
    return RedirectResponse(url="/team-initiatives/" + code, status_code=308)


@app.get("/initiatives/{code}/{rest:path}")
async def initiative_sub_retired(code: str, rest: str):
    return RedirectResponse(url="/team-initiatives/%s/%s" % (code, rest), status_code=308)


@app.post("/initiatives/{code}/{rest:path}")
async def initiative_sub_retired_post(code: str, rest: str):
    return RedirectResponse(url="/team-initiatives/%s/%s" % (code, rest), status_code=308)


@app.get("/initiatives/new")
async def create_form_retired():
    return RedirectResponse(url="/team-initiatives/new", status_code=308)


@app.post("/initiatives")
async def create_submit_retired():
    return RedirectResponse(url="/team-initiatives", status_code=308)


@app.get("/initiatives")
async def initiatives_index_retired():
    return RedirectResponse(url="/team-initiatives", status_code=308)


# --- The intermediate name, retired (2026-10-07) ------------------------------
# The layers were named "Major Initiative" for one deployed round, then renamed
# to "Team Initiative". A bookmark from that round would 404, so the old name
# redirects too, exactly as /initiatives/* does. This is the second rename to
# pass through, so the alias list grows with each one.

@app.get("/major-initiatives/{code}")
async def major_initiative_retired(code: str):
    return RedirectResponse(url="/team-initiatives/" + code, status_code=308)


@app.get("/major-initiatives/{code}/{rest:path}")
async def major_initiative_sub_retired(code: str, rest: str):
    return RedirectResponse(url="/team-initiatives/%s/%s" % (code, rest), status_code=308)


@app.post("/major-initiatives/{code}/{rest:path}")
async def major_initiative_sub_retired_post(code: str, rest: str):
    return RedirectResponse(url="/team-initiatives/%s/%s" % (code, rest), status_code=308)


@app.get("/major-initiatives")
async def major_initiatives_index_retired():
    return RedirectResponse(url="/team-initiatives", status_code=308)


@app.get("/dean-priorities")
async def dean_priorities_retired():
    return RedirectResponse(url="/dean-initiatives", status_code=308)


@app.get("/meeting")
async def meeting(request: Request, since: str | None = None):
    """The Wednesday agenda: an attention list plus changes in a window.

    Defaults to the last 7 days; `?since=YYYY-MM-DD` sets the window to the
    previous meeting date. `?range=` offers the quick ranges the spec names
    (7d, 14d), so the Dean does not have to pick a date by hand.

    ICED (2026-10-06): the surface is hidden and the route returns 404 while
    MEETING_ENABLED is unset. The page, its queries and its tests remain, so
    re-enabling is one environment variable. A visitor who bookmarked the URL
    gets a clean 404, not a stale agenda.
    """
    if not auth.settings().MEETING_ENABLED:
        raise HTTPException(status_code=404, detail="Not found")
    # Quick ranges (overhaul 6.1): range=7d or 14d sets the window; otherwise
    # `since` is used, and with neither the default window applies.
    range_days = {"7d": 7, "14d": 14}.get(request.query_params.get("range", ""))
    if range_days:
        window = queries.default_since(range_days)
        active_range = request.query_params.get("range")
    else:
        window = since or queries.default_since()
        active_range = None

    deltas = queries.update_deltas(window)
    # Grouped by owner, so the change list keeps the per-owner headers the
    # meeting-view requirement names.
    by_owner: dict = {}
    for d in deltas:
        by_owner.setdefault(d["Owner"], []).append(d)

    return templates.TemplateResponse(
        request,
        "meeting.html",
        _ctx(
            request,
            since=window,
            active_range=active_range,
            groups=queries.meeting_updates(window),
            attention=queries.attention_list(),
            # The change deltas (overhaul 6.3): each update with its previous
            # value, so the meeting shows "20% -> 30%", not just the current.
            deltas=deltas,
            deltas_by_owner=sorted(by_owner.items()),
        ),
    )


@app.get("/search")
async def search(request: Request, q: str = ""):
    """Global search (overhaul 3.5).

    An htmx request from the palette gets the bare fragment. A direct load -
    which is what pressing Enter in the palette does - previously got the same
    fragment with no page around it: Times New Roman, no header. A direct load
    now gets a real page; with a single result it redirects straight to it, so
    Enter always lands somewhere useful.
    """
    results = queries.search(q) if q else []
    if not request.headers.get("HX-Request") and q and len(results) == 1:
        return RedirectResponse(url=results[0]["href"], status_code=307)
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request, "_search_results.html", _ctx(request, q=q, results=results))
    return templates.TemplateResponse(
        request, "search.html", _ctx(request, q=q, results=results))


@app.get("/checks")
async def checks(request: Request):
    """Data quality AND coverage, as two distinct sections (5.4).

    "Is the data valid" (checks, from vw_DataChecks) and "is the target
    covered" (coverage, from the taxonomy) are different questions, so they
    render as two sections and are never conflated.

    Reachable by any signed-in person: the existing `data-intake` requirement
    says the page "SHALL show" every failing row, with no role restriction, and
    the weekly meeting links to it. What blueprint-redesign 5.4 changes is the
    NAV - the entry is admin-only so it is not cluttering the primary nav - not
    who may open the page.
    """
    return templates.TemplateResponse(
        request,
        "checks.html",
        _ctx(request, checks=queries.data_checks(), coverage=queries.coverage_summary()),
    )


@app.get("/changes")
async def changes_route(request: Request,
                        _: guards.Target = Depends(guards.admin_only)):
    """The change log: who changed what, newest first.

    Admin-only, enforced by the admin_only guard (403 for anyone else).
    """
    return templates.TemplateResponse(
        request, "changes.html",
        _ctx(request, rows=queries.recent_changes()),
    )


@app.get("/oct16")
async def oct16(request: Request):
    """Legacy route: permanently redirect to /outcomes (blueprint-redesign 5.2).

    The outcomes page used to be tied to a date. The route is kept so old links
    and bookmarks still work, but it never renders - it redirects.
    """
    return RedirectResponse(url="/outcomes", status_code=301)


@app.get("/outcomes")
async def outcomes(request: Request):
    """The October 16 deliverable, under a stable route.

    Option A of the wireframes. Its own definition says "Static, clickable
    pages; no live data feeds", so this renders a fixed data module rather than
    reading the prototype's tables. That is deliberate, not a shortcut: the
    outcome and team model does not exist in the prototype schema, and
    inventing tables for a ten-day deliverable would have been the expensive
    way to get this wrong.

    It also sidesteps the one open question. Option A shows the Dean's own six
    outcomes, which the wireframes note "does not match the 2026 priorities
    presented in May" - so it needs no decision on which priority list is real.
    """
    from app import oct16_data

    return templates.TemplateResponse(
        request, "oct16.html", _ctx(request, d=oct16_data,
                                    outcomes=queries.priority_outcomes(),
                                    provenance=queries.dataset_provenance())
    )




@app.get("/entries/{kind}/{key}/edit")
async def edit_entry_form(request: Request, kind: str, key: str,
                          target: guards.Target = Depends(guards.admin_only)):
    """Edit a goal or priority description (task 8.4).

    The admin gate is the guard; the 404 here is about a goal or priority, not
    an initiative, so it stays local.
    """
    goal = queries.goal_by_number(int(key)) if kind == "goal" else queries.priority_by_name(key)
    if goal is None:
        raise HTTPException(status_code=404, detail="No such entry")
    return templates.TemplateResponse(
        request,
        "edit_entry.html",
        _ctx(request, kind=kind, entry=goal, error=None),
    )


@app.post("/entries/{kind}/{key}/edit")
async def edit_entry_submit(request: Request, kind: str, key: str,
                            target: guards.Target = Depends(guards.admin_only)):
    form = await request.form()
    try:
        repo.update_entry_description(
            kind=kind,
            key=int(key) if kind == "goal" else key,
            description=str(form.get("description", "")),
            person_id=target.person_id,
        )
    except (repo.RuleError, ValueError) as exc:
        message = exc.message if isinstance(exc, repo.RuleError) else "Unknown entry."
        goal = queries.goal_by_number(int(key)) if kind == "goal" else queries.priority_by_name(key)
        return templates.TemplateResponse(
            request, "edit_entry.html",
            _ctx(request, kind=kind, entry=goal, error=message),
            status_code=422,
        )
    # Return to the list this entry was edited from, not to the home screen.
    back = "/goals/" + key if kind == "goal" else "/priorities/" + str(key)
    return RedirectResponse(url=back, status_code=303)


@app.get("/people")
async def people_index(request: Request):
    """The people index (task 1.6). Filters and attention-ordering land in 4.3."""
    return templates.TemplateResponse(
        request, "people.html", _ctx(request, people=queries.all_people())
    )


@app.get("/people/{person_id}")
async def person(request: Request, person_id: int):
    card = queries.person_card(person_id)
    if card is None:
        raise HTTPException(status_code=404, detail="No such person")
    return templates.TemplateResponse(
        request, "person.html", _ctx(request, profile=card["person"], card=card)
    )


@app.get("/")
async def root(request: Request):
    """Home: the portfolio OVERVIEW.

    An overview, not four full catalogs (interconnection-redesign group 5).
    Measured before the cut: 56 KB, 67% of it the 29-row table, and every
    initiative rendered twice. The table now has its own page,
    /team-initiatives; the sections here are compact entry points that state a
    count and link to detail.
    """
    priorities = queries.blueprint_priorities()
    teams = queries.team_overview()
    all_mis = queries.team_initiative_cards()
    # The five goals, with their Team Initiative reach (interconnection 4.1).
    goals = queries.goal_tiles()
    for g in goals:
        g["TeamInitiativeCount"] = len(queries.goal_team_initiatives(g["GoalNumber"]))

    # The stat band: counts, not a performance score. One "Initiatives" count
    # was dropped here (review round, 2026-10-07): after the two-layer merge it
    # was the same 29 as "Team Initiatives", printed twice.
    stats = {
        "priorities": len(priorities),
        "goals": len(goals),
        "teams": len(teams),
        "team_initiatives": len(all_mis),
        "needs_review": sum(1 for k in all_mis if k["TargetStatus"] == "needs_review"),
    }

    # A one-line health read, above the taxonomy (#8): the first question on
    # opening a dashboard is "how are we doing?", not "how is this organised?".
    # Counts by status, not a composite score (the design forbids a rollup).
    #
    # The register ships an EMPTY diary, so every initiative reads "Not started".
    # Printed as a status breakdown that reads "0 on track . 0 at risk . 29 not
    # started" - literally true but it looks like the College has done nothing.
    # When NOTHING has been reported, say so plainly instead; the breakdown
    # appears once an owner logs the first update.
    from collections import Counter
    by_status = Counter((r["Status"] or "Not started") for r in queries.all_initiatives())
    health = {
        "on_track": by_status.get("On track", 0),
        "at_risk": by_status.get("At risk", 0),
        "off_track": by_status.get("Off track", 0),
        "not_started": by_status.get("Not started", 0),
        "total": sum(by_status.values()),
        "has_progress": any(r["HasUpdate"] for r in queries.all_initiatives()),
    }

    plan_year = max((p["PlanYear"] for p in priorities), default=None)
    return templates.TemplateResponse(
        request,
        "home.html",
        _ctx(
            request,
            priorities=priorities,
            teams=teams,
            goals=goals,
            stats=stats,
            health=health,
            plan_year=plan_year,
            dean_initiatives=queries.dean_initiatives(),
        ),
    )


def _mi_index_ctx(request: Request, target: str | None, group: str | None) -> dict:
    """Context for the /team-initiatives index.

    The counts in the controls describe the whole set, not the filtered view,
    so "All 29" stays 29 under any filter.
    """
    all_mis = queries.team_initiative_cards()
    mi_filter = target if target in ("needs_review",) else None
    mi_group = group if group in ("team", "source_area") else None
    mis = queries.filter_and_group_team_initiatives(all_mis, mi_filter, mi_group)
    params = []
    if mi_filter:
        params.append("target=" + mi_filter)
    if mi_group:
        params.append("group=" + mi_group)
    mi_base = "/team-initiatives" + ("?" + "&".join(params) if params else "")
    return _ctx(
        request,
        team_initiatives=mis,
        all_team_initiatives=all_mis,
        needs_review_count=sum(1 for k in all_mis if k["TargetStatus"] == "needs_review"),
        mi_filter=mi_filter,
        mi_group=mi_group,
        mi_groupings={"team": "Team", "source_area": "Source area"},
        mi_base=mi_base,
    )


@app.get("/dean-initiatives")
async def dean_initiatives_page(request: Request):
    """The Dean's own priorities (register, 2026-10-07): FY26 complete, FY27 in
    flight. Moved off the home page, which is an overview; 11 rows with progress
    bars is a full view."""
    return templates.TemplateResponse(
        request, "dean_initiatives.html",
        _ctx(request, dean_initiatives=queries.dean_initiatives(),
             crumbs=[("Dean Initiatives", None)]),
    )


@app.get("/team-initiatives")
async def team_initiative_index(request: Request, target: str | None = None, group: str | None = None):
    """The Team Initiatives index: all 29, filterable and groupable.

    Moved here from the overview, which measured 56 KB with this table as
    two-thirds of it (interconnection-redesign 5).
    """
    return templates.TemplateResponse(
        request, "team_initiatives.html",
        _mi_index_ctx(request, target, group),
    )
