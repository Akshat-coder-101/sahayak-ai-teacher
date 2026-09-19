import uuid
import random
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from ..database import (
    DBLessonSession, 
    DBQuiz, 
    DBQuizAttempt, 
    DBLearningReport, 
    DBLearnerProfile,
    DBCheckpointAttempt,
    DBMaterialChunk
)
from ..models.schemas import (
    Quiz, 
    QuizQuestion, 
    QuizGradeResponse, 
    QuestionGradeResult, 
    LearningReport,
    ConceptAssessmentWeight,
    AssessmentBlueprint,
    ConceptMasteryItem,
    GapMapItem,
    Citation
)
from .llm import LLMService, LLMUnavailable
from .learner_profile import LearnerProfileService
from .learning_path import LearningPathService

logger = logging.getLogger("sahayak.assessment")

GROUNDING_GUARDRAIL_PROMPT = (
    "Teach and test ONLY from the provided source material. Cite it. "
    "If the student asks about something not covered by these sources, "
    "say it is outside this document — do not invent it."
)

class AssessmentService:
    @classmethod
    def create_assessment_blueprint(cls, session_id: str, db: Session) -> AssessmentBlueprint:
        """
        Synthesizes an Assessment Blueprint based on concepts taught, learner level,
        importance, and student performance during segment checkpoints.
        """
        session = db.query(DBLessonSession).filter(DBLessonSession.id == session_id).first()
        topic = session.topic if session else "Foundational Principles"
        plan = session.plan_json if session and session.plan_json else {}
        segments = plan.get("segments", []) if isinstance(plan, dict) else []
        learner_level = str(plan.get("learner_level") or "beginner")

        # Fetch checkpoint performance history
        ck_attempts = db.query(DBCheckpointAttempt).filter(DBCheckpointAttempt.session_id == session_id).all()
        struggled_concepts = set()
        strong_concepts = set()
        for ck in ck_attempts:
            if ck.classification and ck.classification != "correct":
                # Find matching segment concept
                seg_match = next((s for s in segments if s.get("id") == ck.segment_id), None)
                if seg_match:
                    struggled_concepts.add(seg_match.get("concept", topic))
            elif ck.classification == "correct":
                seg_match = next((s for s in segments if s.get("id") == ck.segment_id), None)
                if seg_match:
                    strong_concepts.add(seg_match.get("concept", topic))

        concept_weights: List[ConceptAssessmentWeight] = []
        raw_concepts = [s.get("concept", topic) for s in segments if isinstance(s, dict)]
        if not raw_concepts:
            raw_concepts = session.taught_concepts if session and session.taught_concepts else [topic]

        # Calculate balanced weights with struggle boost
        total_items = max(1, len(raw_concepts))
        base_weight = round(1.0 / total_items, 2)

        cognitive_levels = ["recall", "understand", "apply", "analyze"] if learner_level == "advanced" else ["recall", "understand", "understand", "apply"]
        q_types = ["mcq", "conceptual", "short_answer", "practical_problem"]

        for idx, c_name in enumerate(raw_concepts):
            if c_name in struggled_concepts:
                perf = "struggled"
                weight = base_weight * 1.3
                rec_type = "conceptual" if idx % 2 == 0 else "short_answer"
                cog = "understand"
            elif c_name in strong_concepts:
                perf = "strong"
                weight = base_weight * 0.9
                rec_type = "practical_problem" if learner_level != "beginner" else "mcq"
                cog = "apply" if learner_level != "beginner" else "understand"
            else:
                perf = "moderate"
                weight = base_weight
                rec_type = q_types[idx % len(q_types)]
                cog = cognitive_levels[idx % len(cognitive_levels)]

            concept_weights.append(ConceptAssessmentWeight(
                concept_name=c_name,
                importance="high" if idx < 2 else "medium",
                lesson_performance=perf,
                weight=round(weight, 3),
                target_cognitive_level=cog,
                recommended_question_type=rec_type
            ))

        total_q = max(4, min(8, len(concept_weights)))
        return AssessmentBlueprint(
            session_id=session_id,
            topic=topic,
            concepts=concept_weights,
            total_questions=total_q,
            difficulty=learner_level,
            prerequisites=[c.concept_name for c in concept_weights[:2]]
        )

    @classmethod
    async def generate_quiz_for_session(
        cls, 
        session_id: str, 
        db: Session,
        custom_blueprint: Optional[AssessmentBlueprint] = None
    ) -> Quiz:
        """
        Generates a pedagogically grounded, multi-type assessment matching the Assessment Blueprint.
        """
        session = db.query(DBLessonSession).filter(DBLessonSession.id == session_id).first()
        topic = session.topic if session else "Foundational Principles"
        plan = session.plan_json if session and session.plan_json else {}
        segments = plan.get("segments", []) if isinstance(plan, dict) else []
        material_id = plan.get("material_id") or plan.get("document_id") if isinstance(plan, dict) else None

        blueprint = custom_blueprint or cls.create_assessment_blueprint(session_id, db)

        # Build segment mapping and chunk references
        segment_chunk_map: Dict[int, Dict[str, Any]] = {}
        for s in segments:
            if isinstance(s, dict):
                s_id = s.get("id", 1)
                s_cites = s.get("source_citations", []) or s.get("citations", [])
                c_id = None
                if s_cites and len(s_cites) > 0:
                    first_cite = s_cites[0]
                    c_id = first_cite.get("chunk_id") if isinstance(first_cite, dict) else getattr(first_cite, "chunk_id", None)
                segment_chunk_map[s_id] = {
                    "concept": s.get("concept", topic),
                    "chunk_id": c_id,
                    "summary": s.get("summary", "")
                }

        # Fetch sample chunks if material_id attached
        doc_chunks = []
        if material_id:
            doc_chunks = db.query(DBMaterialChunk).filter(DBMaterialChunk.material_id == material_id).limit(8).all()

        questions: List[QuizQuestion] = []

        # 1. Try real LLM Multi-Type Assessment Generation
        try:
            chunk_excerpts = ""
            if doc_chunks:
                chunk_excerpts = "\n\nDOCUMENT SOURCE EXCERPTS:\n" + "\n".join([
                    f"[Chunk {c.id}, Page {c.page or 1}, Section {c.chapter}]: {c.content[:200]}"
                    for c in doc_chunks
                ])

            blueprint_summary = "\n".join([
                f"- Concept: {c.concept_name} (Perf: {c.lesson_performance}, Cog: {c.target_cognitive_level}, Recommended Type: {c.recommended_question_type})"
                for c in blueprint.concepts
            ])

            system_prompt = (
                "You are an expert psychometric test designer and AI tutor for Sahayak AI Teacher. "
                f"{GROUNDING_GUARDRAIL_PROMPT} "
                "Design a balanced diagnostic assessment with mixed question types (MCQ, Conceptual 'Why/How', Short-Answer, and Practical Problems). "
                "For MCQs, strictly randomize correct option distribution across A, B, C, D. "
                "For open-ended questions, include explicit rubric criteria and expected reasoning steps."
            )

            user_prompt = f"""Generate a {blueprint.total_questions}-question diagnostic assessment based on this blueprint:
Topic: {topic}
Difficulty: {blueprint.difficulty}

ASSESSMENT BLUEPRINT SPECIFICATIONS:
{blueprint_summary}

{chunk_excerpts}

CRITICAL RULES:
1. Question types: Include MCQs, Conceptual questions ('Why/How'), and Practical calculation/application questions.
2. For MCQs: provide 4 distinct choices, clear correct answer, and randomize correct positions.
3. For Conceptual & Short-Answer: provide the question, expected correct concept, rubric criteria, and explanation.
4. For Practical Problems: provide question, expected numerical/symbolic result, and sample solution steps.

JSON schema:
{{
  "questions": [
    {{
      "concept": "Name of concept",
      "type": "mcq | conceptual | short_answer | practical_problem",
      "cognitive_level": "recall | understand | apply | analyze",
      "question": "Question text?",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."] (or null for non-mcq),
      "correct_answer": "B) ... or ideal conceptual answer text",
      "explanation": "Pedagogical explanation of why this answer is correct",
      "rubric_criteria": ["Key point 1", "Key point 2"],
      "sample_solution_steps": ["Step 1: ...", "Step 2: ..."],
      "chunk_id": "chunk_id_if_applicable"
    }}
  ]
}}
"""
            llm_quiz = await LLMService.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema_hint='{"questions": [{"concept": "...", "type": "mcq", "question": "...", "options": ["A) ...", ...], "correct_answer": "...", "explanation": "..."}]}',
                temperature=0.3
            )

            raw_qs = llm_quiz.get("questions", [])
            if raw_qs and len(raw_qs) > 0:
                for idx, q in enumerate(raw_qs):
                    q_type = q.get("type", "mcq")
                    opts = q.get("options")
                    if q_type == "mcq" and (not isinstance(opts, list) or len(opts) < 2):
                        opts = ["A) Standard principle", "B) Inverse condition", "C) Boundary limit", "D) Null baseline"]
                    
                    corr = str(q.get("correct_answer") or (opts[0] if opts else "Standard principle"))
                    q_concept = str(q.get("concept") or topic)
                    assigned_seg_id = idx + 1
                    assigned_chunk_id = q.get("chunk_id")
                    if not assigned_chunk_id and assigned_seg_id in segment_chunk_map:
                        assigned_chunk_id = segment_chunk_map[assigned_seg_id].get("chunk_id")
                    if not assigned_chunk_id and doc_chunks:
                        assigned_chunk_id = doc_chunks[min(idx, len(doc_chunks) - 1)].id

                    questions.append(QuizQuestion(
                        id=str(uuid.uuid4()),
                        type=q_type,
                        concept=q_concept,
                        question=str(q.get("question", f"Diagnostic question on {q_concept}")),
                        options=opts,
                        correct_answer=corr,
                        explanation=str(q.get("explanation", f"Verified principle regarding {q_concept}")),
                        cognitive_level=str(q.get("cognitive_level", "understand")),
                        rubric_criteria=q.get("rubric_criteria") or [f"Demonstrate accurate comprehension of {q_concept}"],
                        sample_solution_steps=q.get("sample_solution_steps") or [f"Apply governing formula of {q_concept}"],
                        chunk_id=assigned_chunk_id,
                        segment_id=assigned_seg_id
                    ))
                logger.info(f"[AssessmentService] Generated {len(questions)} grounded blueprint quiz questions using LLM.")
        except Exception as e:
            logger.warning(f"[AssessmentService] LLM quiz generation failed ({e}); using procedural blueprint generator.")

        # 2. Procedural Fallback if LLM offline
        if not questions:
            option_keys = ["A", "B", "C", "D"]
            for idx, cw in enumerate(blueprint.concepts):
                corr_idx = idx % 4
                seg_id = idx + 1
                assigned_chunk_id = segment_chunk_map.get(seg_id, {}).get("chunk_id")
                if not assigned_chunk_id and doc_chunks:
                    assigned_chunk_id = doc_chunks[min(idx, len(doc_chunks) - 1)].id

                c_name = cw.concept_name
                q_type = cw.recommended_question_type

                if q_type == "conceptual":
                    questions.append(QuizQuestion(
                        id=str(uuid.uuid4()),
                        type="conceptual",
                        concept=c_name,
                        question=f"Why does {c_name} govern system behavior under dynamic boundary conditions?",
                        options=None,
                        correct_answer=f"{c_name} ensures energy and state conservation by maintaining equilibrium between input potentials and resistive forces.",
                        explanation=f"According to foundational principles, {c_name} enforces mechanical and energetic constraints.",
                        cognitive_level="understand",
                        rubric_criteria=[
                            f"Identifies conservation or equilibrium role of {c_name}",
                            "Explains relationship between state variables"
                        ],
                        chunk_id=assigned_chunk_id,
                        segment_id=seg_id
                    ))
                elif q_type == "practical_problem":
                    questions.append(QuizQuestion(
                        id=str(uuid.uuid4()),
                        type="practical_problem",
                        concept=c_name,
                        question=f"If the primary driver for {c_name} is doubled while internal resistance remains constant, calculate the resulting rate of change.",
                        options=None,
                        correct_answer="The rate of change doubles proportionally (2x) following direct linear proportionality.",
                        explanation=f"Direct proportionality in {c_name} dictates that output scales linearly with applied driving potential.",
                        cognitive_level="apply",
                        sample_solution_steps=[
                            "Step 1: Write governing relation Y = k * X",
                            "Step 2: Substitute new input X' = 2X",
                            "Step 3: Evaluate Y' = 2 * (k * X) = 2Y"
                        ],
                        chunk_id=assigned_chunk_id,
                        segment_id=seg_id
                    ))
                elif q_type == "short_answer":
                    questions.append(QuizQuestion(
                        id=str(uuid.uuid4()),
                        type="short_answer",
                        concept=c_name,
                        question=f"In your own words, explain how {c_name} prevents system instability.",
                        options=None,
                        correct_answer=f"{c_name} provides damping and balancing feedback to prevent unbounded exponential divergence.",
                        explanation=f"{c_name} acts as a stabilizing constraint on state transitions.",
                        cognitive_level="understand",
                        rubric_criteria=[
                            "Mentions feedback, damping, or balance",
                            "Distinguishes stable from unstable behavior"
                        ],
                        chunk_id=assigned_chunk_id,
                        segment_id=seg_id
                    ))
                else: # MCQ
                    distractors = [
                        f"{c_name} operates in isolated static equilibrium with zero work exchange.",
                        f"{c_name} bypasses conservation and boundary constraints.",
                        f"{c_name} fluctuates randomly without causal determinants."
                    ]
                    correct_text = f"{c_name} maintains predictable dynamic conservation through verified state transitions."
                    
                    full_options = []
                    d_idx = 0
                    for opt_i in range(4):
                        prefix = f"{option_keys[opt_i]}) "
                        if opt_i == corr_idx:
                            full_options.append(prefix + correct_text)
                        else:
                            full_options.append(prefix + distractors[d_idx])
                            d_idx += 1

                    questions.append(QuizQuestion(
                        id=str(uuid.uuid4()),
                        type="mcq",
                        concept=c_name,
                        question=f"Which statement best characterizes the verified operational principle of {c_name}?",
                        options=full_options,
                        correct_answer=full_options[corr_idx],
                        explanation=f"As demonstrated in the source material, {c_name} relies on structured state conservation and predictable response.",
                        cognitive_level=cw.target_cognitive_level,
                        chunk_id=assigned_chunk_id,
                        segment_id=seg_id
                    ))

        # Store quiz in DB
        db_quiz = DBQuiz(
            id=str(uuid.uuid4()),
            session_id=session_id,
            topic=topic,
            questions_json=[q.model_dump() for q in questions]
        )
        db.add(db_quiz)
        db.commit()

        return Quiz(
            quiz_id=db_quiz.id,
            session_id=session_id,
            topic=topic,
            questions=questions,
            blueprint=blueprint
        )

    @classmethod
    async def grade_quiz_submission(
        cls, 
        session_id: str, 
        answers: Any, 
        db: Session
    ) -> QuizGradeResponse:
        """
        Performs semantic diagnostic grading across objective, conceptual, short-answer,
        and practical questions, distinguishing partial understanding and misconceptions.
        """
        normalized_answers: Dict[str, str] = {}
        if isinstance(answers, list):
            for item in answers:
                if isinstance(item, dict):
                    qid = str(item.get("question_id") or item.get("id") or "")
                    ans = str(item.get("selected_option") or item.get("answer") or item.get("student_answer") or "")
                    if qid:
                        normalized_answers[qid] = ans
        elif isinstance(answers, dict):
            normalized_answers = {str(k): str(v) for k, v in answers.items()}
        answers = normalized_answers

        quiz_record = db.query(DBQuiz).filter(DBQuiz.session_id == session_id).order_by(DBQuiz.created_at.desc()).first()
        if not quiz_record or not quiz_record.questions_json:
            quiz = await cls.generate_quiz_for_session(session_id, db)
            questions_data = [q.model_dump() for q in quiz.questions]
        else:
            questions_data = list(quiz_record.questions_json) if isinstance(quiz_record.questions_json, list) else []

        results: List[QuestionGradeResult] = []
        total_earned_score = 0.0

        for q in questions_data:
            q_id = q["id"]
            user_ans = answers.get(q_id, "").strip()
            correct_ans = q.get("correct_answer", "").strip()
            q_type = q.get("type", "mcq")
            concept = q.get("concept", "Concept")
            explanation = q.get("explanation", "")
            rubric = q.get("rubric_criteria", [])

            is_correct = False
            eval_status = "incorrect"
            partial_score = 0.0
            feedback = ""
            understood_pts: List[str] = []
            missing_pts: List[str] = []
            misconception: Optional[str] = None

            if not user_ans:
                eval_status = "incorrect"
                partial_score = 0.0
                feedback = f"No answer provided. Expected understanding: {correct_ans}."
                missing_pts = [f"Provide answer explaining {concept}"]
            elif q_type == "mcq":
                user_l = user_ans.lower()
                # Check for explicit misconception phrases in answer
                if any(w in user_l for w in ["block", "destroy", "disappear", "infinite", "random"]):
                    eval_status = "misconception"
                    partial_score = 0.0
                    is_correct = False
                    misconception = f"Flawed conceptual model regarding {concept}"
                    missing_pts = ["Applied non-physical or imprecise conceptual model"]
                    feedback = f"Contains a diagnosed misconception: {misconception}. Correct principle: {correct_ans}."
                elif user_ans == correct_ans:
                    is_correct = True
                    eval_status = "correct"
                    partial_score = 1.0
                    understood_pts = [f"Identified correct operational principle of {concept}"]
                    feedback = f"Correct! {explanation}"
                elif len(user_ans) > 0 and len(correct_ans) > 0 and user_ans[0].upper() == correct_ans[0].upper():
                    is_correct = True
                    eval_status = "correct"
                    partial_score = 1.0
                    understood_pts = [f"Selected correct choice ({user_ans[0].upper()})"]
                    feedback = f"Correct! {explanation}"
                elif len(user_ans) > 3 and user_ans.lower() in correct_ans.lower():
                    is_correct = True
                    eval_status = "correct"
                    partial_score = 1.0
                    understood_pts = [f"Matches correct answer keywords"]
                    feedback = f"Correct! {explanation}"
                else:
                    is_correct = False
                    eval_status = "incorrect"
                    partial_score = 0.0
                    missing_pts = [f"Misidentified core definition of {concept}"]
                    feedback = f"Incorrect. Correct answer was: {correct_ans}. {explanation}"
            else:
                # Semantic Diagnostic Evaluation for Open-Ended (Conceptual / Short Answer / Practical)
                try:
                    eval_prompt = f"""Evaluate this student response against the question and rubric:
Question: {q.get('question')}
Question Type: {q_type}
Expected Ideal Concept / Solution: {correct_ans}
Rubric Criteria: {rubric}
Student's Response: "{user_ans}"

Evaluate:
1. Is the answer fully correct (1.0), partially correct (0.5 - 0.75), a misconception (0.0), or incorrect (0.0)?
2. What did the student understand correctly?
3. What key reasoning or technical steps were missing?
4. Is there a specific conceptual misconception (e.g. treating resistance as 'blocking electricity' rather than Ohm's law ratio)?

JSON response:
{{
  "evaluation_status": "correct | partially_correct | incorrect | misconception",
  "partial_score": 1.0 | 0.75 | 0.5 | 0.25 | 0.0,
  "is_correct": true | false,
  "feedback": "Constructive pedagogical feedback explaining what was right and what needs refinement.",
  "understood_points": ["Understood point 1"],
  "missing_points": ["Missing reasoning step 1"],
  "misconception_identified": "Name of misconception or null"
}}
"""
                    res = await LLMService.generate_json(
                        system_prompt="You are an expert pedagogical grader. Provide detailed diagnostic evaluation of student conceptual responses.",
                        user_prompt=eval_prompt,
                        schema_hint='{"evaluation_status": "partially_correct", "partial_score": 0.5, "is_correct": false, "feedback": "...", "understood_points": [...], "missing_points": [...], "misconception_identified": null}',
                        temperature=0.2
                    )
                    eval_status = res.get("evaluation_status", "partially_correct")
                    partial_score = float(res.get("partial_score", 0.5 if eval_status == "partially_correct" else (1.0 if eval_status == "correct" else 0.0)))
                    is_correct = bool(res.get("is_correct", partial_score >= 0.8))
                    feedback = res.get("feedback", explanation)
                    understood_pts = [str(p) for p in res.get("understood_points", [])]
                    missing_pts = [str(m) for m in res.get("missing_points", [])]
                    misconception = res.get("misconception_identified")
                except Exception:
                    # Procedural semantic heuristic
                    user_l = user_ans.lower()
                    corr_l = correct_ans.lower()
                    
                    matched_words = [w for w in corr_l.split() if len(w) > 3 and w in user_l]
                    overlap_ratio = len(matched_words) / max(1, len([w for w in corr_l.split() if len(w) > 3]))

                    # Misconception keyword check
                    if any(w in user_l for w in ["block", "destroy", "disappear", "infinite", "random", "nothing"]):
                        eval_status = "misconception"
                        partial_score = 0.2
                        is_correct = False
                        misconception = f"Imprecise physical intuition regarding {concept}"
                        understood_pts = ["Recognized relationship between parameters"]
                        missing_pts = ["Applied non-physical or imprecise conceptual model"]
                        feedback = f"Partially intuitive, but contains a misconception: {misconception}. Correct principle: {correct_ans}."
                    elif overlap_ratio >= 0.5:
                        eval_status = "correct"
                        partial_score = 1.0
                        is_correct = True
                        understood_pts = [f"Accurately described core mechanism of {concept}"]
                        feedback = f"Great explanation! {explanation}"
                    elif overlap_ratio >= 0.2:
                        eval_status = "partially_correct"
                        partial_score = 0.5
                        is_correct = False
                        understood_pts = [f"Identified basic context of {concept}"]
                        missing_pts = [f"Missing formal quantitative or relational reasoning"]
                        feedback = f"Partially correct. You identified key aspects, but missed formal relationship: {correct_ans}."
                    else:
                        eval_status = "incorrect"
                        partial_score = 0.0
                        is_correct = False
                        missing_pts = [f"Needs review of fundamental {concept} definition"]
                        feedback = f"Incorrect. Correct explanation: {correct_ans}."

            total_earned_score += partial_score

            results.append(QuestionGradeResult(
                question_id=q_id,
                concept=concept,
                is_correct=is_correct,
                evaluation_status=eval_status,
                partial_score=partial_score,
                student_answer=user_ans if user_ans else "No answer provided",
                correct_answer=correct_ans,
                feedback=feedback,
                understood_points=understood_pts,
                missing_points=missing_pts,
                misconception_identified=misconception
            ))

        total_questions = len(questions_data)
        score_pct = round((total_earned_score / total_questions * 100), 1) if total_questions > 0 else 0.0

        # Save Attempt
        attempt = DBQuizAttempt(
            id=str(uuid.uuid4()),
            session_id=session_id,
            score_percentage=score_pct,
            details_json=[r.model_dump() for r in results]
        )
        db.add(attempt)
        db.commit()

        return QuizGradeResponse(
            session_id=session_id,
            total_score=round(total_earned_score, 1),
            max_score=total_questions,
            score_percentage=score_pct,
            results=results
        )

    @classmethod
    async def build_learning_report(cls, session_id: str, db: Session) -> LearningReport:
        """
        Builds an evidence-backed, concept-level mastery report with progression gating
        and actionable revision tasks.
        """
        session = db.query(DBLessonSession).filter(DBLessonSession.id == session_id).first()
        topic = session.topic if session else "General Topic"
        user_id = session.user_id if session and session.user_id else "default-user"

        latest_attempt = db.query(DBQuizAttempt).filter(DBQuizAttempt.session_id == session_id).order_by(DBQuizAttempt.created_at.desc()).first()
        ck_attempts = db.query(DBCheckpointAttempt).filter(DBCheckpointAttempt.session_id == session_id).all()
        
        plan = session.plan_json if session and session.plan_json else {}
        segments = plan.get("segments", []) if isinstance(plan, dict) else []
        concepts = [s.get("concept", topic) for s in segments if isinstance(s, dict)] or [topic]

        # Extract question-level grades
        grade_results: List[Dict[str, Any]] = []
        if latest_attempt and isinstance(latest_attempt.details_json, list):
            grade_results = [r for r in latest_attempt.details_json if isinstance(r, dict)]

        # Group assessment results by concept
        concept_stats: Dict[str, Dict[str, Any]] = {
            c: {
                "total_q": 0,
                "earned_score": 0.0,
                "misconceptions": [],
                "evidence": []
            } for c in concepts
        }

        for gr in grade_results:
            c_name = gr.get("concept", topic)
            # Find closest matching concept
            matched_c = next((c for c in concepts if c.lower() in c_name.lower() or c_name.lower() in c.lower()), c_name)
            if matched_c not in concept_stats:
                concept_stats[matched_c] = {"total_q": 0, "earned_score": 0.0, "misconceptions": [], "evidence": []}
            
            p_score = float(gr.get("partial_score", 1.0 if gr.get("is_correct") else 0.0))
            concept_stats[matched_c]["total_q"] += 1
            concept_stats[matched_c]["earned_score"] += p_score
            
            status = gr.get("evaluation_status", "correct" if gr.get("is_correct") else "incorrect")
            concept_stats[matched_c]["evidence"].append(f"Assessment Q: {status} (score: {p_score})")

            if gr.get("misconception_identified"):
                concept_stats[matched_c]["misconceptions"].append(str(gr.get("misconception_identified")))

        # Merge Checkpoint attempts evidence
        for ck in ck_attempts:
            matching_seg = next((s for s in segments if isinstance(s, dict) and s.get("id") == ck.segment_id), None)
            c_name = matching_seg.get("concept", topic) if matching_seg else topic
            if c_name not in concept_stats:
                concept_stats[c_name] = {"total_q": 0, "earned_score": 0.0, "misconceptions": [], "evidence": []}
            
            if ck.classification != "correct":
                concept_stats[c_name]["misconceptions"].append(ck.classification or "Checkpoint misconception")
                concept_stats[c_name]["evidence"].append(f"Checkpoint S{ck.segment_id}: {ck.classification}")
            else:
                concept_stats[c_name]["evidence"].append(f"Checkpoint S{ck.segment_id}: correct")

        # Determine Concept-Level Mastery Items
        concept_masteries: List[ConceptMasteryItem] = []
        understood_list: List[str] = []
        weak_list: List[str] = []
        all_misconceptions: List[str] = []

        for c_name, st in concept_stats.items():
            t_q = st["total_q"]
            e_s = st["earned_score"]
            c_pct = round((e_s / t_q * 100), 1) if t_q > 0 else (100.0 if not st["misconceptions"] else 50.0)
            
            # Classification
            if st["misconceptions"]:
                mastery_state = "misunderstood"
                rev_needed = True
            elif c_pct >= 85:
                mastery_state = "mastered"
                rev_needed = False
            elif c_pct >= 70:
                mastery_state = "strong"
                rev_needed = False
            elif c_pct >= 50:
                mastery_state = "developing"
                rev_needed = True
            else:
                mastery_state = "weak"
                rev_needed = True

            if rev_needed:
                weak_list.append(c_name)
            else:
                understood_list.append(c_name)

            for m in st["misconceptions"]:
                if m not in all_misconceptions:
                    all_misconceptions.append(m)

            concept_masteries.append(ConceptMasteryItem(
                concept=c_name,
                mastery=mastery_state,
                score_percent=c_pct,
                confidence=0.90 if t_q >= 1 else 0.75,
                evidence=st["evidence"] or [f"Assessed during lesson on {c_name}"],
                misconceptions=st["misconceptions"],
                revision_needed=rev_needed
            ))

        # Overall Score
        has_attempts = latest_attempt is not None or len(ck_attempts) > 0
        if latest_attempt and latest_attempt.score_percentage is not None:
            score_pct = latest_attempt.score_percentage
        elif len(ck_attempts) > 0:
            correct_cks = sum(1 for c in ck_attempts if c.classification == "correct")
            score_pct = round((correct_cks / len(ck_attempts)) * 100, 1)
        else:
            score_pct = 0.0

        # Progression Gate Determination
        critical_deficits = [cm.concept for cm in concept_masteries if cm.mastery in ["weak", "misunderstood"]]
        is_ready_for_next = len(critical_deficits) == 0 and score_pct >= 70.0

        if is_ready_for_next:
            readiness_reason = f"Demonstrated high conceptual mastery ({score_pct}%) with zero unresolved misconceptions. Ready for advanced topics."
            suggested_next = [
                f"Advanced Applications of {topic}",
                f"Integrated Systems & Edge Cases in {topic}"
            ]
        else:
            readiness_reason = f"Targeted revision required for {', '.join(critical_deficits) if critical_deficits else 'growth areas'} before advancing."
            suggested_next = [
                f"Targeted Revision: {critical_deficits[0] if critical_deficits else topic}",
                f"Foundational Mastery Review for {topic}"
            ]

        # Actionable Revision Tasks
        revision_tasks: List[Dict[str, Any]] = []
        gap_map: List[GapMapItem] = []

        for cm in concept_masteries:
            if cm.revision_needed:
                matched_seg = next((s for s in segments if isinstance(s, dict) and s.get("concept") == cm.concept), None)
                seg_id = matched_seg.get("id", 1) if matched_seg else 1
                
                cite_obj = None
                if matched_seg:
                    s_cites = matched_seg.get("source_citations", []) or matched_seg.get("citations", [])
                    if s_cites and len(s_cites) > 0:
                        fc = s_cites[0]
                        cite_obj = Citation(
                            chunk_id=fc.get("chunk_id") if isinstance(fc, dict) else getattr(fc, "chunk_id", None),
                            chapter=fc.get("chapter", "Document Section") if isinstance(fc, dict) else getattr(fc, "chapter", "Document Section"),
                            page=fc.get("page", 1) if isinstance(fc, dict) else getattr(fc, "page", 1),
                            quote=fc.get("quote", "") if isinstance(fc, dict) else getattr(fc, "quote", ""),
                            snippet=fc.get("snippet", "") if isinstance(fc, dict) else getattr(fc, "snippet", "")
                        )
                if not cite_obj:
                    cite_obj = Citation(chapter=topic, page=1, quote=f"Review verified source material for {cm.concept}.", snippet=f"Review {cm.concept}.")

                task_desc = f"Review Segment {seg_id} ('{cm.concept}') on Page {cite_obj.page or 1} and solve 2 practice derivations."
                revision_tasks.append({
                    "concept": cm.concept,
                    "segment_id": seg_id,
                    "action": task_desc,
                    "page": cite_obj.page or 1,
                    "status": "pending"
                })

                gap_map.append(GapMapItem(
                    concept=cm.concept,
                    segment_id=seg_id,
                    citation=cite_obj,
                    recommendation=task_desc
                ))

        recommended_revision = [t["action"] for t in revision_tasks] or [
            f"Review the core governing formulas for {concepts[0] if concepts else topic}.",
            "Practice additional boundary condition questions."
        ]

        report = LearningReport(
            session_id=session_id,
            user_id=user_id,
            topic=topic,
            score_percent=score_pct,
            time_spent_minutes=session.time_budget if session else 20,
            concepts_understood=understood_list or concepts,
            weak_areas=weak_list,
            misconceptions_encountered=all_misconceptions,
            recommended_revision=recommended_revision,
            suggested_next_topics=suggested_next,
            concept_masteries=concept_masteries,
            is_ready_for_next_topic=is_ready_for_next,
            readiness_reason=readiness_reason,
            actionable_revision_tasks=revision_tasks,
            gap_map=gap_map
        )

        # Persist report
        existing_rep = db.query(DBLearningReport).filter(DBLearningReport.session_id == session_id).first()
        if not existing_rep:
            db_rep = DBLearningReport(
                id=str(uuid.uuid4()),
                session_id=session_id,
                user_id=user_id,
                topic=topic,
                score_percent=score_pct,
                time_spent=session.time_budget if session else 20,
                report_json=report.model_dump(mode="json")
            )
            db.add(db_rep)
            db.commit()

        # Update Learner Profile History & Mastery via LearnerProfileService
        try:
            LearnerProfileService.update_profile_from_assessment(user_id=user_id, report=report, db=db)
            LearningPathService.update_path_from_assessment(user_id=user_id, topic_id=topic, report=report, db=db)
        except Exception as e:
            logger.warning(f"[AssessmentService] Failed to update profile or learning path: {e}")

        return report
