import pytest
from app.state_machine.teacher_agent import TeacherAgentStateMachine
from app.database import SessionLocal, init_db
from app.services.tts import TTSService
from app.services.youtube import YouTubeService

@pytest.mark.asyncio
async def test_tamil_lesson_planning_and_rendering():
    """Verify that lesson planning and segment delivery in Tamil (ta) produce Tamil-tuned output."""
    init_db()
    db = SessionLocal()
    try:
        plan = await TeacherAgentStateMachine.generate_lesson_plan(
            topic="Newton's Laws of Motion",
            material_id=None,
            profile=None,
            time_budget_minutes=10,
            language="ta",
            db=db
        )
        assert plan is not None
        assert plan.language == "ta"
        assert len(plan.segments) > 0

        # Render segment 1 in Tamil
        render = await TeacherAgentStateMachine.render_segment(
            session_id=plan.session_id,
            segment_id=1,
            language="ta",
            db=db
        )
        assert render is not None
        assert render.spoken_script
        assert render.on_screen_text
        assert len(render.captions) > 0
    finally:
        db.close()

def test_tamil_tts_voice_mapping():
    """Verify that Tamil maps to Google தமிழ் in Web Speech fallback."""
    import asyncio
    res = asyncio.run(TTSService.synthesize_speech("வணக்கம் மாணவர்களே", language="ta"))
    assert res is not None
    if res.get("provider") == "browser_speech_synthesis":
        assert res.get("voice_name") == "Google தமிழ்"

@pytest.mark.asyncio
async def test_tamil_youtube_search_localization():
    """Verify that Tamil topics append Tamil hint and set hl=ta."""
    query = await YouTubeService._generate_search_query("Gravity", "ta", None)
    assert "tamil" in query.lower()

    url = YouTubeService._fallback_search_url("Gravity", "ta")
    assert "hl=ta" in url
    assert "gl=IN" in url
