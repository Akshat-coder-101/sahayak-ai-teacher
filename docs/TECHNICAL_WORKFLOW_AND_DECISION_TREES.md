# SAHAYAK AI TEACHER — TECHNICAL WORKFLOW & DECISION TREES

---

## 1. OVERALL SYSTEM WORKFLOW

```
┌─────────────────────────────────────────────────────────────────────┐
│                     LEARNER INITIATES SESSION                        │
│  (Provides: Topic OR Upload Document, Language, Level, Time Budget) │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │   PARSE STUDENT INSTRUCTION (LLM)   │
        │  Extract: level, time_budget,        │
        │  language, style, specific chapter   │
        └──────────────────┬───────────────────┘
                           │
                ┌──────────┴──────────┐
                │                     │
                ▼                     ▼
         [Document          [No Document
          Provided?]        → Generic Topic]
           │                      │
           │                      ▼
           │              ┌──────────────────┐
           │              │ Use External KB  │
           │              │ (YouTube Search) │
           │              └────────┬─────────┘
           │                       │
           └───────────┬───────────┘
                       │
                       ▼
      ┌────────────────────────────────────┐
      │ INGEST & CHUNK (if document)       │
      │ • Parse PDF/DOCX/PPTX/TXT          │
      │ • Split into ~250-word chunks      │
      │ • Embed each chunk (Gemini/SHA256) │
      │ • Store in DB with metadata        │
      └─────────────┬──────────────────────┘
                    │
                    ▼
      ┌────────────────────────────────────┐
      │ RETRIEVE GROUNDED CONTEXT (RAG)    │
      │ • Hybrid search (cosine + keyword) │
      │ • Return top-K chunks + citations  │
      └─────────────┬──────────────────────┘
                    │
                    ▼
      ┌────────────────────────────────────┐
      │ LOAD LEARNER PROFILE (if returning)│
      │ • Mastery map per concept          │
      │ • Known misconceptions             │
      │ • Score history                    │
      │ • Learning path progress           │
      └─────────────┬──────────────────────┘
                    │
                    ▼
      ╔════════════════════════════════════╗
      ║   10-STATE TEACHER AGENT LOOP      ║
      ║                                    ║
      ║ UNDERSTAND ──┐                     ║
      ║              │                     ║
      ║         ┌────▼────┐                ║
      ║         │   PLAN  │                ║
      ║         └────┬────┘                ║
      ║              │                     ║
      ║    ┌─────────┴──────────┐           ║
      ║    │  (Segment Loop)    │           ║
      ║    │                    │           ║
      ║    ▼                    │           ║
      ║ EXPLAIN ◄──────┐        │           ║
      ║    │           │        │           ║
      ║    ▼           │        │           ║
      ║ DEMONSTRATE    │        │           ║
      ║    │           │        │           ║
      ║    ▼           │        │           ║
      ║ QUESTION       │        │           ║
      ║    │           │        │           ║
      ║    ├─ EVALUATE │        │           ║
      ║    │           │        │           ║
      ║    ├─ ADAPT (?) ┼────┐  │           ║
      ║    │           │    │  │           ║
      ║    ▼           │    │  │           ║
      ║ CONTINUE? ─────┼────┘  │           ║
      ║    │           │       │           ║
      ║    ├─ YES ─────┘       │           ║
      ║    │                   │           ║
      ║    └─ NO ──────────────┘           ║
      ║                                    ║
      ║         ┌────┬────┐                ║
      ║         ▼    │    ▼                ║
      ║      ASSESS  │  REPORT             ║
      ║         │    │    │                ║
      ║         └────┴────┘                ║
      ║              │                     ║
      ║              ▼                     ║
      ║         GENERATE REPORT            ║
      ║         (Quiz + Learning Path)     ║
      ║                                    ║
      ╚════════════════════════════════════╝
                    │
                    ▼
      ┌────────────────────────────────────┐
      │ UPDATE LEARNER PROFILE             │
      │ • New mastery scores               │
      │ • Misconceptions encountered       │
      │ • Score history append             │
      │ • Update learning path DAG         │
      └────────────────┬───────────────────┘
                       │
                       ▼
      ┌────────────────────────────────────┐
      │ EXPORT OPTIONS                     │
      │ • Download full lesson video       │
      │ • Export report as PDF             │
      │ • Share learning path              │
      │ • Save progress                    │
      └────────────────────────────────────┘
```

---

## 2. LESSON PLANNING DECISION TREE

