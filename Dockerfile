# Root Dockerfile for Railway / Cloud Container Deployments
FROM python:3.11-slim

# System dependencies:
#   ffmpeg + libx264  -> MP4 lesson rendering
#   fonts-dejavu-core -> text on Pillow slides / matplotlib charts
#   curl              -> container HEALTHCHECK
#   build-essential   -> native compilation support
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libx264-dev \
    fonts-dejavu-core \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend source
COPY backend/ /app/

# Install python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create persistent storage directories
RUN mkdir -p /app/data/media /app/data/docs /app/data/video_cache

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    MEDIA_DIR=data/media \
    DOC_STORAGE_DIR=data/docs \
    VIDEO_CACHE_DIR=data/video_cache \
    DATABASE_URL=sqlite:////app/data/sahayak.db \
    HOST=0.0.0.0 \
    PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Start FastAPI application bound to dynamic cloud $PORT
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
