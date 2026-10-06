"""The database has one path and one connection interface.

Covers the `data-connection` spec of deepen-dashboard-modules.

The failure this guards against actually happened: a second default path let an
empty database be opened from the app's own directory and packaged beside the
real one in a deploy archive (commit 35fc22e). These tests fail if a second
default or a second connection helper is reintroduced.
"""
import ast
import os
import re

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(APP, "app")


def _sources():
    for name in sorted(os.listdir(SRC)):
        if name.endswith(".py"):
            path = os.path.join(SRC, name)
            yield name, open(path, encoding="utf-8").read()


def _docstring_lines(text):
    """Line numbers occupied by module, class, and function docstrings.

    A docstring explaining the rule must not trip the rule's own check. This
    was found the hard way: the scan first fired on a comment, then on the
    `write()` docstring that documents `BEGIN IMMEDIATE`. A gate that flags its
    own documentation gets switched off, so it is made blind to both.
    """
    lines = set()
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if (isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            for n in range(first.lineno, (first.end_lineno or first.lineno) + 1):
                lines.add(n)
    return lines


def _code_lines(text):
    """Yield (line_number, code), skipping comments, blank lines, docstrings."""
    skip = _docstring_lines(text)
    for i, raw in enumerate(text.splitlines(), 1):
        if i in skip:
            continue
        code = raw.split("#", 1)[0]
        if code.strip():
            yield i, code


def test_no_second_default_database_path():
    """A second default path must not exist.

    Config.DB_PATH is the one place a path is named. A `DEFAULT_DB_PATH` or a
    second literal default anywhere else is the bug this whole spec exists for.
    """
    offenders = []
    for name, text in _sources():
        for i, line in _code_lines(text):
            if "DEFAULT_DB_PATH" in line:
                offenders.append("%s:%d: %s" % (name, i, line.strip()))
    assert not offenders, (
        "a second default database path was reintroduced; there must be exactly "
        "one, in Config.DB_PATH:\n" + "\n".join(offenders)
    )


def test_database_file_literal_appears_only_in_config():
    """The default filename is named in Config, and nowhere else as a default."""
    offenders = []
    for name, text in _sources():
        if name == "config.py":
            continue
        for i, line in _code_lines(text):
            # A literal default like "./cll_initiatives.db" outside config is a
            # second place the path is decided.
            if "cll_initiatives.db" in line and "getenv" in line:
                offenders.append("%s:%d: %s" % (name, i, line.strip()))
    assert not offenders, "a second database default exists:\n" + "\n".join(offenders)


def test_one_connection_interface():
    """Only db.connect() opens a connection; nothing else calls sqlite3.connect.

    A second helper reaching the database is a second answer to "how do I get a
    connection?", which is what this spec removes.
    """
    offenders = []
    for name, text in _sources():
        if name == "db.py":
            continue
        for i, line in _code_lines(text):
            if "sqlite3.connect(" in line:
                offenders.append("%s:%d: %s" % (name, i, line.strip()))
    assert not offenders, (
        "a connection was opened outside db.connect():\n" + "\n".join(offenders)
    )


def test_the_write_lock_is_taken_in_one_place():
    """BEGIN IMMEDIATE belongs to db.connect(write=True), not to callers."""
    offenders = []
    for name, text in _sources():
        if name == "db.py":
            continue
        for i, line in _code_lines(text):
            if re.search(r"BEGIN\s+IMMEDIATE", line):
                offenders.append("%s:%d: %s" % (name, i, line.strip()))
    assert not offenders, (
        "the write lock is taken outside db.connect(write=True):\n"
        + "\n".join(offenders)
    )


def test_a_read_and_a_write_in_one_request_see_the_same_file(fresh_db):
    """Both go through db.connect() and therefore the one configured path.

    The spec's scenario: a read and a write in the same request must see the
    same data. They do because there is one path, not because they agree by
    coincidence.
    """
    from app import db, repo

    # A write through repo (write=True) ...
    new_id = repo.add_progress_update(
        code="D-A", percent=42, status="On track", note="read/write agree",
        entered_by_id=1,
    )
    assert new_id is not None

    # ... is visible to a read through db.connect() (the read path).
    with db.connect() as conn:
        row = conn.execute(
            "SELECT PercentComplete FROM ProgressUpdates WHERE UpdateID = ?", (new_id,)
        ).fetchone()
    assert row is not None and row["PercentComplete"] == 42

