import logging
import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..database import (
    DBLearnerProfile,
    DBLearningPath,
    DBLessonSession,
    DBQuizAttempt,
    DBLearningReport,
    DBMaterialChunk
)
from ..models.schemas import (
    TeacherPersonalityConfig,
    FlashcardItem,
    FlashcardSet,
    StudyNotes,
    HomeworkTask,
    HomeworkAssignment,
    ExamPrepMilestone,
    ExamPrepPlan,
    StudyPlanTask,
    StudyPlanDay,
    StudyPlan,
    ScoreHistoryPoint,
    LearningAnalyticsData,
    LessonPlan,
    LessonSegmentPlan
)
from ..services.learner_profile import LearnerProfileService
from ..services.learning_path import LearningPathService
from ..services.llm import LLMService

logger = logging.getLogger("sahayak.study_tools")

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

TEACHER_PERSONALITIES: Dict[str, TeacherPersonalityConfig] = {
    "socratic": TeacherPersonalityConfig(
        personality="socratic",
        title="Socratic Guide",
        description="Asks guiding questions frequently, prompts critical thinking, and encourages deep conceptual reasoning.",
        tone="thoughtful and inquisitive",
        question_frequency="high",
        explanation_style="guided",
        feedback_style="constructive"
    ),
    "friendly": TeacherPersonalityConfig(
        personality="friendly",
        title="Friendly Mentor",
        description="Warm, conversational, and highly encouraging. Uses everyday relatable analogies, perfect for beginners.",
        tone="warm, encouraging, and accessible",
        question_frequency="medium",
        explanation_style="conversational",
        feedback_style="encouraging"
    ),
    "strict_coach": TeacherPersonalityConfig(
        personality="strict_coach",
        title="Strict Exam Coach",
        description="Focused on precision, test patterns, time management, and rigorous correctness with no fluff.",
        tone="direct, disciplined, and razor-sharp",
        question_frequency="focused",
        explanation_style="direct",
        feedback_style="strict"
    ),
    "visual": TeacherPersonalityConfig(
        personality="visual",
        title="Visual Architect",
        description="Explains ideas through structured mental models, diagrams, step-by-step visual metaphors, and spatial layouts.",
        tone="clear, structured, and illustrative",
        question_frequency="medium",
        explanation_style="visual",
        feedback_style="visual_scaffolded"
    )
}

