# Sahayak AI Teacher 🎓
### AI Innovation Hackathon 2026 · Technical Submission
**Track**: *AI Teacher: Build a Human-Like AI Educator That Teaches Through Video*

> **"A True Adaptive AI Teacher, Not Just Another Chatbot."**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js 15](https://img.shields.io/badge/frontend-Next.js%2015-black.svg)](https://nextjs.org/)
[![React 19](https://img.shields.io/badge/ui-React%2019-61dafb.svg)](https://react.dev/)
[![TailwindCSS](https://img.shields.io/badge/styling-TailwindCSS-38bdf8.svg)](https://tailwindcss.com/)
[![Docker Ready](https://img.shields.io/badge/docker-compose%20ready-2496ED.svg)](https://www.docker.com/)
[![PostgreSQL & pgvector](https://img.shields.io/badge/database-PostgreSQL%2016%20%2B%20pgvector-336791.svg)](https://github.com/pgvector/pgvector)
[![Auth & RBAC](https://img.shields.io/badge/auth-JWT%20%2B%20RBAC-orange.svg)]()
[![YouTube Data API](https://img.shields.io/badge/grounding-YouTube%20API%20v3-red.svg)](https://developers.google.com/youtube/v3)
[![Tests](https://img.shields.io/badge/tests-85%20passed%20%7C%202%20skipped%20(100%25)-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🧭 1. Problem Statement

Traditional digital learning platforms typically deliver static pre-recorded videos or generic text chatbots. However, effective pedagogy requires active, adaptive teaching:
* **Diagnoses prior knowledge** and dynamically calibrates depth, prerequisites, and pacing.
* **Plans a structured cognitive progression** grounded strictly in verified source materials without hallucinations.
* **Explains orally with synchronized visual illustrations** on an interactive blackboard (formulas, diagrams, charts, runnable code).
* **Periodically pauses for pedagogical checkpoints** to test comprehension via text or spoken voice.
* **Detects misconceptions**, identifies cognitive root causes, and reteaches adaptively using fresh analogies and alternate visual modalities.
* **Validates mastery** with document-attributed quizzes and a diagnostic learning gap map.
* **Retains continuous student state** across lessons to personalize homework, flashcards, study schedules, and exam readiness.

**Sahayak AI Teacher** is an autonomous pedagogical educator that replaces conversational chatbots with an end-to-end interactive, animated teaching video, adaptive state machine, isolated sandbox execution, and continuous learner profile intelligence.

---

## 💡 2. Solution Overview & Unified Pipeline

Sahayak transforms any uploaded educational document (textbook PDF, DOCX, PPTX, lecture notes) or user-specified topic into an immersive, personalized, video-augmented classroom session:

```mermaid
flowchart TD
    Auth[JWT Auth & RBAC: Student / Teacher] --> Student[Student Identity & Learner Profile]
    Student --> Path[Curriculum Learning Path DAG]
    Path --> Teacher[AI Teacher Engine]
    
    subgraph Personalities [Teacher Personalities]
        Socratic[Socratic Guide]
        Friendly[Friendly Mentor]
        Strict[Strict Exam Coach]
        VisualP[Visual Architect]
    end
    Teacher --> Personalities
    
    Teacher --> Video[Animated Video & Blackboard]
    Video --> Sandbox[Hardened Python Code Sandbox]
    Video --> Checkpoint[In-Lesson Checkpoints]
    Checkpoint --> Assess[Assessment & Evaluator]
    Assess --> Mastery[Concept Mastery & Gap Map]
    
    Mastery --> Rev[Revision Mode]
    Mastery --> FC[Flashcard Deck & Review]
    Mastery --> Notes[Smart Revision Notes]
    Mastery --> HW[Personalized Homework]
    Mastery --> Exam[Exam Prep Roadmap]
    Mastery --> Plan[Dynamic Study Planner]
    Mastery --> Analytics[Learning Analytics & Trajectories]
    
    FC -. Updates Mastery .-> Mastery
    Rev -. Reassesses .-> Mastery
    Plan -. Rebalances .-> Path
    Analytics -. Continuous Feedback .-> Student
```

### Core Innovations:
1. **Document-Grounded Lesson Pipeline**: Every lesson segment, video explanation, and quiz question is strictly attributed to source document chunks with verbatim citations, page numbers, and confidence ratings.
2. **Multiple Teacher Personalities**: Choose between `Socratic Guide`, `Friendly Mentor`, `Strict Exam Coach`, and `Visual Architect` without altering factual curriculum accuracy.
3. **8 Advanced Integrated Study Tools**: Revision Mode, Interactive Flashcards, Automatic Structured Notes, Adaptive Tiered Homework, Exam Preparation Tracks, Dynamic Study Planner, and Learning Analytics with Trajectory tracking.
4. **Multi-Provider AI Avatar & Video Engine**: Supports **D-ID**, **HeyGen**, **Synthesia**, **Tavus**, **Colossyan**, **Replicate (LivePortrait)**, **Hugging Face SDXL**, and a built-in **Zero-Cost Audio-Reactive Canvas Avatar**.
5. **AI-Curated YouTube Educational Grounding**: Leverages YouTube Data API v3 with SQLite caching and LLM re-ranking to embed real, verified video deep-dives without hallucinations.
6. **Multi-Tiered Isolated Code Execution Sandbox**: CS/Coding lessons execute in an isolated, network-egress-blocked, memory-capped Docker container (`python:3.9-slim`, `--network none`, `--memory 128m`, `--cpus 0.5`, `--pids-limit 30`, read-only rootfs) with automatic fallback to an in-host hardened, fork-bomb protected subprocess runner.
7. **Secure Authentication & RBAC**: Dual-mode JWT bearer token and HTTP-only cookie authentication (`/api/auth/register`, `/api/auth/login`, `/api/auth/logout`, `/api/auth/me`), student profile scoping, and teacher cohort management.
8. **Dual-Engine Persistence & Alembic Migrations**: Native PostgreSQL 16 + `pgvector` for fast semantic similarity search in production, with zero-dependency local SQLite fallback and versioned Alembic migrations.
9. **Hierarchical Multilingual Speech**: ElevenLabs Neural Voice $\rightarrow$ Local Offline Piper Neural TTS $\rightarrow$ Web Speech API fallback across **7 languages** (English, Hindi, Hinglish, Tamil, Telugu, Bengali, Spanish).
10. **Diagnostic Learning Gap Map**: Pinpoints conceptual strengths and weaknesses linked directly to document source chunks with actionable revision steps.

---

## 🌟 3. Advanced Pedagogical Features Matrix

| Feature | Capability | Implementation & Endpoints |
|---|---|---|
| **Authentication & RBAC** | Student and Teacher registration, login, HTTP-only secure cookie, profile isolation | `POST /api/auth/register`<br>`POST /api/auth/login`<br>`POST /api/auth/logout`<br>`GET /api/auth/me` |
| **Multiple Teacher Personalities** | 4 distinct archetypes adjusting tone, question frequency, and scaffolding | `GET /api/study-tools/personalities`<br>`POST /api/study-tools/personalities/select` |
| **Targeted Revision Mode** | Remediation lessons prioritizing weak & misunderstood concepts | `POST /api/study-tools/revision-session` |
| **Grounded Flashcards** | Generates structured cards (definitions, formulas, misconceptions) with review tracking | `POST /api/study-tools/flashcards/generate`<br>`POST /api/study-tools/flashcards/review` |
| **Automatic Revision Notes** | Extracts key ideas, formulas, examples, and common traps into structured markdown | `POST /api/study-tools/notes/generate` |
| **Personalized Homework** | Tiered difficulty (Advanced Challenge, Standard, Remedial with step hints) | `POST /api/study-tools/homework/generate` |
| **Exam Preparation Mode** | 4-phase milestone roadmaps prioritizing high-weight topics & scheduled mock exams | `POST /api/study-tools/exam-prep/generate` |
| **Dynamic Study Planner** | Converts curriculum nodes to daily schedules; auto-rebalances for missed days | `POST /api/study-tools/study-plan/generate`<br>`POST /api/study-tools/study-plan/recalculate` |
| **Learning Analytics & Trajectory** | Aggregates mastery %, study time, questions answered, and tracks momentum (`improving`, `recovering`) | `GET /api/study-tools/analytics/{user_id}` |
| **Document RAG Ingest** | Parses `.pdf`, `.docx`, `.pptx`, `.txt`, `.md` with chunk indexing and citations | `POST /api/documents/upload`<br>`POST /api/ingest` |
| **Isolated Code Execution** | Zero-network, memory-capped Docker container sandbox with subprocess fallback | `POST /api/sandbox/run` |
| **Talking AI Presenter** | Mouth articulation & blinking synced to audio waveforms on HTML5 Canvas | Web Audio API (`AnalyserNode`) |
| **Voice Q&A** | Real-time speech-to-text for oral student checkpoint responses | Deepgram Nova-2 (`POST /api/interact/transcribe-audio`) |
| **Curriculum DAG & Prerequisite Gating** | Visual directed acyclic graph enforcing prerequisite mastery before advancement | `GET /api/learning-path/{user_id}/{topic_id}`<br>`POST /api/learning-path/advance` |

---

## 🏛️ 4. System Architecture

```mermaid
graph TD
    subgraph Client ["Frontend (Next.js 15 App Router + React 19)"]
        AuthUI[Auth Portal: Login / Register / Roles]
        UI[Theater Mode Classroom / Split View]
        Dash[Learning Hub & Advanced Tools Dashboard]
        Upload[Document Drag & Drop Ingestion]
        Avatar[Audio-Reactive Canvas Avatar]
        YTComp[Curated YouTube Video Player]
        VoiceIn[Deepgram Nova-2 Mic Capture]
        DAG[Learning Path DAG Explorer]
        GapMap[Diagnostic Gap Map Report]
    end

    subgraph Backend ["FastAPI Core Engine"]
        AuthSvc[Auth & RBAC Service: JWT + Cookies]
        FSM[Teacher Agent State Machine]
        ING[Multi-Format RAG Ingestion Service]
        ST[Advanced Study Tools Service]
        LPService[Learner Profile & Mastery Engine]
        PathService[Learning Path Curriculum DAG Engine]
        LLMRouter[Multi-LLM Router: Gemini / Groq / Anthropic]
        Eval[Semantic Misconception Evaluator]
        VR[Domain Visual Routers: Math / Physics / Bio / Code / History]
        Sandbox[Isolated Docker Sandbox / Subprocess Runner]
        AvatarService[Avatar Engine: D-ID / HeyGen / Synthesia / Tavus / Canvas]
        TTS[Hierarchical TTS: ElevenLabs / Piper / WebSpeech]
        YTRouter[YouTube Data API Grounding Service]
        Assess[Adaptive Quiz & Gap Map Engine]
    end

    subgraph Storage ["Persistence & Vector Layer"]
        DB[(PostgreSQL 16 / SQLite with Alembic)]
        VEC[(pgvector / Pinecone / SHA-256 Vector Store)]
        Media[(Static Media & Video Exports Storage)]
    end

    AuthUI <-->|JWT / Auth Cookies| AuthSvc
    Upload -->|Upload PDF/DOCX/PPTX/TXT| ING
    ING -->|Chunk & Embed| VEC
    ING -->|Material Metadata| DB
    UI <-->|REST / SSE Streaming| Backend
    Dash <-->|Study Tools APIs| ST
    FSM --> ING
    FSM --> LLMRouter
    FSM --> VR
    FSM --> Eval
    FSM --> AvatarService
    FSM --> YTRouter
    FSM --> Assess
    ST --> LPService
    ST --> PathService
    VR --> Sandbox
    AvatarService --> Media
    TTS --> Media
```

---

## 🧠 5. Teacher Agent Cognitive State Machine

The pedagogical lifecycle implements a formal Finite State Machine (FSM):

```mermaid
stateDiagram-v2
    [*] --> Ingest: Ingest Topic or Uploaded Document
    Ingest --> Plan: Calibrate Learner Profile, Personality, Depth & Chunk Coverage
    Plan --> Explain: Generate Multi-Scene Lecture, Citations & Timed Captions
    Explain --> Demonstrate: Render Domain Blackboard (LaTeX / Plot / Code / SVG)
    Demonstrate --> Question: Interactive Checkpoint (MCQ / Voice STT)
    Question --> Evaluate: Diagnose Understanding & Classify Errors
    Evaluate --> Adapt: Misconception Detected (Switch Visual & Inject Fresh Analogy)
    Adapt --> Explain: Reteach Remediation Loop
    Evaluate --> Continue: Concept Mastered (Advance Curriculum Segment)
    Continue --> Assess: All Segments Completed
    Assess --> Report: Generate Diagnostic Gap Map & Source Chunk Attributions
    Report --> StudyTools: Update Profile & Generate Homework / Flashcards / Revision
    StudyTools --> [*]: Ready for Next Learning Session
```

---

## 📚 6. Document-Grounded RAG Pipeline

1. **Multi-Format Ingestion**: Parses `.pdf`, `.docx`, `.pptx`, `.txt`, and `.md` files securely with page and slide retention.
2. **Safe Storage & Chunking**: Stores files under unique UUID directories and splits content into 250–300 word chunks with 40-word semantic overlap.
3. **Vector Embeddings**: Generates 768-dimensional embeddings using Gemini `text-embedding-004` (with deterministic SHA-256 fallback).
4. **Full-Document Coverage Planning**: Partitions document chunks evenly across lesson segments to guarantee complete coverage without omission.
5. **Verbatim Grounding & Citations**: Every segment explanation re-retrieves its cited chunks and prompts the LLM:
   > *"Teach ONLY from the provided source material. Cite it. If the student asks about something not covered by these sources, say it is outside this document — do not invent it."*
6. **Citation Chips**: Clickable Coursera-style citation chips display document name, chunk ID, page number, and quote snippets directly in the classroom UI.

---

## 🔒 7. Hardened Code Execution Sandbox

For Computer Science and Programming curricula, Sahayak provides safe in-browser code execution without exposing host infrastructure:

- **Tier 1 — Ephemeral Isolated Docker Container**:
  - Container image: `python:3.9-slim`
  - Zero network egress: `--network none`
  - Memory ceiling: `--memory 128m`
  - CPU quota: `--cpus 0.5`
  - Process limit: `--pids-limit 30` (prevents fork-bombs)
  - Read-only root filesystem with ephemeral tmpfs: `--read-only --tmpfs /tmp:rw,size=16m,noexec,nosuid`
- **Tier 2 — Hardened Host Subprocess Harness**:
  - Fork-bomb defense intercepting process spawns
  - Socket monkey-patching blocking network connectivity
  - Linux `RLIMIT_AS` memory capping (128MB)
  - Strict 5–10s timeout enforcement
  - Ephemeral scratch directory isolation with path sanitization
- **Standardized Error Taxonomy**:
  - Automatically identifies and reports `timeout`, `memory_limit_exceeded`, `cpu_limit_exceeded`, `network_violation`, `fork_bomb_prevented`, `syntax_error`, and `runtime_error`.

---

## 🎭 8. AI Avatar & Video Generation Suite

Sahayak supports an extensive suite of free and paid video/avatar generation engines:

| Provider | Setting | Best For |
| :--- | :--- | :--- |
| **Interactive Canvas Avatar** | `AVATAR_PROVIDER=free_avatar` | 100% free, zero API key required, reactive Web Audio mouth articulation & equalizer. |
| **D-ID API** | `AVATAR_PROVIDER=did` | Photo-to-talking-head video lectures from a single teacher portrait. |
| **HeyGen API** | `AVATAR_PROVIDER=heygen` | Ultra-realistic digital twins, studio presenters, and streaming WebRTC avatars. |
| **Synthesia API** | `AVATAR_PROVIDER=synthesia` | Enterprise classroom video lectures with 160+ multilingual instructors. |
| **Tavus API** | `AVATAR_PROVIDER=tavus` | Low-latency conversational replicas. |
| **Colossyan API** | `AVATAR_PROVIDER=colossyan` | Multi-actor educational video courseware. |
| **Replicate (LivePortrait)** | `AVATAR_PROVIDER=replicate` | High-fidelity open-source portrait animation. |
| **Hugging Face SDXL** | `AVATAR_PROVIDER=huggingface` | Generates custom AI professor portraits from text prompts. |

---

## 🌐 9. Multilingual Support

Sahayak supports **7 languages** with in-flight switching mid-lesson:
* 🇬🇧 **English** (`en`)
* 🇮🇳 **Hindi** (`hi` - हिंदी)
* 🇮🇳 **Hinglish** (`hinglish` - Conversational)
* 🇮🇳 **Tamil** (`ta` - தமிழ்)
* 🇮🇳 **Telugu** (`te` - తెలుగు)
* 🇮🇳 **Bengali** (`bn` - বাংলা)
* 🇪🇸 **Spanish** (`es` - Español)

Students can switch languages via the UI toggle or via natural language commands (e.g., *"Ab Hindi me samjhao"*).

---

## 📊 10. Assessment, Mastery & Study Hub

1. **In-Lesson Checkpoint Evaluation**: Evaluator classifies responses as `mastery`, `partial`, `misconception`, or `unclear`. Misconceptions trigger targeted remediation loops.
2. **Document-Grounded Quiz**: Generates adaptive questions tagged with Bloom's taxonomy cognitive levels (`Recall`, `Understand`, `Apply`, `Analyze`) and mapped to specific document `chunk_id`s.
3. **Diagnostic Gap Map**: Visual breakdown of strong vs. weak concepts with citations, error diagnosis, and recommended next topics.
4. **Learning Hub & Advanced Dashboard**:
   - **Teacher Personalities tab**: Toggle between Socratic, Friendly, Strict Coach, and Visual Architect styles.
   - **Revision Mode tab**: Launch instant targeted lessons on weak concepts.
   - **Flashcards Deck tab**: Interactive flipping cards with real-time mastery tracking.
   - **Revision Notes tab**: Structured summaries with formulas and common traps.
   - **Personalized Homework tab**: Tiered homework tailored to student mastery level.
   - **Exam Prep tab**: Milestone roadmaps and scheduled mock assessments.
   - **Study Planner tab**: Daily schedules with 1-click dynamic catch-up rebalancing.

---

## 🚀 11. Quick Start & Setup Instructions

> [!TIP]
> **For Evaluators & Judges:**
> Sahayak can be launched in seconds using either Docker Compose (recommended, zero host dependency configuration) or native local commands. FFmpeg is bundled automatically inside Docker.

### Option A: One-Command Docker Compose (Recommended)

Run the full stack (PostgreSQL 16 + pgvector, FastAPI Backend, Next.js Frontend) in unified containers:

```bash
git clone https://github.com/Akshat-coder-101/sahayak-ai-teacher.git
cd sahayak-ai-teacher

# Configure environment keys (optional, fallback engines active by default)
cp .env.example .env

# Build and start all services
docker-compose up --build
```
* **Frontend Web Application**: [http://localhost:3000](http://localhost:3000)
* **Backend API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Backend Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

### Option B: Local Development Setup

#### Prerequisites
* **Python 3.10+**
* **Node.js 18+** and `npm`
* **FFmpeg** (`brew install ffmpeg` on macOS / `sudo apt install ffmpeg` on Linux / `winget install Gyan.FFmpeg` on Windows)

#### Step 1: Configure Environment Variables
```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

#### Step 2: Start Backend (FastAPI)
```bash
cd backend
python -m venv ../venv
source ../venv/bin/activate   # On Windows: ..\venv\Scripts\activate
pip install -r requirements.txt

# Run database migrations (SQLite or PostgreSQL)
alembic upgrade head

# Start server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Step 3: Start Frontend (Next.js 15)
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
* Web Application: [http://localhost:3000](http://localhost:3000)
* Login / Register Portal: [http://localhost:3000/login](http://localhost:3000/login)
* Learning Hub & Study Tools: [http://localhost:3000/dashboard](http://localhost:3000/dashboard)
* Document Upload: [http://localhost:3000/upload](http://localhost:3000/upload)

---

## 🧪 12. Automated Test Suite

Sahayak comes with a comprehensive, rigorous automated test suite with **85 passing tests** and **2 skipped** (which require live external cloud API keys), demonstrating 100% automated pass rate:

```bash
cd backend
source ../venv/bin/activate
pytest tests/ -v
```

### Complete Test Matrix (13 Test Suites / 87 Items):
* **`test_advanced_features.py`** (6/6 passed): Personalities, Revision Mode, Tiered Homework, Flashcards, Exam Prep, Planner & Mastery Updates
* **`test_all_endpoints.py`** (18/18 passed, 1 skipped): Core REST APIs, lesson generation, RAG retrieval, media security, and canonical error formats
* **`test_assessment_pipeline.py`** (6/6 passed): Bloom's taxonomy quizzes, misconception evaluators, gap maps, and rubric grading
* **`test_auth.py`** (7/7 passed): Registration, login, JWT token expiration, invalid token handling, role-based access scoping (student vs teacher), `/me`, and logout
* **`test_document_and_export.py`** (7/7 passed): Multi-format DOCX/PPTX/PDF/Markdown parsing, grounded lesson creation, and MP4 video export worker lifecycle
* **`test_groq_token_cap.py`** (2/2 passed): Token cap bounds validation and multi-segment plan generation without truncation
* **`test_instruction_and_adaptation.py`** (6/6 passed): Student instruction parsing, topic filtering, time-budget scaling, and Hindi hybrid pedagogy
* **`test_profile_and_learning_path.py`** (7/7 passed): Curriculum DAG generation, returning student skipping mastered fundamentals, prerequisite gating, and resume learning
* **`test_rag_benchmark.py`** (1/1 passed): Retrieval latency and ranking benchmarks across 1,000+ document chunks
* **`test_regional_language.py`** (3/3 passed): Tamil lesson planning, TTS voice mapping, and YouTube search localization
* **`test_sandbox.py`** (6/6 passed): Normal Python execution, network egress blocking, timeout termination, fork-bomb prevention, syntax error classification, and scratch directory isolation
* **`test_visual_planning.py`** (8/8 passed): Domain-aware visual routing (mathematics KaTeX, physics free-body diagrams, biology anatomy, history timelines, CS runnable code)

---

## 🔌 13. Third-Party Services Disclosed

| Service / Tool | Purpose | Fallback / Alternative |
|---|---|---|
| **Google Gemini / Groq LLaMA 3.3 / Anthropic** | LLM pedagogical reasoning, lesson planning, evaluation | Multi-provider fallback + deterministic templates |
| **YouTube Data API v3** | Curated video grounding & deep-dives | Direct search URL generation |
| **ElevenLabs API** | Multilingual neural text-to-speech | Local Piper ONNX / Browser Web Speech |
| **Deepgram Nova-2** | Student microphone voice Q&A | Text keyboard submission |
| **D-ID / HeyGen / Synthesia / Tavus / Colossyan** | Photorealistic AI teacher video generation | Interactive Canvas Avatar (Zero-cost) |
| **KaTeX & Recharts** | Mathematical LaTeX formulas & Cartesian plots | Interactive SVGs & Python Sandbox |
| **PostgreSQL 16 + pgvector** | Production relational and vector database | Zero-dependency SQLite fallback |

---

## 👥 Hackathon Team

* **Project**: Sahayak AI Teacher 🎓
* **Hackathon**: AI Innovation Hackathon 2026
* **Repository**: [Akshat-coder-101/sahayak-ai-teacher](https://github.com/Akshat-coder-101/sahayak-ai-teacher)
* **License**: MIT

