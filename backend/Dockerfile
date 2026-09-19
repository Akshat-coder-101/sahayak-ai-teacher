# Production Dockerfile for the Sahayak AI Teacher backend.
# Bundles Python 3.9, system FFmpeg (with libx264) for video synthesis, and
# TrueType fonts for slide text rendering. Build context is the backend/ directory:
#   docker build -t sahayak-backend backend/
FROM python:3.9-slim

# System dependencies:
#   ffmpeg + libx264  -> MP4 lesson rendering (app/services/video.py)
#   fonts-dejavu-core -> text on Pillow slides / matplotlib charts
#   curl              -> container HEALTHCHECK
#   build-essential   -> wheels that need compilation on some architectures
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libx264-dev \
    fonts-dejavu-core \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the backend source (respecting .dockerignore) and install the project plus
# its runtime dependencies declared in pyproject.toml.
COPY . /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Writable, persistable storage. Mount a volume at /app/data to persist the SQLite
# database, uploaded documents, and generated media across container restarts.
RUN mkdir -p /app/data/media /app/data/docs

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    MEDIA_DIR=data/media \
    DOC_STORAGE_DIR=data/docs \
    DATABASE_URL=sqlite:////app/data/sahayak.db \
    HOST=0.0.0.0 \
    PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# The FastAPI instance is `app` in backend/main.py, so the ASGI target is main:app.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
