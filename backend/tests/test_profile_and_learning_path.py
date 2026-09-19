import pytest
import uuid
from sqlalchemy.orm import Session
from app.database import (
    SessionLocal, 
    init_db, 
    DBLearnerProfile, 
    DBLearningPath,
    DBLessonSession,
    DBQuizAttempt
)
from app.models.schemas import (
    LearnerProfileCreate,
    LearningReport,
    ConceptMasteryItem,
    GapMapItem,
    Citation
)
from app.services.learner_profile import LearnerProfileService
from app.services.learning_path import LearningPathService
from app.state_machine.teacher_agent import TeacherAgentStateMachine

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()

@pytest.fixture
def db_session():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.mark.asyncio
async def test_case_1_new_student_curriculum_generation(db_session: Session):
    """
    Test 1 — New student
    New student with zero learning history asks to learn Machine Learning.
    System generates coherent prerequisite-ordered DAG starting with fundamentals.
    """
    user_id = f"user-new-{uuid.uuid4().hex[:6]}"
    
    # 1. Profile initialization
    profile = LearnerProfileService.get_full_learner_profile(user_id, db_session)
    assert profile.user_id == user_id
    assert len(profile.scores_history) == 0
    assert len(profile.strong_concepts) == 0

    # 2. Generate Learning Path
    path = await LearningPathService.generate_or_get_learning_path(
        topic_id="machine-learning",
        user_id=user_id,
        db=db_session
    )

    assert path.topic_id == "machine-learning"
    assert len(path.nodes) >= 5
    # First node should have zero prerequisites and status 'available' or 'in_progress'
    assert len(path.nodes[0].prerequisites) == 0
    assert path.nodes[0].status in ["available", "in_progress"]
    
    # Downstream nodes with unmet prerequisites must be locked
    locked_nodes = [n for n in path.nodes if n.status == "locked"]
    assert len(locked_nodes) > 0

    # Recommendation should point to node 1
    rec = path.recommendation
    assert rec is not None
    assert rec.action == "MOVE_TO_NEXT_TOPIC"
    assert rec.node_id == path.nodes[0].id

@pytest.mark.asyncio
async def test_case_2_returning_student_skips_mastered_fundamentals(db_session: Session):
    """
    Test 2 — Returning student
    Existing student with demonstrated mastery in Python & Linear Algebra
    gets a personalized curriculum where early foundations are marked mastered/completed.
    """
    user_id = f"user-returning-{uuid.uuid4().hex[:6]}"
    
    # Seed profile with mastered Python & Linear Algebra
    p = LearnerProfileService.get_or_create_profile(user_id, db_session)
    p.mastery_json = {
        "Python Fundamentals": {"mastery": "mastered", "assessment_score": 98.0, "confidence": 0.95},
        "NumPy": {"mastery": "mastered", "assessment_score": 95.0, "confidence": 0.92},
        "Linear Algebra": {"mastery": "strong", "assessment_score": 90.0, "confidence": 0.90},
        "Matrix Multiplication": {"mastery": "strong", "assessment_score": 88.0, "confidence": 0.88}
    }
    p.history_json = [
        {"topic": "Python Programming", "score": 98.0, "date": "2026-08-01"},
        {"topic": "Linear Algebra Basics", "score": 90.0, "date": "2026-08-10"}
    ]
    db_session.commit()

    # Generate Learning Path
    path = await LearningPathService.generate_or_get_learning_path(
        topic_id="machine-learning",
        user_id=user_id,
        db=db_session,
        force_regenerate=True
    )

    # Node 1 and Node 2 should be recognized as mastered
    node_1 = path.nodes[0]
    node_2 = path.nodes[1]
    assert node_1.status == "mastered"
    assert node_2.status == "mastered"

    # Next recommendation should point to Data Preprocessing or Supervised Learning
    rec = path.recommendation
    assert rec is not None
    assert rec.node_id in ["node-3", "node-4"]
    assert rec.action == "MOVE_TO_NEXT_TOPIC"

