"""The Docker image must be able to serve the whole app.

Found 2026-10-08: the Dockerfile copied only `app`, `db`, `requirements.txt` and
the database, so the in-app `/guide` (which renders `DOCS_PATH=./docs`) was empty
in the container. The zip-deploy path and the Docker path are different, and only
the zip path was guarded. These checks read the Dockerfile and assert the
runtime-required files are copied.
"""
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCKERFILE = os.path.join(REPO, "Dockerfile")


def _dockerfile():
    return open(DOCKERFILE, encoding="utf-8").read()


def test_the_image_copies_the_docs_the_guide_renders():
    """DOCS_PATH defaults to ./docs; the guide renders it. If docs/ is not in the
    image, /guide is empty."""
    text = _dockerfile()
    assert "COPY docs" in text, "the Dockerfile does not copy docs/ (the guide needs it)"


def test_the_image_copies_the_app_and_the_database_and_the_schema():
    text = _dockerfile()
    assert "COPY ${APP_DIR} ./app" in text or "COPY app ./app" in text
    assert "cll_initiatives.db" in text
    assert "COPY db ./db" in text


def test_the_image_requires_an_index_for_the_app():
    """`COPY app ./app` ships the package; app/main.py must exist for the import."""
    assert os.path.exists(os.path.join(REPO, "app", "main.py"))


def test_a_dockerignore_keeps_secrets_and_scratch_out_of_the_build():
    ignore = os.path.join(REPO, ".dockerignore")
    assert os.path.exists(ignore), "no .dockerignore: the build context ships .git/.env"
    text = open(ignore, encoding="utf-8").read()
    for entry in (".env", ".git", "deploy.zip"):
        assert entry in text, ".dockerignore does not exclude %s" % entry
