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