```
                    ┌─────────────────────┐
                    │  START LESSON PLAN  │
                    │  (time_budget given)│
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Calculate # Segments│
                    │ (based on time_budget)
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
   <=5 min             6-20 min              >20 min
        │                      │                      │
        ▼                      ▼                      ▼
    2 SEGMENTS         4 SEGMENTS          6 SEGMENTS
     (3 min ea)         (5 min ea)          (4-5 min ea)
        │                      │                      │
        └──────────┬───────────┴──────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────┐
    │ LOAD LEARNER CONTEXT (if profile)    │
    │ • Current mastery per concept        │
    │ • Known misconceptions to address    │
    │ • Preferred teaching style           │
    │ • Language preference                │
    └────────────┬─────────────────────────┘
                 │
                 ▼
    ┌──────────────────────────────────────┐
    │ FOR EACH SEGMENT:                    │
    │                                      │
    │ 1. Retrieve grounded context (RAG)   │
    │    (Top 3-5 chunks per segment)      │
    │                                      │
    │ 2. Inject learner context into prompt│
    │                                      │
    │ 3. Call LLM with pedagogical order:  │
    │    • Prerequisite check              │
    │    • Core concept intro              │
    │    • Intuitive explanation           │
    │    • Relatable example               │
    │    • Misconception clarification     │
    │                                      │
    │ 4. LLM returns structured plan:      │
    │    {                                 │
    │      segment_id: int,                │
    │      title: str,                     │
    │      narration_script: str,          │
    │      visual_type: enum,              │
    │      checkpoint_question: str,       │
    │      cited_chunk_ids: [str],         │
    │      expected_concepts: [str]        │
    │    }                                 │
    │                                      │
    │ 5. Append to plan                    │
    └────────────┬─────────────────────────┘
                 │
                 ▼
    ┌──────────────────────────────────────┐
    │ GUARD CHECK: Grounding Guardrail     │
    │ • Verify each segment cites chunks   │
    │ • Reject if hallucinating            │
    │ • Re-ask LLM if failed               │
    └────────────┬─────────────────────────┘
                 │
                 ▼
    ┌──────────────────────────────────────┐
    │ RETURN LESSON PLAN                   │
    │ {                                    │
    │   session_id: str,                   │
    │   topic: str,                        │
    │   segments: [SegmentPlan],           │
    │   total_time_minutes: int,           │
    │   language: str,                     │
    │   learner_level: str                 │
    │ }                                    │
    │                                      │
    │ PERSIST: Save to DBLessonSession     │
    └──────────────────────────────────────┘
```

---

## 3. SEGMENT RENDERING WORKFLOW

```
           ┌─────────────────────────┐
           │ RENDER SEGMENT REQUEST  │
           │ (session_id, segment_id)│
           └────────────┬────────────┘
                        │
                        ▼
           ┌─────────────────────────┐
           │ Fetch segment plan data │
           │ from DBLessonSession    │
           └────────────┬────────────┘
                        │
                        ▼
           ┌─────────────────────────┐
           │ STEP 1: NARRATION       │
           │ (script already in plan)│
           └────────────┬────────────┘
                        │
           ┌────────────┴────────────┐
           │                         │
           ▼                         ▼
       [Language?]
           │                    Other
      Hindi/Hinglish        (English/etc.)
           │                    │
           ▼                    ▼
    ┌──────────────┐    ┌──────────────┐
    │ ElevenLabs   │    │ ElevenLabs   │
    │ +Hindi voice │    │ Default voice│
    │ (key present)│    │              │
    └──────┬───────┘    └───────┬──────┘
           │                    │
           └────────┬───────────┘
                    │
           ┌────────▼────────┐
           │ Fallback: Piper │ (if pkg available)
           │ local neural TTS│
           └────────┬────────┘
                    │
           ┌────────▼────────┐
           │ Fallback: HTML5 │
           │ Web Speech API  │
           └────────┬────────┘
                    │
                    ▼
           ┌─────────────────────────┐
           │ Save audio to file       │
           │ (generated_media/...)    │
           └────────────┬────────────┘
                        │
                        ▼
           ┌─────────────────────────┐
           │ STEP 2: VISUAL ROUTING  │
           │ (based on visual_type   │
           │  from segment plan)     │
           └────────────┬────────────┘
                        │
         ┌──────────────┼──────────────┬─────────────┐
         │              │              │             │
         ▼              ▼              ▼             ▼
    [DIAGRAM]      [EQUATION]    [CODE_DEMO]   [TIMELINE]
         │              │              │             │
         ▼              ▼              ▼             ▼
    ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌──────────┐
    │ Render  │   │ Plot    │   │ Execute  │   │ Render   │
    │ labeled │   │ graph   │   │ Python   │   │ timeline │
    │ diagram │   │ + eqn   │   │ code     │   │ /map     │
    │ (Pillow)│   │ (mpl)   │   │ (sandbox)│   │ (Pillow) │
    └────┬────┘   └────┬────┘   └────┬─────┘   └────┬─────┘
         │             │             │             │
         └─────────────┴─────────────┴─────────────┘
                       │
                       ▼
           ┌─────────────────────────┐
           │ STEP 3: VIDEO ASSEMBLY  │
           │ (ffmpeg pipeline)       │
           │                         │
           │ 1. Create SRT subtitles │
           │ 2. Render slides (PIL)  │
           │ 3. Concat w/ audio      │
           │ 4. Add Ken Burns motion │
           │ 5. Encode MP4 (x264)    │
           │ 6. Burn subtitles in    │
           └────────────┬────────────┘
                        │
                        ▼
           ┌─────────────────────────┐
           │ Fallback: Video status  │
           │ "unavailable" if        │
           │ ffmpeg missing          │
           └────────────┬────────────┘
                        │
                        ▼
           ┌─────────────────────────┐
           │ STEP 4: RETURN RESPONSE │
           │ {                       │
           │   segment_id: int,      │
           │   video_url: str,       │
           │   audio_url: str,       │
           │   visual_data: {...},   │
           │   narration_script: str,│
           │   checkpoint_question:  │
           │     {...}               │
           │ }                       │
           └─────────────────────────┘
```

