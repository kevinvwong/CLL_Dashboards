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

import hashlib
import hmac
import os
import secrets
import sqlite3

from fastapi import Request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import Config
from app.db import connect, engine
from app import port

PASSCODE_COOKIE = "cll_passcode"
PERSON_COOKIE = "cll_person"

# The shared-access spec says 30 days.
COOKIE_MAX_AGE = 60 * 60 * 24 * 30

# Reachable without the passcode cookie.
EXEMPT_PATHS = frozenset({
    "/login", "/whoami", "/healthz", "/favicon.ico", "/robots.txt",
    # Clerk (ADR-0004): the sign-in page and its unlinked explanation are the
    # gate's own destinations, so they must be reachable before a person exists.
    "/clerk/sign-in", "/clerk/unlinked", "/clerk/sign-out",
})

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

    if settings().AUTH_PROVIDER == "clerk":
        # Clerk (ADR-0004): identity comes from the verified session token, not
        # a person cookie. Everything downstream keeps calling current_person.
        from app import clerk_auth
        person = person_by_clerk_id(clerk_auth.clerk_user_id(request))
        request.state.person = person
        request.state.person_resolved = True
        return person

    person_id = person_id_from_cookie(request)
    if person_id is None:
        request.state.person = None
        request.state.person_resolved = True
        return None
    with _conn() as conn:
        person = port.auth_person(conn, person_id)
    request.state.person = person
    request.state.person_resolved = True
    return person


def active_people() -> list[dict]:
    with _conn() as conn:
        return port.auth_active_people(conn)


def person_exists(person_id) -> bool:
    try:
        person_id = int(person_id)
    except (TypeError, ValueError):
        return False
    with _conn() as conn:
        return port.auth_person(conn, person_id) is not None


def get_initiative(mi_id: str):
    """Resolve a Team Initiative by its canon key, if active."""
    with _conn() as conn:
        return port.auth_get_initiative(conn, mi_id)


def is_admin(person) -> bool:
    """Platform administration: users, configuration, everything.

    Reads the local `PlatformAdmin` role (ADR-0005, DR-05). The earlier `admin`
    name and the deprecated `IsAdmin` column are honoured during the migration.
    """
    if not person:
        return False
    if has_role(person, "PlatformAdmin") or has_role(person, "admin"):
        return True
    return bool(person.get("IsAdmin"))


def is_executive_sponsor(person) -> bool:
    """The Executive Sponsor: the Dean's application authorization relationship.

    Was `is_dean`, keyed on the free-text Title 'Dean' (a person). DR-23 records
    the role as `ExecutiveSponsor` — an authorization relationship that survives a
    personnel change. This grants EXECUTIVE ACTION authority, never routine data
    maintenance: it must not be used inside a general update guard.
    """
    if not person:
        return False
    if has_role(person, "ExecutiveSponsor") or has_role(person, "dean"):
        return True
    return (person.get("Title") or "").strip().lower() == "dean"


def is_dean(person) -> bool:
    """Deprecated alias for `is_executive_sponsor` (kept for callers/tests)."""
    return is_executive_sponsor(person)


def is_data_owner(person) -> bool:
    """The Data Owner: governs portfolio data (approvals, exceptions, quality)."""
    return bool(person and (has_role(person, "DataOwner")))


def is_operator(person) -> bool:
    """Strategic Operations / Operator: operational and data-maintenance authority."""
    return bool(person and (has_role(person, "Operator")))


def has_capability(person, capability: str) -> bool:
    """Whether a person's roles include a named capability (DR-05).

    A small, explicit map from capability to the roles that hold it, so a guard
    asks a capability question rather than an identity question. `Administrator`
    holds every capability; the others are deliberately disjoint (DR-23: the
    model is not a hierarchy).
    """
    if not person:
        return False
    roles = roles_of(person)
    if "PlatformAdmin" in roles or "Administrator" in roles or "admin" in roles or person.get("IsAdmin"):
        return True
    holders = _CAPABILITIES.get(capability, frozenset())
    return bool(roles & holders)


#: capability -> the roles that hold it. `Administrator` is handled above (all).
_CAPABILITIES = {
    "maintain_data": frozenset({"Operator"}),
    "govern_data": frozenset({"DataOwner"}),
    "execute_action": frozenset({"ExecutiveSponsor", "dean"}),
    "contribute": frozenset({"Contributor"}),
    "view": frozenset({"Viewer", "ExecutiveSponsor", "DataOwner", "Operator",
                       "Contributor", "dean"}),
}


#: role name -> RoleID, read once. Empty if the schema predates the roles tables.
def _role_ids() -> dict:
    # Any store error means "no role ids"; the caller treats an empty map as
    # "roles unavailable", which is the same outcome the sqlite3.Error guard gave.
    try:
        with _conn() as conn:
            return port.auth_role_ids(conn)
    except Exception:
        return {}


def roles_of(person) -> set:
    """The role names a person holds."""
    if not person:
        return set()
    with _conn() as conn:
        return port.auth_roles_of(conn, person["PersonID"])


def has_role(person, role: str) -> bool:
    return role in roles_of(person)


