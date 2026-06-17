# Use Python 3.13 slim image for smaller footprint
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt gunicorn

# Copy the entire project
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Set environment variables for production
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Cloud Run injects PORT env var (default 8080)
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run with Gunicorn for production (1 worker for SQLite compatibility)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 4 --timeout 120 --preload --chdir backend app:app

