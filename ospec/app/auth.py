"""Access gate and server-side permission checks.

Access is two steps (design.md decision 5): a shared passcode, then a person
picker. Both are remembered in cookies signed with ``APP_SECRET``. The
passcode itself is never stored in a cookie - only a signed marker saying
"the passcode was entered".

Every permission helper here re-reads the database. Buttons may be hidden in
the UI, but that is presentation; these functions are the control, and the
``admin-editing`` and ``progress-updates`` specs require a 403 from the server
rather than an absent button.

``Config`` is instantiated per call rather than cached, so tests can point
``DB_PATH`` at a temporary copy between cases.
"""

import secrets
import sqlite3

from fastapi import Request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import Config
from app.db import connect

PASSCODE_COOKIE = "cll_passcode"
PERSON_COOKIE = "cll_person"

# The shared-access spec says 30 days.
COOKIE_MAX_AGE = 60 * 60 * 24 * 30

# Reachable without the passcode cookie.
EXEMPT_PATHS = frozenset({"/login", "/whoami", "/healthz", "/favicon.ico", "/robots.txt"})

PASSCODE_MARKER = "passcode-ok"


def settings() -> Config:
    return Config()


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings().APP_SECRET, salt="cll-access")


def _conn():
    return connect()


def passcode_matches(candidate: str) -> bool:
    expected = settings().APP_PASSCODE
    if not expected:
        return False
    return secrets.compare_digest(candidate or "", expected)


def passcode_marker() -> str:
    return _serializer().dumps(PASSCODE_MARKER)


def has_passcode(request: Request) -> bool:
    token = request.cookies.get(PASSCODE_COOKIE)
    if not token:
        return False
    try:
        return _serializer().loads(token, max_age=COOKIE_MAX_AGE) == PASSCODE_MARKER
    except (BadSignature, SignatureExpired):
        return False


def set_passcode_cookie(response, request: Request):
    response.set_cookie(
        PASSCODE_COOKIE,
        passcode_marker(),
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(request),
    )
    return response


def set_person_cookie(response, request: Request, person_id: int):
    response.set_cookie(
        PERSON_COOKIE,
        _serializer().dumps(person_id),
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(request),
    )
    return response


def _cookie_secure(request: Request) -> bool:
    """Secure whenever the request is HTTPS, and always when APP_ENV is live.

    Task 9.1 asks for Secure cookies on the live site. Keying off the request
    scheme alone would let a live deployment that arrived over plain HTTP set
    a non-Secure cookie, which is the case worth being strict about.
    """
    return request.url.scheme == "https" or settings().APP_ENV == "live"


def person_id_from_cookie(request: Request):
    token = request.cookies.get(PERSON_COOKIE)
    if not token:
        return None
    try:
        return int(_serializer().loads(token, max_age=COOKIE_MAX_AGE))
    except (BadSignature, SignatureExpired, TypeError, ValueError):
        return None


def current_person(request: Request) -> dict | None:
    # Resolved once per request (design D2). The access gate, the template
    # context, and each permission check all ask for the signed-in person; the
    # first ask reads the database and the rest reuse it. Cached on the request
    # so every caller sees the same person. `_resolved` distinguishes "not yet
    # asked" from "asked, and there is no signed-in person".
    if getattr(request.state, "person_resolved", False):
        return request.state.person

    person_id = person_id_from_cookie(request)
    if person_id is None:
        request.state.person = None
        request.state.person_resolved = True
        return None
    with _conn() as conn:
        row = conn.execute(
            "SELECT PersonID, Name, Title, ReportsToID, IsAdmin "
            "FROM People WHERE PersonID = ? AND IsActive = 1",
            (person_id,),
        ).fetchone()
    person: dict | None = dict(row) if row else None
    request.state.person = person
    request.state.person_resolved = True
    return person


def active_people() -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT PersonID, Name, Title FROM People WHERE IsActive = 1 ORDER BY Name"
        ).fetchall()
    return [dict(r) for r in rows]


def person_exists(person_id) -> bool:
    try:
        person_id = int(person_id)
    except (TypeError, ValueError):
        return False
    with _conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM People WHERE PersonID = ? AND IsActive = 1", (person_id,)
        ).fetchone()
    return row is not None


def get_initiative(code: str):
    with _conn() as conn:
        row = conn.execute(
            "SELECT InitiativeID, Code, InitiativeName, Level, OwnerID "
            "FROM Initiatives WHERE Code = ? AND IsActive = 1",
            (code,),
        ).fetchone()
    return dict(row) if row else None


def is_admin(person) -> bool:
    return bool(person and person["IsAdmin"])


def is_dean(person) -> bool:
    """The Dean is the top-level person who owns Dean-level initiatives.

    ``ReportsToID IS NULL`` alone is not sufficient: Kevin is also top-level
    and would be granted Dean powers by that test alone. The second clause is
    what distinguishes Bill.
    """
    if not person or person["ReportsToID"] is not None:
        return False
    with _conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM Initiatives "
            "WHERE OwnerID = ? AND Level = 'Dean' AND IsActive = 1 LIMIT 1",
            (person["PersonID"],),
        ).fetchone()
    return row is not None


def can_update(request: Request, code: str) -> bool:
    """Owner, Dean, or admin may append a progress update."""
    person = current_person(request)
    if not person:
        return False
    if is_admin(person) or is_dean(person):
        return True
    initiative = get_initiative(code)
    return bool(initiative and initiative["OwnerID"] == person["PersonID"])


def can_edit_details(request: Request, code: str) -> bool:
    """Owner or admin may edit name and description."""
    person = current_person(request)
    if not person:
        return False
    if is_admin(person):
        return True
    initiative = get_initiative(code)
    return bool(initiative and initiative["OwnerID"] == person["PersonID"])


def is_admin_request(request: Request) -> bool:
    """For routes that only admins may reach: tags, links, create, retire,
    and goal/priority descriptions. The admin-editing spec requires a 403
    from the server, not just hidden controls."""
    return is_admin(current_person(request))


def database_reachable() -> bool:
    try:
        with _conn() as conn:
            conn.execute("SELECT 1 FROM Initiatives LIMIT 1").fetchone()
    except sqlite3.Error:
        return False
    return True


# --- login lockout (task 9.2) ---------------------------------------------
#
# The shared-access spec: block an IP for 15 minutes after 10 failed attempts
# within 15 minutes, and refuse the 11th attempt *even if the passcode is
# correct*. In-memory by design (the task says so): this is a prototype with
# one instance, and a counter that resets on restart is better than none.

import time
from collections import defaultdict

LOCKOUT_THRESHOLD = 10
LOCKOUT_WINDOW_SECONDS = 15 * 60

_failures: dict = defaultdict(list)


def client_ip(request) -> str:
    return request.client.host if request.client else "unknown"


def too_many_attempts(ip: str) -> bool:
    now = time.time()
    recent = [t for t in _failures.get(ip, []) if now - t < LOCKOUT_WINDOW_SECONDS]
    _failures[ip] = recent
    return len(recent) >= LOCKOUT_THRESHOLD


def record_failure(ip: str) -> None:
    _failures[ip].append(time.time())


def clear_failures(ip: str) -> None:
    _failures.pop(ip, None)


def reset_lockouts() -> None:
    """Test hook."""
    _failures.clear()