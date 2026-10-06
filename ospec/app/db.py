import sqlite3

from app.config import Config

# A connection is obtained through connect() only, and always for the path
# named by Config.DB_PATH. There is deliberately no default path here: a second
# default is what let an empty database be opened (and once shipped in a deploy
# archive). See the `data-connection` spec and design D3.


def connect(write: bool = False) -> sqlite3.Connection:
    """Open the configured database with the pragmas every caller needs.

    One interface for every caller: read and write differ only by ``write``, so
    "how do I get a connection?" has one answer (design D3).

    * Foreign-key enforcement is on, so the schema's referential rules hold.
    * Write-ahead logging, for concurrent reads while a write is in flight.
    * ``busy_timeout`` 5000 ms, so a writer waits for a reader instead of
      failing.
    * ``row_factory`` returns rows as ``sqlite3.Row``, so callers use names.
    * ``write=True`` takes the write lock up front, so a read inside the same
      transaction sees a consistent snapshot and two writers cannot interleave.
    """
    conn = sqlite3.connect(Config().DB_PATH, timeout=5.0)  # seconds; 5 s = 5000 ms
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row
    if write:
        conn.execute("BEGIN IMMEDIATE")
    return conn

