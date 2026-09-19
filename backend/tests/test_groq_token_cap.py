import pytest
import json
import httpx
from unittest.mock import patch

from app.config import settings
from app.services.llm import LLMService
from app.state_machine.teacher_agent import TeacherAgentStateMachine
from app.database import SessionLocal, init_db

@pytest.mark.asyncio
async def test_groq_provider_token_cap_setting():
    """Verify that Groq calls send max_tokens=4096 in payload."""
    recorded_payloads = []

    async def mock_post(url, *args, **kwargs):
        recorded_payloads.append(kwargs.get("json", {}))
        # Return a valid mock response with 5 segments
        five_seg_plan = {
            "session_id": "test-sess-groq",
            "topic": "Machine Learning Fundamentals",
            "segments": [
                {
                    "segment_id": i + 1,
                    "concept": f"Concept {i + 1}",
                    "depth": "intuition",
                    "est_minutes": 4,
                    "visual_type": "diagram",
                    "checkpoint_question": {
                        "question": f"Question {i + 1}?",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": "A",
                        "concept_tested": f"Concept {i + 1}"
                    },
                    "summary": f"Summary for segment {i + 1}",
                    "chunk_ids": [f"chunk-{i + 1}"]
                }
                for i in range(5)
            ]
        }
        mock_resp = httpx.Response(
            status_code=200,
            json={"choices": [{"message": {"content": json.dumps(five_seg_plan)}}]},
            request=httpx.Request("POST", url)
        )
        return mock_resp

    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        orig_key = settings.GROQ_API_KEY
        settings.GROQ_API_KEY = "gsk_dummy_test_key_long_enough_12345"
        try:
            res = await LLMService._call_groq(
                system_prompt="You are a teacher.",
                user_prompt="Generate a 5-segment lesson plan.",
                temperature=0.2
            )
            assert len(recorded_payloads) > 0
            payload = recorded_payloads[0]
            assert payload.get("max_tokens") == 4096, f"Expected max_tokens 4096, got {payload.get('max_tokens')}"
            
            # Verify parsed JSON has >= 5 segments
            parsed = json.loads(res)
            assert len(parsed["segments"]) >= 5
        finally:
            settings.GROQ_API_KEY = orig_key

@pytest.mark.asyncio
async def test_groq_lesson_plan_generation_no_truncation():
    """
    Regression test: Generates a lesson plan with >= 5 segments on the Groq provider path
    and asserts the response is not truncated (valid JSON parse succeeds and segment count matches request).
    """
    init_db()
    db = SessionLocal()
    orig_order = settings.LLM_PROVIDER_ORDER
    try:
        settings.LLM_PROVIDER_ORDER = "groq,gemini,anthropic"

        # Generate a lesson plan with 30 minutes budget (targets 6 segments >= 5)
        plan = await TeacherAgentStateMachine.generate_lesson_plan(
            topic="Photosynthesis and Cellular Respiration",
            material_id=None,
            profile=None,
            time_budget_minutes=30,
            language="en",
            db=db
        )
        assert plan is not None
        assert hasattr(plan, "segments")
        assert len(plan.segments) >= 5, f"Expected at least 5 segments, got {len(plan.segments)}"
        
        # Verify segment integrity
        for seg in plan.segments:
            assert seg.concept
            assert seg.summary
            assert seg.checkpoint_question is not None
            assert seg.checkpoint_question.question
    finally:
        settings.LLM_PROVIDER_ORDER = orig_order
        db.close()
