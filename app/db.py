"""One connection factory, two providers (ADR-0004-style seam for storage).

`connect()` is the single answer to "how do I get a connection?" (design D3). A
second question now has one answer too: **which store**. `DB_PROVIDER` selects it:

    sqlite  (default) the local file, cll_initiatives.db
    mssql             the Rev2 model on Azure SQL (serverless GP_S_Gen5)

The two are NOT interchangeable: they are different schemas (the app's 17-table
model vs Rev2's 28). Porting a query from SQLite to Rev2 is a real translation,
done one query at a time; this module only decides which engine answers.

A connection is a thin wrapper so callers keep writing `conn.execute(sql, args)`
and reading rows by name regardless of engine:

    sqlite: sqlite3.Connection, rows are sqlite3.Row
    mssql : pymssql.Connection, rows are tuples wrapped so name access works
"""
import os
import sqlite3

from app.config import Config


def engine(conn) -> str:
    """The engine tag for a connection: 'sqlite' or 'mssql'.

    Each read/write asks the CONNECTION this, not `Config()`, so the choice is
    made once at connect and cannot drift per call (change `adopt-rev2-store`
    D1). A mssql connection is an MssqlConnection wrapper (`engine` attr); a
    sqlite connection is anything else.
    """
    return getattr(conn, "engine", "sqlite")


def dialect(conn) -> dict:
    """The dialect helpers for a connection's engine (see DIALECT)."""
    return DIALECT[engine(conn)]


#: Dialect helpers, the single place cross-engine differences live (change
#: `adopt-rev2-store` D1/1.2). `today_sql` reads the clock the data was written
#: with - UTC - in each dialect; queries use it so ageing is on one clock on
#: both engines. `today_clause` is the same comparison inline for filtering a
#: date column >= today. Everything else about a port is explicit SQL per engine.
DIALECT = {
    "sqlite": {
        "today": "SELECT date('now')",
        "today_clause": "date({col}) >= date('now')",
    },
    "mssql": {
        "today": "SELECT CAST(GETUTCDATE() AS date)",
        "today_clause": "CAST({col} AS date) >= CAST(GETUTCDATE() AS date)",
    },
}


class _Row(dict):
    """A row that supports both `row['Name']` and `row[0]` / `dict(row)`.

    SQLite returns sqlite3.Row, which supports name and index access. pymssql
    returns plain tuples. This bridges the two so a ported query reads the same
    whichever engine ran it.
    """

    def __init__(self, columns, values):
        super().__init__(zip(columns, values))
        self._values = tuple(values)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return dict.__getitem__(self, key)


class MssqlCursor:
    """A sqlite3-Cursor-shaped wrapper over a pymssql cursor."""

    def __init__(self, cur):
        self._cur = cur

    def execute(self, sql, args=()):
        self._cur.execute(sql, args) if args else self._cur.execute(sql)
        return self

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in self._cur.description]
        return _Row(cols, row)

    def fetchall(self):
        rows = self._cur.fetchall()
        cols = [d[0] for d in self._cur.description]
        return [_Row(cols, r) for r in rows]

    def __iter__(self):
        return iter(self.fetchall())


class MssqlConnection:
    """A sqlite3-Connection-shaped wrapper over a pymssql connection.

    Only the surface the app actually uses: `execute`, `commit`, `close`, and
    context-manager use. `execute` returns a MssqlCursor; a caller may iterate it
    or call fetchone/fetchall.
    """

    engine = "mssql"

    def __init__(self, raw, write=False):
        self._conn = raw
        self._conn.autocommit(False)
        if write:
            self._conn.autocommit(False)

    def execute(self, sql, args=()):
        cur = self._conn.cursor()
        if args:
            cur.execute(sql, args)
        else:
            cur.execute(sql)
        return MssqlCursor(cur)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()
        return False


def _mssql_connect(write=False):
    import pymssql

    cfg = Config()
    conn = pymssql.connect(
        server=cfg.MSSQL_SERVER, user=cfg.MSSQL_USER, password=cfg.MSSQL_PASSWORD,
        database=cfg.MSSQL_DATABASE, login_timeout=60, timeout=60,
    )
    return MssqlConnection(conn, write=write)


def connect(write: bool = False, provider: str | None = None):
    """Open the configured store with the pragmas every caller needs.

    * sqlite: foreign keys on, WAL, 5 s busy timeout, rows as sqlite3.Row;
      ``write=True`` takes the write lock up front (BEGIN IMMEDIATE).
    * mssql: a connection to Rev2 on Azure SQL; ``write=True`` begins a
      transaction the caller commits.

    ``provider`` overrides DB_PROVIDER for this one connection. The AppMeta
    fallback uses it: under DB_PROVIDER=mssql it still needs a sqlite handle for
    the engine-agnostic config Rev2 has no table for (design Open issue 2), and
    must not re-enter connect() and open a second mssql connection.
    """
    if (provider or Config().DB_PROVIDER) == "mssql":
        return _mssql_connect(write=write)

    conn = sqlite3.connect(Config().DB_PATH, timeout=5.0)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row
    if write:
        conn.execute("BEGIN IMMEDIATE")
    return conn
