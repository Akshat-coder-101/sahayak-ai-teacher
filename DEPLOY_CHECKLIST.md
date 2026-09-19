# Sahayak AI Teacher — Production Deployment Checklist

This document provides exact, verified deployment instructions for deploying **Sahayak AI Teacher** to production across **Supabase (Database)**, **Railway (FastAPI Backend + FFmpeg)**, and **Vercel (Next.js Frontend)**, followed by an end-to-end smoke test verification protocol.

---

## 1. Cloud Architecture & Infrastructure Targets

* **Frontend**: Vercel Edge CDN ([FILL: live frontend URL])
* **Backend API**: Railway Container Service ([FILL: live backend API URL])
* **Relational & Vector DB**: Supabase Managed PostgreSQL with `pgvector`
* **Zero-Key Graceful Fallback**: Supported (system boots and runs core features with zero paid API keys)

---

## 2. Step-by-Step Deployment Guide

### Step 1: Managed Database (Supabase PostgreSQL + pgvector)
1. Sign in to [supabase.com](https://supabase.com) and click **New project**.
2. Set project name: `sahayak-db`, set region (e.g. `ap-south-1` Mumbai or nearest to users).
3. Once provisioned, open the **SQL Editor** tab and execute:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
4. Navigate to **Project Settings $\rightarrow$ Database**.
5. Under **Connection string**, select **URI** and copy the connection string.
   > **Note on Railway Connectivity**: Use the IPv4 Connection Pooler URI (port `6543` or `5432`) to ensure reliable resolution from container runners.
   ```
   DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
   ```

---

### Step 2: Backend API Deployment (Railway)
1. Sign in to [railway.app](https://railway.app) and click **New Project $\rightarrow$ Deploy from GitHub Repo**.
2. Select repository: `Akshat-coder-101/sahayak-ai-teacher`.
3. In service **Settings**:
   - **Root Directory**: `/backend`
   - Railway automatically detects `backend/Dockerfile` which bundles Python 3.11, system FFmpeg, and DejaVu fonts.
   - **Healthcheck Path**: `/health/ready`
4. In **Variables**, configure the environment variables:

| Variable | Description | Value / Example |
|---|---|---|
| `ENV` | Environment Mode | `production` |
| `DATABASE_URL` | Supabase Pooler URI | `postgresql://...` |
| `JWT_SECRET_KEY` | JWT Signing Key ($\ge 32$ characters) | `[FILL: generate 32+ char secure key]` |
| `FRONTEND_URL` | Deployed Vercel URL | `https://[FILL: live frontend URL]` |
| `CORS_ORIGINS` | Comma-separated CORS allowed origins | `https://[FILL: live frontend URL],http://localhost:3000` |
| `VIDEO_MODE` | Lecture generation mode | `demo` |
| `AVATAR_PROVIDER` | Default avatar engine | `free_avatar` |
| `GEMINI_API_KEY` | Google AI Studio Key (Optional) | `[FILL: optional gemini key]` |
| `GROQ_API_KEY` | Groq Failover Key (Optional) | `[FILL: optional groq key]` |
| `YOUTUBE_API_KEY`| YouTube Data API Key (Optional) | `[FILL: optional youtube key]` |
| `ELEVENLABS_API_KEY` | TTS Engine (Optional) | `[FILL: optional elevenlabs key]` |
| `DEEPGRAM_API_KEY` | Voice STT Engine (Optional) | `[FILL: optional deepgram key]` |

5. Under **Volumes**, add a persistent volume:
   - Mount Path: `/app/generated_media` (preserves rendered video clips and audio).
6. In **Networking**, click **Generate Domain** (e.g. `https://sahayak-backend-production.up.railway.app`).
7. Run database migrations and seed baseline accounts:
   ```bash
   # From your local terminal using the production DATABASE_URL:
   alembic upgrade head
   python scripts/seed_demo.py
   ```

---

### Step 3: Frontend Web Application Deployment (Vercel)
1. Sign in to [vercel.com](https://vercel.com) and click **Add New $\rightarrow$ Project**.
2. Import repository: `Akshat-coder-101/sahayak-ai-teacher`.
3. In Project Configuration:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: Click *Edit* and choose `frontend`.
4. In **Environment Variables**, add:
   ```env
   NEXT_PUBLIC_API_BASE_URL=https://[FILL: live backend API URL]/api
   ```
5. Click **Deploy**. Vercel compiles the Next.js 15 App Router bundle.
6. Copy the assigned Vercel URL (e.g. `https://sahayak-frontend.vercel.app`) back into Railway's `FRONTEND_URL` and `CORS_ORIGINS`.

---

## 3. Graceful Zero-Key Degradation Matrix

If deployed with **zero third-party paid API keys**, Sahayak gracefully falls back to built-in deterministic offline engines:

| Subsystem | Behavior with Valid API Key | Graceful Fallback with ZERO Keys |
|---|---|---|
| **LLM Reasoning** | Gemini 2.5 Flash / Groq LLaMA 3.3 / Claude 3.7 | Structured rule-based lesson planner & evaluation heuristics |
| **Embeddings (RAG)** | 768-dim `gemini-embedding-001` vectors | 768-dim SHA-256 deterministic pseudo-vectors with cosine similarity |
| **Video Narration (TTS)** | ElevenLabs Neural Voice / Piper Neural TTS | Client-side HTML5 Web Speech API (`speechSynthesis`) |
| **Voice Q&A (STT)** | Deepgram Nova-2 speech recognition | Client-side Web Speech Recognition / text keyboard entry |
| **Teacher Avatar** | Colossyan / D-ID / HeyGen photo-realism | Audio-reactive HTML5 Canvas Avatar with waveform mouth sync |
| **YouTube Enrichment** | YouTube Data API v3 validated embeddable videos | Verified search deep-links (`https://youtube.com/results?search_query=...`) |
| **Video Rendering** | FFmpeg MP4 with H.264 video & AAC audio | Progressive slide viewer + blackboard visuals + HTML5 audio |

---

## 4. Post-Deployment Smoke Test Protocol

Run this 6-step smoke test after deploying to verify system integrity:

### Test 1: Health & Readiness Check
* **Target**: `GET https://[FILL: live backend API URL]/health` and `/health/ready`
* **Expected Response**: HTTP 200 `{"status": "healthy", "service": "sahayak-backend"}`
* **Verification Command**:
  ```bash
  curl -i https://[FILL: live backend API URL]/health
  ```

### Test 2: One-Click Demo Student Authentication
* **Target**: Click **"⚡ Try Demo (One-Click Judge Access)"** on the landing page or login page.
* **Expected Outcome**: Instant session establishment without manual credential typing; redirects to `/lesson/session-demo-photosynthesis`.
* **API Check**:
  ```bash
  curl -X POST https://[FILL: live backend API URL]/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email": "demo.student@sahayak.edu", "password": "DemoStudent2026!"}'
  ```

### Test 3: Document Upload & Ingestion
* **Target**: Open `https://[FILL: live frontend URL]/upload`
* **Action**: Drag and drop `samples/photosynthesis_chapter.pdf`.
* **Expected Outcome**: Successfully uploads, parses 3 pages, extracts key topics, and displays chunk count.

### Test 4: Interactive Lesson Playback & Subtitles
* **Target**: `https://[FILL: live frontend URL]/lesson/session-demo-photosynthesis`
* **Expected Outcome**:
  * Blackboard visual diagram loads cleanly.
  * Audio plays narration.
  * Synchronized subtitle pill appears docked at the bottom of the video player above timeline scrub bar.
  * Canvas avatar articulates in sync with audio.

### Test 5: Instant Mid-Lesson Language Switch
* **Target**: While on the lesson player, click the **"हिंदी"** or **"Hinglish"** language button.
* **Expected Outcome**: Button displays an animated translation spinner, and within ~1–2 seconds updates the blackboard text and synthesized narration.

### Test 6: Checkpoint Evaluation & Adaptive Remediation
* **Target**: In segment checkpoint, submit the deliberate misconception:
  *"Plants appear green because chlorophyll absorbs green light."*
* **Expected Outcome**:
  * Semantic Evaluator diagnoses misconception (`status: "misconception"`).
  * Opens Misconception Remediation Modal explaining the difference between absorption and reflection with a fresh analogy.