---

## 4. CHECKPOINT QUESTION & EVALUATION TREE

```
          ┌──────────────────────────┐
          │ CHECKPOINT QUESTION POSED│
          │ (from segment plan)       │
          └────────────┬──────────────┘
                       │
                       ▼
          ┌──────────────────────────┐
          │ STUDENT PROVIDES ANSWER  │
          │ (text or voice → STT)     │
          └────────────┬──────────────┘
                       │
                       ▼
          ┌──────────────────────────┐
          │ ANSWER EVALUATION (LLM)  │
          │                          │
          │ Inject prompt:           │
          │  • Question + context    │
          │  • Expected concepts     │
          │  • Student answer        │
          │  • Rubric for scoring    │
          │                          │
          │ LLM returns:             │
          │ {                        │
          │   classification: str,   │
          │   score: float,          │
          │   feedback: str,         │
          │   misconception_name: str│
          │ }                        │
          └────────────┬──────────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
         ▼             ▼             ▼
    [CORRECT]   [PARTIAL]      [MISCONCEPTION]
      (1.0)      (0.5-0.75)         or
         │             │         [NO_UNDERSTANDING]
         │             │             │
         ▼             ▼             ▼
    ┌────────┐   ┌────────┐   ┌──────────────┐
    │Praise  │   │Clarify │   │Name the      │
    │Next seg│   │missing │   │misconception │
    │        │   │parts   │   │              │
    └────┬───┘   └───┬────┘   └───────┬──────┘
         │           │                │
         │           └────────┬───────┘
         │                    │
         │                    ▼
         │          ┌──────────────────────┐
         │          │ ADAPT: Generate      │
         │          │ Re-teach Content     │
         │          │                      │
         │          │ 1. Fresh analogy     │
         │          │    (not used before  │
         │          │     in session)      │
         │          │                      │
         │          │ 2. Different visual  │
         │          │    type (avoid       │
         │          │    repeating)        │
         │          │                      │
         │          │ 3. Concrete example  │
         │          │                      │
         │          │ 4. Follow-up Q       │
         │          │                      │
         │          │ Insert into session  │
         │          │ state                │
         │          │ (taught_concepts,    │
         │          │  analogies_used)     │
         │          └──────────┬───────────┘
         │                     │
         └──────────┬──────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ UPDATE SESSION STATE │
         │ • current_segment    │
         │ • state machine      │
         │ • taught_concepts    │
         │ • analogies_used     │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ PERSIST ATTEMPT      │
         │ → DBCheckpointAttempt│
         │ (q, answer, class,   │
         │  feedback, created)  │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ TRANSITION STATE     │
         │                      │
         │ IF correct:          │
         │  → CONTINUE          │
         │                      │
         │ IF misconception:    │
         │  → ADAPT (re-teach)  │
         │  → QUESTION (ask Q2) │
         │  → EVALUATE (score)  │
         │  → CONTINUE          │
         │                      │
         │ IF no_understanding: │
         │  → ADAPT (thorough)  │
         │  → Loop up to 2x     │
         │  → If still stuck,   │
         │    → CONTINUE        │
         └──────────────────────┘
```

---

## 5. ASSESSMENT & QUIZ PIPELINE

