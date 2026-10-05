# Dockerfile for CLL Initiative Dashboard prototype
FROM python:3.12-slim
WORKDIR /app

# Install system dependencies (none needed beyond python)

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source and sample DB
COPY ospec/cll_initiatives.db ./ospec/cll_initiatives.db
COPY app ./app
COPY ospec ./ospec

# Copy the .env template (will be used at runtime)
COPY .env .env

# Expose the FastAPI port
EXPOSE 8000

# Set environment variables (they can be overridden at container run time)
ENV APP_ENV=PROD
ENV PORT=8000

# Command to run the FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
