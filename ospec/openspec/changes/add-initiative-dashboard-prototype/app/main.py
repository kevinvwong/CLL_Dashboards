import os

# Stamped by the deploy step as an app setting, and echoed by /healthz, so
# "is the code I just deployed the code being served?" is answerable over
# plain HTTP without shell access to the instance.
DEPLOY_MARKER = os.getenv("DEPLOY_MARKER", "dev")
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

from app import auth, guards, queries, repo, status

app = FastAPI()

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# One status presentation (design D4, the `status-presentation` spec). Templates
# call these instead of re-implementing `| lower | replace(' ', '-')` six times.
templates.env.filters["status_class"] = status.status_class
templates.env.filters["milestone_class"] = status.milestone_class
templates.env.filters["availability_class"] = status.availability_class
# The per-priority key colour (blueprint-redesign 1.1/1.3). A priority keeps
# its colour across the stage, the cards and the cascade. Deliberately a
# separate scale from status, so the two can never be confused.
templates.env.filters["priority_colour"] = status.priority_colour_var

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
                         ("/meeting", "meeting"), ("/outcomes", "outcomes")):
        if path == prefix or path.startswith(prefix + "/"):
            section = name
            break
    return {
        "person": auth.current_person(request),
        "app_env": auth.settings().APP_ENV,
        # Every page needs to know whether to offer admin-only entry points
        # (new initiative, edit description). Task 8.4 built the routes but
        # nothing linked to them.
        "may_admin": auth.is_admin_request(request),
        # The sample-data banner is dismissible for the session (task 2.4). The
        # session scope is the cookie the dismiss handler sets; the footer
        # marker is rendered regardless, so dismissal never hides the state.
        "banner_dismissed": bool(request.cookies.get("sample_banner_dismissed")),
        "section": section,
        # The failing-check count for the admin nav badge (5.4). Zero renders
        # no badge. Wrapped because a broken read must not break every page.
        "failing_checks": _failing_check_count(),
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
    return RedirectResponse(url=f"/initiatives/{code}", status_code=303)


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
    if not auth.person_exists(person_id):
        return templates.TemplateResponse(
            request,
            "whoami.html",
            _ctx(request, people=auth.active_people(), error="Pick who you are."),
            status_code=400,
        )
    response = RedirectResponse(url="/", status_code=303)
    return auth.set_person_cookie(response, request, int(person_id))


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
            dean_rows=dean_rows,
            d1_groups=d1_groups,
            grouped=queries.group_rows(rows, group) if group else [],
            group_by=group if group in queries.GROUPINGS else None,
            groupings={k: v.capitalize() for k, v in queries.GROUPINGS.items()},
            counts=counts,
            rollup=queries.rollup_label(len(rows), counts),
        ),
    )


@app.get("/priorities/{priority_name}")
async def priority_list(request: Request, priority_name: str, group: str | None = None):
    priority = queries.priority_by_name(priority_name)
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
            heading=f"{priority['PriorityName']} ({priority['PlanYear']})",
            description=priority["Description"],
            entry_kind="priority",
            entry_key=priority["PriorityName"],
            plan_year=priority["PlanYear"],
            dean_rows=dean_rows,
            d1_groups=d1_groups,
            grouped=queries.group_rows(rows, group) if group else [],
            group_by=group if group in queries.GROUPINGS else None,
            groupings={k: v.capitalize() for k, v in queries.GROUPINGS.items()},
            counts=counts,
            rollup=queries.rollup_label(len(rows), counts),
        ),
    )


# Declared before /initiatives/{code}: otherwise "new" is captured as a code
# and the create form 404s.
@app.get("/initiatives/new")
async def create_form(request: Request, _: guards.Target = Depends(guards.admin_only)):
    return templates.TemplateResponse(
        request,
        "edit_create.html",
        _ctx(request, people=auth.active_people(), error=None),
    )


@app.get("/initiatives/{code}")
async def initiative(request: Request, code: str,
                     target: guards.Target = Depends(guards.known_target)):
    """Initiative card.

    Task 5.1: an HTMX request gets the bare fragment to swap into the modal;
    a direct navigation gets the same content wrapped in a full page.
    """
    context = _ctx(
        request,
        card=target.card,
        # Breadcrumbs on the full page only (5.2); the fragment goes into a
        # drawer over the page that already shows them.
        crumbs=[("Initiatives", "/initiatives"), (code, None)],
        may_update=auth.can_update(request, code),
        may_edit_details=auth.can_edit_details(request, code),
        may_admin=auth.is_admin_request(request),
    )
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(request, "card.html", context)
    return templates.TemplateResponse(request, "card_full.html", context)


