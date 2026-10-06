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
        self.BACKUP_DIR = os.getenv("BACKUP_DIR", "./backups")
        self.PORT = int(os.getenv("PORT", "8000"))
