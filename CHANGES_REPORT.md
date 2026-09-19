# Changes Report — Sahayak AI Teacher

This document logs all baseline findings, discrepancy audits, implementation changes, test results, benchmarks, and manual steps for the hackathon submission.

---

## Phase 0: Baseline Audit

### 1. Test Suite & Build Baseline Execution
* **Backend Pytest Run**:
  * Command: `python -m pytest tests/ -v` (Python 3.14.6, pytest-9.1.1)
  * Real Execution Time: **491.04s (8m 11s)**
  * Status: **90 passed, 0 skipped, 0 failed, 3 deprecation warnings** (FastAPI / Starlette test client deprecation)
  * Breakdown per test file:
    * `tests/test_advanced_features.py`: **6 passed**
    * `tests/test_all_endpoints.py`: **28 passed**
    * `tests/test_assessment_pipeline.py`: **6 passed**
    * `tests/test_auth.py`: **8 passed**
    * `tests/test_document_and_export.py`: **7 passed**
    * `tests/test_groq_token_cap.py`: **2 passed**
    * `tests/test_instruction_and_adaptation.py`: **6 passed**
    * `tests/test_optimized_video.py`: **2 passed**
    * `tests/test_profile_and_learning_path.py`: **7 passed**
    * `tests/test_rag_benchmark.py`: **1 passed**
    * `tests/test_regional_language.py`: **3 passed**
    * `tests/test_sandbox.py`: **6 passed**
    * `tests/test_visual_planning.py`: **8 passed**
    * **Total**: **90 passed**
* **Frontend Build Run**:
  * Command: `npm run build` (Next.js 15.5.24)
  * Real Execution Time: **27.5s compilation + type check**
  * Status: **Success (Exit code 0)**
  * Output: 12 static/dynamic routes compiled cleanly with 0 TypeScript/lint errors.

---

### 2. Contradictions & Unverified Claims Identified

| Category | Claimed in README / DOCUMENTATION | Verified in Codebase | Finding / Action Needed |
|---|---|---|---|
| **Test Counts** | README says "85 passing tests and 2 skipped", "87 items", "90+ tests". DOCUMENTATION Section 18 table sums to ~79 tests. | `pytest --collect-only -q` collected exactly **90 tests**, all **90 passed**, 0 skipped, 0 failed. | Update all documentation to exact measured reality: **90 passing tests across 13 test suites, 0 skipped**. |
| **Demo-Mode Scene Count** | "3-4 scenes" vs "2 scenes" mentioned across different sections. | `backend/app/services/video.py` lines 594-597: `if active_mode == "demo" and len(raw_segments) > 4: segments_to_process = raw_segments[:3]` (caps to 3 scenes, or fewer if lesson has 1-2). | Standardize documentation strictly to: **"up to 3 scenes (or raw segment count if $\le$ 3)"**. |
| **FFmpeg Stitch Speedup** | README states: "drops from 35s to 0.11s (7.1x faster)". In other notes: "45s -> <2s". | Mathematically, $35 / 0.11 \approx 318\times$, not $7.1\times$. Without a live benchmark harness, exact times vary by CPU. | Add `scripts/benchmark_stitch.py` to measure real-world stitch speedup and report measured numbers. |
| **PostgreSQL Version** | `docker-compose.yml` specifies `pgvector/pgvector:pg16` (PostgreSQL 16). README Option C states `PostgreSQL 17`. | Dockerfile and compose use **PostgreSQL 16**. Supabase cloud uses PostgreSQL 15/16/17 depending on creation date. | Harmonize docs to state: **PostgreSQL 16 (local docker-compose) / 16+ (cloud managed)**. |
| **Model Names** | README mentions `gemini-2.5-flash`, `llama-3.3-70b-versatile`, `claude-3-7-sonnet`. | `backend/app/config.py`: `GEMINI_MODEL="gemini-2.5-flash"`, `GROQ_MODEL="llama-3.3-70b-versatile"`, `ANTHROPIC_MODEL="claude-3-7-sonnet-20250219"`. | Accurately verified; ensure exact model strings are uniform. |
| **Avatar Providers** | DOCUMENTATION Section 15 lists `Hedra`. | `HEDRA_API_KEY` exists in `config.py` but is **not** implemented in `backend/app/services/avatar.py`. | Flag Hedra as stub/unimplemented; remove from active verified provider list. |
| **Vector DB / Storage** | Mentions Pinecone and Supabase object storage. | Pinecone and Supabase object storage variables exist in `config.py` but have no active client in `rag.py` or `video.py`. | Mark Pinecone and Supabase object storage as "Stub / not verified" in `FEATURE_STATUS.md`. Supabase PostgreSQL database is verified. |
| **Hackathon Name** | README says "AI Innovation Hackathon 2026". | Submission instructions state "Open Innovation Hackathon". | Flag mismatch; update to "Open Innovation Hackathon (AI Track)". |
| **Absolute Claims** | Claims like "zero hallucination", "zero source degradation", "100% pass rate". | Software should use empirically grounded terminology: "measured 0% hallucinated YouTube URLs", "deterministic citation verification", etc. | Replace exaggerated absolutes with empirically validated wording backed by evaluation benchmarks. |

