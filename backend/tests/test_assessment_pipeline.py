import pytest
import uuid
from app.services.assessment import AssessmentService
from app.state_machine.teacher_agent import TeacherAgentStateMachine
from app.database import SessionLocal, init_db, DBLessonSession, DBCheckpointAttempt
from app.models.schemas import (
    Quiz, 
    QuizGradeResponse, 
    LearningReport, 
    AssessmentBlueprint, 
    ConceptMasteryItem
)

@pytest.fixture(scope="module")
def db_session():
    init_db()
    db = SessionLocal()
    yield db
    db.close()

async def create_electricity_session(db_session) -> str:
    """Creates a sample Electricity lesson session with segments: Current, Voltage, Resistance, Ohm's Law."""
    plan = await TeacherAgentStateMachine.generate_lesson_plan(
        topic="Foundations of Electricity: Current, Voltage, Resistance, and Ohm's Law",
        material_id=None,
        profile=None,
        time_budget_minutes=20,
        language="en",
        db=db_session
    )
    return plan.session_id

@pytest.mark.asyncio
async def test_case_1_strong_student(db_session):
    """Case 1: Strong student answers all questions correctly."""
    session_id = await create_electricity_session(db_session)
    quiz = await AssessmentService.generate_quiz_for_session(session_id, db_session)
    assert isinstance(quiz, Quiz)
    assert len(quiz.questions) >= 4

    # Build 100% correct answers dict
    correct_answers = {q.id: q.correct_answer for q in quiz.questions}
    grade_res = await AssessmentService.grade_quiz_submission(session_id, correct_answers, db_session)
    
    assert isinstance(grade_res, QuizGradeResponse)
    assert grade_res.score_percentage >= 90.0
    assert all(r.is_correct for r in grade_res.results)
    assert all(r.evaluation_status == "correct" for r in grade_res.results)

    # Learning Report Verification
    report = await AssessmentService.build_learning_report(session_id, db_session)
    assert isinstance(report, LearningReport)
    assert report.score_percent >= 90.0
    assert report.is_ready_for_next_topic is True
    assert "cleared" in report.readiness_reason.lower() or "ready" in report.readiness_reason.lower() or "mastery" in report.readiness_reason.lower()
    assert len(report.weak_areas) == 0

    # Every concept should be mastered or strong
    for cm in report.concept_masteries:
        assert cm.mastery in ["mastered", "strong"]
        assert cm.revision_needed is False

@pytest.mark.asyncio
async def test_case_2_weak_student(db_session):
    """Case 2: Weak student gives multiple incorrect answers."""
    session_id = await create_electricity_session(db_session)
    quiz = await AssessmentService.generate_quiz_for_session(session_id, db_session)

    # Build wrong answers
    wrong_answers = {q.id: "Non-existent contradictory claim" for q in quiz.questions}
    grade_res = await AssessmentService.grade_quiz_submission(session_id, wrong_answers, db_session)

    assert grade_res.score_percentage <= 30.0
    assert not all(r.is_correct for r in grade_res.results)

    # Learning Report Verification
    report = await AssessmentService.build_learning_report(session_id, db_session)
    assert report.score_percent <= 30.0
    assert report.is_ready_for_next_topic is False
    assert len(report.weak_areas) > 0
    assert len(report.actionable_revision_tasks) > 0
    assert "revision required" in report.readiness_reason.lower() or "prerequisite" in report.readiness_reason.lower()

    # Concepts should reflect weak status
    weak_count = sum(1 for cm in report.concept_masteries if cm.mastery in ["weak", "misunderstood"])
    assert weak_count >= 1

@pytest.mark.asyncio
async def test_case_3_partial_understanding(db_session):
    """Case 3: Student gives a conceptual answer that is partially correct with missing reasoning."""
    session_id = str(uuid.uuid4())
    plan = await TeacherAgentStateMachine.generate_lesson_plan(
        topic="Physics Dynamics and Resistance",
        material_id=None,
        profile=None,
        time_budget_minutes=15,
        language="en",
        db=db_session
    )
    quiz = await AssessmentService.generate_quiz_for_session(plan.session_id, db_session)
    
    # Locate a conceptual / open question or test semantic evaluator on question 1
    q1 = quiz.questions[0]
    
    # Give a partial answer (e.g. mentions basic concept but lacks formal relationship)
    partial_ans = f"It relates to how {q1.concept} changes when the input changes."
    grade_res = await AssessmentService.grade_quiz_submission(plan.session_id, {q1.id: partial_ans}, db_session)
    
    q1_res = grade_res.results[0]
    # Check that partial credit was evaluated
    assert q1_res.partial_score >= 0.0
    assert len(q1_res.understood_points) > 0 or len(q1_res.missing_points) > 0

