import sys
import os
import json
from typing import Any, Dict, List

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            getattr(sys.stdout, "reconfigure")(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            getattr(sys.stderr, "reconfigure")(encoding="utf-8")
    except Exception:
        pass

import httpx

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

BASE = "http://localhost:8000"
results: List[Dict[str, Any]] = []

def log_test(name: str, success: bool, detail: str = ""):
    status_str = "PASS" if success else "FAIL"
    results.append({"endpoint": name, "status": status_str, "detail": detail})
    prefix = "[OK]" if success else "[ERROR]"
    print(f"{prefix} [{status_str}] {name} - {detail}")

# Probe if external server is listening on BASE; otherwise seamlessly use in-process TestClient
client: Any = None
try:
    with httpx.Client(timeout=1.5) as probe:
        r_probe = probe.get(f"{BASE}/health")
        if r_probe.status_code == 200:
            client = httpx.Client(base_url=BASE, timeout=25.0)
            print(f"[*] Connected to active backend server at {BASE}")
except Exception:
    pass

if client is None:
    from fastapi.testclient import TestClient
    from main import app
    from app.database import init_db
    init_db()
    client = TestClient(app)
    print("[*] Live server not detected on port 8000; executing via high-speed FastAPI TestClient.")

# 1. Health & Root
try:
    r = client.get("/")
    log_test("GET /", r.status_code == 200, f"status={r.status_code}")
except Exception as e:
    log_test("GET /", False, str(e))

try:
    r = client.get("/api/health")
    log_test("GET /api/health", r.status_code == 200, f"status={r.status_code}")
except Exception as e:
    log_test("GET /api/health", False, str(e))

# 2. Lesson Plan
session_id = None
correct_answer = ""
try:
    r = client.post("/api/lesson/plan", json={
        "topic": "Newton's Laws of Motion",
        "time_budget_minutes": 20,
        "language": "en"
    })
    data = r.json()
    session_id = data.get("session_id")
    segments = data.get("segments", [])
    if segments:
        correct_answer = segments[0].get("checkpoint_question", {}).get("correct_answer", "")
    log_test("POST /api/lesson/plan", r.status_code == 200 and bool(session_id), f"session_id={session_id[:8] if session_id else 'None'}... segments={len(segments)}")
except Exception as e:
    log_test("POST /api/lesson/plan", False, str(e))

# 3. Segment Render
if session_id:
    try:
        r = client.post(f"/api/lesson/segment/1/render?session_id={session_id}")
        data = r.json()
        log_test("POST /api/lesson/segment/1/render", r.status_code == 200 and "visual_spec" in data, f"concept={data.get('concept', '')[:25]} captions={len(data.get('captions', []))}")
    except Exception as e:
        log_test("POST /api/lesson/segment/1/render", False, str(e))

# 4. Checkpoint Answer (Mastery)
if session_id:
    try:
        ans = correct_answer or "A"
        r = client.post("/api/interact/answer", json={
            "session_id": session_id,
            "segment_id": 1,
            "student_answer": ans,
            "is_demo_mode": False
        })
        data = r.json()
        log_test("POST /api/interact/answer (Mastery)", r.status_code == 200 and data.get("action") == "advance", f"action={data.get('action')}")
    except Exception as e:
        log_test("POST /api/interact/answer (Mastery)", False, str(e))

# 5. Misconception & Dynamic Reteach Loop
if session_id:
    try:
        r = client.post("/api/interact/answer", json={
            "session_id": session_id,
            "segment_id": 1,
            "student_answer": "I think force is stored in a moving body until it runs out.",
            "force_misconception": True
        })
        data = r.json()
        is_reteach = data.get("action") == "reteach"
        log_test("POST /api/interact/answer (Reteach Loop)", r.status_code == 200 and is_reteach, f"misconception={data.get('misconception_name', '')[:30]}")
    except Exception as e:
        log_test("POST /api/interact/answer (Reteach Loop)", False, str(e))

# 6. Simplify Explanation
if session_id:
    try:
        r = client.post("/api/interact/request-simplification", json={
            "session_id": session_id,
            "segment_id": 1
        })
        data = r.json()
        log_test("POST /api/interact/request-simplification", r.status_code == 200 and data.get("action") == "reteach", f"action={data.get('action')}")
    except Exception as e:
        log_test("POST /api/interact/request-simplification", False, str(e))

# 7. Code Sandbox
try:
    r = client.post("/api/sandbox/run", json={
        "code": "print(sum([x**2 for x in range(5)]))"
    })
    data = r.json()
    log_test("POST /api/sandbox/run (Code Runner)", r.status_code == 200 and data.get("stdout", "").strip() == "30", f"stdout={data.get('stdout', '').strip()}")
except Exception as e:
    log_test("POST /api/sandbox/run", False, str(e))

# 8. Learning Path DAG
try:
    r = client.get("/api/learning-path/quantum-computing")
    data = r.json()
    nodes = data.get("nodes", [])
    log_test("GET /api/learning-path/{topic_id}", r.status_code == 200 and len(nodes) > 0, f"nodes={len(nodes)}")
except Exception as e:
    log_test("GET /api/learning-path/{topic_id}", False, str(e))

# 9. Assessment Quiz Generation & Grading
if session_id:
    try:
        r = client.post(f"/api/assess/quiz/{session_id}")
        data = r.json()
        questions = data.get("questions", [])
        log_test("POST /api/assess/quiz/{session_id}", r.status_code == 200 and len(questions) > 0, f"questions={len(questions)}")
        
        # Grade Quiz
        if questions:
            answers = {str(q.get("id", f"q_{idx}")): str(q.get("options", ["A"])[0]) for idx, q in enumerate(questions)}
            r_grade = client.post("/api/assess/grade", json={
                "session_id": session_id,
                "answers": answers
            })
            g_data = r_grade.json()
            log_test("POST /api/assess/grade", r_grade.status_code == 200 and "score_percentage" in g_data, f"score={g_data.get('score_percentage')}%")
    except Exception as e:
        log_test("POST /api/assess/quiz/{session_id}", False, str(e))

# 10. Learning Report
if session_id:
    try:
        r = client.get(f"/api/report/{session_id}")
        data = r.json()
        has_score = "overall_score" in data or "score_percent" in data
        score_val = data.get("overall_score", data.get("score_percent", 0))
        log_test("GET /api/report/{session_id}", r.status_code == 200 and has_score, f"score={score_val}%")
    except Exception as e:
        log_test("GET /api/report/{session_id}", False, str(e))

# 11. Media TTS Audio
try:
    r = client.post("/api/media/tts", json={
        "text": "Welcome to Sahayak AI Teacher.",
        "language": "en"
    })
    data = r.json()
    log_test("POST /api/media/tts (Neural Voice)", r.status_code == 200 and data.get("success"), f"provider={data.get('provider')}")
except Exception as e:
    log_test("POST /api/media/tts", False, str(e))

# 12. Learner Profile
try:
    r = client.get("/api/profile/default-user")
    log_test("GET /api/profile/{user_id}", r.status_code == 200, f"user={r.json().get('user_id')}")
except Exception as e:
    log_test("GET /api/profile/{user_id}", False, str(e))

total_passed = sum(1 for res in results if res["status"] == "PASS")
print("\n==========================================")
print(f"Diagnostic Summary: {total_passed}/{len(results)} Endpoints Operational.")
print("==========================================")