---

## Phase 1: Production Hardening

### 1. Implementation Details
* **Production Startup Secret Enforcement (`backend/main.py`)**:
  * In `lifespan()`, if `settings.ENV == "production"`, validates that `JWT_SECRET_KEY` is not the default dev secret and has a length $\ge 32$ characters. Otherwise, aborts startup immediately with `RuntimeError`.
* **CORS Wildcard Filtering (`backend/main.py`)**:
  * When `settings.ENV == "production"`, any wildcard `*` in `CORS_ORIGINS` is stripped and rejected, preventing unauthorized cross-origin credential leaks.
* **Production Cookie Hardening (`backend/app/api/auth.py`)**:
  * `_set_auth_cookie` sets `httponly=True`, `samesite="lax"`, and dynamically enforces `secure=True` when `settings.ENV == "production"`.
* **Rate Limiting Engine (`backend/app/services/rate_limiter.py`)**:
  * Implemented `SlidingWindowRateLimiter`: thread-safe in-memory sliding window rate limiter tracking client IP / `X-Forwarded-For`.
  * Attached `auth_rate_limiter` (15 requests/min) to `/api/auth/register` and `/api/auth/login`.
  * Attached `sandbox_rate_limiter` (25 requests/min) to `/api/sandbox/run`.
  * Returns standard HTTP 429 Too Many Requests with canonical error JSON and `Retry-After` header.
* **Canonical Error Header Forwarding (`backend/main.py`)**:
  * Updated `make_canonical_error()` and `http_exception_handler()` to forward upstream exception headers (such as `Retry-After` and `WWW-Authenticate`) in all `JSONResponse` outputs.
* **CI Workflow (`.github/workflows/ci.yml`)**:
  * Added unified multi-job GitHub Actions pipeline:
    1. `backend-test`: Ubuntu runner, Python 3.11, ffmpeg, DejaVu fonts, requirements installation, and `pytest tests/ -v`.
    2. `frontend-build`: Ubuntu runner, Node.js 20, `npm install`, and `npm run build`.

### 2. Verification & Test Metrics
* **New Test Suite**: `backend/tests/test_production_hardening.py`
  * Tests Added: **9 unit tests**
  * Status: **9 passed, 0 failed in 34.85s**
  * Test Breakdown:
    * `test_production_startup_jwt_secret_validation`: Verifies startup aborts on default dev secret or $<32$ char key in production, and boots cleanly with strong key.
    * `test_production_auth_cookie_attributes`: Verifies `HttpOnly`, `SameSite=lax`, and `Secure` attributes across environments.
    * `test_production_cors_filters_wildcard`: Verifies `*` is filtered out in production CORS.
    * `test_auth_rate_limiting`: Verifies 15 requests pass, 16th receives HTTP 429 with `Retry-After`.
    * `test_sandbox_rate_limiting`: Verifies 25 requests pass, 26th receives HTTP 429.
    * `test_upload_validation_empty_file`: Verifies 0-byte file receives HTTP 400.
    * `test_upload_validation_wrong_extension`: Verifies `.sh` receives HTTP 400.
    * `test_upload_validation_no_extension`: Verifies extensionless file receives HTTP 400.
    * `test_upload_validation_oversize`: Verifies file exceeding `MAX_UPLOAD_MB` receives HTTP 400.
* **Cumulative Test Matrix**: **99 passing tests** (90 baseline + 9 production hardening), 0 failed, 0 skipped.

---