```
           ┌─────────────────────────┐
           │ FORMAL ASSESSMENT PHASE │
           │ (after all segments)    │
           └────────────┬────────────┘
                        │
                        ▼
           ┌─────────────────────────┐
           │ CREATE ASSESSMENT BLUE  │
           │ PRINT (Blueprint)       │
           │                         │
           │ Input:                  │
           │ • session: DBLessonSession
           │ • learner_level         │
           │ • taught_concepts       │
           │                         │
           │ Blueprint defines:      │
           │ • # MCQs (e.g., 4)      │
           │ • # Conceptual (e.g., 3)│
           │ • # Short answer (e.g.,2)
           │ • Difficulty per level  │
           └────────────┬────────────┘
                        │
                        ▼
           ┌─────────────────────────┐
           │ GENERATE QUIZ (LLM)     │
           │                         │
           │ For each question type: │
           │                         │
           │ MCQ:                    │
           │  • Concept picked from  │
           │    taught_concepts      │
           │  • Generate 4 options   │
           │  • 1 correct, 3 plausib │
           │    misconception traps  │
           │                         │
           │ Conceptual:             │
           │  • Open-ended           │
           │  • Rubric defined       │
           │  • 2-3 exemplar answers │
           │                         │
           │ Short answer:           │
           │  • Key concepts tested  │
           │  • Rubric: 0/0.5/1.0    │
           │                         │
           │ Result:                 │
           │ → DBQuiz (questions_json)
           └────────────┬────────────┘
                        │
                        ▼
           ┌─────────────────────────┐
           │ STUDENT SUBMITS ANSWERS │
           │ {                       │
           │   session_id: str,      │
           │   responses: [          │
           │     {                   │
           │       question_id: str, │
           │       answer: str       │
           │     }, ...              │
           │   ]                     │
           │ }                       │
           └────────────┬────────────┘
                        │
                        ▼
           ┌─────────────────────────┐
           │ GRADE SUBMISSION        │
           │                         │
           │ For each question:      │
           └────────────┬────────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
         ▼              ▼              ▼
    [MCQ]         [Conceptual]   [Short Answer]
         │              │              │
         ▼              ▼              ▼
  ┌─────────┐    ┌──────────┐   ┌──────────────┐
  │Check vs │    │Call LLM  │   │Call LLM w/   │
  │correct  │    │with      │   │rubric +      │
  │answer   │    │rubric    │   │exemplars     │
  │         │    │          │   │              │
  │Score:   │    │Generate: │   │Return:       │
  │ 1.0 or  │    │ • score  │   │ • score      │
  │ 0.0     │    │ • reason │   │ • reason     │
  │         │    │ • partial│   │ • misconc.   │
  │         │    │  credit  │   │              │
  │         │    │ • misconc│   │              │
  │         │    │  diagnosis    │              │
  └────┬────┘    └────┬─────┘   └────┬─────────┘
       │              │              │
       └──────────────┼──────────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │ AGGREGATE SCORES            │
        │                             │
        │ • Per-question score        │
        │ • Per-question misconception│
        │ • Overall percentage        │
        │ • Concept mastery rollup    │
        │                             │
        │ Store → DBQuizAttempt       │
        └──────────┬──────────────────┘
                   │
                   ▼
        ┌─────────────────────────────┐
        │ UPDATE LEARNER PROFILE      │
        │                             │
        │ For each question result:   │
        │ • Concept mastery_json      │
        │ • Misconceptions list       │
        │ • Recommendation (next      │
        │   topic to learn)           │
        │                             │
        │ Calls:                      │
        │ update_profile_from_        │
        │ assessment()                │
        └──────────┬──────────────────┘
                   │
                   ▼
        ┌─────────────────────────────┐
        │ GENERATE LEARNING REPORT    │
        │                             │
        │ {                           │
        │   session_id: str,          │
        │   score_percent: float,     │
        │   concepts_mastered: [...], │
        │   misconceptions: [...],    │
        │   next_recommendations: [...│
        │   time_spent: int,          │
        │   engagement_score: float   │
        │ }                           │
        │                             │
        │ → DBLearningReport          │
        └─────────────────────────────┘
```

---

## 6. VISUAL ROUTING DECISION TREE

```
              ┌──────────────────────┐
              │ CHOOSE VISUAL TYPE   │
              │ (for a concept)      │
              └────────────┬─────────┘
                           │
                ┌──────────┴──────────┐
                │                     │
         [Concept] ──LLM────→  [Determine best visual]
                │
         ┌──────┼──────┬──────┬─────────┐
         │      │      │      │         │
         ▼      ▼      ▼      ▼         ▼
     [Is it]  [Structure]  [Temporal]  [Data]
     [Spatial?] [Hierarchy?] [Sequence?] [Driven?]
         │      │      │      │         │
       YES     YES    YES    YES       YES
         │      │      │      │         │
         ▼      ▼      ▼      ▼         ▼
      DIAGRAM  ORG    TIMELINE GRAPH
      (labeled CHART         
      shapes,          
      arrows)          
         │      │      │      │         │
         └──────┴──────┴──────┴─────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │ ALSO CHECK:            │
         │                        │
         │ Does concept involve   │
         │ code/executable demo?  │
         └────────┬───────────────┘
                  │
         ┌────────┴────────┐
         │                 │
         YES              NO
         │                 │
         ▼                 ▼
      CODE_DEMO      [Use above choice]
      (execute +        │
       display output)  └──────┬──────┐
         │                     │      │
         └─────────────────────┴──────┘
                       │
                       ▼
        ┌──────────────────────────┐
        │ AVOID REPETITION:        │
        │                          │
        │ • Check session state    │
        │ • visual_types_used_this │
        │   _lesson: [...]         │
        │ • If visual_type already │
        │   used for a similar     │
        │   concept, pick alternate│
        │ • Reinforce via variety  │
        └──────────┬───────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ RETURN VISUAL TYPE       │
        │ + visual_data            │
        │ (e.g., diagram SVG,      │
        │  graph JSON, code string)│
        └──────────────────────────┘
```

