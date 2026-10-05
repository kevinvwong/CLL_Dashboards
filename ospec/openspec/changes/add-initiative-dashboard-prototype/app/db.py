import sqlite3
from pathlib import Path

# Path to the SQLite database – default from config, but we keep it simple here.
# In production you would import Config from app.config and use Config.DB_PATH.
DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "db.sqlite3"

def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Return a SQLite connection with sensible defaults.

    * Foreign‑key enforcement is enabled.
    * Write‑ahead logging (WAL) is set for better concurrency.
    * ``busy_timeout`` is set to 5000 ms so writers wait for readers.
    * ``row_factory`` returns rows as ``sqlite3.Row`` (dict‑like access).
    """
    path = db_path or str(DEFAULT_DB_PATH)
    conn = sqlite3.connect(path, timeout=5.0)  # timeout is seconds → 5 s == 5000 ms
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row
    return conn

# Helper for simple queries – useful in tests or scripts.
def query(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    with get_connection() as conn:
        cur = conn.execute(sql, params)
        return cur.fetchall()
