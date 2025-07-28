# Dockerfile

FROM python:3.10-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies for building Python packages and Postgres client libraries
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      gcc \
      python3-dev \
      libssl-dev \
      libpq-dev \
      curl && \
    rm -rf /var/lib/apt/lists/*

# Create a non‑root user to run our app
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Install Python dependencies
COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure the app directory is owned by our non‑root user
RUN chown -R appuser:appgroup /app

# Switch to non‑root user
USER appuser

# Healthcheck to hit FastAPI root (adjust path if you add a /health endpoint)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Start the app with multiple workers
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