@pytest.mark.asyncio
async def test_case_4_misconception_diagnosis(db_session):
    """Case 4: Student demonstrates a specific physical misconception (e.g. resistance blocks/destroys electricity)."""
    session_id = str(uuid.uuid4())
    plan = await TeacherAgentStateMachine.generate_lesson_plan(
        topic="Electric Resistance and Circuits",
        material_id=None,
        profile=None,
        time_budget_minutes=15,
        language="en",
        db=db_session
    )
    quiz = await AssessmentService.generate_quiz_for_session(plan.session_id, db_session)
    q1 = quiz.questions[0]

    misconception_ans = "Because resistance blocks and destroys the electricity completely."
    grade_res = await AssessmentService.grade_quiz_submission(plan.session_id, {q1.id: misconception_ans}, db_session)
    
    q1_res = grade_res.results[0]
    assert q1_res.evaluation_status in ["misconception", "partially_correct", "incorrect"]
    assert q1_res.misconception_identified is not None or "misconception" in q1_res.feedback.lower()

    report = await AssessmentService.build_learning_report(plan.session_id, db_session)
    assert len(report.misconceptions_encountered) > 0 or any(cm.mastery == "misunderstood" for cm in report.concept_masteries)

@pytest.mark.asyncio
async def test_case_5_mixed_performance_electricity(db_session):
    """
    Case 5: Mixed Performance (Electricity Benchmark Case):
    - Current: Correct
    - Voltage: Correct
    - Resistance: Incorrect
    - Ohm's Law: Partial credit
    Expected: Granular concept differentiation (Current/Voltage mastered, Resistance weak, Ohm's Law developing).
    """
    session_id = str(uuid.uuid4())
    plan = await TeacherAgentStateMachine.generate_lesson_plan(
        topic="Electricity: Current, Voltage, Resistance, Ohm's Law",
        material_id=None,
        profile=None,
        time_budget_minutes=20,
        language="en",
        db=db_session
    )
    quiz = await AssessmentService.generate_quiz_for_session(plan.session_id, db_session)
    
    # Map questions to concepts
    submission_answers = {}
    for q in quiz.questions:
        c_low = q.concept.lower()
        if "current" in c_low:
            submission_answers[q.id] = q.correct_answer
        elif "voltage" in c_low:
            submission_answers[q.id] = q.correct_answer
        elif "resistance" in c_low:
            submission_answers[q.id] = "Contradictory incorrect statement"
        else: # Ohm's Law or synthesis
            submission_answers[q.id] = f"Relates to {q.concept} proportionally but omitted formal ratio equation."

    grade_res = await AssessmentService.grade_quiz_submission(plan.session_id, submission_answers, db_session)
    report = await AssessmentService.build_learning_report(plan.session_id, db_session)

    assert len(report.concept_masteries) >= 3
    # Check concept-level differentiation
    mastery_map = {cm.concept: cm.mastery for cm in report.concept_masteries}
    
    # Ensure some are strong/mastered and some require revision
    has_strong = any(m in ["mastered", "strong"] for m in mastery_map.values())
    has_weak_or_dev = any(m in ["weak", "developing", "misunderstood"] for m in mastery_map.values())
    assert has_strong is True
    assert has_weak_or_dev is True

    # Check actionable revision tasks generated specifically for weak areas
    assert len(report.actionable_revision_tasks) > 0

@pytest.mark.asyncio
async def test_case_6_assessment_blueprint_struggle_adaptation(db_session):
    """Case 6: Assessment Blueprint assigns higher weight to concepts where student struggled during checkpoints."""
    session_id = str(uuid.uuid4())
    plan = await TeacherAgentStateMachine.generate_lesson_plan(
        topic="Newtonian Physics and Friction Dynamics",
        material_id=None,
        profile=None,
        time_budget_minutes=20,
        language="en",
        db=db_session
    )
    # Simulate a checkpoint attempt where student had a misconception on segment 2 (Friction)
    db_ck = DBCheckpointAttempt(
        id=str(uuid.uuid4()),
        session_id=plan.session_id,
        segment_id=2,
        question_text="What happens to friction?",
        student_answer="Friction is purely random",
        classification="misconception_friction",
        feedback="Friction opposes relative motion."
    )
    db_session.add(db_ck)
    db_session.commit()

    blueprint = AssessmentService.create_assessment_blueprint(plan.session_id, db_session)
    assert isinstance(blueprint, AssessmentBlueprint)
    assert len(blueprint.concepts) > 0

    # The concept corresponding to segment 2 should be marked 'struggled'
    struggled_item = next((c for c in blueprint.concepts if c.lesson_performance == "struggled"), None)
    assert struggled_item is not None
    assert struggled_item.weight > 0.20