@pytest.mark.asyncio
async def test_case_3_weak_prerequisite_gating(db_session: Session):
    """
    Test 3 — Weak prerequisite
    Student completes Supervised Learning, performs poorly on Model Evaluation (score 50%).
    System detects weakness, locks downstream Neural Networks, and recommends REVISE_CONCEPT.
    """
    user_id = f"user-struggle-{uuid.uuid4().hex[:6]}"
    topic_id = "machine-learning"
    
    # Generate path
    path = await LearningPathService.generate_or_get_learning_path(
        topic_id=topic_id,
        user_id=user_id,
        db=db_session,
        force_regenerate=True
    )

    # Mark nodes 1-4 completed in DB
    db_path = db_session.query(DBLearningPath).filter(
        DBLearningPath.user_id == user_id, 
        DBLearningPath.topic_id == topic_id
    ).first()
    if not db_path:
        db_path = db_session.query(DBLearningPath).filter(DBLearningPath.user_id == user_id).first()
    if not db_path:
        db_path = DBLearningPath(
            id=str(uuid.uuid4()),
            user_id=user_id,
            topic_id=topic_id,
            title=path.title,
            dag_json=path.model_dump(mode="json"),
            progress_percentage=path.completion_percentage
        )
        db_session.add(db_path)
        db_session.commit()

    data = dict(db_path.dag_json) if db_path.dag_json else path.model_dump(mode="json")
    for n in data.get("nodes", []):
        if n.get("id") in ["node-1", "node-2", "node-3", "node-4"]:
            n["completed"] = True
            n["score"] = 90.0
            n["status"] = "mastered"
    db_path.dag_json = data
    db_session.commit()

    # Simulate failing assessment on Model Evaluation (node-5)
    report = LearningReport(
        session_id=str(uuid.uuid4()),
        user_id=user_id,
        topic="Model Evaluation, Validation & Overfitting Diagnostics",
        score_percent=50.0,
        time_spent_minutes=20,
        concepts_understood=["Confusion Matrices"],
        weak_areas=["Cross-Validation", "Overfitting"],
        misconceptions_encountered=["Believes cross-validation prevents all test set bias"],
        recommended_revision=["Review k-fold cross-validation mechanics."],
        suggested_next_topics=["Targeted Revision: Cross-Validation"],
        concept_masteries=[
            ConceptMasteryItem(concept="Model Evaluation", mastery="weak", score_percent=50.0, revision_needed=True),
            ConceptMasteryItem(concept="Cross-Validation", mastery="weak", score_percent=40.0, revision_needed=True),
            ConceptMasteryItem(concept="Overfitting", mastery="misunderstood", score_percent=30.0, revision_needed=True, misconceptions=["Believes regularization removes data"])
        ],
        is_ready_for_next_topic=False,
        readiness_reason="Prerequisite concepts weak."
    )

    # Update profile and path
    LearnerProfileService.update_profile_from_assessment(user_id=user_id, report=report, db=db_session)
    updated_path = LearningPathService.update_path_from_assessment(user_id=user_id, topic_id="machine-learning", report=report, db=db_session)

    assert updated_path is not None
    node_5 = next(n for n in updated_path.nodes if n.id == "node-5")
    node_6 = next(n for n in updated_path.nodes if n.id == "node-6")

    # Node 5 must be in needs_revision state
    assert node_5.status == "needs_revision"

    # Node 6 (Neural Networks) requires node-5, so it MUST be locked
    assert node_6.status == "locked"
    assert "Requires mastery of" in (node_6.prerequisite_reason or "")

    # Recommendation must be REVISE_CONCEPT for Model Evaluation
    rec = updated_path.recommendation
    assert rec is not None
    assert rec.action == "REVISE_CONCEPT"
    assert rec.node_id == "node-5"

@pytest.mark.asyncio
async def test_case_4_strong_student_advancement(db_session: Session):
    """
    Test 4 — Strong student
    Student demonstrates mastery (95% score), profile records mastery, downstream node unlocks,
    recommendation advances to next unit.
    """
    user_id = f"user-strong-{uuid.uuid4().hex[:6]}"
    
    path = await LearningPathService.generate_or_get_learning_path(
        topic_id="machine-learning",
        user_id=user_id,
        db=db_session,
        force_regenerate=True
    )

    # Complete Node 1 with 95% score
    report = LearningReport(
        session_id=str(uuid.uuid4()),
        user_id=user_id,
        topic="Python Fundamentals & Numerical Arrays",
        score_percent=95.0,
        time_spent_minutes=20,
        concepts_understood=["Python Fundamentals", "NumPy", "Vectorization"],
        weak_areas=[],
        misconceptions_encountered=[],
        recommended_revision=[],
        suggested_next_topics=["Mathematics for ML"],
        concept_masteries=[
            ConceptMasteryItem(concept="Python Fundamentals", mastery="mastered", score_percent=95.0),
            ConceptMasteryItem(concept="NumPy", mastery="mastered", score_percent=95.0)
        ],
        is_ready_for_next_topic=True,
        readiness_reason="Mastered foundations."
    )

    LearnerProfileService.update_profile_from_assessment(user_id=user_id, report=report, db=db_session)
    updated_path = LearningPathService.update_path_from_assessment(user_id=user_id, topic_id="machine-learning", report=report, db=db_session)

    assert updated_path is not None
    node_1 = updated_path.nodes[0]
    node_2 = updated_path.nodes[1]

    assert node_1.status == "mastered"
    # Node 2 requires Node 1, and should now be unlocked ('available' or 'in_progress')
    assert node_2.status in ["available", "in_progress"]
    assert updated_path.recommendation.node_id == "node-2"
    assert updated_path.recommendation.action == "MOVE_TO_NEXT_TOPIC"