---

## 7. MULTILINGUAL ROUTING DECISION TREE

```
          ┌─────────────────────────┐
          │ LANGUAGE REQUESTED      │
          │ (from session)          │
          └────────────┬────────────┘
                       │
     ┌─────────────────┼─────────────────┐
     │                 │                 │
   HINDI         HINGLISH           OTHER
     │                 │                 │
     ▼                 ▼                 ▼
  ┌─────────┐   ┌────────────┐   ┌───────────────┐
  │Special  │   │Special     │   │Generic LLM    │
  │Hindi    │   │Hinglish    │   │instruction    │
  │clauses: │   │clauses:    │   │               │
  │         │   │            │   │"Translate to  │
  │"Explain │   │"Mix Hindi  │   │[LANG] and     │
  │in       │   │and English │   │keep technical │
  │Devanag- │   │naturally.  │   │terms in       │
  │ari, keep│   │Code-switch │   │English"       │
  │technical│   │is natural. │   │               │
  │terms in │   │Speak like  │   │Supported:     │
  │English" │   │learners    │   │• Tamil (ta)   │
  │         │   │think."     │   │• Telugu (te)  │
  │         │   │            │   │• Bengali (bn) │
  │         │   │            │   │• Spanish (es) │
  └────┬────┘   └─────┬──────┘   └────────┬──────┘
       │              │                    │
       └──────────────┼────────────────────┘
                      │
                      ▼
        ┌──────────────────────────┐
        │ LLM generates narration  │
        │ script in target language│
        └──────────┬───────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ TTS LANGUAGE ROUTING     │
        │                          │
        │ Input: language, script  │
        └──────────┬───────────────┘
                   │
     ┌─────────────┼────────────────┐
     │             │                │
   HINDI    HINGLISH         OTHER
     │             │                │
     ▼             ▼                ▼
┌─────────┐  ┌──────────┐    ┌────────────┐
│ElevenLabs│  │ElevenLabs│   │ElevenLabs  │
│Hindi     │  │English   │   │(best match)│
│voice     │  │(code-mix │   │            │
│          │  │ natural) │   │Fallback:   │
│Fallback: │  │          │   │Piper (if   │
│Piper     │  │Fallback: │   │available)  │
│Hindi     │  │Piper     │   │            │
│model     │  │English   │   │Fallback:   │
│(if pkg)  │  │(if pkg)  │   │Web Speech  │
│          │  │          │   │            │
│Fallback: │  │Fallback: │   │Fallback:   │
│Web Speech│  │Web Speech│   │Web Speech  │
└────┬─────┘  └────┬─────┘   └──────┬─────┘
     │             │                │
     └─────────────┼────────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ GENERATE AUDIO FILE      │
        │ • Save to media dir      │
        │ • Include language       │
        │   metadata in filename   │
        │ • Return audio_url       │
        └──────────────────────────┘
```

---

## 8. LEARNER PROFILE & PERSONALIZATION FLOW

