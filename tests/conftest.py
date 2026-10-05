import os
import shutil
import sys
import tempfile
from pathlib import Path

# Add the change's source tree to PYTHONPATH so imports resolve
repo_root = Path(__file__).resolve().parents[1]
sys.path.append(str(repo_root / "ospec" / "openspec" / "changes" / "add-initiative-dashboard-prototype"))

import pytest
from fastapi.testclient import TestClient

# Load the FastAPI app from the change's source tree without relying on package import
import importlib.util
app_path = Path(__file__).resolve().parents[1] / "ospec" / "openspec" / "changes" / "add-initiative-dashboard-prototype" / "app" / "main.py"
spec = importlib.util.spec_from_file_location("app.main", str(app_path))
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load FastAPI app from {app_path}")
app_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_mod)
app = app_mod.app

# Path to the repository‑wide sample database (built by build_db.py)
REPO_DB = Path(__file__).resolve().parents[1] / "ospec" / "cll_initiatives.db"

@pytest.fixture(scope="function")
def fresh_db():
    """Create a fresh copy of the sample SQLite database for each test.
    The copy lives in a temporary directory which is removed after the test.
    """
    tmp_dir = tempfile.mkdtemp()
    db_path = Path(tmp_dir) / "cll_initiatives.db"
    shutil.copy2(REPO_DB, db_path)

    # Point the application to this temporary DB via environment variable
    os.environ["DB_PATH"] = str(db_path)
    # Ensure any other required env vars are present (placeholder values)
    os.environ.setdefault("APP_PASSCODE", "testpass")
    os.environ.setdefault("APP_SECRET", "testsecret")
    os.environ.setdefault("APP_ENV", "test")

    yield db_path

    # Cleanup after the test
    try:
        shutil.rmtree(tmp_dir)
    except Exception:
        pass

@pytest.fixture(scope="function")
def client(fresh_db):
    """Return a FastAPI TestClient that uses the fresh DB.
    The placeholder app currently has no auth, so the client can request the
    root endpoint directly. The fixture is ready for future login steps.
    """
    with TestClient(app) as c:
        yield c

