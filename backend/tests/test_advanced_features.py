import pytest
from fastapi.testclient import TestClient
from main import app
from app.database import SessionLocal, DBLearnerProfile, DBLessonSession, DBQuizAttempt

client = TestClient(app)

def test_teacher_personalities():
    """Verify listing teacher personalities and setting personality for a student."""
    # 1. Get available personalities
    resp = client.get("/api/study-tools/personalities")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 4
    personalities = [p["personality"] for p in data]
    assert "socratic" in personalities
    assert "friendly" in personalities
    assert "strict_coach" in personalities
    assert "visual" in personalities

    # 2. Select teacher personality
    user_id = "test-personality-user"
    resp2 = client.post(f"/api/study-tools/personalities/select?user_id={user_id}&personality=strict_coach")
    assert resp2.status_code == 200
    res2 = resp2.json()
    assert res2["teacher_personality"] == "strict_coach"
    assert res2["config"]["tone"] == "direct, disciplined, and razor-sharp"


def test_weak_student_revision_mode_and_homework():
    """
    Test B: Weak Student
    - Set up a student with weak & misunderstood concepts
    - Revision Mode generates targeted session focusing on weak concepts
    - Personalized Homework generates 'remedial' stepped-guidance assignments
    """
    db = SessionLocal()
    user_id = "test-weak-student"
    try:
        p = db.query(DBLearnerProfile).filter(DBLearnerProfile.user_id == user_id).first()
        if not p:
            p = DBLearnerProfile(
                user_id=user_id,
                name="Struggling Student",
                level="beginner",
                mastery_json={
                    "Ohm's Law": {"mastery": "weak", "misconceptions": ["Confusing current with voltage"]},
                    "Kirchhoff's Laws": {"mastery": "developing"},
                    "Resistance": {"mastery": "weak"}
                },
                history_json=[{"topic": "Electricity", "score": 52, "date": "2026-09-01"}]
            )
            db.add(p)
            db.commit()
    finally:
        db.close()

    # 1. Test Revision Mode session generation
    rev_resp = client.post("/api/study-tools/revision-session", json={
        "user_id": user_id,
        "topic": "Electricity"
    })
    assert rev_resp.status_code == 200
    rev_data = rev_resp.json()
    assert rev_data["mode"] == "revision"
    assert "Ohm's Law" in rev_data["weak_concepts_targeted"] or "Resistance" in rev_data["weak_concepts_targeted"]
    assert len(rev_data["segments"]) >= 1

    # 2. Test Personalized Homework (Should be remedial / guided tier)
    hw_resp = client.post(f"/api/study-tools/homework/generate?user_id={user_id}&topic=Ohm's Law")
    assert hw_resp.status_code == 200
    hw_data = hw_resp.json()
    assert hw_data["tier"] == "remedial"
    assert len(hw_data["tasks"]) >= 1
    assert any(t.get("guided_steps") is not None for t in hw_data["tasks"])

    # 3. Test Flashcard Generation (prioritizing weak concepts)
    fc_resp = client.post(f"/api/study-tools/flashcards/generate?user_id={user_id}&topic=Electricity")
    assert fc_resp.status_code == 200
    fc_data = fc_resp.json()
    assert len(fc_data["cards"]) >= 3
    assert "Ohm's Law" in fc_data["mastery_focus"] or "Resistance" in fc_data["mastery_focus"]


def test_strong_student_advanced_homework_and_notes():
    """
    Test A: Strong Student
    - Set up a high-performing student
    - Personalized Homework generates 'advanced' challenge & design exercises
    - Automatic Notes generation creates structured revision blocks
    """
    db = SessionLocal()
    user_id = "test-strong-student"
    try:
        p = db.query(DBLearnerProfile).filter(DBLearnerProfile.user_id == user_id).first()
        if not p:
            p = DBLearnerProfile(
                user_id=user_id,
                name="Advanced Scholar",
                level="advanced",
                mastery_json={
                    "Machine Learning": {"mastery": "mastered"},
                    "Neural Networks": {"mastery": "strong"},
                    "Backpropagation": {"mastery": "mastered"}
                },
                history_json=[
                    {"topic": "Machine Learning", "score": 95, "date": "2026-09-02"},
                    {"topic": "Neural Networks", "score": 92, "date": "2026-09-03"}
                ]
            )
            db.add(p)
            db.commit()
    finally:
        db.close()

    # 1. Homework should be advanced challenge tier
    hw_resp = client.post(f"/api/study-tools/homework/generate?user_id={user_id}&topic=Machine Learning")
    assert hw_resp.status_code == 200
    hw_data = hw_resp.json()
    assert hw_data["tier"] == "advanced"
    assert any(t["task_type"] in ["challenge", "design"] for t in hw_data["tasks"])

    # 2. Automatic Notes Generation
    notes_resp = client.post(f"/api/study-tools/notes/generate?user_id={user_id}&topic=Machine Learning")
    assert notes_resp.status_code == 200
    notes_data = notes_resp.json()
    assert notes_data["topic"] == "Machine Learning"
    assert len(notes_data["key_ideas"]) >= 1
    assert "summary_markdown" in notes_data


