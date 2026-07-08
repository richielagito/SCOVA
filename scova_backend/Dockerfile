FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if needed (e.g. for psycopg2)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    proj-bin \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway injects the PORT environment variable
CMD gunicorn --bind 0.0.0.0:$PORT app:app