```
          ┌────────────────────────┐
          │ RETURNING LEARNER?     │
          │ (user_id provided)     │
          └────────────┬───────────┘
                       │
         ┌─────────────┴─────────────┐
         │                           │
        YES                         NO
         │                           │
         ▼                           ▼
    ┌────────────┐            ┌──────────┐
    │Load        │            │Create    │
    │DBLearner   │            │default   │
    │Profile     │            │profile   │
    │            │            │(all 0s)  │
    │ mastery_   │            └────┬─────┘
    │ json       │                 │
    │ history_   │                 │
    │ json       │                 │
    └────┬───────┘                 │
         │                         │
         └────────────┬────────────┘
                      │
                      ▼
        ┌─────────────────────────┐
        │ BUILD LEARNER CONTEXT   │
        │ STRING (for LLM)        │
        │                         │
        │ Include:                │
        │ • Current mastery per   │
        │   concept (developing,  │
        │   struggling, mastered) │
        │                         │
        │ • Known misconceptions  │
        │   "Student often thinks │
        │    velocity = distance/ │
        │    height; dispel this" │
        │                         │
        │ • Preferred style       │
        │   (visual, step-by-step,│
        │   story-based, etc.)    │
        │                         │
        │ • Historical patterns   │
        │   "Learns well with     │
        │    analogies, weak on   │
        │    math"                │
        │                         │
        │ Result: prompt injection│
        │ to lesson planner       │
        └─────────┬───────────────┘
                  │
                  ▼
        ┌─────────────────────────┐
        │ LESSON PLANNER receives │
        │ enriched context        │
        │                         │
        │ → adapts lesson to      │
        │   address known gaps    │
        │                         │
        │ → prioritizes concepts  │
        │   learner is weak on    │
        │                         │
        │ → avoids concepts       │
        │   already mastered      │
        │                         │
        │ → picks teaching style  │
        │   that matches learner  │
        └─────────┬───────────────┘
                  │
                  ▼
        ┌─────────────────────────┐
        │ AFTER SESSION COMPLETES │
        │                         │
        │ Call:                   │
        │ update_profile_from_    │
        │ assessment(             │
        │   user_id,              │
        │   quiz_results          │
        │ )                       │
        │                         │
        │ Updates:                │
        │ • mastery_json per      │
        │   concept (new score)   │
        │ • misconceptions list   │
        │ • history_json append   │
        │ • updated_at timestamp  │
        └─────────────────────────┘
```

---

## 9. LEARNING PATH DAG CONSTRUCTION

```
        ┌─────────────────────────┐
        │ GENERATE/UPDATE DAG     │
        │ (after each assessment) │
        └────────────┬────────────┘
                     │
                     ▼
        ┌─────────────────────────┐
        │ Fetch learned concepts  │
        │ from session            │
        └────────────┬────────────┘
                     │
                     ▼
        ┌─────────────────────────┐
        │ For each concept:       │
        │                         │
        │ 1. Query LLM:           │
        │    "What are the        │
        │     prerequisites for   │
        │     this concept?"      │
        │                         │
        │ 2. LLM returns:         │
        │    {                    │
        │      prerequisites: [   │
        │        "Algebra",       │
        │        "Variables"      │
        │      ],                 │
        │      related: [...],    │
        │      advanced: [...]    │
        │    }                    │
        │                         │
        │ 3. Check learner's      │
        │    mastery_json for     │
        │    each prereq          │
        │                         │
        │ 4. Build edge if prereq │
        │    not yet mastered     │
        └────────────┬────────────┘
                     │
                     ▼
        ┌─────────────────────────┐
        │ Construct DAG JSON:     │
        │ {                       │
        │   nodes: [              │
        │     {                   │
        │       id: "algebra",    │
        │       label: "Algebra", │
        │       mastery: 0.6,     │
        │       status: "dev"     │
        │     }, ...              │
        │   ],                    │
        │   edges: [              │
        │     {                   │
        │       from: "algebra",  │
        │       to: "calculus",   │
        │       label: "prereq"   │
        │     }, ...              │
        │   ]                     │
        │ }                       │
        │                         │
        │ → Save to DBLearningPath│
        └─────────────────────────┘
```

---

## 10. ERROR HANDLING & FALLBACK CASCADE

```
          ┌────────────────────────┐
          │ ANY OPERATION FAILS    │
          │ (LLM, TTS, embed, etc.)│
          └────────────┬───────────┘
                       │
              ┌────────▼────────┐
              │ What failed?    │
              └────────┬────────┘
                       │
     ┌─────────────────┼─────────────────┐
     │                 │                 │
   [LLM]           [Embedding]       [TTS/STT]
     │                 │                 │
     ▼                 ▼                 ▼
  ┌─────────┐    ┌──────────┐    ┌────────────┐
  │Provider │    │Provider  │    │Provider    │
  │1 failed │    │1 failed  │    │1 failed    │
  │         │    │          │    │            │
  │Try      │    │Try       │    │Try         │
  │Provider │    │SHA-256   │    │Provider 2  │
  │2 (Groq) │    │fallback  │    │(Piper/     │
  │         │    │(deterministic)
  │         │    │          │    │Web Speech) │
  │         │    │ ALWAYS   │    │            │
  │         │    │ works    │    │ Graceful   │
  │         │    │ offline  │    │ silence if │
  │         │    │          │    │ all fail   │
  └────┬────┘    └────┬─────┘    └──────┬─────┘
       │              │                 │
       ▼              ▼                 ▼
   Provider 2      [Success]       [Audio
   response       (proceeds)        fallback]
       │                              │
       └──────────┬───────────────────┘
                  │
                  ▼
        ┌─────────────────────────┐
        │ IF ALL PROVIDERS FAIL   │
        │                         │
        │ → Log error             │
        │ → Return safe default   │
        │ → Continue session      │
        │ → Notify user (optional)│
        │ → Don't crash           │
        └─────────────────────────┘
```