# --- the credential stopgap (auth hardening, 2026-10-07) ---------------------
#
# The escalation vector was never the passcode; it was that POST /whoami let
# anyone holding the passcode BECOME any person, including the admin. A PIN that
# only that person knows closes it. Stored as PBKDF2-HMAC-SHA256, salted, never
# in the seed. This is the local implementation behind the seam below; an Entra
# or Clerk adapter replaces `authenticate` later without touching the routes.

PBKDF2_ITERATIONS = 60000


def hash_pin(pin: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", (pin or "").encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return "pbkdf2_sha256$%d$%s$%s" % (PBKDF2_ITERATIONS, salt.hex(), dk.hex())


def check_pin(stored: str, pin: str) -> bool:
    try:
        algo, iters, salt_hex, hash_hex = (stored or "").split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", (pin or "").encode("utf-8"),
                                 bytes.fromhex(salt_hex), int(iters))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except (ValueError, TypeError):
        return False


def pin_stopgap_enabled(conn=None) -> bool:
    """Whether the local PIN stopgap is in force for the configured store.

    True on sqlite. False on the Rev2 store, which keeps no credential material
    (DEVIATIONS 010) because production identity is Clerk there. Callers skip the
    PIN gate rather than failing, so the picker is a local-only path.

    Asks the CONNECTION when given one (authoritative — a test or a caller may
    hold a store other than the ambient config), else the configured store.
    """
    if conn is not None:
        return engine(conn) != "mssql"
    return Config().DB_PROVIDER != "mssql"


def person_credential(person_id):
    """The stored credential hash for a person, or None (no PIN set).

    Local stopgap only: refuses on the Rev2 store, which never holds a
    credential (see DEVIATIONS 010).
    """
    try:
        pid = int(person_id)
    except (TypeError, ValueError):
        return None
    with _conn() as conn:
        if engine(conn) == "mssql":
            raise port.auth_pin_refused()
        row = conn.execute(
            "SELECT Credential FROM People WHERE PersonID = ? AND IsActive = 1",
            (pid,)).fetchone()
    return row["Credential"] if row else None


def verify_person_pin(person_id, pin) -> bool:
    stored = person_credential(person_id)
    if not stored:
        return False
    return check_pin(stored, pin)


def set_person_pin(person_id, pin: str):
    with connect(write=True) as conn:
        if engine(conn) == "mssql":
            raise port.auth_pin_refused()
        conn.execute("UPDATE People SET Credential = ? WHERE PersonID = ?",
                     (hash_pin(pin), int(person_id)))
        conn.commit()


class Principal:
    """The authenticated subject and what it may do (ADR-0004).

    The identity provider answers "who"; the local roles answer "what". Routes
    read a Principal, never a raw cookie, so swapping the provider is one
    function.
    """

    __slots__ = ("person", "roles")

    def __init__(self, person: dict, roles: set):
        self.person = person
        self.roles = roles

    @property
    def person_id(self) -> int:
        return self.person["PersonID"]

    @property
    def name(self) -> str:
        return self.person["Name"]

    def has_role(self, role: str) -> bool:
        return role in self.roles


def person_by_clerk_id(clerk_user_id):
    """The active person linked to a Clerk user id, or None."""
    if not clerk_user_id:
        return None
    with _conn() as conn:
        return port.auth_person_by_clerk_id(conn, clerk_user_id)


def link_person_to_clerk(person_id, clerk_user_id: str):
    """An admin links a person to a Clerk user id (Rev2: person.clerk_user_id)."""
    with connect(write=True) as conn:
        port.auth_link_person_to_clerk(conn, person_id, clerk_user_id)
        conn.commit()


def authenticate(request: Request):
    """The one entry point every auth path goes through (ADR-0004).

    Returns a Principal for a signed-in person, else None. Which provider runs
    is a config switch (`AUTH_PROVIDER`): the local stopgap (passcode + picker),
    or Clerk. The routes do not change either way.
    """
    if settings().AUTH_PROVIDER == "clerk":
        from app import clerk_auth
        person = person_by_clerk_id(clerk_auth.clerk_user_id(request))
    else:
        person = current_person(request)
    if not person:
        return None
    return Principal(person, roles_of(person))


def can_update(request: Request, mi_id: str) -> bool:
    """Who may append a progress update to an initiative.

    The owner, an Operator (Strategic Operations data maintenance), or an
    Administrator — and NOT the Executive Sponsor by virtue of being Dean
    (DR-23: executive authority is not routine data-maintenance authority; the
    Dean authorizes a change through an executive action, which Strategic
    Operations then performs).
    """
    person = current_person(request)
    if not person:
        return False
    if is_admin(person) or is_operator(person):
        return True
    initiative = get_initiative(mi_id)
    return bool(initiative and initiative["OwnerID"] == person["PersonID"])


def can_edit_details(request: Request, mi_id: str) -> bool:
    """Owner or admin may edit name and description."""
    person = current_person(request)
    if not person:
        return False
    if is_admin(person):
        return True
    initiative = get_initiative(mi_id)
    return bool(initiative and initiative["OwnerID"] == person["PersonID"])


def is_admin_request(request: Request) -> bool:
    """For routes that only admins may reach: tags, links, create, retire,
    and goal/priority descriptions. The admin-editing spec requires a 403
    from the server, not just hidden controls."""
    return is_admin(current_person(request))


def database_reachable() -> bool:
    try:
        with _conn() as conn:
            port.auth_database_reachable(conn)
    except Exception:
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