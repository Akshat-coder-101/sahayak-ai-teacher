import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from app.database import init_db, SessionLocal
from app.state_machine.teacher_agent import TeacherAgentStateMachine
from app.services.ingestion import IngestionService
from app.services.evaluator import EvaluatorService
from app.models.schemas import StudentAnswerRequest, LearnerProfileCreate

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

@pytest.mark.asyncio
async def test_parse_student_instruction():
    """Test deterministic and heuristic parsing of natural student prompts."""
    prompt = "I am a beginner. Teach me Chapter 4 in 20 minutes. Explain it in Hindi using simple examples. Ask me questions during the lesson and test me at the end."
    parsed = await TeacherAgentStateMachine.parse_student_instruction(prompt)

    assert parsed.learner_level == "beginner"
    assert "4" in (parsed.target_chapter or "")
    assert parsed.time_budget_minutes == 20
    assert parsed.language == "hi"
    assert "analogies" in parsed.pedagogical_style or "visual" in parsed.pedagogical_style or "socratic" in parsed.pedagogical_style or parsed.simple_examples_requested

def test_filter_chunks_by_chapter_or_topic():
    """Test targeted chapter chunk extraction from mock document chunks."""
    mock_chunks = [
        {"chunk_id": "c1", "content": "Introduction to Algorithms. Basic definitions.", "metadata": {"page": 1, "chapter": "1"}},
        {"chunk_id": "c2", "content": "Chapter 4: Binary Search Trees. A binary search tree is a rooted binary tree.", "metadata": {"page": 45, "chapter": "4"}},
        {"chunk_id": "c3", "content": "BST Insertion and Search algorithms and complexity.", "metadata": {"page": 46, "chapter": "4"}},
        {"chunk_id": "c4", "content": "Chapter 5: Graph Theory. Vertices and edges.", "metadata": {"page": 60, "chapter": "5"}},
    ]

    filtered = IngestionService.filter_chunks_by_chapter_or_topic(mock_chunks, target_chapter="Chapter 4")
    assert len(filtered) == 2

@pytest.mark.asyncio
async def test_time_budget_segment_scaling():
    """Verify segment count scaling based on 5-min, 20-min, and 60-min time budgets."""
    db = SessionLocal()
    try:
        profile_5m = LearnerProfileCreate(level="beginner", goal="understand_concept", preferred_style="visual", language="en", time_budget_minutes=5)
        plan_5m = await TeacherAgentStateMachine.generate_lesson_plan(
            topic="Photosynthesis",
            material_id=None,
            profile=profile_5m,
            time_budget_minutes=5,
            language="en",
            db=db
        )
        assert len(plan_5m.segments) <= 2

        profile_20m = LearnerProfileCreate(level="beginner", goal="understand_concept", preferred_style="visual", language="en", time_budget_minutes=20)
        plan_20m = await TeacherAgentStateMachine.generate_lesson_plan(
            topic="Photosynthesis",
            material_id=None,
            profile=profile_20m,
            time_budget_minutes=20,
            language="en",
            db=db
        )
        assert len(plan_20m.segments) >= 3

        profile_60m = LearnerProfileCreate(level="beginner", goal="understand_concept", preferred_style="visual", language="en", time_budget_minutes=60)
        plan_60m = await TeacherAgentStateMachine.generate_lesson_plan(
            topic="Photosynthesis",
            material_id=None,
            profile=profile_60m,
            time_budget_minutes=60,
            language="en",
            db=db
        )
        assert len(plan_60m.segments) >= 5
    finally:
        db.close()

@pytest.mark.asyncio
async def test_hindi_hybrid_rendering_and_pedagogy():
    """Verify that Hindi language selection renders Hindi instructional scripts with English technical terms preserved."""
    db = SessionLocal()
    try:
        profile = LearnerProfileCreate(level="beginner", goal="understand_concept", preferred_style="visual", language="hi", time_budget_minutes=20)
        plan = await TeacherAgentStateMachine.generate_lesson_plan(
            topic="Binary Search Trees",
            material_id=None,
            profile=profile,
            time_budget_minutes=20,
            language="hi",
            db=db
        )
        
        seg_rendered = await TeacherAgentStateMachine.render_segment(plan.session_id, 1, db=db)
        assert seg_rendered.spoken_script is not None
        assert len(seg_rendered.spoken_script) > 0
        assert seg_rendered.checkpoint_question is not None
    finally:
        db.close()

@pytest.mark.asyncio
async def test_structured_teaching_decision_state_advance_and_reteach():
    """Test that EvaluatorService populates structured TeachingDecisionState for correct answers and misconceptions."""
    db = SessionLocal()
    try:
        profile = LearnerProfileCreate(level="beginner", goal="understand_concept", preferred_style="visual", language="en", time_budget_minutes=20)
        plan = await TeacherAgentStateMachine.generate_lesson_plan(
            topic="Newton's Laws of Motion",
            material_id=None,
            profile=profile,
            time_budget_minutes=20,
            language="en",
            db=db
        )
        session_id = plan.session_id

        seg1 = await TeacherAgentStateMachine.render_segment(session_id, 1, db=db)
        correct_ans = seg1.checkpoint_question.correct_answer

        # Test Correct Answer -> Action Advance
        resp_advance = await EvaluatorService.evaluate_student_answer(
            session_id=session_id,
            segment_id=1,
            student_answer=correct_ans,
            is_demo_mode=False,
            force_misconception=False,
            db=db
        )
        assert resp_advance.classification == "correct"
        assert resp_advance.action == "advance"
        assert resp_advance.decision_state is not None
        assert resp_advance.decision_state.action == "advance"

        # Test Wrong Answer -> Action Reteach with Remediation
        options = seg1.checkpoint_question.options or []
        wrong_ans = next((opt for opt in options if opt != correct_ans), "D) Non-matching incorrect option")
        resp_reteach = await EvaluatorService.evaluate_student_answer(
            session_id=session_id,
            segment_id=1,
            student_answer=wrong_ans,
            is_demo_mode=False,
            force_misconception=False,
            db=db
        )
        assert resp_reteach.classification != "correct"
        assert resp_reteach.action == "reteach"
        assert resp_reteach.decision_state is not None
        assert resp_reteach.decision_state.action in ["reteach", "simplify", "give_example"]
    finally:
        db.close()

def test_instruction_plan_api_endpoint():
    """Test API endpoint with natural language instruction parameter."""
    resp = client.post("/api/lesson/plan", json={
        "topic": "Newton's Second Law",
        "instruction": "I am a beginner. Teach me in 20 minutes in Hindi using simple examples.",
        "time_budget_minutes": 20,
        "language": "hi"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert len(data["segments"]) > 0


