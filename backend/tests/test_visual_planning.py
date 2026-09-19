import pytest
from app.services.visual_router import VisualRouter
from app.services.code_sandbox import CodeSandboxService
from app.state_machine.teacher_agent import TeacherAgentStateMachine
from app.models.schemas import VisualDecision, VisualSpec, LessonPlan, LessonSegmentPlan
from app.database import SessionLocal, init_db

@pytest.fixture(scope="module")
def db_session():
    init_db()
    db = SessionLocal()
    yield db
    db.close()

def test_mathematics_visual_decision():
    """Test 1: Mathematics - Quadratic Equations & Calculus"""
    decision = VisualRouter.decide_visual_strategy("Quadratic Functions and Parabolic Trajectories", "Algebra", "intermediate")
    assert decision.subject == "mathematics"
    assert decision.concept_type in ["algebraic_transformation", "quantitative_derivation"]
    assert decision.visual_type == "equation/graph"
    assert "plot" in decision.pedagogical_goal.lower() or "curve" in decision.pedagogical_goal.lower() or "function" in decision.pedagogical_goal.lower() or "algebraic" in decision.pedagogical_goal.lower()
    assert decision.observation_prompt != ""
    assert decision.knowledge_check != ""

    spec = VisualRouter.generate_visual_spec("Quadratic Equations", "equation/graph", "intermediate")
    assert spec.type == "equation/graph"
    assert "equations" in spec.payload
    assert "x_values" in spec.payload
    assert "y_values" in spec.payload
    assert len(spec.payload["x_values"]) > 0
    assert spec.decision is not None
    assert spec.decision.subject == "mathematics"

def test_physics_free_body_diagram_decision():
    """Test 2: Physics - Newton's Second Law & Force Vectors"""
    decision = VisualRouter.decide_visual_strategy("Newton's Second Law of Motion", "Friction and Applied Forces", "beginner")
    assert decision.subject == "physics"
    assert decision.concept_type == "force_dynamics"
    assert decision.visual_needed == "required"
    assert decision.visual_type == "free_body_diagram"
    assert "arrow" in decision.observation_prompt.lower() or "vector" in decision.observation_prompt.lower()
    
    spec = VisualRouter.generate_visual_spec("Newton's Laws and Applied Force", "free_body_diagram", "beginner")
    assert spec.type == "free_body_diagram"
    assert "<svg" in spec.payload.get("svg_code", "")
    assert "equations" in spec.payload
    assert "vectors" in spec.payload
    assert len(spec.payload["vectors"]) >= 2

def test_biology_cellular_process_and_anatomy():
    """Test 3: Biology - Photosynthesis biochemical cycle and Cell Organelles"""
    # Biochemical cycle
    cycle_decision = VisualRouter.decide_visual_strategy("Photosynthesis and Light Reactions", "Cellular Bioenergetics", "beginner")
    assert cycle_decision.subject == "biology"
    assert cycle_decision.concept_type == "cellular_process"
    assert cycle_decision.visual_type == "process_cycle"

    cycle_spec = VisualRouter.generate_visual_spec("Photosynthesis Cycle", "process_cycle", "beginner")
    assert cycle_spec.type == "process_cycle"
    assert "<svg" in cycle_spec.payload.get("svg_code", "")
    assert "stages" in cycle_spec.payload
    assert len(cycle_spec.payload["stages"]) >= 2

    # Structural anatomy
    anatomy_decision = VisualRouter.decide_visual_strategy("Mitochondria Structure", "Cell Organelles", "intermediate")
    assert anatomy_decision.subject == "biology"
    assert anatomy_decision.visual_type == "labeled-diagram"

    anatomy_spec = VisualRouter.generate_visual_spec("Mitochondria", "labeled-diagram", "intermediate")
    assert anatomy_spec.type == "labeled-diagram"
    assert "<svg" in anatomy_spec.payload.get("svg_code", "")
    assert "labels" in anatomy_spec.payload

