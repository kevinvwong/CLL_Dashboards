import os
from pathlib import Path
from dotenv import load_dotenv

class Config:
    """Simple configuration loader.
    
    It first loads variables from a `.env` file (if present) and then
    falls back to the OS environment.  All values are returned as strings.
    """
    def __init__(self, env_path: str | None = None):
        # Load .env if it exists.  ``load_dotenv`` is safe to call multiple
        # times – it only loads the file once per process.
        env_file = env_path or (Path(__file__).parent.parent / ".env")
        if Path(env_file).exists():
            load_dotenv(dotenv_path=env_file, override=False)
        # Retrieve values – they may be empty strings if not set.
        self.APP_PASSCODE = os.getenv("APP_PASSCODE", "")
        self.APP_SECRET = os.getenv("APP_SECRET", "")
        # `local` or `live`. Drives the LOCAL banner and Secure cookies (9.1).
        self.APP_ENV = os.getenv("APP_ENV", "local")
        # The one configured database path. This is the only place a path is
        # named; db.get_connection() has no default of its own, so nothing can
        # open a different file by accident (see the `data-connection` spec).
        self.DB_PATH = os.getenv("DB_PATH", "./cll_initiatives.db")
        # Where the in-app guide renders its markdown from (the repo's docs/).
        # Like DB_PATH, a single named path so the app and the renderer cannot
        # disagree; the deploy sets DOCS_PATH to the shipped copy.
        self.DOCS_PATH = os.getenv("DOCS_PATH", "./docs")
        self.BACKUP_DIR = os.getenv("BACKUP_DIR", "./backups")
        self.PORT = int(os.getenv("PORT", "8000"))
        # The meeting surface is ICED (2026-10-06): hidden from the nav and its
        # route returns 404, while the page, its queries and its tests stay in
        # the tree so re-enabling is one environment variable, not a rebuild.
        # Off by default; set MEETING_ENABLED=1 to bring it back.
        self.MEETING_ENABLED = os.getenv("MEETING_ENABLED", "0") == "1"

        # --- authentication provider (ADR-0004) -------------------------------
        # Which adapter `authenticate()` uses. `local` is the built-in stopgap
        # (shared passcode + self-asserted picker, closed per person by a PIN).
        # `clerk` verifies a Clerk session token instead. The routes do not
        # change either way; only this switch does.
        self.AUTH_PROVIDER = os.getenv("AUTH_PROVIDER", "local").strip().lower()
        # The Clerk backend secret key (server-side only; never sent to the
        # browser). Empty means the Clerk adapter is not usable.
        self.CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")
        # The publishable key, safe to expose, injected into the page for clerk-js.
        self.CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY", "")
        # The origin(s) allowed to mint a session for this app, for
        # authenticate_request's `authorized_parties` check. Comma-separated.
        self.CLERK_AUTHORIZED_PARTY = os.getenv(
            "CLERK_AUTHORIZED_PARTY",
            "http://localhost:8000,http://127.0.0.1:8000",
        )
        # Optional: the Clerk frontend-API host for the clerk-js loader. Normally
        # derived from the publishable key, so this is only an override.
        self.CLERK_FRONTEND_API = os.getenv("CLERK_FRONTEND_API", "")
