# Dockerfile for CLL Initiative Dashboard prototype
FROM python:3.12-slim
WORKDIR /app

# Drop privileges before the app code is copied in, so nothing that lands in
# /app can be written by the running process. The data directory has to be
# owned by the same user, because the SQLite file is bind-mounted in.
RUN useradd --create-home --uid 10001 appuser \
 && mkdir -p /app/data \
 && chown -R appuser:appuser /app

# The application source lives in the OpenSpec change directory, not at the
# repository root. APP_DIR is the single place that has to change if the
# change is archived out of openspec/changes/ and promoted to the root.
ARG APP_DIR=ospec/openspec/changes/add-initiative-dashboard-prototype

# Copy requirements and install them
COPY ${APP_DIR}/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source and sample DB
COPY ospec/cll_initiatives.db ./ospec/cll_initiatives.db
COPY ${APP_DIR}/app ./app
COPY ospec ./ospec

# Non-root from here on. Task 9.4 asked for this explicitly.
#
# NOTE: uid 10001 must be able to WRITE the database, including the -wal and
# -shm files SQLite creates beside it. Under docker-compose the database is a
# single-file bind mount from the host, so it is owned by whoever owns it on the
# host, not by appuser. On Linux, either chown the file to 10001 or run
# `docker compose run --user root` once to fix ownership. This is unverified
# here - no Docker daemon on this machine - so treat first run as a test.
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