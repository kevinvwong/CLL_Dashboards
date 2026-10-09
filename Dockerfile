# Dockerfile for CLL Initiative Dashboard prototype
FROM python:3.12-slim
WORKDIR /app

# Drop privileges before the app code is copied in, so nothing that lands in
# /app can be written by the running process. The data directory has to be
# owned by the same user, because the SQLite file is bind-mounted in.
RUN useradd --create-home --uid 10001 appuser \
 && mkdir -p /app/data \
 && chown -R appuser:appuser /app

# The application lives at the repo root: the app package, requirements.txt,
# and the sample database. APP_DIR is the one place that has to change if the
# app is relocated.
ARG APP_DIR=app

# Copy requirements and install them
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application package (static/ and templates/ are inside it) and the
# sample database, which DB_PATH points at relative to WORKDIR.
COPY cll_initiatives.db ./cll_initiatives.db
COPY ${APP_DIR} ./app
COPY db ./db
# The in-app guide renders markdown from DOCS_PATH (default ./docs). Without
# this the /guide page is empty in the container.
COPY docs ./docs

# Hand /app to appuser AFTER the copies above, not before. The earlier chown
# only covered the then-empty directory, so every file COPY brought in
# afterwards (cll_initiatives.db, app/, db/, docs/) landed owned by root:root.
# The app runs as uid 10001, so opening the database raised "attempt to write a
# readonly database" the moment connect() set PRAGMA journal_mode=WAL -- which
# database_reachable() reports as "database unreachable", so /healthz answered
# 503 against a perfectly readable database.
#
# /app is chowned whole rather than just the .db because SQLite also writes the
# -wal and -shm sidecars into the directory holding the database, and BACKUP_DIR
# defaults to ./backups underneath it.
RUN chown -R appuser:appuser --from=root /app

# Non-root from here on. Task 9.4 asked for this explicitly.
#
# Under docker-compose the database may instead be a single-file bind mount from
# the host, in which case this chown is masked by the host's ownership: either
# chown the host file to 10001, or run `docker compose run --user root` once.
USER appuser

# The port comes from the environment at runtime: docker-compose publishes
# 8000, the deployment platform injects its own PORT. 8000 stays the default
# so `docker run -p 8000:8000` and local development keep working.
ENV APP_ENV=PROD
ENV PORT=8000
EXPOSE 8000

# Command to run the FastAPI server. Shell form so ${PORT} is expanded --
# exec form would pass the literal string. DB_PATH is relative to WORKDIR.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]