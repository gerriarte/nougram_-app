FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway injects PORT at runtime)
EXPOSE 8000

# Run migrations then start the app (Railway uses PORT env var)
CMD ["sh", "-c", "alembic upgrade head && exec gunicorn main:app -c gunicorn_config.py -b 0.0.0.0:${PORT:-8000}"]





