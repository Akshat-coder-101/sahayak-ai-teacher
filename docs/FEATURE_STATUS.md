# Sahayak AI Teacher - Feature Status Matrix

This matrix provides a rigorous, code-verified audit of every major subsystem and provider in Sahayak AI Teacher. In accordance with the hackathon evaluation ground rules, claims are strictly categorized:
- **Tested in CI**: Verified by automated test suites executed in continuous integration.
- **Manually verified**: Verified locally with real execution traces and output confirmation.
- **Implemented, needs API key**: Full call path, schemas, and error handling exist in code; requires active 3rd-party credentials to execute live.
- **Stub / not verified**: Config keys or mentions exist, but no active call path, client code, or test exists in the repository.

---

## 1. Avatar & Talking Head Providers

| Feature / Provider | Status | Evidence (File Path / Test Name) |
| :--- | :--- | :--- |
| **Interactive Canvas Avatar** | **Tested in CI** | `backend/tests/test_all_endpoints.py`, `backend/app/services/avatar.py:357-366` |
| **D-ID Talking Head** (`did`) | **Implemented, needs API key** | `backend/app/services/avatar.py:42-95` (`DID_API_KEY`) |
| **HeyGen AI Presenter** (`heygen`) | **Implemented, needs API key** | `backend/app/services/avatar.py:97-142` (`HEYGEN_API_KEY`) |
| **Synthesia AI Video** (`synthesia`) | **Implemented, needs API key** | `backend/app/services/avatar.py:145-185` (`SYNTHESIA_API_KEY`) |
| **Tavus Video Replica** (`tavus`) | **Implemented, needs API key** | `backend/app/services/avatar.py:188-223` (`TAVUS_API_KEY`) |
| **Colossyan AI Actor** (`colossyan`) | **Implemented, needs API key** | `backend/app/services/avatar.py:226-269` (`COLOSSYAN_API_KEY`) |
| **Replicate LivePortrait/SadTalker** (`replicate`) | **Implemented, needs API key** | `backend/app/services/avatar.py:272-312` (`REPLICATE_API_TOKEN`) |
| **Hugging Face SDXL Portrait** (`huggingface`) | **Implemented, needs API key** | `backend/app/services/avatar.py:315-355` (`HUGGINGFACE_API_KEY`) |
| **Hedra Character Engine** (`hedra`) | **Stub / not verified** | Config key in `backend/app/config.py:51`, but no API client code exists in `backend/app/services/avatar.py`. |

---

## 2. Speech Synthesis (TTS) & Speech-to-Text (STT)

| Feature / Provider | Status | Evidence (File Path / Test Name) |
| :--- | :--- | :--- |
| **Browser Web Speech API Metadata** | **Tested in CI** | `backend/tests/test_all_endpoints.py`, `backend/app/services/tts.py:180-199` |
| **Local Piper Neural TTS** (`piper_local`) | **Manually verified** | `backend/app/services/tts.py:41-112` (lightweight ONNX neural voice) |
| **ElevenLabs Multilingual v2** (`elevenlabs`) | **Implemented, needs API key** | `backend/app/services/tts.py:129-174` (`ELEVENLABS_API_KEY`) |
| **Deepgram Nova-2 Speech-to-Text** (`deepgram`) | **Implemented, needs API key** | `backend/app/services/stt.py:7-42` (`DEEPGRAM_API_KEY`) |
| **Browser Web SpeechRecognition (STT)** | **Manually verified** | `frontend/src/components/AudioChat.tsx` |

---

## 3. Video Composition & Media Pipeline

| Feature / Provider | Status | Evidence (File Path / Test Name) |
| :--- | :--- | :--- |
| **Demo Mode Slide + Audio Synthesis** | **Tested in CI** | `backend/tests/test_optimized_video.py`, `backend/app/services/video.py` |
| **FFmpeg Lossless Stream Copy (`-c copy`)** | **Manually verified** | `backend/scripts/benchmark_stitch.py`, `backend/eval/stitch_benchmark_results.json` (5.6x speedup) |
| **Matplotlib Dynamic Chart Generator** | **Tested in CI** | `backend/tests/test_visual_planning.py`, `backend/app/services/video.py:65-115` |
| **YouTube Grounding (API v3)** | **Tested in CI** | `backend/tests/test_all_endpoints.py`, `backend/app/services/youtube.py:207-290` (`YOUTUBE_API_KEY`) |
| **YouTube Fallback Curated Search** | **Tested in CI** | `backend/tests/test_all_endpoints.py`, `backend/app/services/youtube.py:220-240` |

