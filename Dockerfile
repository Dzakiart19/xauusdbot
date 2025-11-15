FROM python:3.11-slim

# Install system dependencies for matplotlib & database
RUN apt-get update && apt-get install -y \
    gcc \
    libgl1-mesa-glx \
    libgomp1 \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create persistent directories
RUN mkdir -p /app/data /app/logs /app/data/charts

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Run bot
CMD ["python", "-u", "main.py"]