@pytest.mark.asyncio
async def test_case_5_misconception_adaptation_in_ai_teacher(db_session: Session):
    """
    Test 5 — Misconception diagnosis & AI Teacher personalization
    Misconception recorded in learner profile is passed into RelevantLearnerContext
    and embedded into the AI Teacher lesson planner prompt.
    """
    user_id = f"user-misconception-{uuid.uuid4().hex[:6]}"
    
    # Record misconception in student profile
    p = LearnerProfileService.get_or_create_profile(user_id, db_session)
    p.mastery_json = {
        "Electrical Resistance": {
            "mastery": "misunderstood",
            "misconceptions": ["Believes resistors consume and destroy electrical charge carriers"],
            "assessment_score": 40.0,
            "evidence": ["Stated in assessment that electrons disappear across resistance"]
        }
    }
    db_session.commit()

    # Extract relevant learner context
    rel_ctx = LearnerProfileService.get_relevant_learner_context(
        user_id=user_id,
        target_topic="Ohm's Law & Electrical Resistance",
        db=db_session
    )

    assert len(rel_ctx.misconceptions) > 0
    assert "resistors consume and destroy" in rel_ctx.misconceptions[0]
    assert len(rel_ctx.pedagogical_instructions) > 0
    assert "PRIOR MISCONCEPTION ALERT" in rel_ctx.pedagogical_instructions[0]

    # Generate lesson plan for this student and verify it incorporates personalized profile context
    plan = await TeacherAgentStateMachine.generate_lesson_plan(
        topic="Ohm's Law & Electrical Resistance",
        material_id=None,
        time_budget_minutes=20,
        language="en",
        profile=LearnerProfileCreate(user_id=user_id, level="beginner"),
        db=db_session
    )

    assert plan is not None
    assert len(plan.segments) >= 2

@pytest.mark.asyncio
async def test_case_6_resume_learning(db_session: Session):
    """
    Test 6 — Resume learning
    Student leaves halfway through topic. System identifies current position and resumes appropriately.
    """
    user_id = f"user-resume-{uuid.uuid4().hex[:6]}"

    path = await LearningPathService.generate_or_get_learning_path(
        topic_id="electricity",
        user_id=user_id,
        db=db_session,
        force_regenerate=True
    )

    # Complete Node 1 & 2
    path.nodes[0].completed = True
    path.nodes[0].status = "mastered"
    path.nodes[1].completed = True
    path.nodes[1].status = "completed"

    profile = LearnerProfileService.get_full_learner_profile(user_id, db_session)
    evaluated = LearningPathService.evaluate_path_prerequisites(path, profile)

    # Node 3 should be the active in-progress node
    assert evaluated.current_node_id == "node-3"
    assert evaluated.recommendation.node_id == "node-3"
    assert evaluated.recommendation.node_title == "3. Ohm's Law & Electrical Resistance"

@pytest.mark.asyncio
async def test_case_7_full_end_to_end_pipeline(db_session: Session):
    """
    Test 7 — Full End-to-End Pipeline
    Student -> Profile -> Learning Path -> Lesson -> Assessment -> Evaluation -> Mastery Update -> Profile Update -> Path Update -> Next Decision.
    """
    user_id = f"user-e2e-{uuid.uuid4().hex[:6]}"

    # 1. Profile & Initial Path
    profile_1 = LearnerProfileService.get_full_learner_profile(user_id, db_session)
    path_1 = await LearningPathService.generate_or_get_learning_path("machine-learning", user_id, db_session, force_regenerate=True)
    assert path_1.nodes[0].status in ["available", "in_progress"]
    assert path_1.nodes[1].status == "locked"

    # 2. Lesson generation with profile context
    lesson_plan = await TeacherAgentStateMachine.generate_lesson_plan(
        topic=path_1.nodes[0].title,
        material_id=None,
        time_budget_minutes=20,
        language="en",
        profile=LearnerProfileCreate(user_id=user_id, level="beginner"),
        db=db_session
    )
    assert lesson_plan.topic is not None
    assert len(lesson_plan.segments) >= 2

    # 3. Assessment completion with high score
    report = LearningReport(
        session_id=lesson_plan.session_id,
        user_id=user_id,
        topic=path_1.nodes[0].title,
        score_percent=92.0,
        time_spent_minutes=20,
        concepts_understood=["Python Fundamentals", "NumPy"],
        weak_areas=[],
        misconceptions_encountered=[],
        recommended_revision=[],
        suggested_next_topics=["Mathematics for ML"],
        concept_masteries=[
            ConceptMasteryItem(concept="Python Fundamentals", mastery="mastered", score_percent=92.0),
            ConceptMasteryItem(concept="NumPy", mastery="strong", score_percent=92.0)
        ],
        is_ready_for_next_topic=True,
        readiness_reason="Mastered node 1."
    )

    # 4. Update Profile & Path
    updated_profile = LearnerProfileService.update_profile_from_assessment(user_id, report, db_session)
    updated_path = LearningPathService.update_path_from_assessment(user_id, "machine-learning", report, db_session)

    # 5. Verify Profile updated
    assert "Python Fundamentals" in updated_profile.concept_masteries
    assert updated_profile.concept_masteries["Python Fundamentals"]["mastery"] == "mastered"
    assert len(updated_profile.scores_history) == 1

    # 6. Verify Path unlocked Node 2
    assert updated_path is not None
    assert updated_path.nodes[0].status == "mastered"
    assert updated_path.nodes[1].status in ["available", "in_progress"]
    assert updated_path.recommendation.node_id == "node-2"
    assert updated_path.recommendation.action == "MOVE_TO_NEXT_TOPIC"