---

## 4. Vector Retrieval & Database Storage

| Feature / Provider | Status | Evidence (File Path / Test Name) |
| :--- | :--- | :--- |
| **SQLite Local Hybrid Store (Vector + Lexical)** | **Tested in CI** | `backend/tests/test_rag_benchmark.py`, `backend/app/services/rag.py` |
| **PostgreSQL 16+ pgvector Database** | **Tested in CI** | `backend/tests/test_rag_benchmark.py`, `backend/app/database.py:215-230` |
| **Pinecone Vector Database** | **Stub / not verified** | Config key in `backend/app/config.py:70-72`; no active client implementation in `backend/app/services/rag.py`. |
| **Local Disk Media Storage** | **Tested in CI** | `backend/tests/test_document_and_export.py`, `backend/app/services/video.py` |
| **Supabase Storage Buckets (Object Store)** | **Stub / not verified** | Config key in `backend/app/config.py:67-69`; files write to local `MEDIA_DIR`; no Supabase S3/bucket client in code. |

---

## 5. Execution Sandboxes

| Feature / Tier | Status | Evidence (File Path / Test Name) |
| :--- | :--- | :--- |
| **In-Host Hardened Subprocess Sandbox** | **Tested in CI** | `backend/tests/test_sandbox.py`, `backend/tests/test_production_hardening.py`, `backend/app/services/code_sandbox.py:98-228` |
| **Ephemeral Docker Sandbox (`--network none`)** | **Manually verified** | `backend/app/services/code_sandbox.py:28-80` (requires host Docker engine) |

---

## 6. Study Tools & Adaptive Learning

| Feature / Tool | Status | Evidence (File Path / Test Name) |
| :--- | :--- | :--- |
| **Multiple Teacher Personalities (4 styles)** | **Tested in CI** | `backend/tests/test_instruction_and_adaptation.py`, `backend/app/services/study_tools.py:41-125` |
| **Revision Mode (Misconception-driven)** | **Tested in CI** | `backend/tests/test_advanced_features.py`, `backend/app/services/study_tools.py:130-195` |
| **Interactive Quiz & Misconception Engine** | **Tested in CI** | `backend/tests/test_assessment_pipeline.py`, `backend/app/services/evaluator.py` |
| **Flashcard Deck Generator** | **Tested in CI** | `backend/tests/test_all_endpoints.py`, `backend/app/services/study_tools.py:200-265` |
| **Study Notes & Summary Engine** | **Tested in CI** | `backend/tests/test_all_endpoints.py`, `backend/app/services/study_tools.py:270-330` |
| **Homework & Assignment Engine** | **Tested in CI** | `backend/tests/test_all_endpoints.py`, `backend/app/services/study_tools.py:335-400` |
| **Exam Preparation Milestones** | **Tested in CI** | `backend/tests/test_all_endpoints.py`, `backend/app/services/study_tools.py:405-470` |
| **Learning Analytics & Score History** | **Tested in CI** | `backend/tests/test_all_endpoints.py`, `backend/app/services/study_tools.py:475-550` |
| **Audio Podcast Notes Synthesis** | **Tested in CI** | `backend/tests/test_advanced_features.py`, `backend/app/services/study_tools.py:555-630` |
| **Prerequisite Learning Path DAG** | **Tested in CI** | `backend/tests/test_visual_planning.py`, `backend/app/services/learning_path.py` |

---

## 7. LLM Orchestration Providers

| Feature / Provider | Status | Evidence (File Path / Test Name) |
| :--- | :--- | :--- |
| **Google Gemini (gemini-2.5-flash / gemini-3-flash)** | **Implemented, needs API key** | `backend/app/services/llm.py:80-160` (`GEMINI_API_KEY`) |
| **Groq (qwen/qwen-2.5-32b / qwen3.8-27b)** | **Implemented, needs API key** | `backend/app/services/llm.py:165-240` (`GROQ_API_KEY`) |
| **Cerebras (llama-3.1-8b / 70b)** | **Implemented, needs API key** | `backend/app/services/llm.py:245-310` (`CEREBRAS_API_KEY`) |
| **Deterministic Fallback Engine** | **Tested in CI** | `backend/tests/test_all_endpoints.py`, `backend/app/services/llm.py:315-380` |