@app.get("/initiatives/{code}/update")
async def update_form(request: Request, code: str,
                      target: guards.Target = Depends(guards.may_update)):
    """The update form. 403 for anyone who may not update (task 6.4).

    A fragment: it is opened with hx-get into #card-modal. Rendered through the
    helper so a direct load still gets the full layout.
    """
    return _fragment_or_full(
        request, "update_form.html", "update_form_full.html",
        _ctx(request, card=target.card, statuses=repo.STATUSES, note_max=repo.NOTE_MAX),
    )


@app.post("/initiatives/{code}/updates")
async def submit_update(request: Request, code: str,
                        target: guards.Target = Depends(guards.may_update)):
    """Append a progress update, then re-render the card.

    The permission check is in the guard, on the server, and not only on the
    button: the progress-updates spec requires a 403 for a non-owner posting
    directly. The guard also enforces existence before permission, so an
    unknown code is a 404 and a known-but-forbidden one a 403.
    """
    form = await request.form()
    try:
        repo.add_progress_update(
            code=code,
            percent=str(form.get("percent", 0)),
            status=str(form.get("status", "")),
            note=str(form.get("note", "")),
            entered_by_id=target.person_id,
        )
    except repo.RuleError as exc:
        # Refused by a rule: show the message rather than a 500.
        return templates.TemplateResponse(
            request,
            "update_form.html",
            _ctx(
                request,
                card=queries.initiative_card(code),
                statuses=repo.STATUSES,
                note_max=repo.NOTE_MAX,
                error=exc.message,
            ),
            status_code=422,
        )

    card = queries.initiative_card(code)
    response = templates.TemplateResponse(request, "card.html", _ctx(request, card=card))
    # Tells a list screen behind the modal that its row is now stale (task 6.3).
    response.headers["HX-Trigger"] = f'{{"initiativeUpdated": "{code}"}}'
    return response


@app.get("/meeting")
async def meeting(request: Request, since: str | None = None):
    """The Wednesday agenda: an attention list plus changes in a window.

    Defaults to the last 7 days; `?since=YYYY-MM-DD` sets the window to the
    previous meeting date. `?range=` offers the quick ranges the spec names
    (7d, 14d), so the Dean does not have to pick a date by hand.
    """
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
    """Global search (overhaul 3.5). Returns a fragment for the palette."""
    results = queries.search(q) if q else []
    return templates.TemplateResponse(
        request, "_search_results.html", _ctx(request, q=q, results=results)
    )


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
        request, "oct16.html", _ctx(request, d=oct16_data)
    )


@app.get("/initiatives/{code}/edit/details")
async def edit_details_form(request: Request, code: str,
                            target: guards.Target = Depends(guards.may_edit_details)):
    return _fragment_or_full(
        request, "edit_details.html", "edit_details_full.html",
        _ctx(request, card=target.card),
    )


@app.post("/initiatives/{code}/edit/details")
async def edit_details_submit(request: Request, code: str,
                              target: guards.Target = Depends(guards.may_edit_details)):
    form = await request.form()
    try:
        repo.update_initiative_details(
            code=code,
            name=str(form.get("name", "")),
            description=str(form.get("description", "")),
            person_id=target.person_id,
        )
    except repo.RuleError as exc:
        return templates.TemplateResponse(
            request,
            "edit_details.html",
            _ctx(request, card=queries.initiative_card(code), error=exc.message),
            status_code=422,
        )
    return _edit_result(request, code)


@app.get("/initiatives/{code}/edit/tags")
async def edit_tags_form(request: Request, code: str,
                         target: guards.Target = Depends(guards.admin_for)):
    options = queries.tag_edit_options(target.card["InitiativeID"])
    return _fragment_or_full(
        request, "edit_tags.html", "edit_tags_full.html",
        _ctx(request, card=target.card, error=None, **options),
    )