def test_history_chronology_decision():
    """Test 4: History - Chronological timeline with causal milestones"""
    decision = VisualRouter.decide_visual_strategy("World War II Pacific Theater", "Global Conflicts in the 20th Century", "beginner")
    assert decision.subject == "history"
    assert decision.concept_type == "chronological_sequence"
    assert decision.visual_type == "timeline/map"
    assert "timeline" in decision.pedagogical_goal.lower() or "chronol" in decision.pedagogical_goal.lower()

    spec = VisualRouter.generate_visual_spec("World War II", "timeline/map", "beginner")
    assert spec.type == "timeline/map"
    assert "events" in spec.payload
    assert len(spec.payload["events"]) >= 3
    assert all("year" in ev and "title" in ev for ev in spec.payload["events"])

def test_computer_science_code_execution():
    """Test 5: Computer Science - Binary Search Algorithm & Live Sandbox"""
    decision = VisualRouter.decide_visual_strategy("Binary Search Algorithm", "Divide and Conquer Search in Arrays", "beginner")
    assert decision.subject == "computer_science"
    assert decision.concept_type == "algorithmic_procedure"
    assert decision.visual_type == "code+execution"

    spec = VisualRouter.generate_visual_spec("Binary Search", "code+execution", "beginner")
    assert spec.type == "code+execution"
    assert "def binary_search" in spec.payload.get("code", "")
    
    # Run sandbox code verification
    exec_result = CodeSandboxService.run_python_code(spec.payload["code"])
    assert exec_result["success"] is True
    assert "Found target 23" in exec_result["stdout"]

def test_learner_level_visual_adaptation():
    """Test 6: Learner level complexity adaptation (beginner vs advanced)"""
    beginner_decision = VisualRouter.decide_visual_strategy("Kinetic Energy", "Classical Mechanics", "beginner")
    advanced_decision = VisualRouter.decide_visual_strategy("Kinetic Energy", "Classical Mechanics", "advanced")

    assert beginner_decision.complexity == "simple"
    assert advanced_decision.complexity == "advanced"

    beginner_spec = VisualRouter.generate_visual_spec("Newton Force", "free_body_diagram", "beginner")
    advanced_spec = VisualRouter.generate_visual_spec("Newton Force", "free_body_diagram", "advanced")
    
    # Advanced uses formal LaTeX subscripts in equations
    assert "\\mu_k" in advanced_spec.payload["equations"][0] or "\\Sigma F" in advanced_spec.payload["equations"][0]

@pytest.mark.asyncio
async def test_teacher_agent_lesson_plan_visual_integration(db_session):
    """Test 7: TeacherAgent generates lesson plan with VisualDecisions attached"""
    plan = await TeacherAgentStateMachine.generate_lesson_plan(
        topic="Newton's Laws of Motion and Gravitation",
        material_id=None,
        profile=None,
        time_budget_minutes=20,
        language="en",
        db=db_session
    )
    assert isinstance(plan, LessonPlan)
    assert len(plan.segments) > 0
    for seg in plan.segments:
        assert isinstance(seg, LessonSegmentPlan)
        assert seg.visual_decision is not None
        assert isinstance(seg.visual_decision, VisualDecision)
        assert seg.visual_decision.subject in ["physics", "mathematics", "general"]
        assert seg.visual_type != ""

@pytest.mark.asyncio
async def test_teacher_agent_render_segment_with_observation_guidance(db_session):
    """Test 8: TeacherAgent render_segment produces visual spec, observation prompt, and checkpoint"""
    plan = await TeacherAgentStateMachine.generate_lesson_plan(
        topic="Photosynthesis and Cellular Respiration",
        material_id=None,
        profile=None,
        time_budget_minutes=10,
        language="en",
        db=db_session
    )
    rendered = await TeacherAgentStateMachine.render_segment(
        session_id=plan.session_id,
        segment_id=1,
        language="en",
        db=db_session
    )
    assert rendered.visual_decision is not None
    assert rendered.visual_spec is not None
    assert rendered.visual_spec.decision is not None
    assert rendered.checkpoint_question is not None
    assert rendered.spoken_script != ""
    assert len(rendered.captions) > 0
