# Dockerfile for CLL Initiative Dashboard prototype
FROM python:3.12-slim
WORKDIR /app

# The application source lives under ospec/app. APP_DIR is the single place
# that has to change if the app is relocated.
ARG APP_DIR=ospec/app

# Copy requirements and install them
COPY ${APP_DIR}/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source and sample DB
COPY ospec/cll_initiatives.db ./ospec/cll_initiatives.db
COPY ${APP_DIR}/app ./app
COPY ospec ./ospec

# The port comes from the environment at runtime: docker-compose publishes
# 8000, the deployment platform injects its own PORT. 8000 stays the default
# so `docker run -p 8000:8000` and local development keep working.
ENV APP_ENV=PROD
ENV PORT=8000
EXPOSE 8000

# Command to run the FastAPI server. Shell form so ${PORT} is expanded --
# exec form would pass the literal string. DB_PATH is relative to WORKDIR.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]