@app.post("/initiatives/{code}/edit/tags")
async def edit_tags_submit(request: Request, code: str,
                           target: guards.Target = Depends(guards.admin_for)):
    form = await request.form()

    def collect(primary_field):
        """Build the tag list from the submitted form.

        The form uses a radio per list, so a browser sends exactly one
        primary. This still reads every `*_primary` value rather than just
        the first: a hand-crafted POST carrying two primaries must be
        rejected by repo.replace_tags with the spec's message, not silently
        reduced to one.
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
            code=code,
            goal_tags=collect("goal_primary"),
            priority_tags=collect("priority_primary"),
            person_id=target.person_id,
        )
    except repo.RuleError as exc:
        card = queries.initiative_card(code)
        return templates.TemplateResponse(
            request,
            "edit_tags.html",
            _ctx(
                request,
                card=card,
                goals=[],
                priorities=[],
                chosen_goals=set(),
                chosen_priorities=set(),
                error=exc.message,
            ),
            status_code=422,
        )
    return _edit_result(request, code)


@app.get("/initiatives/{code}/edit/links")
async def edit_links_form(request: Request, code: str,
                          target: guards.Target = Depends(guards.admin_for)):
    options = queries.link_edit_options(target.card["InitiativeID"])
    return _fragment_or_full(
        request, "edit_links.html", "edit_links_full.html",
        _ctx(request, card=target.card, error=None, **options),
    )


@app.post("/initiatives/{code}/edit/links")
async def edit_links_submit(request: Request, code: str,
                            target: guards.Target = Depends(guards.admin_for)):
    form = await request.form()
    ids = []
    for raw in form.getlist("dean_initiative_id"):
        try:
            ids.append(int(str(raw)))
        except (TypeError, ValueError):
            continue
    try:
        repo.replace_links(code=code, dean_initiative_ids=ids, person_id=target.person_id)
    except repo.RuleError as exc:
        return templates.TemplateResponse(
            request,
            "edit_links.html",
            _ctx(
                request,
                card=queries.initiative_card(code),
                deans=queries.link_edit_options(target.card["InitiativeID"])["deans"],
                chosen=set(ids),
                error=exc.message,
            ),
            status_code=422,
        )
    return _edit_result(request, code)



@app.post("/initiatives")
async def create_submit(request: Request,
                        target: guards.Target = Depends(guards.admin_only)):
    form = await request.form()
    try:
        repo.create_initiative(
            code=str(form.get("code", "")),
            name=str(form.get("name", "")),
            level=str(form.get("level", "")),
            owner_id=int(str(form.get("owner_id") or 0)),
            description=str(form.get("description", "")),
            person_id=target.person_id,
        )
    except (repo.RuleError, ValueError) as exc:
        message = exc.message if isinstance(exc, repo.RuleError) else "Pick an owner."
        return templates.TemplateResponse(
            request,
            "edit_create.html",
            _ctx(request, people=auth.active_people(), error=message),
            status_code=422,
        )
    return RedirectResponse(url="/checks", status_code=303)


@app.post("/initiatives/{code}/retire")
async def retire_submit(request: Request, code: str,
                        target: guards.Target = Depends(guards.admin_for)):
    try:
        repo.retire_initiative(code=code, person_id=target.person_id)
    except repo.RuleError as exc:
        raise HTTPException(status_code=422, detail=exc.message)
    return RedirectResponse(url="/checks", status_code=303)


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


@app.get("/initiatives")
async def initiatives_index(request: Request):
    """The initiatives index (task 1.6; filters task 3.4).

    Filter state lives in the query string, so a filtered view is shareable and
    the controls can reflect what is applied. The controls are plain links, so
    the page works without JavaScript.
    """
    q = request.query_params
    filters: dict = {k: q.get(k) for k in ("status", "owner", "tier", "goal", "priority")
                     if q.get(k)}
    if q.get("stale"):
        filters["stale"] = True

    all_rows = queries.all_initiatives()
    rows = queries.all_initiatives(filters) if filters else all_rows

    # The filter options come from the data, so a control never offers a value
    # that matches nothing.
    owners = sorted({r["Owner"] for r in all_rows if r["Owner"]})
    statuses = sorted({r["Status"] or "Not started" for r in all_rows})
    goals = sorted({g for r in all_rows for g in r["Goals"]})

    return templates.TemplateResponse(
        request,
        "initiatives.html",
        _ctx(
            request,
            initiatives=rows,
            total=len(all_rows),
            filters=filters,
            owners=owners,
            statuses=statuses,
            goals=goals,
        ),
    )


@app.get("/")
async def root(request: Request):
    """Home: a portfolio dashboard in our own design.

    Deliberately NOT the Dean's prototype's layout (hero stage + Dean node).
    This is a dashboard: a stat band, then the six priorities as cards carrying
    every governed field, then the four teams, then the team-KPI table. It shows
    all the prototype's content without copying its shape.
    """
    priorities = queries.blueprint_priorities()
    teams = queries.team_overview()
    kpis = queries.kpi_cards()

    # The stat band: counts, not a performance score.
    stats = {
        "priorities": len(priorities),
        "goals": len(queries.goal_tiles()),
        "teams": len(teams),
        "kpis": len(kpis),
        "needs_review": sum(1 for k in kpis if k["TargetStatus"] == "needs_review"),
        "initiatives": len(queries.all_initiatives()),
    }

    plan_year = max((p["PlanYear"] for p in priorities), default=None)
    return templates.TemplateResponse(
        request,
        "home.html",
        _ctx(
            request,
            priorities=priorities,
            teams=teams,
            kpis=kpis,
            stats=stats,
            plan_year=plan_year,
        ),
    )
