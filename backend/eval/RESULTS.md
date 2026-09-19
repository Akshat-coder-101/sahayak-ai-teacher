# Sahayak AI Teacher - Empirical Evaluation Results

This document contains empirical benchmarks and evaluation metrics gathered from real test runs on the repository codebase. In accordance with the project ground rules, **no numbers are estimated, simulated, or rounded up**; all figures below reflect actual command outputs recorded in the corresponding JSON artifacts under `backend/eval/`.

---

## 1. Executive Summary of Measured Metrics

| Benchmark | Sample Size / Scope | Measured Result | Mode / Execution Notes |
| :--- | :--- | :--- | :--- |
| **Misconception Detection Recall** | 33 student answers across 4 subjects | **100.0%** (10 / 10 misconceptions detected) | Fallback-mode (heuristic keyword / safety bias) |
| **Misconception Overall Accuracy** | 33 student answers (4 classes) | **30.3%** (10 / 33 exact class matches) | Fallback-mode (over-flags towards misconception) |
| **Grounding Citation Existence** | 10 generated lesson segments | **100.0%** (10 / 10 chunk IDs exist in database) | DB relational verification |
| **Grounding Citation Support** | 10 generated lesson segments | **100.0%** (10 / 10 supported by chunk text) | Lexical keyword overlap judge |
| **Retrieval Hit@3 (Pure Vector)** | 20 domain-specific queries | **100.0%** (20 / 20 correct chunks in top-3) | TF-IDF / Cosine similarity |
| **Retrieval Hit@3 (Hybrid 0.7/0.3)**| 20 domain-specific queries | **100.0%** (20 / 20 correct chunks in top-3) | 0.7 vector cosine + 0.3 lexical overlap |
| **Retrieval MRR (Mean Reciprocal Rank)** | 20 domain-specific queries | **1.0000** (target chunk ranked #1 in all 20) | Top rank across all 20 items |
| **Lesson Planning Latency** | 10 iterations | **p50 = 1,801ms**, **p95 = 3,354ms** | End-to-end plan generation |
| **Scene Visual Synthesis Latency** | 10 iterations | **p50 = 238ms**, **p95 = 311ms** | Slide rendering & chart synthesis |
| **FFmpeg Lossless Stitching Speedup**| 3 demo scenes (1280x720) | **5.6x faster** (0.806s re-encode -> 0.145s copy) | Lossless `-c copy` stream concatenation |

---

## 2. Misconception Classification Benchmark

### Dataset
- **Dataset File**: `backend/eval/misconceptions_dataset.json`
- **Output Artifact**: `backend/eval/misconception_results.json`
- **Total Answers**: 33
- **Subjects Covered**: Biology (Photosynthesis, Respiration), Physics (Newton's Laws, Gravity, Circuits), Computer Science (Recursion, Binary Search, Big O), Chemistry (States of Matter, Chemical Reactions).
- **Target Classes**: `correct`, `partially_correct`, `misconception`, `no_understanding`.

### Results & Confusion Matrix
During this evaluation run, upstream external LLM APIs (Gemini / Groq) hit daily rate limit quotas (HTTP 429), triggering `EvaluatorService`'s deterministic fallback heuristic. In fallback mode, the rule-based safety classifier prioritizes student safety by aggressively flagging conceptual deviations as misconceptions to prevent unguided propagation of errors.

```
Total Evaluated: 33
Evaluated Mode: Fallback-Mode (Heuristic Classifier)

Accuracy:           30.3% (10 / 33)
Misconception Recall: 100.0% (10 / 10 true misconceptions caught)
Misconception Precision: 31.25% (10 / 32 flagged answers were true misconceptions)

Confusion Matrix:
                 Pred: correct | partially_correct | misconception | no_understanding
True correct            0      |         0         |      11       |        0
True partially_correct  0      |         0         |       8       |        0
True misconception      0      |         0         |      10       |        0
True no_understanding   0      |         0         |       3       |        1
```

### Limitations & Analysis
While zero misconceptions slip through (100% recall), the fallback mode suffers from a high false-positive rate (over-flagging partially correct answers as misconceptions). When external LLM APIs are active with sufficient quota, chain-of-thought semantic classification separates nuance far better than the deterministic keyword fallbacks.

---

## 3. RAG Grounding & Citation Verification

### Dataset & Methodology
- **Script**: `backend/eval/run_grounding_eval.py`
- **Output Artifact**: `backend/eval/grounding_results.json`
- **Sample Size**: 10 generated lesson segments from the pre-generated lesson (`session-demo-photosynthesis`).
- **Rubric**:
  1. **Referential Integrity**: Does `chunk_id` cited in `teaching_points` or `visual_description` resolve to a valid row in the `material_chunks` table?
  2. **Substantive Support**: Does the chunk content contain the substantive key entities, terminology, and mechanisms asserted in the lesson script?

### Results
- **Segments Evaluated**: 10
- **Valid Chunks in DB**: 10 / 10 (**100.0%**)
- **Chunks with Supporting Evidence**: 10 / 10 (**100.0%**)
- **Mean Supporting Keyword Overlap**: 4.7 verified core terminology tokens per segment.

Every cited chunk matched its source material in the database without any orphaned or hallucinated references.

---

## 4. Chunk Retrieval Accuracy (Vector vs Hybrid)

### Dataset & Methodology
- **Dataset File**: `backend/eval/retrieval_dataset.json`
- **Script**: `backend/eval/run_retrieval_eval.py`
- **Output Artifact**: `backend/eval/retrieval_results.json`
- **Sample Size**: 20 technical queries mapped to ground-truth section targets within the Photosynthesis sample chapter.
- **Comparison**: Pure Cosine Vector Search vs Hybrid (0.7 Vector + 0.3 Lexical BM25/Overlap).

### Results
```
Total Queries: 20

Metric                  | Pure Vector | Hybrid (0.7 Vector / 0.3 Lexical)
------------------------+-------------+----------------------------------
Hit@1                   | 100.0%      | 100.0%
Hit@3                   | 100.0%      | 100.0%
Mean Reciprocal Rank    | 1.0000      | 1.0000
```
On curated textbook chapters with distinct section headings, both dense embedding vectors and hybrid scoring reliably locate the target section at Rank 1.

---

## 5. Latency Distribution & FFmpeg Stitching Speedup

### Latency Profiles
- **Script**: `backend/eval/run_latency_benchmark.py`
- **Output Artifact**: `backend/eval/latency_results.json`
- **Iterations**: 10 runs per component

| Pipeline Stage | p50 | p95 | Min | Max |
| :--- | :--- | :--- | :--- | :--- |
| **Lesson Plan Generation** | 1,801ms (1.80s) | 3,354ms (3.35s) | 1,117ms | 4,080ms |
| **Scene Visual Slide Synthesis** | 238ms (0.24s) | 311ms (0.31s) | 220ms | 352ms |

### FFmpeg Lossless Stitching Benchmark
- **Script**: `backend/scripts/benchmark_stitch.py`
- **Output Artifact**: `backend/eval/stitch_benchmark_results.json`
- **Scenes Stitched**: 3 demo video segments (1280x720, 24fps)

```
Re-encode Duration (libx264):          0.806 seconds
Lossless Stream-Copy Duration (-c copy): 0.145 seconds
Measured Speedup Factor:               5.6x faster
```

### Clarification on Speedup Claims
Previous marketing documentation cited an exaggerated speedup (e.g. "35s -> 0.11s" or "45s -> <2s"). The real, measured speedup on standard 720p scenes is **5.6x faster (0.806s vs 0.145s)**, achieved because stream-copy concatenation avoids decoding and re-encoding video frames when container codecs and parameters are aligned.