class StudyToolsService:

    # -----------------------------------------------------------------------
    # 1. Multiple Teacher Personalities
    # -----------------------------------------------------------------------
    @classmethod
    def get_personalities(cls) -> List[TeacherPersonalityConfig]:
        return list(TEACHER_PERSONALITIES.values())

    @classmethod
    def get_personality_config(cls, personality: str) -> TeacherPersonalityConfig:
        key = personality.lower().replace("-", "_").strip()
        return TEACHER_PERSONALITIES.get(key, TEACHER_PERSONALITIES["socratic"])

    @classmethod
    def get_personality_instruction_prompt(cls, personality: str) -> str:
        cfg = cls.get_personality_config(personality)
        if cfg.personality == "socratic":
            return (
                "TEACHER PERSONALITY: SOCRATIC GUIDE.\n"
                "- Do NOT simply spoon-feed answers. Prompt the student with reflective leading questions.\n"
                "- Encourage the student to reason through intermediate steps.\n"
                "- In explanations, highlight 'Why does this happen?' before stating 'What happens'."
            )
        elif cfg.personality == "friendly":
            return (
                "TEACHER PERSONALITY: FRIENDLY MENTOR.\n"
                "- Use a warm, enthusiastic, and highly supportive tone.\n"
                "- Use simple everyday analogies (e.g., water pipes for electricity, recipes for algorithms).\n"
                "- Celebrate every milestone and frame mistakes as exciting learning opportunities."
            )
        elif cfg.personality == "strict_coach":
            return (
                "TEACHER PERSONALITY: STRICT EXAM COACH.\n"
                "- Be concise, direct, and focused strictly on high-yield exam concepts and formulas.\n"
                "- Highlight common exam traps, strict definition wording, and numerical precision.\n"
                "- Provide clear, unfiltered feedback on mistakes immediately."
            )
        elif cfg.personality == "visual":
            return (
                "TEACHER PERSONALITY: VISUAL ARCHITECT.\n"
                "- Focus on visual structures, step-by-step workflows, and concrete spatial metaphors.\n"
                "- Explicitly reference diagrams, flowcharts, and component interactions.\n"
                "- Break down multi-step concepts into clear numbered visual checkpoints."
            )
        return ""

    # -----------------------------------------------------------------------
    # 2. Revision Mode
    # -----------------------------------------------------------------------
    @classmethod
    def generate_revision_lesson_plan(
        cls,
        user_id: str,
        topic: Optional[str],
        db: Session
    ) -> Dict[str, Any]:
        """
        Builds a high-impact revision lesson plan targeting weak concepts and misconceptions.
        """
        profile = LearnerProfileService.get_full_learner_profile(user_id, db)
        target_topic = topic or profile.current_topic or (profile.topics_studied[0] if profile.topics_studied else "General Subject")
        
        weak_concepts = profile.weak_concepts
        misconceptions = profile.misunderstood_concepts
        
        # Priority concepts needing revision
        revision_targets = list(dict.fromkeys(misconceptions + weak_concepts))
        if not revision_targets:
            revision_targets = [f"{target_topic} Core Fundamentals", f"{target_topic} Problem Solving"]

        # Build 2 targeted revision segments
        segments = []
        seg1_concepts = revision_targets[:2]
        seg2_concepts = revision_targets[2:4] if len(revision_targets) > 2 else revision_targets[:2]

        segments.append({
            "segment_id": 1,
            "title": f"Targeted Review: {', '.join(seg1_concepts)}",
            "key_concept": seg1_concepts[0],
            "teaching_goal": f"Clear fundamental misconceptions and reinforce core rules for {', '.join(seg1_concepts)}.",
            "checkpoint_question": {
                "id": str(uuid.uuid4()),
                "type": "mcq",
                "question": f"When applying {seg1_concepts[0]}, what is the key underlying rule to keep in mind?",
                "options": [
                    f"Always verify base parameters of {seg1_concepts[0]}",
                    "Assume values are constant in all conditions",
                    "Ignore intermediate boundary cases",
                    "Directly apply without checking prerequisites"
                ],
                "correct_answer": f"Always verify base parameters of {seg1_concepts[0]}",
                "hints": [f"Think about how {seg1_concepts[0]} interacts with related principles."],
                "concept_tested": seg1_concepts[0]
            }
        })

        if len(revision_targets) > 1:
            segments.append({
                "segment_id": 2,
                "title": f"Guided Practice & Mastery Check: {', '.join(seg2_concepts)}",
                "key_concept": seg2_concepts[-1],
                "teaching_goal": f"Apply {seg2_concepts[-1]} in a practical problem scenario.",
                "checkpoint_question": {
                    "id": str(uuid.uuid4()),
                    "type": "problem_solving",
                    "question": f"How do you resolve a typical problem involving {seg2_concepts[-1]} step by step?",
                    "options": [],
                    "correct_answer": f"Identify given values, formulate relationship for {seg2_concepts[-1]}, and solve systematically.",
                    "hints": ["Review previous mistake patterns."],
                    "concept_tested": seg2_concepts[-1]
                }
            })

        return {
            "mode": "revision",
            "topic": target_topic,
            "user_id": user_id,
            "weak_concepts_targeted": revision_targets,
            "segments": segments,
            "total_segments": len(segments),
            "estimated_minutes": 10
        }

    # -----------------------------------------------------------------------
    # 3. Flashcard Generation
    # -----------------------------------------------------------------------
    @classmethod
    async def generate_flashcards(
        cls,
        user_id: str,
        topic: str,
        session_id: Optional[str],
        db: Session
    ) -> FlashcardSet:
        """
        Generates structured flashcards grounded in study material, prioritizing weak concepts.
        """
        profile = LearnerProfileService.get_full_learner_profile(user_id, db)
        weak_set = set(profile.weak_concepts + profile.misunderstood_concepts)
        
        # Retrieve chunks from material or session
        chunks: List[str] = []
        if session_id:
            s = db.query(DBLessonSession).filter(DBLessonSession.id == session_id).first()
            if s and s.plan_json:
                for seg in s.plan_json.get("segments", []):
                    chunks.append(f"{seg.get('title', '')}: {seg.get('teaching_goal', '')}")
        
        if not chunks:
            # Look up material chunks for topic
            db_chunks = db.query(DBMaterialChunk).limit(5).all()
            for ch in db_chunks:
                if ch.content:
                    chunks.append(ch.content[:300])

        prompt = f"""
Generate 5 high-quality, structured educational flashcards for topic: '{topic}'.
Learner weak concepts to prioritize: {list(weak_set) if weak_set else 'General concepts'}
Reference context:
{' '.join(chunks[:3]) if chunks else topic}

Return ONLY a valid JSON object matching this schema:
{{
  "cards": [
    {{
      "front": "Question, formula, or concept prompt",
      "back": "Clear, concise answer or explanation",
      "concept": "Name of concept",
      "difficulty": "easy" | "medium" | "hard",
      "card_type": "definition" | "formula" | "concept" | "qa" | "misconception",
      "misconception_addressed": "Optional misconception note or null"
    }}
  ]
}}
"""
        cards_data: List[Dict[str, Any]] = []
        try:
            parsed = await LLMService.generate_json(
                system_prompt="You are an expert educational AI creating high-yield flashcards.",
                user_prompt=prompt,
                schema_hint={"cards": [{"front": "str", "back": "str", "concept": "str", "difficulty": "str", "card_type": "str", "misconception_addressed": "str"}]}
            )
            cards_data = parsed.get("cards", []) if isinstance(parsed, dict) else []
        except Exception as e:
            logger.warning(f"Flashcard LLM fallback triggered: {e}")

        if not cards_data:
            # Deterministic fallback cards grounded in topic & weak areas
            focus_concept = list(weak_set)[0] if weak_set else topic
            cards_data = [
                {
                    "front": f"What is the fundamental principle of {focus_concept}?",
                    "back": f"{focus_concept} defines the core relationship and operational behavior in {topic}.",
                    "concept": focus_concept,
                    "difficulty": "easy",
                    "card_type": "definition",
                    "misconception_addressed": None
                },
                {
                    "front": f"What key formula or rule governs {topic}?",
                    "back": f"The governing principle relates primary variables directly to determine system output.",
                    "concept": topic,
                    "difficulty": "medium",
                    "card_type": "formula",
                    "misconception_addressed": "Do not mix units or omit boundary constraints."
                },
                {
                    "front": f"Common Misconception in {focus_concept}",
                    "back": f"Remember that {focus_concept} changes dynamically based on input variables rather than staying static.",
                    "concept": focus_concept,
                    "difficulty": "hard",
                    "card_type": "misconception",
                    "misconception_addressed": f"Confusing static assumptions with dynamic behavior in {focus_concept}"
                }
            ]

        flashcards = [
            FlashcardItem(
                id=str(uuid.uuid4()),
                front=c.get("front", ""),
                back=c.get("back", ""),
                concept=c.get("concept", topic),
                difficulty=c.get("difficulty", "medium"),
                card_type=c.get("card_type", "concept"),
                misconception_addressed=c.get("misconception_addressed")
            )
            for c in cards_data
        ]

        return FlashcardSet(
            id=str(uuid.uuid4()),
            user_id=user_id,
            topic=topic,
            cards=flashcards,
            mastery_focus=list(weak_set)
        )

    @classmethod
    def record_flashcard_review(
        cls,
        user_id: str,
        card_id: str,
        concept: str,
        result: str, # correct | incorrect | needs_review
        db: Session
    ) -> Dict[str, Any]:
        """
        Updates learner profile concept mastery when a flashcard is reviewed.
        """
        p = LearnerProfileService.get_or_create_profile(user_id, db)
        mastery_map = dict(p.mastery_json) if isinstance(p.mastery_json, dict) else {}
        
        current_data = mastery_map.get(concept, {"mastery": "developing", "attempts": 0, "correct_count": 0})
        attempts = current_data.get("attempts", 0) + 1
        correct_count = current_data.get("correct_count", 0) + (1 if result == "correct" else 0)
        
        ratio = correct_count / max(1, attempts)
        if (ratio >= 0.65 and attempts >= 2) or (correct_count >= 2 and result == "correct"):
            new_state = "mastered"
        elif result == "incorrect":
            new_state = "weak"
        else:
            new_state = "developing"
            
        mastery_map[concept] = {
            "mastery": new_state,
            "attempts": attempts,
            "correct_count": correct_count,
            "last_reviewed": get_utc_now().isoformat()
        }
        p.mastery_json = mastery_map
        db.commit()

        return {
            "user_id": user_id,
            "card_id": card_id,
            "concept": concept,
            "new_mastery_state": new_state,
            "attempts": attempts
        }

    # -----------------------------------------------------------------------
    # 4. Automatic Notes Generation
    # -----------------------------------------------------------------------
    @classmethod
    async def generate_notes(
        cls,
        user_id: str,
        topic: str,
        session_id: Optional[str],
        db: Session
    ) -> StudyNotes:
        """
        Creates concise, revision-optimized structured notes from lesson context.
        """
        taught_concepts: List[str] = []
        if session_id:
            s = db.query(DBLessonSession).filter(DBLessonSession.id == session_id).first()
            if s and s.taught_concepts:
                taught_concepts = list(s.taught_concepts)

        prompt = f"""
Generate structured revision study notes for topic: '{topic}'.
Concepts covered: {taught_concepts if taught_concepts else [topic]}

Return ONLY a valid JSON object matching this schema:
{{
  "key_ideas": ["Key point 1", "Key point 2"],
  "definitions": [{{"term": "Term", "definition": "Clear definition"}}],
  "formulas_and_rules": [{{"name": "Rule/Formula Name", "expression": "Expression", "note": "When to apply"}}],
  "concrete_examples": [{{"title": "Example 1", "explanation": "Step-by-step resolution"}}],
  "common_mistakes": [{{"mistake": "Common trap", "how_to_avoid": "Clear correction guideline"}}],
  "summary_markdown": "# Summary\\nDetailed revision markdown summary."
}}
"""
        try:
            parsed = await LLMService.generate_json(
                system_prompt="You are an expert educational tutor creating structured revision study notes.",
                user_prompt=prompt,
                schema_hint={"key_ideas": [], "definitions": [], "formulas_and_rules": [], "concrete_examples": [], "common_mistakes": [], "summary_markdown": "str"}
            )
            return StudyNotes(
                id=str(uuid.uuid4()),
                user_id=user_id,
                topic=topic,
                key_ideas=parsed.get("key_ideas", [f"{topic} core fundamentals"]),
                definitions=parsed.get("definitions", [{"term": topic, "definition": f"Core subject area of {topic}"}]),
                formulas_and_rules=parsed.get("formulas_and_rules", []),
                concrete_examples=parsed.get("concrete_examples", []),
                common_mistakes=parsed.get("common_mistakes", []),
                summary_markdown=parsed.get("summary_markdown", f"# {topic}\\n\\nComprehensive revision notes for {topic}.")
            )
        except Exception as e:
            logger.warning(f"Automatic Notes generation fallback: {e}")
            return StudyNotes(
                id=str(uuid.uuid4()),
                user_id=user_id,
                topic=topic,
                key_ideas=[
                    f"Understanding the core governing mechanism of {topic}.",
                    "Applying fundamental principles systematically to solve problems."
                ],
                definitions=[
                    {"term": topic, "definition": f"The study and application of principles governing {topic}."}
                ],
                formulas_and_rules=[
                    {"name": f"{topic} Core Formula", "expression": "Output = Function(Inputs)", "note": "Ensure consistent units."}
                ],
                concrete_examples=[
                    {"title": f"Basic {topic} Problem", "explanation": "1. Identify given values. 2. Substitute into equation. 3. Verify units."}
                ],
                common_mistakes=[
                    {"mistake": "Overlooking edge cases or unit conversions", "how_to_avoid": "Double check standard SI units before calculating."}
                ],
                summary_markdown=f"# Revision Notes: {topic}\n\n## Overview\n{topic} requires solid conceptual clarity and systematic problem-solving.\n\n## Quick Checklist\n- [ ] Master core definitions\n- [ ] Review formula applications\n- [ ] Practice typical problem setups"
            )

    # -----------------------------------------------------------------------
    # 5. Personalized Homework
    # -----------------------------------------------------------------------
    @classmethod
    def generate_personalized_homework(
        cls,
        user_id: str,
        topic: str,
        session_id: Optional[str],
        db: Session
    ) -> HomeworkAssignment:
        """
        Generates tiered homework adapted to the student's mastery:
        - Strong (>80% / mastered): Challenge & Design problems
        - Developing (60-80%): Standard Application problems
        - Struggling (<60% / weak): Guided Remediation with step hints
        """
        profile = LearnerProfileService.get_full_learner_profile(user_id, db)
        
        # Check topic mastery or average score
        is_strong = topic in profile.strong_concepts or any(h.get("score", 0) >= 80 for h in profile.scores_history if h.get("topic") == topic)
        is_weak = topic in profile.weak_concepts or topic in profile.misunderstood_concepts or any(h.get("score", 0) < 65 for h in profile.scores_history if h.get("topic") == topic)

        if is_strong and not is_weak:
            tier = "advanced"
            rationale = f"Student demonstrated strong mastery in {topic}. Providing challenge & synthesis exercises."
            tasks = [
                HomeworkTask(
                    id=str(uuid.uuid4()),
                    task_type="challenge",
                    title=f"Advanced Application of {topic}",
                    instruction=f"Design an end-to-end system utilizing {topic} that optimizes performance under constrained resources.",
                    target_concept=topic,
                    difficulty_tier="challenge",
                    expected_output_hint="Include structural architecture and boundary edge-case analysis."
                ),
                HomeworkTask(
                    id=str(uuid.uuid4()),
                    task_type="design",
                    title=f"Critical Analysis & Optimization",
                    instruction=f"Explain what theoretical failure modes occur when parameters in {topic} scale 10x, and how you would mitigate them.",
                    target_concept=topic,
                    difficulty_tier="challenge"
                )
            ]
        elif is_weak:
            tier = "remedial"
            rationale = f"Student encountered difficulties in {topic}. Providing step-by-step guided practice."
            tasks = [
                HomeworkTask(
                    id=str(uuid.uuid4()),
                    task_type="practice",
                    title=f"Step-by-Step Guided {topic} Problem",
                    instruction=f"Solve a basic foundational problem for {topic} following the guided steps below.",
                    target_concept=topic,
                    difficulty_tier="foundational",
                    guided_steps=[
                        "Step 1: Write down all given variables and identify the target quantity.",
                        f"Step 2: State the primary definition or formula for {topic}.",
                        "Step 3: Solve step-by-step and write out your final answer with units."
                    ],
                    expected_output_hint="Focus on clarity and showing every arithmetic step."
                ),
                HomeworkTask(
                    id=str(uuid.uuid4()),
                    task_type="conceptual_explanation",
                    title=f"Misconception Clarification",
                    instruction=f"In your own words, explain why the common misconception in {topic} is incorrect and give a simple counterexample.",
                    target_concept=topic,
                    difficulty_tier="foundational"
                )
            ]
        else:
            tier = "standard"
            rationale = f"Student has developing proficiency in {topic}. Providing standard problem-solving practice."
            tasks = [
                HomeworkTask(
                    id=str(uuid.uuid4()),
                    task_type="practice",
                    title=f"Standard Problem Set: {topic}",
                    instruction=f"Solve two standard scenario problems involving {topic}.",
                    target_concept=topic,
                    difficulty_tier="standard"
                ),
                HomeworkTask(
                    id=str(uuid.uuid4()),
                    task_type="practice",
                    title=f"Application Analysis",
                    instruction=f"Explain how changing one key variable influences the overall result in {topic}.",
                    target_concept=topic,
                    difficulty_tier="standard"
                )
            ]

        return HomeworkAssignment(
            id=str(uuid.uuid4()),
            user_id=user_id,
            topic=topic,
            tier=tier,
            rationale=rationale,
            tasks=tasks,
            suggested_completion_minutes=20 if tier == "remedial" else (30 if tier == "advanced" else 25)
        )

    # -----------------------------------------------------------------------
    # 6. Exam Preparation Mode
    # -----------------------------------------------------------------------
    @classmethod
    def generate_exam_prep(
        cls,
        user_id: str,
        subject: str,
        days_until_exam: int,
        target_score_percent: float,
        daily_study_hours: float,
        db: Session
    ) -> ExamPrepPlan:
        """
        Builds a comprehensive exam roadmap prioritizing high-weight topics,
        weak concepts, and targeted mock test milestones.
        """
        profile = LearnerProfileService.get_full_learner_profile(user_id, db)
        
        weak_areas = profile.weak_concepts + profile.misunderstood_concepts
        strong_areas = profile.strong_concepts
        
        # High weight topics list
        high_weight = [subject, f"{subject} Core Applications", f"{subject} Advanced Problem Solving"]
        if weak_areas:
            high_weight = list(dict.fromkeys(weak_areas + high_weight))

        # Split days into 4 logical phases
        d_p1 = max(1, int(days_until_exam * 0.3))
        d_p2 = max(1, int(days_until_exam * 0.3))
        d_p3 = max(1, int(days_until_exam * 0.25))
        d_p4 = max(1, days_until_exam - d_p1 - d_p2 - d_p3)

        milestones = [
            ExamPrepMilestone(
                phase="Foundation & High-Yield Diagnostics",
                day_range=f"Days 1 - {d_p1}",
                focus_topics=high_weight[:2],
                weak_areas_addressed=weak_areas[:2] if weak_areas else [],
                recommended_activities=[
                    "Diagnostic quiz to establish baseline",
                    "Targeted review notes for high-yield formulas",
                    "Daily 20-min flashcard drill"
                ],
                mock_test_scheduled=False
            ),
            ExamPrepMilestone(
                phase="Intensive Weak Concept Remediation",
                day_range=f"Days {d_p1 + 1} - {d_p1 + d_p2}",
                focus_topics=weak_areas if weak_areas else high_weight,
                weak_areas_addressed=weak_areas,
                recommended_activities=[
                    "Revision mode sessions on misunderstood concepts",
                    "Tiered practice homework assignments",
                    "Error log review of previous mistakes"
                ],
                mock_test_scheduled=False
            ),
            ExamPrepMilestone(
                phase="Timed Drills & Speed Practice",
                day_range=f"Days {d_p1 + d_p2 + 1} - {d_p1 + d_p2 + d_p3}",
                focus_topics=high_weight,
                weak_areas_addressed=weak_areas,
                recommended_activities=[
                    "Timed section quizzes under exam conditions",
                    "High-speed formula recall practice"
                ],
                mock_test_scheduled=True
            ),
            ExamPrepMilestone(
                phase="Full Mock Exam & Final Polish",
                day_range=f"Days {d_p1 + d_p2 + d_p3 + 1} - {days_until_exam}",
                focus_topics=[subject, "Comprehensive Review"],
                weak_areas_addressed=[],
                recommended_activities=[
                    "Full-length comprehensive mock assessment",
                    "Quick-look formula cheat-sheet revision",
                    "Light review & confidence building"
                ],
                mock_test_scheduled=True
            )
        ]

        strategy_summary = (
            f"Tailored {days_until_exam}-day exam preparation track for {subject} with a target score of {target_score_percent}%. "
            f"Prioritizing {len(weak_areas)} identified weak areas ({', '.join(weak_areas[:3]) if weak_areas else 'none currently'}) "
            f"with {daily_study_hours}h daily dedicated study time."
        )

        return ExamPrepPlan(
            id=str(uuid.uuid4()),
            user_id=user_id,
            subject=subject,
            days_until_exam=days_until_exam,
            target_score_percent=target_score_percent,
            daily_study_hours=daily_study_hours,
            high_weight_topics=high_weight,
            weak_areas_prioritized=weak_areas,
            strong_areas=strong_areas,
            milestones=milestones,
            strategy_summary=strategy_summary
        )

    # -----------------------------------------------------------------------
    # 7. Automatic Study Planner
    # -----------------------------------------------------------------------
    @classmethod
    def generate_study_plan(
        cls,
        user_id: str,
        topic_id: str,
        daily_minutes: int,
        target_days: int,
        db: Session
    ) -> StudyPlan:
        """
        Creates a day-by-day structured task schedule from learning path nodes & weak concepts.
        """
        profile = LearnerProfileService.get_full_learner_profile(user_id, db)
        
        db_path = db.query(DBLearningPath).filter(DBLearningPath.topic_id == topic_id).first()
        topic_title = topic_id
        if db_path and db_path.dag_json and isinstance(db_path.dag_json, dict):
            raw_nodes = db_path.dag_json.get("nodes", [])
            node_titles = [n.get("title", f"Concept {idx+1}") for idx, n in enumerate(raw_nodes) if isinstance(n, dict)]
            topic_title = db_path.title or topic_id
        else:
            node_titles = [f"{topic_id} Introduction", f"{topic_id} Core Concepts", f"{topic_id} Applications", f"{topic_id} Mastery"]

        days_list: List[StudyPlanDay] = []
        node_idx = 0
        
        for d in range(1, target_days + 1):
            tasks: List[StudyPlanTask] = []
            curr_node = node_titles[node_idx % len(node_titles)]
            
            if d == 1:
                # Day 1: Learn intro & flashcards
                tasks.append(StudyPlanTask(id=str(uuid.uuid4()), title=f"Learn: {curr_node}", activity_type="learn", duration_minutes=int(daily_minutes * 0.6), concept_or_node=curr_node))
                tasks.append(StudyPlanTask(id=str(uuid.uuid4()), title="Flashcards: Core Definitions", activity_type="flashcards", duration_minutes=int(daily_minutes * 0.4), concept_or_node=curr_node))
                node_idx += 1
            elif d % 3 == 0 or (d == 2 and profile.weak_concepts):
                # Revision day
                weak_target = profile.weak_concepts[0] if profile.weak_concepts else curr_node
                tasks.append(StudyPlanTask(id=str(uuid.uuid4()), title=f"Targeted Revision: {weak_target}", activity_type="revision", duration_minutes=int(daily_minutes * 0.5), concept_or_node=weak_target))
                tasks.append(StudyPlanTask(id=str(uuid.uuid4()), title="Practice Problems & Homework", activity_type="practice", duration_minutes=int(daily_minutes * 0.5), concept_or_node=weak_target))
            elif d == target_days:
                # Final day: Comprehensive Assessment
                tasks.append(StudyPlanTask(id=str(uuid.uuid4()), title="Final Mastery Assessment", activity_type="assessment", duration_minutes=int(daily_minutes * 0.7), concept_or_node=topic_id))
                tasks.append(StudyPlanTask(id=str(uuid.uuid4()), title="Review Notes Summary", activity_type="revision", duration_minutes=int(daily_minutes * 0.3), concept_or_node=topic_id))
            else:
                # Standard learning day
                tasks.append(StudyPlanTask(id=str(uuid.uuid4()), title=f"Learn: {curr_node}", activity_type="learn", duration_minutes=int(daily_minutes * 0.6), concept_or_node=curr_node))
                tasks.append(StudyPlanTask(id=str(uuid.uuid4()), title=f"Practice Questions: {curr_node}", activity_type="practice", duration_minutes=int(daily_minutes * 0.4), concept_or_node=curr_node))
                node_idx += 1

            days_list.append(StudyPlanDay(
                day_number=d,
                day_label=f"Day {d}",
                total_minutes=daily_minutes,
                tasks=tasks
            ))

        return StudyPlan(
            id=str(uuid.uuid4()),
            user_id=user_id,
            topic_id=topic_id,
            topic_title=topic_title,
            total_days=target_days,
            daily_budget_minutes=daily_minutes,
            current_day=1,
            days=days_list,
            auto_adjusted=False
        )

    @classmethod
    def recalculate_study_plan(
        cls,
        user_id: str,
        topic_id: str,
        missed_up_to_day: int,
        db: Session
    ) -> StudyPlan:
        """
        Dynamically adjusts remaining days when a student falls behind.
        """
        base_plan = cls.generate_study_plan(user_id, topic_id, daily_minutes=60, target_days=7, db=db)
        
        # Shift unfinished tasks from missed days into the remaining timeline
        rebalanced_days: List[StudyPlanDay] = []
        for d in base_plan.days:
            if d.day_number <= missed_up_to_day:
                # Mark as shifted / backlog
                shifted_tasks = [
                    StudyPlanTask(
                        id=str(uuid.uuid4()),
                        title=f"[Shifted] {t.title}",
                        activity_type=t.activity_type,
                        duration_minutes=t.duration_minutes,
                        concept_or_node=t.concept_or_node,
                        completed=False
                    )
                    for t in d.tasks
                ]
                rebalanced_days.append(StudyPlanDay(
                    day_number=d.day_number,
                    day_label=f"Day {d.day_number} (Missed - Catch Up)",
                    total_minutes=d.total_minutes,
                    tasks=shifted_tasks
                ))
            else:
                rebalanced_days.append(d)

        base_plan.days = rebalanced_days
        base_plan.auto_adjusted = True
        base_plan.adjustment_reason = f"Schedule automatically rebalanced to accommodate missed sessions up to Day {missed_up_to_day} without skipping core concepts."
        return base_plan

    # -----------------------------------------------------------------------
    # 8. Learning Analytics
    # -----------------------------------------------------------------------
    @classmethod
    def get_learning_analytics(cls, user_id: str, db: Session) -> LearningAnalyticsData:
        """
        Computes rich learning analytics: mastery progress, score trends,
        learning trajectory, and actionable next steps.
        """
        profile = LearnerProfileService.get_full_learner_profile(user_id, db)
        
        # Score history
        score_points: List[ScoreHistoryPoint] = []
        scores: List[float] = []
        for h in profile.scores_history:
            s_val = float(h.get("score", 0.0))
            scores.append(s_val)
            score_points.append(ScoreHistoryPoint(
                topic=h.get("topic", "Quiz"),
                score=s_val,
                date=h.get("date", get_utc_now().strftime("%Y-%m-%d"))
            ))

        # Overall mastery percentage
        mastery_map = profile.concept_masteries
        total_concepts = max(1, len(mastery_map))
        mastered_count = sum(1 for m in mastery_map.values() if isinstance(m, dict) and m.get("mastery") in ["mastered", "strong"])
        overall_mastery = round((mastered_count / total_concepts) * 100, 1) if mastery_map else (round(sum(scores) / len(scores), 1) if scores else 50.0)

        # Learning trajectory determination
        if len(scores) >= 2:
            recent_avg = sum(scores[-2:]) / 2
            prev_avg = sum(scores[:-2]) / len(scores[:-2]) if len(scores) > 2 else scores[0]
            
            if recent_avg >= 80 and recent_avg > prev_avg:
                trajectory = "improving"
                trajectory_reason = "Assessment performance shows consistent upward momentum."
            elif recent_avg < 60:
                trajectory = "struggling"
                trajectory_reason = "Multiple recent assessment scores are below threshold; revision recommended."
            elif len(profile.weak_concepts) > 0 and recent_avg >= 70:
                trajectory = "recovering_after_revision"
                trajectory_reason = "Successfully remediating previously weak concepts."
            else:
                trajectory = "stable"
                trajectory_reason = "Demonstrating steady and consistent concept comprehension."
        else:
            trajectory = "stable"
            trajectory_reason = "Baseline learning progression established."

        # Actionable recommendations
        recommendations: List[str] = []
        if profile.weak_concepts:
            recommendations.append(f"Launch Revision Mode to reinforce weak concepts: {', '.join(profile.weak_concepts[:2])}.")
        if profile.misunderstood_concepts:
            recommendations.append(f"Review Flashcards for misconception clarification on {profile.misunderstood_concepts[0]}.")
        if overall_mastery >= 80:
            recommendations.append("Ready for advanced challenge homework and higher-tier learning path modules.")
        if not recommendations:
            recommendations.append("Continue standard learning path lessons and take end-of-segment checkpoint quizzes.")

        return LearningAnalyticsData(
            user_id=user_id,
            name=profile.name,
            overall_mastery_percent=overall_mastery,
            total_study_minutes=max(15, len(profile.topics_studied) * 20),
            lessons_completed=len(profile.topics_studied),
            questions_answered=len(scores) * 4 + len(profile.concepts_studied),
            topics_mastered_count=mastered_count,
            learning_trajectory=trajectory,
            trajectory_reason=trajectory_reason,
            strong_concepts=profile.strong_concepts,
            weak_concepts=profile.weak_concepts,
            misunderstood_concepts=profile.misunderstood_concepts,
            recent_scores=score_points[-5:],
            actionable_recommendations=recommendations,
            current_learning_path=profile.current_topic or (profile.topics_studied[0] if profile.topics_studied else "General")
        )
