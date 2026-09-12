# Ultra-lightweight Python 3.11/3.12 slim image for strict < 1 GB footprint
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install minimal system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source tree and configuration
COPY . .

# Create persistent lightweight data directory
RUN mkdir -p data/temp data/cache data/sheets_export

# Default entrypoint runs the full pipeline
ENTRYPOINT ["python", "-m", "src.main"]
CMD ["--all"]