---

## 11. STATE MACHINE TRANSITIONS

```
                    ┌──────────────┐
                    │  UNDERSTAND  │  (Initial)
                    │  State: NEW  │
                    └──────┬───────┘
                           │
                    [Parse instruction,
                     verify resources]
                           │
                           ▼
                    ┌──────────────┐
                    │    PLAN      │  (Plan lesson)
                    │ State: PLAN  │
                    └──────┬───────┘
                           │
            [Retrieve context,
             build segment plans]
                           │
                    ┌──────┴──────┐
                    │             │
                    ▼             │
            ┌──────────────────┐  │
            │  EXPLAIN         │  │
            │  (Seg N narration)   │
            └──────┬───────────┘  │
                   │              │
                   ▼              │
            ┌──────────────────┐  │
            │ DEMONSTRATE      │  │
            │ (Visual + audio)  │  │
            └──────┬───────────┘  │
                   │              │
                   ▼              │
            ┌──────────────────┐  │
            │ QUESTION         │  │
            │ (Ask checkpoint) │  │
            └──────┬───────────┘  │
                   │              │
                   ▼              │
            ┌──────────────────┐  │
            │ EVALUATE         │  │
            │ (Score answer)   │  │
            └──────┬───────────┘  │
                   │              │
        ┌──────────┴──────────┐   │
        │                     │   │
   [Correct/           [Misconception
    Partial]            or No Understanding]
        │                     │   │
        ▼                     ▼   │
   ┌─────────┐          ┌──────────────┐
   │CONTINUE │          │ ADAPT        │
   │(next seg)│          │ (Re-teach)   │
   └────┬────┘          └──────┬───────┘
        │                      │
        │          [Generate fresh
        │           analogy + visual]
        │                      │
        │                      │
        │                      ▼
        │              ┌──────────────┐
        │              │ QUESTION (2) │
        │              │ (Ask follow) │
        │              └──────┬───────┘
        │                     │
        │                     ▼
        │              ┌──────────────┐
        │              │ EVALUATE (2) │
        │              └──────┬───────┘
        │                     │
        │           ┌─────────┴─────────┐
        │           │                   │
        │      [Correct]           [Still wrong]
        │           │                   │
        │           └──────┬────────────┘
        │                  │
        └──────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ More segments left?  │
        └──────┬───────────────┘
               │
         ┌─────┴─────┐
         │           │
        YES         NO
         │           │
         ▼           │
    [Loop back       │
     to EXPLAIN      │
     for seg N+1]    │
         │           │
         │           ▼
         │    ┌─────────────┐
         │    │   ASSESS    │
         │    │ (Run formal │
         │    │  quiz)      │
         │    └──────┬──────┘
         │           │
         │           ▼
         │    ┌─────────────┐
         │    │   REPORT    │
         │    │(Generate    │
         │    │ learning    │
         │    │ report)     │
         │    └──────┬──────┘
         │           │
         └───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  COMPLETE            │
        │ State: REPORT_READY  │
        │ (Session ends)       │
        └──────────────────────┘
```

---

## 12. DATABASE PERSISTENCE CHECKPOINTS

```
       ┌─────────────────────────┐
       │ KEY PERSISTENCE EVENTS  │
       └──────────┬──────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
[Session      [Checkpoint    [Assessment
 Created]      Attempted]     Complete]
    │             │             │
    ▼             ▼             ▼
DBLessonSession
    ├─ id
    ├─ user_id
    ├─ topic
    ├─ language
    ├─ time_budget
    ├─ current_segment_id
    ├─ state
    ├─ plan_json
    ├─ taught_concepts
    ├─ analogies_used
    ├─ created_at
    └─ updated_at
          │
          └──────────────┐
                         │
DBCheckpointAttempt  DBQuiz
    ├─ id               ├─ id
    ├─ session_id       ├─ session_id
    ├─ segment_id       ├─ topic
    ├─ question_text    └─ questions_json
    ├─ student_answer
    ├─ classification   DBQuizAttempt
    ├─ feedback         ├─ id
    └─ created_at       ├─ session_id
                        ├─ score_percentage
                        ├─ details_json
                        └─ created_at

                        DBLearningReport
                        ├─ id
                        ├─ session_id
                        ├─ user_id
                        ├─ topic
                        ├─ score_percent
                        ├─ time_spent
                        ├─ report_json
                        └─ created_at

                        DBLearnerProfile
                        ├─ user_id (PK)
                        ├─ name
                        ├─ level
                        ├─ goal
                        ├─ preferred_style
                        ├─ language
                        ├─ history_json
                        ├─ mastery_json
                        └─ updated_at

                        DBLearningPath
                        ├─ id
                        ├─ user_id
                        ├─ topic_id
                        ├─ title
                        ├─ dag_json
                        ├─ progress_percentage
                        └─ updated_at
```

