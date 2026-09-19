# Sahayak AI Teacher — Deployment & Production Guide

This guide covers deployment options for Sahayak AI Teacher across local development, multi-container Docker Compose staging/production, and cloud production environments.

---

## 1. Architecture Overview

```
                      +-----------------------------+
                      |         Web Client          |
                      |   (Browser / Mobile Web)    |
                      +--------------+--------------+
                                     |
                                     | HTTPS / WSS
                                     v
                      +-----------------------------+
                      |    Reverse Proxy / Ingress  |
                      |        (Nginx / Caddy)      |
                      +------+---------------+------+
                             |               |
              /api/*, /media |               | SSR / Static
                             v               v
             +---------------+--+     +------+-----------+
             |  FastAPI Backend |     | Next.js Frontend |
             |    (Port 8000)   |     |    (Port 3000)   |
             +--------+---------+     +------------------+
                      |
        +-------------+-------------+
        |                           |
        v                           v
+-------------------+      +------------------+
|  PostgreSQL 16    |      |  Isolated Code   |
|    + pgvector     |      |  Sandbox Runner  |
|    (Port 5432)    |      | (Egress Blocked) |
+-------------------+      +------------------+
```

### Components:
1. **Frontend:** Next.js 15 (React 19, TypeScript) with Standalone server output.
2. **Backend:** FastAPI (Python 3.9+) with JWT RBAC, Provider Cascade, and RAG Engine.
3. **Database:** PostgreSQL 16 with `pgvector` extension enabled (or zero-dependency SQLite fallback).
4. **Code Execution Sandbox:** Subprocess isolation with ephemeral scratch directory, memory limits (128MB), timeout (10s), network egress denial, and fork-bomb prevention.

---

## 2. Environment Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Configure core security variables:
   ```env
   JWT_SECRET_KEY=use-a-strong-random-secret-at-least-32-chars-long
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
   ```

3. Configure database:
   - **SQLite (Zero setup local dev):**
     ```env
     DATABASE_URL=sqlite:///./sahayak.db
     ```
   - **PostgreSQL + pgvector (Production / Docker):**
     ```env
     DATABASE_URL=postgresql+psycopg2://sahayak:sahayak_pass@db:5432/sahayak_db
     ```

4. Configure AI Providers (optional - zero-API-key fallbacks are built in):
   ```env
   GEMINI_API_KEY=AIzaSy...
   GROQ_API_KEY=gsk_...
   ANTHROPIC_API_KEY=sk-ant-...
   ```

---

## 3. Local Development Setup

### 3.1 Backend
```bash
cd backend
python3 -m venv ../venv
source ../venv/bin/activate
pip install -r requirements.txt

# Run database migrations (SQLite or Postgres)
alembic upgrade head

# Start FastAPI dev server
uvicorn main:app --reload --port 8000
```

### 3.2 Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser. Default test accounts:
- **Teacher:** `teacher@sahayak.ai` / `password123`
- **Student:** `student@sahayak.ai` / `password123`

---

## 4. Docker Compose Deployment (Recommended)

Sahayak provides a multi-container stack orchestrated via `docker-compose.yml` with:
- `db`: `pgvector/pgvector:pg16`
- `backend`: FastAPI Python container
- `frontend`: Next.js 15 standalone multi-stage container

### 4.1 Launching the Stack
```bash
# Build and launch all services in detached mode
docker compose up --build -d

# Verify all containers are healthy
docker compose ps
```

### 4.2 Running Database Migrations in Docker
```bash
docker compose exec backend alembic upgrade head
```

### 4.3 Viewing Logs
```bash
# Backend logs
docker compose logs -f backend

# Frontend logs
docker compose logs -f frontend

# Database logs
docker compose logs -f db
```

### 4.4 Stopping the Stack
```bash
docker compose down
# Or with data volume wipe:
docker compose down -v
```

---

## 5. Database Migrations (Alembic)

Database schema updates are managed with Alembic located in `backend/alembic/`.

### Migration Commands:
```bash
cd backend

# Apply all pending migrations:
alembic upgrade head

# Check current revision:
alembic current

# Rollback one migration:
alembic downgrade -1

# Generate a new migration after editing models in app/database.py:
alembic revision --autogenerate -m "describe_changes"
```

The database automatically supports:
- `pgvector.sqlalchemy.Vector(768)` when running against PostgreSQL with pgvector.
- Serialized JSON fallback vector storage when running against SQLite.

---

## 6. Cloud Production & Hardening Best Practices

### 6.1 Reverse Proxy (Nginx Configuration Example)
Deploy Nginx in front of Docker containers with HTTP/2 and SSL/TLS termination:

```nginx
server {
    listen 443 ssl http2;
    server_name sahayak.example.com;

    ssl_certificate /etc/letsencrypt/live/sahayak.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sahayak.example.com/privkey.pem;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Frontend SSR & Assets
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API Endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    # Audio & Generated Media
    location /media/ {
        proxy_pass http://127.0.0.1:8000/media/;
        expires 7d;
        add_header Cache-Control "public, no-transform";
    }
}
```

### 6.2 Health Checks & Monitoring
- **Backend Liveness:** `GET http://localhost:8000/health`
  - Returns `{"status": "healthy", "service": "sahayak-backend"}`
- **Authentication Check:** `GET http://localhost:8000/api/auth/me`
  - Requires `Authorization: Bearer <token>` or `access_token` cookie.
- **Frontend Health:** `GET http://localhost:3000/api/health`

### 6.3 Resource Limits & Sandboxing Security
The backend execution sandbox runs student-generated Python snippets. For maximum production isolation:
1. Docker Host: ensure the backend container has access to Docker socket if container-in-container execution is desired, or relies on the hardened in-host sandbox.
2. The in-host runner enforces:
   - 10-second hard wall clock timeout.
   - 128MB RAM limit.
   - Sockets & networking blocked (`BlockedSocket` raises `PermissionError`).
   - Forking disabled (`os.fork` monkeypatched to prevent fork bombs).
   - Scratch directories cleaned up after execution.
