"""The Clerk identity adapter behind the `authenticate()` seam (ADR-0004).

Clerk answers "who is this?"; the app's own `Roles` answer "what may they do".
This module verifies a Clerk session token on an incoming request and maps the
Clerk user id to a local `People` row (via `People.ClerkUserID`), then hands back
the same `Principal` the local provider does. Nothing else in the app changes:
routes read a Principal, never a cookie or a Clerk object.

The session token is read from the Clerk `__session` cookie (server-rendered
app), verified with the backend SDK's `authenticate_request`. Verification is
server-side only; `CLERK_SECRET_KEY` never leaves the server.
"""

from app.config import Config


def _requestish(request):
    """Adapt a Starlette request to what the Clerk SDK reads (a `.headers` map).

    The SDK's Requestish protocol is just `headers`; a Starlette request already
    exposes exactly that, so no shim is needed beyond handing it over.
    """
    return request


def _authorized_parties() -> list[str]:
    raw = Config().CLERK_AUTHORIZED_PARTY or ""
    return [p.strip() for p in raw.split(",") if p.strip()]


def is_configured() -> bool:
    """Whether the Clerk adapter has the settings it needs to run."""
    cfg = Config()
    return bool(cfg.CLERK_SECRET_KEY and cfg.CLERK_PUBLISHABLE_KEY)


def frontend_api() -> str:
    """The Clerk frontend-API host, for the clerk-js loader.

    Clerk's publishable key encodes it: `pk_test_`/`pk_live_` + base64url of
    `<frontend-api>$`. Derived so the page needs no second setting; a
    `CLERK_FRONTEND_API` setting overrides it if ever needed.
    """
    cfg = Config()
    override = (cfg.CLERK_FRONTEND_API or "").strip()
    if override:
        return override
    key = cfg.CLERK_PUBLISHABLE_KEY or ""
    for prefix in ("pk_test_", "pk_live_"):
        if key.startswith(prefix):
            import base64
            blob = key[len(prefix):]
            blob += "=" * (-len(blob) % 4)
            try:
                decoded = base64.urlsafe_b64decode(blob).decode("utf-8").rstrip("$")
                return decoded
            except Exception:
                return ""
    return ""



def clerk_user_id(request):
    """The verified Clerk user id for a request, or None.

    None covers every failure the same way: no token, an invalid/expired token,
    a token minted for another origin, or the SDK not being installed. The
    caller treats all of them as "not signed in", which is the safe default.
    """
    try:
        from clerk_backend_api import Clerk
        from clerk_backend_api.security import authenticate_request
        from clerk_backend_api.security.types import AuthenticateRequestOptions
    except ImportError:  # the dependency is declared; degrade rather than crash
        return None

    cfg = Config()
    if not cfg.CLERK_SECRET_KEY:
        return None
    try:
        sdk = Clerk(bearer_auth=cfg.CLERK_SECRET_KEY)
        state = sdk.authenticate_request(
            _requestish(request),
            AuthenticateRequestOptions(authorized_parties=_authorized_parties()),
        )
        if not state.is_signed_in or not state.payload:
            return None
        return state.payload.get("sub")
    except Exception:
        # A malformed token, a network blip, or an SDK error is "not signed in",
        # never a 500 on every page.
        return None