---

## 13. PROVIDER SELECTION LOGIC

```
            ┌──────────────────────┐
            │ NEED: LLM Response   │
            └────────────┬─────────┘
                         │
            ┌────────────▼────────────┐
            │ Read LLM_PROVIDER_ORDER │
            │ (from .env or config)   │
            │ Default: "gemini,groq,  │
            │           anthropic"    │
            └────────────┬────────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │ PROVIDER 1: GEMINI     │
            └────────────┬────────────┘
                         │
            ┌────────────▼────────────┐
            │ Check:                  │
            │ GEMINI_API_KEY set?     │
            └────────────┬────────────┘
                         │
            ┌────────────┴────────────┐
            │                         │
           YES                       NO
            │                         │
            ▼                         ▼
     ┌────────────┐          ┌─────────────┐
     │ Call REST  │          │ Skip → try  │
     │ API v1beta │          │ Provider 2  │
     │            │          └──────┬──────┘
     │ Response OK?           │
     └────┬───────┘           │
          │                   │
     ┌────┴────┐              │
     │          │              │
   YES        NO              │
     │          │              │
     ▼          ▼              │
 [Return]  [Log error]        │
 response  [Try Provider 2]   │
                              │
         ┌────────────────────┘
         │
         ▼
   ┌────────────────────────┐
   │ PROVIDER 2: GROQ       │
   └────────────┬───────────┘
                │
   ┌────────────▼───────────┐
   │ Check:                 │
   │ GROQ_API_KEY set?      │
   └────────────┬───────────┘
                │
   ┌────────────┴───────────┐
   │                        │
  YES                      NO
   │                        │
   ▼                        ▼
┌──────────┐         ┌─────────────┐
│ Call REST │         │ Skip → try  │
│ API       │         │ Provider 3  │
│ (OpenAI  │         └──────┬──────┘
│ -compat) │               │
└────┬─────┘               │
     │                     │
  [Success?]               │
     │                     │
 ┌───┴───┐                 │
 │       │                 │
YES     NO                │
 │       │                 │
 ▼       ▼                 │
[Return] [Log error]      │
response [Try Provider 3] │
                          │
         ┌────────────────┘
         │
         ▼
   ┌────────────────────────┐
   │ PROVIDER 3: ANTHROPIC  │
   └────────────┬───────────┘
                │
   ┌────────────▼───────────┐
   │ Check:                 │
   │ ANTHROPIC_API_KEY set? │
   └────────────┬───────────┘
                │
   ┌────────────┴───────────┐
   │                        │
  YES                      NO
   │                        │
   ▼                        ▼
┌──────────┐         ┌──────────────┐
│ Call REST │         │ ALL PROVIDERS│
│ Messages  │         │ EXHAUSTED    │
│ API       │         │              │
└────┬─────┘         │ Raise        │
     │               │ LLMUnavailable
  [Success?]         └──────┬───────┘
     │                      │
 ┌───┴───┐                  │
 │       │                  │
YES     NO                  │
 │       │                  │
 ▼       ▼                  │
[Return] ┌─────────────────┘
response | Call fallback:
         │ • Use cached response
         │ • Use deterministic model
         │ • Return safe default
         │ • Log for admin review
         └──────────────┬─────────┘
                        │
                        ▼
                  [Session continues
                   with degraded
                   experience]
```

---

## SUMMARY: KEY DECISION POINTS

| Decision | Input | Logic | Output |
|---|---|---|---|
| **# Segments** | time_budget | ≤5min→2, 6-20→4, >20→6 | segment_count |
| **Grounding** | RAG results | Hybrid score ≥0.3 | top_k_chunks |
| **Personalization** | learner_profile | Inject context + misconceptions | enriched_prompt |
| **Visual Type** | concept | Spatial→Diagram, Hierarchy→OrgChart, Temporal→Timeline, Data→Graph | visual_type |
| **Misconception?** | answer classification | LLM evaluates vs. rubric | misconception_name |
| **Re-teach?** | classification | If misconception/no_understanding → ADAPT | fresh_analogy |
| **Language** | session.language | If Hindi/Hinglish → special clauses | language_prompt |
| **TTS Provider** | language + API keys | ElevenLabs → Piper → Web Speech | audio_url |
| **LLM Provider** | LLM_PROVIDER_ORDER | Try Gemini → Groq → Anthropic | llm_response |
| **Assessment Difficulty** | learner_level | Beginner→Easy, Intermediate→Medium, Advanced→Hard | quiz_blueprint |
| **Next Topic** | mastery_json | Find ≤0.6 mastery concepts | recommended_next |

---

**This workflow document provides the complete decision logic for developers and architects implementing or extending Sahayak AI Teacher.**