def test_exam_preparation_mode():
    """
    Test C: Exam Preparation Mode
    - Request targeted exam roadmap
    - Validates milestone phases, high-yield topic prioritization, and mock exam schedules
    """
    user_id = "test-exam-prep-student"
    exam_payload = {
        "user_id": user_id,
        "subject": "Quantum Mechanics",
        "days_until_exam": 20,
        "target_score_percent": 90.0,
        "daily_study_hours": 2.0
    }
    resp = client.post("/api/study-tools/exam-prep/generate", json=exam_payload)
    assert resp.status_code == 200
    plan = resp.json()
    assert plan["subject"] == "Quantum Mechanics"
    assert plan["days_until_exam"] == 20
    assert len(plan["milestones"]) == 4
    assert any(m["mock_test_scheduled"] for m in plan["milestones"])


def test_automatic_study_planner_and_recalculation():
    """
    Test Study Planner & Dynamic Catch-up Recalculation
    """
    user_id = "test-planner-student"
    plan_payload = {
        "user_id": user_id,
        "topic_id": "Data Structures",
        "daily_minutes": 60,
        "target_days": 5
    }
    # 1. Initial Plan Generation
    resp = client.post("/api/study-tools/study-plan/generate", json=plan_payload)
    assert resp.status_code == 200
    plan = resp.json()
    assert len(plan["days"]) == 5
    assert plan["auto_adjusted"] is False

    # 2. Recalculate schedule when falling behind on Day 2
    recalc_payload = {
        "user_id": user_id,
        "topic_id": "Data Structures",
        "missed_up_to_day": 2
    }
    recalc_resp = client.post("/api/study-tools/study-plan/recalculate", json=recalc_payload)
    assert recalc_resp.status_code == 200
    recalc_plan = recalc_resp.json()
    assert recalc_plan["auto_adjusted"] is True
    assert "rebalanced" in recalc_plan["adjustment_reason"].lower()


def test_flashcard_review_and_mastery_improvement():
    """
    Test E: Flashcard Review -> Concept Mastery Update -> Learning Analytics
    """
    user_id = "test-mastery-improvement-user"
    db = SessionLocal()
    try:
        p = db.query(DBLearnerProfile).filter(DBLearnerProfile.user_id == user_id).first()
        if not p:
            p = DBLearnerProfile(
                user_id=user_id,
                name="Improving Learner",
                mastery_json={"Calculus Derivatives": {"mastery": "weak", "attempts": 1, "correct_count": 0}},
                history_json=[
                    {"topic": "Calculus", "score": 60, "date": "2026-09-01"},
                    {"topic": "Calculus Derivatives", "score": 85, "date": "2026-09-04"}
                ]
            )
            db.add(p)
            db.commit()
    finally:
        db.close()

    # 1. Review flashcards correctly
    rev1 = client.post("/api/study-tools/flashcards/review", json={
        "user_id": user_id,
        "card_id": "card-1",
        "concept": "Calculus Derivatives",
        "result": "correct"
    })
    assert rev1.status_code == 200

    # 2. Review second time correctly -> should promote to mastered
    rev2 = client.post("/api/study-tools/flashcards/review", json={
        "user_id": user_id,
        "card_id": "card-2",
        "concept": "Calculus Derivatives",
        "result": "correct"
    })
    assert rev2.status_code == 200
    assert rev2.json()["new_mastery_state"] == "mastered"

    # 3. Learning Analytics reflects improvement
    an_resp = client.get(f"/api/study-tools/analytics/{user_id}")
    assert an_resp.status_code == 200
    an_data = an_resp.json()
    assert an_data["overall_mastery_percent"] > 0
    assert an_data["learning_trajectory"] in ["improving", "recovering_after_revision", "stable"]
    assert len(an_data["recent_scores"]) >= 1
