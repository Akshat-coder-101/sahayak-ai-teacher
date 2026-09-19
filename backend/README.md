# Sahayak AI Teacher — Backend

FastAPI + SQLAlchemy adaptive teaching backend providing real-time personalized tutoring, document RAG, assessment grading, vector similarity search, and hardened code sandbox execution.

---

## 1. Authentication & Access Control (RBAC)

The backend enforces JWT-based authentication across all functional API routers (`/api/lesson`, `/api/interact`, `/api/assess`, `/api/report`, `/api/profile`, `/api/learning-path`, `/api/study-tools`, `/api/videos`, `/api/sandbox`, `/api/documents`, `/api/ingest`).

- **Token Transmission**: Dual-mode — accepts `Authorization: Bearer <token>` HTTP header and fallback `access_token` `httpOnly` cookie.
- **Roles**: `student` and `teacher`.
- **Scoped Data Isolation**:
  - Students can only read and update their own profile and session reports. Attempting to query another student's profile returns `403 Forbidden`.
  - Teachers can access student profiles across their designated cohort (or all students if cohort is unconstrained).
- **Public Endpoints**: `/health`, `/api/health`, `/`, `/api/auth/login`, `/api/auth/register`, and `/media/*`.

---

## 2. Hardened Code Sandbox Architecture

Public-facing code execution is defended by a multi-tiered isolation runner implemented in `app/services/code_sandbox.py`.

### Isolation Tiers

1. **Docker Container Isolation (Production / Docker Host)**:
   - When Docker is detected on the host, execution runs in an ephemeral container:
     ```bash
     docker run --rm -i \
       --network none \
       --memory 128m \
       --cpus 0.5 \
       --pids-limit 30 \
       --read-only \
       --tmpfs /tmp:rw,size=16m,noexec,nosuid \
       python:3.9-slim python3 -
     ```
2. **Hardened In-Host Subprocess Runner (Local Dev / Offline / Lightweight)**:
   - When running without a Docker daemon, execution is isolated via:
     - **Process Limit / Fork Bomb Defense**: Intercepts `os.fork` and `os.forkpty` to block child process creation.
     - **Network Egress Denial**: Socket calls (`connect`, `connect_ex`, `send`, `sendto`, `bind`) are intercepted by a `BlockedSocket` harness that raises `PermissionError("Network egress is strictly forbidden in sandbox.")`.
     - **Memory Cap**: Linux address space limit (`RLIMIT_AS`) bounded to 128MB.
     - **Execution Timeout**: Hard cap bounded between 1 and 10 seconds (default 5s).
     - **Filesystem Isolation**: Ephemeral scratch directory via `tempfile.TemporaryDirectory()`; paths sanitized before returning to client.

### Structured Error Output

Failures never leak raw unhandled host stack traces. The endpoint returns structured JSON:

```json
{
  "success": false,
  "stdout": "",
  "stderr": "Execution timed out after 5 seconds.",
  "error_type": "timeout",
  "returncode": -1,
  "output": "Execution timed out after 5 seconds.",
  "isolation_mode": "hardened_subprocess"
}
```

Possible `error_type` values:
- `timeout`
- `memory_limit_exceeded`
- `cpu_limit_exceeded`
- `network_violation`
- `fork_bomb_prevented`
- `syntax_error`
- `runtime_error`

---

## 3. Database & pgvector

- **Primary Target**: PostgreSQL with `pgvector` extension for native vector similarity queries on `material_chunks.embedding` (`Vector(768)`).
- **Local Dev Fallback**: SQLite with deterministic SHA-256 and cosine similarity ranking.
- **Migrations**: Alembic migrations managed in `alembic/`.
