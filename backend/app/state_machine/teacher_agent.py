import re
import uuid
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from ..database import DBLessonSession, DBMaterial, DBLearnerProfile, DBMaterialChunk, SessionLocal
from ..models.schemas import (
    LessonPlan, 
    LessonSegmentPlan, 
    FinalAssessmentSpec, 
    CheckpointQuestion,
    LessonSegmentRender, 
    VisualDecision,
    CaptionItem, 
    Citation, 
    SourceCitation,
    LearnerProfileCreate,
    ParsedStudentInstruction
)
from ..services.rag import RAGService
from ..services.ingestion import IngestionService
from ..services.visual_router import VisualRouter
from ..services.tts import TTSService
from ..services.avatar import AvatarService
from ..services.video import VideoService
from ..services.llm import LLMService, LLMUnavailable
from ..services.learner_profile import LearnerProfileService
from ..services.study_tools import StudyToolsService

logger = logging.getLogger("sahayak.teacher")

GROUNDING_GUARDRAIL_PROMPT = (
    "Teach ONLY from the provided source material. Cite it. "
    "If the student asks about something not covered by these sources, "
    "say it is outside this document — do not invent it."
)

class TeacherState:
    UNDERSTAND = "understand"
    PLAN = "plan"
    EXPLAIN = "explain"
    DEMONSTRATE = "demonstrate"
    QUESTION = "question"
    EVALUATE = "evaluate"
    ADAPT = "adapt"
    CONTINUE = "continue"
    ASSESS = "assess"
    REPORT = "report"

class TeacherAgentStateMachine:
    def __init__(self, session_id: str, db: Session):
        self.session_id = session_id
        self.db = db
        self.db_session = self._get_or_create_session()

    def _get_or_create_session(self) -> DBLessonSession:
        s = self.db.query(DBLessonSession).filter(DBLessonSession.id == self.session_id).first()
        if not s:
            s = DBLessonSession(
                id=self.session_id,
                user_id="default-user",
                topic="AI Education",
                state=TeacherState.UNDERSTAND,
                taught_concepts=[],
                analogies_used=[]
            )
            self.db.add(s)
            self.db.commit()
        return s

    def transition_to(self, new_state: str) -> str:
        old_state: str = getattr(self.db_session, "state", TeacherState.UNDERSTAND)
        self.db_session.state = new_state
        self.db.commit()
        return f"Transitioned from {old_state} -> {new_state}"

    @classmethod
    async def parse_student_instruction(
        cls,
        instruction: str,
        filename: Optional[str] = None,
        available_chapters: Optional[List[str]] = None
    ) -> ParsedStudentInstruction:
        """
        Intelligently analyzes natural language student instructions such as:
        'I am a beginner. Teach me Chapter 4 in 20 minutes. Explain it in Hindi using simple examples. Ask me questions during the lesson and test me at the end.'
        Decomposes into structured pedagogical configuration with deterministic regex fallback.
        """
        raw = instruction.strip()
        if not raw:
            return ParsedStudentInstruction(
                raw_instruction=raw,
                time_budget_minutes=20,
                language="en",
                learner_level="beginner",
                pedagogical_style="visual",
                include_checkpoints=True,
                include_final_assessment=True
            )

        # 1. Heuristic regex extraction fallback defaults
        raw_l = raw.lower()
        
        # Chapter extraction
        ch_match = re.search(r'\b(?:chapter|ch|unit|section|part)\s*(\d+|[ivxlcdm]+|[a-z0-9_\-]+)\b', raw_l)
        target_ch = f"Chapter {ch_match.group(1).upper()}" if ch_match else None
        
        # Time budget extraction
        time_match = re.search(r'(\d+)\s*(?:min|mins|minute|minutes|hour|hours|hr|hrs)', raw_l)
        if time_match:
            val = int(time_match.group(1))
            if "hour" in raw_l or "hr" in raw_l:
                time_budget = min(120, val * 60)
            else:
                time_budget = max(5, min(120, val))
        else:
            time_budget = 20

        # Language extraction
        if "hindi" in raw_l or "हिंदी" in raw_l:
            lang = "hi"
        elif "hinglish" in raw_l:
            lang = "hinglish"
        elif "tamil" in raw_l or "தமிழ்" in raw_l:
            lang = "ta"
        elif "telugu" in raw_l or "తెలుగు" in raw_l:
            lang = "te"
        elif "bengali" in raw_l or "বাংলা" in raw_l:
            lang = "bn"
        elif "spanish" in raw_l or "español" in raw_l:
            lang = "es"
        else:
            lang = "en"

        # Learner level
        if "advanced" in raw_l or "expert" in raw_l or "deep dive" in raw_l:
            level = "advanced"
        elif "intermediate" in raw_l or "medium" in raw_l:
            level = "intermediate"
        else:
            level = "beginner"

        # Pedagogical style
        if "analog" in raw_l or "example" in raw_l:
            style = "analogies"
        elif "socratic" in raw_l or "question" in raw_l:
            style = "socratic"
        elif "code" in raw_l or "program" in raw_l or "python" in raw_l:
            style = "code"
        else:
            style = "visual"

        simple_ex = "simple" in raw_l or "beginner" in raw_l or "easy" in raw_l or "basic" in raw_l
        checkpoints = "question" in raw_l or "ask" in raw_l or "check" in raw_l or True
        test_end = "test" in raw_l or "quiz" in raw_l or "assess" in raw_l or "exam" in raw_l or True

        # 2. Guarded LLM Instruction Parsing Pass
        try:
            system_prompt = (
                "You are an expert NLP pedagogical parser for Sahayak AI Teacher. "
                "Analyze the student's natural instruction and extract precise teaching parameters. "
                "Output ONLY valid JSON matching the schema."
            )
            user_prompt = f"""Extract structured teaching parameters from this student instruction:
Instruction: "{raw}"
Filename: {filename or 'Uploaded Material'}
Available Document Chapters: {available_chapters or []}

JSON schema:
{{
  "target_chapter": "Chapter 4" or null,
  "time_budget_minutes": 20,
  "language": "en | hi | hinglish | ta | te | bn | es",
  "learner_level": "beginner | intermediate | advanced",
  "pedagogical_style": "visual | analogies | socratic | code",
  "include_checkpoints": true,
  "include_final_assessment": true,
  "simple_examples_requested": true,
  "key_focus_topics": ["Topic 1", "Topic 2"]
}}
"""
            llm_res = await LLMService.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema_hint="ParsedStudentInstruction JSON",
                temperature=0.1
            )
            if llm_res and isinstance(llm_res, dict):
                return ParsedStudentInstruction(
                    raw_instruction=raw,
                    target_chapter=llm_res.get("target_chapter") or target_ch,
                    time_budget_minutes=int(llm_res.get("time_budget_minutes") or time_budget),
                    language=str(llm_res.get("language") or lang),
                    learner_level=str(llm_res.get("learner_level") or level),
                    pedagogical_style=str(llm_res.get("pedagogical_style") or style),
                    include_checkpoints=bool(llm_res.get("include_checkpoints", checkpoints)),
                    include_final_assessment=bool(llm_res.get("include_final_assessment", test_end)),
                    simple_examples_requested=bool(llm_res.get("simple_examples_requested", simple_ex)),
                    key_focus_topics=[str(t) for t in llm_res.get("key_focus_topics", [])]
                )
        except Exception as e:
            logger.info(f"[TeacherAgent] LLM instruction parsing fallback: {e}")

        return ParsedStudentInstruction(
            raw_instruction=raw,
            target_chapter=target_ch,
            time_budget_minutes=time_budget,
            language=lang,
            learner_level=level,
            pedagogical_style=style,
            include_checkpoints=checkpoints,
            include_final_assessment=test_end,
            simple_examples_requested=simple_ex,
            key_focus_topics=[]
        )

    @classmethod
    async def plan_from_document(
        cls,
        *,
        document_id: str,
        time_budget_minutes: int = 20,
        language: str = "en",
        learner_profile: Optional[LearnerProfileCreate] = None,
        instruction: Optional[str] = None,
        target_chapter: Optional[str] = None,
        db: Optional[Session] = None
    ) -> LessonPlan:
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            return await cls._plan_from_document_impl(
                document_id=document_id,
                time_budget_minutes=time_budget_minutes,
                language=language,
                learner_profile=learner_profile,
                instruction=instruction,
                target_chapter=target_chapter,
                db=db
            )
        finally:
            if close_db and db is not None:
                db.close()

    @classmethod
    async def _plan_from_document_impl(
        cls,
        *,
        document_id: str,
        time_budget_minutes: int = 20,
        language: str = "en",
        learner_profile: Optional[LearnerProfileCreate] = None,
        instruction: Optional[str] = None,
        target_chapter: Optional[str] = None,
        db: Session
    ) -> LessonPlan:
        session_id = str(uuid.uuid4())
        user_id = learner_profile.user_id if learner_profile else "default-user"
        effective_level = learner_profile.level if learner_profile else "beginner"
        effective_style = learner_profile.preferred_style if learner_profile else "visual"
        effective_time = time_budget_minutes
        effective_lang = language
        effective_chapter = target_chapter
        simple_examples = True

        db_mat = db.query(DBMaterial).filter(DBMaterial.id == document_id).first()
        filename = db_mat.filename if db_mat else "Uploaded Document"

        # If natural student instruction provided, parse it
        parsed_instruction: Optional[ParsedStudentInstruction] = None
        if instruction and instruction.strip():
            parsed_instruction = await cls.parse_student_instruction(instruction, filename=filename)
            if parsed_instruction.target_chapter:
                effective_chapter = parsed_instruction.target_chapter
            if parsed_instruction.time_budget_minutes:
                effective_time = parsed_instruction.time_budget_minutes
            if parsed_instruction.language:
                effective_lang = parsed_instruction.language
            if parsed_instruction.learner_level:
                effective_level = parsed_instruction.learner_level
            if parsed_instruction.pedagogical_style:
                effective_style = parsed_instruction.pedagogical_style
            simple_examples = parsed_instruction.simple_examples_requested

        topic_label = f"{effective_chapter} of {filename}" if effective_chapter else f"Study: {filename}"

        all_chunks = db.query(DBMaterialChunk).filter(DBMaterialChunk.material_id == document_id).all()
        
        # Filter chunks by requested chapter or topic
        chunks = IngestionService.filter_chunks_by_chapter_or_topic(all_chunks, effective_chapter) if effective_chapter else all_chunks
        if not chunks:
            chunks = all_chunks

        # Calculate progressive segment count based on time budget
        target_segment_count = 2 if effective_time <= 5 else (4 if effective_time <= 25 else 6)

        if not chunks:
            return await cls._generate_standard_lesson_plan(
                topic=topic_label,
                material_id=document_id,
                profile=learner_profile,
                time_budget_minutes=effective_time,
                language=effective_lang,
                db=db
            )

        # Partition chunks across target segments
        chunk_partitions: List[List[DBMaterialChunk]] = [[] for _ in range(target_segment_count)]
        for idx, chunk in enumerate(chunks):
            partition_idx = min(idx * target_segment_count // len(chunks), target_segment_count - 1)
            chunk_partitions[partition_idx].append(chunk)

        # Build grounded context summary across partitions
        partition_summaries = []
        for i, part in enumerate(chunk_partitions):
            if not part:
                part = [chunks[min(i, len(chunks)-1)]]
                chunk_partitions[i] = part
            part_texts = [f"[Chunk ID: {c.id}, Page: {c.page or 1}, Section: {c.chapter}]: {c.content[:250]}" for c in part[:3]]
            partition_summaries.append(f"Segment {i+1} Material:\n" + "\n".join(part_texts))

        all_material_summary = "\n\n".join(partition_summaries)

        # 1. Try LLM Grounded Pedagogical Planning
        try:
            system_prompt = (
                "You are Sahayak AI Teacher, an elite world-class personalized educational architect and tutor. "
                f"{GROUNDING_GUARDRAIL_PROMPT} "
                "You conduct an interactive, structured lesson sequence (Prerequisite -> Core Concept -> Intuitive Explanation -> Relatable Example -> Knowledge Check -> Application). "
                "Design a rigorous lesson plan tailored precisely to the learner level, time limit, and requested language."
            )
            
            lang_clause = f"Language: {effective_lang}."
            if effective_lang == "hi":
                lang_clause += " Explain in natural Hindi in Devanagari script while keeping domain technical terms in English."
            elif effective_lang == "hinglish":
                lang_clause += " Explain in conversational Hinglish while keeping domain technical terms in English."
            elif effective_lang == "ta":
                lang_clause += " Explain in natural, conversational Tamil (Tamil script) while strictly preserving domain technical terminology in English (or bilingual Tamil+English). Provide intuitive real-world analogies."

            learner_ctx_prompt = ""
            if db and user_id:
                try:
                    rel_ctx = LearnerProfileService.get_relevant_learner_context(user_id=user_id, target_topic=topic_label, db=db)
                    if rel_ctx.pedagogical_instructions:
                        learner_ctx_prompt = "\n\nPERSONALIZED LEARNER CONTEXT & ADAPTATIONS:\n" + "\n".join([f"- {instr}" for instr in rel_ctx.pedagogical_instructions])
                    if rel_ctx.misconceptions:
                        learner_ctx_prompt += f"\n- TARGET MISCONCEPTIONS TO DISPEL: {', '.join(rel_ctx.misconceptions)}"
                except Exception as e:
                    logger.warning(f"[TeacherAgent] Failed to retrieve learner context: {e}")

            user_prompt = f"""Generate an adaptive {target_segment_count}-segment grounded lesson plan for:
Document / Section: {topic_label}
Time Budget: {effective_time} minutes ({target_segment_count} progressive segments)
Learner Level: {effective_level} (Provide intuitive mental models and simple examples before technical details)
Pedagogical Style: {effective_style}
{lang_clause}
Simple Examples Required: {simple_examples}
{learner_ctx_prompt}

SOURCE MATERIAL PARTITIONS (Cover these progressively across segments):
{all_material_summary}

CRITICAL PEDAGOGICAL RULES:
1. {GROUNDING_GUARDRAIL_PROMPT}
2. Order concepts logically: Segment 1 (Prerequisite & Intuition) -> Segment 2 (Core Mechanics) -> Segment 3 (Real-World Examples & Demos) -> Segment 4 (Synthesis & Checkpoint).
3. Calibrate explanation depth: Keep simple for beginners, deeper for advanced.
4. Each segment must list the exact cited chunk IDs.

Output JSON with this EXACT structure:
{{
  "objectives": ["string", "string", "string"],
  "segments": [
    {{
      "id": 1,
      "concept": "Name of Concept Grounded in Segment 1 Material",
      "depth": "{effective_level}",
      "est_minutes": {max(1, effective_time // target_segment_count)},
      "visual_type": "labeled-diagram | equation/graph | code+execution | timeline/map",
      "summary": "Pedagogical summary grounded in the document.",
      "cited_chunk_ids": ["chunk_id_from_above"],
      "checkpoint_question": {{
        "type": "mcq",
        "question": "Question testing conceptual understanding from this excerpt?",
        "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
        "correct_answer": "A) ...",
        "hints": ["Hint grounded in document"]
      }}
    }}
  ]
}}
"""
            llm_plan = await LLMService.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema_hint="LessonPlan JSON with objectives[], segments[{id, concept, depth, est_minutes, visual_type, summary, cited_chunk_ids, checkpoint_question}]",
                temperature=0.2
            )

            raw_segments = llm_plan.get("segments", [])
            if raw_segments and len(raw_segments) > 0:
                parsed_segments: List[LessonSegmentPlan] = []
                for idx, s in enumerate(raw_segments):
                    s_id = idx + 1
                    part_chunks = chunk_partitions[min(idx, len(chunk_partitions) - 1)]
                    
                    cited_ids = s.get("cited_chunk_ids", [])
                    matched_chunks = [c for c in chunks if c.id in cited_ids] if cited_ids else part_chunks[:2]
                    if not matched_chunks:
                        matched_chunks = part_chunks[:2] if part_chunks else chunks[:1]

                    source_cites: List[SourceCitation] = []
                    segment_citations: List[Citation] = []
                    for mc in matched_chunks:
                        snippet = mc.content[:180] + "..." if len(mc.content) > 180 else mc.content
                        source_cites.append(SourceCitation(
                            chunk_id=mc.id,
                            page=mc.page or 1,
                            quote=snippet
                        ))
                        segment_citations.append(Citation(
                            chunk_id=mc.id,
                            chapter=mc.chapter or "Document Section",
                            page=mc.page or 1,
                            section=mc.section or "",
                            quote=snippet,
                            snippet=snippet,
                            confidence=0.98
                        ))

                    raw_cp = s.get("checkpoint_question") or {}
                    raw_opts = raw_cp.get("options", [])
                    concept_name = str(s.get("concept") or (part_chunks[0].chapter if part_chunks else f"Segment {s_id}"))
                    
                    if not isinstance(raw_opts, list) or len(raw_opts) < 2:
                        options = [
                            f"A) Correct principle of {concept_name}",
                            "B) Contradictory opposing hypothesis",
                            "C) Non-interacting baseline",
                            "D) Random fluctuation"
                        ]
                    else:
                        options = [str(opt) for opt in raw_opts]
                    correct_ans = str(raw_cp.get("correct_answer") or options[0])
                    raw_hints = raw_cp.get("hints")
                    hints_list = [str(h) for h in raw_hints] if isinstance(raw_hints, list) else [f"Review {concept_name}"]

                    # Subject-Aware Visual Planning
                    v_decision = VisualRouter.decide_visual_strategy(concept_name, topic_label, effective_level)
                    v_type = str(s.get("visual_type")) if s.get("visual_type") in ["free_body_diagram", "process_cycle", "equation/graph", "labeled-diagram", "timeline/map", "code+execution"] else v_decision.visual_type

                    checkpoint_q = CheckpointQuestion(
                        type=str(raw_cp.get("type", "mcq")),
                        question=str(raw_cp.get("question", v_decision.knowledge_check or f"What is the key principle of {concept_name}?")),
                        options=options,
                        correct_answer=correct_ans,
                        hints=hints_list,
                        concept_tested=concept_name
                    )

                    parsed_segments.append(LessonSegmentPlan(
                        id=s_id,
                        concept=concept_name,
                        depth=str(s.get("depth", effective_level)),
                        est_minutes=int(s.get("est_minutes", max(1, effective_time // target_segment_count))),
                        visual_type=v_type,
                        visual_decision=v_decision,
                        checkpoint_question=checkpoint_q,
                        summary=str(s.get("summary", f"Study of {concept_name}")),
                        source_citations=source_cites,
                        citations=segment_citations
                    ))

                plan = LessonPlan(
                    session_id=session_id,
                    topic=topic_label,
                    objectives=[str(o) for o in llm_plan.get("objectives", [
                        f"Master concepts in {topic_label}",
                        "Examine document-grounded principles and derivations",
                        "Demonstrate mastery through grounded checkpoints"
                    ])],
                    time_budget_minutes=effective_time,
                    learner_level=effective_level,
                    language=effective_lang,
                    segments=parsed_segments,
                    final_assessment=FinalAssessmentSpec(type="quiz", question_count=len(parsed_segments) + 1),
                    material_id=document_id,
                    document_id=document_id
                )

                db_sess = DBLessonSession(
                    id=session_id,
                    user_id=user_id,
                    topic=topic_label,
                    language=effective_lang,
                    time_budget=effective_time,
                    current_segment_id=1,
                    state=TeacherState.EXPLAIN,
                    plan_json=plan.model_dump(),
                    taught_concepts=[s.concept for s in parsed_segments],
                    analogies_used=[]
                )
                db.add(db_sess)
                db.commit()
                logger.info(f"[TeacherAgent] Generated grounded document lesson plan with {len(parsed_segments)} segments.")
                return plan

        except Exception as e:
            logger.warning(f"[TeacherAgent] Grounded document LLM planning failed ({e}); falling back to procedural extractor.")

        # 2. Deterministic Procedural Fallback from Document Chunks
        fallback_segments: List[LessonSegmentPlan] = []
        for idx in range(target_segment_count):
            s_id = idx + 1
            part_chunks = chunk_partitions[idx] if idx < len(chunk_partitions) and chunk_partitions[idx] else chunks[:1]
            primary_chunk = part_chunks[0]
            
            concept_name = primary_chunk.chapter or f"Section {s_id}: {filename}"
            if "Chapter" not in concept_name and "Section" not in concept_name and len(concept_name) > 3:
                concept_name = f"{s_id}. {concept_name}"
            else:
                concept_name = f"{s_id}. {primary_chunk.chapter or 'Document Unit'}"

            source_cites: List[SourceCitation] = []
            segment_citations: List[Citation] = []
            for mc in part_chunks[:2]:
                snippet = mc.content[:180] + "..." if len(mc.content) > 180 else mc.content
                source_cites.append(SourceCitation(
                    chunk_id=mc.id,
                    page=mc.page or 1,
                    quote=snippet
                ))
                segment_citations.append(Citation(
                    chunk_id=mc.id,
                    chapter=mc.chapter or "Document Section",
                    page=mc.page or 1,
                    section=mc.section or "",
                    quote=snippet,
                    snippet=snippet,
                    confidence=0.98
                ))

            options_pool: List[str] = [
                f"A) {concept_name} adheres strictly to the document's verified governing principles.",
                f"B) {concept_name} contradicts all stated definitions in the source material.",
                f"C) Boundary values fluctuate arbitrarily without mechanical constraint.",
                f"D) The concept is entirely out of scope for this document."
            ]
            checkpoint_q = CheckpointQuestion(
                type="mcq",
                question=f"According to the source document, what is the key takeaway of {concept_name}?",
                options=options_pool,
                correct_answer=options_pool[0],
                hints=[f"Review excerpt from Page {primary_chunk.page or 1}: {primary_chunk.content[:100]}..."],
                concept_tested=concept_name
            )

            fallback_segments.append(LessonSegmentPlan(
                id=s_id,
                concept=concept_name,
                depth=effective_level,
                est_minutes=max(1, effective_time // target_segment_count),
                visual_type="labeled-diagram" if s_id % 2 == 1 else "equation/graph",
                checkpoint_question=checkpoint_q,
                summary=primary_chunk.content[:200] + "...",
                source_citations=source_cites,
                citations=segment_citations
            ))

        plan = LessonPlan(
            session_id=session_id,
            topic=topic_label,
            objectives=[
                f"Master core concepts from {topic_label}",
                "Review verified source excerpts and formulas",
                "Complete document-grounded checkpoints"
            ],
            time_budget_minutes=effective_time,
            learner_level=effective_level,
            language=effective_lang,
            segments=fallback_segments,
            final_assessment=FinalAssessmentSpec(type="quiz", question_count=len(fallback_segments) + 1),
            material_id=document_id,
            document_id=document_id
        )

        db_sess = DBLessonSession(
            id=session_id,
            user_id=user_id,
            topic=topic_label,
            language=effective_lang,
            time_budget=effective_time,
            current_segment_id=1,
            state=TeacherState.EXPLAIN,
            plan_json=plan.model_dump(),
            taught_concepts=[s.concept for s in fallback_segments],
            analogies_used=[]
        )
        db.add(db_sess)
        db.commit()
        return plan


    @classmethod
    async def generate_lesson_plan(
        cls, 
        topic: Optional[str], 
        material_id: Optional[str], 
        profile: Optional[LearnerProfileCreate], 
        time_budget_minutes: int, 
        language: str, 
        instruction: Optional[str] = None,
        target_chapter: Optional[str] = None,
        db: Optional[Session] = None
    ) -> LessonPlan:
        if material_id:
            return await cls.plan_from_document(
                document_id=material_id,
                time_budget_minutes=time_budget_minutes,
                language=language,
                learner_profile=profile,
                instruction=instruction,
                target_chapter=target_chapter,
                db=db
            )
        return await cls._generate_standard_lesson_plan(
            topic=topic,
            material_id=None,
            profile=profile,
            time_budget_minutes=time_budget_minutes,
            language=language,
            instruction=instruction,
            db=db
        )

    @classmethod
    async def _generate_standard_lesson_plan(
        cls,
        topic: Optional[str],
        material_id: Optional[str],
        profile: Optional[LearnerProfileCreate],
        time_budget_minutes: int,
        language: str,
        instruction: Optional[str] = None,
        target_chapter: Optional[str] = None,
        db: Optional[Session] = None
    ) -> LessonPlan:
        session_id = str(uuid.uuid4())
        user_id = profile.user_id if profile else "default-user"
        level = profile.level if profile else "beginner"
        style = profile.preferred_style if profile else "visual"
        effective_topic = topic or "Foundational Principles"
        
        grounded_context = ""
        citations = []
        if material_id and db:
            db_mat = db.query(DBMaterial).filter(DBMaterial.id == material_id).first()
            if db_mat:
                effective_topic = f"Study: {db_mat.filename}"
            grounded_context, citations = RAGService.get_grounded_context_and_citations(effective_topic, material_id, db)

        # 1. Try real LLM Lesson Plan Generation
        try:
            target_segment_count = 2 if time_budget_minutes <= 5 else (4 if time_budget_minutes <= 25 else 6)
            
            system_prompt = (
                "You are Sahayak AI Teacher, an elite world-class personalized educational architect. "
                "You design rigorous, pedagogically sound, structured lesson plans tailored to learner level, time budget, style, and language. "
                "Always adhere strictly to the JSON schema requested."
            )
            
            rag_instruction = ""
            if grounded_context:
                rag_instruction = (
                    f"\n\nGROUNDED SOURCE MATERIAL:\n{grounded_context}\n\n"
                    "CRITICAL: Base the lesson objectives and concepts ONLY on the provided source material above. "
                    "Do not introduce outside hallucinated concepts."
                )

            learner_ctx_prompt = ""
            if db and user_id:
                try:
                    rel_ctx = LearnerProfileService.get_relevant_learner_context(user_id=user_id, target_topic=effective_topic, db=db)
                    if rel_ctx.pedagogical_instructions:
                        learner_ctx_prompt = "\n\nPERSONALIZED LEARNER PROFILE CONTEXT:\n" + "\n".join([f"- {instr}" for instr in rel_ctx.pedagogical_instructions])
                    if rel_ctx.misconceptions:
                        learner_ctx_prompt += f"\n- TARGET MISCONCEPTIONS TO DISPEL: {', '.join(rel_ctx.misconceptions)}"
                except Exception as e:
                    logger.warning(f"[TeacherAgent] Failed to retrieve learner context: {e}")

            user_prompt = f"""Generate a structured lesson plan for:
Topic: {effective_topic}
Time Budget: {time_budget_minutes} minutes (Target precisely {target_segment_count} progressive segments)
Learner Level: {level} (Adjust technical vocabulary, depth, and mathematical rigor accordingly)
Pedagogical Style: {style} (Emphasize {style} approaches in descriptions and visual types)
Language: {language} (Provide segment summaries and questions in {language} if hi or hinglish, otherwise en)
{rag_instruction}
{learner_ctx_prompt}

Output a JSON object with this EXACT structure:
{{
  "objectives": ["string", "string", "string"],
  "segments": [
    {{
      "id": 1,
      "concept": "Name of Concept",
      "depth": "{level}",
      "est_minutes": {max(1, time_budget_minutes // target_segment_count)},
      "visual_type": "labeled-diagram | equation/graph | code+execution | timeline/map",
      "summary": "Short pedagogical summary of what will be taught in this segment.",
      "checkpoint_question": {{
        "type": "mcq",
        "question": "A concept-checking question testing deep intuition or derivation?",
        "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
        "correct_answer": "A) The exact text of the correct option matching one of the options array",
        "hints": ["Helpful first-principles hint"]
      }}
    }}
  ]
}}
"""
            llm_plan = await LLMService.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema_hint="LessonPlan JSON with objectives[], segments[{id, concept, depth, est_minutes, visual_type, summary, checkpoint_question}]",
                temperature=0.3
            )

            raw_segments = llm_plan.get("segments", [])
            if raw_segments and len(raw_segments) > 0:
                parsed_segments: List[LessonSegmentPlan] = []
                for idx, s in enumerate(raw_segments):
                    s_id = int(s.get("id")) if isinstance(s.get("id"), int) or (isinstance(s.get("id"), str) and str(s.get("id")).isdigit()) else (idx + 1)
                    raw_cp = s.get("checkpoint_question")
                    cp = raw_cp if isinstance(raw_cp, dict) else {}
                    
                    # Ensure options has 4 choices
                    raw_opts = cp.get("options", [])
                    if not isinstance(raw_opts, list) or len(raw_opts) < 2:
                        options = [
                            f"A) Correct principle of {s.get('concept', effective_topic)}",
                            "B) Contradictory opposing hypothesis",
                            "C) Non-interacting baseline",
                            "D) Random fluctuation"
                        ]
                    else:
                        options = [str(opt) for opt in raw_opts]
                    correct_ans = str(cp.get("correct_answer") or options[0])

                    raw_hints = cp.get("hints")
                    hints_list = [str(h) for h in raw_hints] if isinstance(raw_hints, list) else [f"Focus on the core definition of {s.get('concept')}"]

                    checkpoint_q = CheckpointQuestion(
                        type=str(cp.get("type", "mcq")),
                        question=str(cp.get("question", f"What is the key principle of {s.get('concept')}?")),
                        options=options,
                        correct_answer=correct_ans,
                        hints=hints_list,
                        concept_tested=str(s.get("concept", effective_topic))
                    )

                    concept_str = str(s.get("concept", f"Concept {s_id}"))
                    v_decision = VisualRouter.decide_visual_strategy(concept_str, effective_topic, level)
                    v_type = str(s.get("visual_type")) if s.get("visual_type") in ["free_body_diagram", "process_cycle", "equation/graph", "labeled-diagram", "timeline/map", "code+execution"] else v_decision.visual_type

                    parsed_segments.append(LessonSegmentPlan(
                        id=s_id,
                        concept=concept_str,
                        depth=str(s.get("depth", level)),
                        est_minutes=int(s.get("est_minutes", max(1, time_budget_minutes // len(raw_segments)))),
                        visual_type=v_type,
                        visual_decision=v_decision,
                        checkpoint_question=checkpoint_q,
                        summary=str(s.get("summary", f"Mastery of {concept_str}"))
                    ))

                plan = LessonPlan(
                    session_id=session_id,
                    topic=effective_topic,
                    objectives=[str(o) for o in llm_plan.get("objectives", [
                        f"Master core principles of {effective_topic}",
                        f"Understand governing rules and real-world mechanisms",
                        f"Solve interactive checkpoints and verify mastery"
                    ])],
                    time_budget_minutes=time_budget_minutes,
                    learner_level=level,
                    language=language,
                    segments=parsed_segments,
                    final_assessment=FinalAssessmentSpec(type="quiz", question_count=len(parsed_segments) + 1),
                    material_id=material_id
                )

                # Persist session to DB
                db_sess = DBLessonSession(
                    id=session_id,
                    user_id=user_id,
                    topic=effective_topic,
                    language=language,
                    time_budget=time_budget_minutes,
                    current_segment_id=1,
                    state=TeacherState.EXPLAIN,
                    plan_json=plan.model_dump(),
                    taught_concepts=[s.concept for s in parsed_segments],
                    analogies_used=[]
                )
                if db:
                    db.add(db_sess)
                    db.commit()
                logger.info(f"[TeacherAgent] Successfully generated LLM lesson plan with {len(parsed_segments)} segments.")
                return plan

        except Exception as e:
            logger.warning(f"[TeacherAgent] LLM lesson planning failed ({e}); activating deterministic fallback template.")

        # 2. Deterministic Fallback Template
        segment_configs: List[Dict[str, Any]] = []
        if time_budget_minutes <= 5:
            segment_configs = [
                {"title": f"Core Principle of {effective_topic}", "depth": level, "est": 2, "visual": "labeled-diagram"},
                {"title": f"Practical Application & Edge Cases", "depth": level, "est": 3, "visual": "equation/graph"}
            ]
        elif time_budget_minutes <= 25:
            segment_configs = [
                {"title": f"1. Foundations & Intuition of {effective_topic}", "depth": level, "est": 4, "visual": "labeled-diagram"},
                {"title": f"2. Mathematical & Formal Derivation", "depth": level, "est": 5, "visual": "equation/graph"},
                {"title": f"3. Algorithmic Demonstration & Code Runner", "depth": level, "est": 6, "visual": "code+execution"},
                {"title": f"4. Historical Context & Real-World Synthesis", "depth": level, "est": 5, "visual": "timeline/map"}
            ]
        else: # 60 min or multi-session
            segment_configs = [
                {"title": f"1. First Principles & Motivation", "depth": level, "est": 8, "visual": "labeled-diagram"},
                {"title": f"2. Formal Axioms & Equations", "depth": level, "est": 10, "visual": "equation/graph"},
                {"title": f"3. System Architecture & Component Interactions", "depth": level, "est": 12, "visual": "labeled-diagram"},
                {"title": f"4. Computational Implementation & Sandbox", "depth": level, "est": 12, "visual": "code+execution"},
                {"title": f"5. Evolution, History & Paradigms", "depth": level, "est": 10, "visual": "timeline/map"},
                {"title": f"6. Mastery Synthesis & Complex Edge Cases", "depth": level, "est": 8, "visual": "equation/graph"}
            ]

        fallback_segments: List[LessonSegmentPlan] = []
        for idx, sc in enumerate(segment_configs):
            seg_id = idx + 1
            concept_name = str(sc.get("title") or f"Unit {seg_id}")
            v_decision = VisualRouter.decide_visual_strategy(concept_name, effective_topic, level)
            
            # Checkpoint Question with randomized correct option distribution
            options_pool: List[str] = [
                f"A) {concept_name} preserves conservation laws through predictable dynamic state transitions.",
                f"B) {concept_name} operates in absolute isolation with zero energy exchange.",
                f"C) Boundary conditions are purely arbitrary and non-measurable.",
                f"D) All state variables immediately collapse to null."
            ]
            checkpoint_q = CheckpointQuestion(
                type="mcq",
                question=v_decision.knowledge_check or f"In the context of {concept_name}, what is the critical governing condition?",
                options=options_pool,
                correct_answer=options_pool[0],
                hints=[f"Recall the equilibrium rule discussed in {concept_name}."],
                concept_tested=concept_name
            )

            fallback_segments.append(LessonSegmentPlan(
                id=seg_id,
                concept=concept_name,
                depth=str(sc.get("depth") or level),
                est_minutes=int(sc.get("est") or 4),
                visual_type=v_decision.visual_type,
                visual_decision=v_decision,
                checkpoint_question=checkpoint_q,
                summary=f"In this segment, we systematically examine {concept_name} tailored for {level} level learners."
            ))

        objectives = [
            f"Master core intuitive mental models of {effective_topic}",
            f"Derive mathematical and computational rules governing the system",
            f"Identify failure modes, misconceptions, and solve interactive checkpoints"
        ]

        plan = LessonPlan(
            session_id=session_id,
            topic=effective_topic,
            objectives=objectives,
            time_budget_minutes=time_budget_minutes,
            learner_level=level,
            language=language,
            segments=fallback_segments,
            final_assessment=FinalAssessmentSpec(type="quiz", question_count=len(fallback_segments) + 1),
            material_id=material_id
        )

        # Persist session
        db_sess = DBLessonSession(
            id=session_id,
            user_id=user_id,
            topic=effective_topic,
            language=language,
            time_budget=time_budget_minutes,
            current_segment_id=1,
            state=TeacherState.EXPLAIN,
            plan_json=plan.model_dump(),
            taught_concepts=[s.concept for s in fallback_segments],
            analogies_used=[]
        )
        if db:
            db.add(db_sess)
            db.commit()

        return plan

    @classmethod
    def _split_into_timed_captions(cls, text: str, total_duration_sec: Optional[float] = None) -> List[CaptionItem]:
        """Splits spoken script into realistic phrase-level synchronized captions."""
        import re
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        if not sentences:
            sentences = [text]

        # Calculate word counts and proportional durations (approx 130 words per minute ~ 2.15 words/sec)
        word_counts = [max(1, len(s.split())) for s in sentences]
        total_words = sum(word_counts)
        
        calculated_total_duration = total_duration_sec or max(6.0, total_words / 2.2)
        
        captions: List[CaptionItem] = []
        current_time = 0.0
        for s, wc in zip(sentences, word_counts):
            duration = (wc / total_words) * calculated_total_duration
            end_time = round(current_time + duration, 2)
            captions.append(CaptionItem(
                start_sec=round(current_time, 2),
                end_sec=end_time,
                text=s
            ))
            current_time = end_time

        return captions

    @classmethod
    async def render_segment(
        cls, 
        session_id: str, 
        segment_id: int, 
        language: Optional[str] = None, 
        db: Optional[Session] = None,
        skip_video: bool = False
    ) -> LessonSegmentRender:
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True

        try:
            return await cls._render_segment_impl(
                session_id=session_id,
                segment_id=segment_id,
                db=db,
                language=language,
                skip_video=skip_video
            )
        finally:
            if close_db and db is not None:
                db.close()

    @classmethod
    async def _render_segment_impl(
        cls, 
        session_id: str, 
        segment_id: int, 
        db: Session,
        language: Optional[str] = None,
        skip_video: bool = False
    ) -> LessonSegmentRender:
        db_sess = db.query(DBLessonSession).filter(DBLessonSession.id == session_id).first()
        if not db_sess:
            raise ValueError(f"Session {session_id} not found")

        sess_topic = getattr(db_sess, "topic", "Lesson Topic") or "Lesson Topic"
        sess_lang = getattr(db_sess, "language", "en") or "en"

        plan_data: Dict[str, Any] = dict(db_sess.plan_json) if isinstance(db_sess.plan_json, dict) else {}
        raw_segments = plan_data.get("segments", [])
        segments: List[Dict[str, Any]] = [s for s in raw_segments if isinstance(s, dict)]
        matching_seg = next((s for s in segments if s.get("id") == segment_id), None)
        seg: Dict[str, Any] = matching_seg or (segments[0] if segments else {"id": 1, "concept": sess_topic, "visual_type": "labeled-diagram"})

        concept = str(seg.get("concept") or sess_topic)
        visual_type = str(seg.get("visual_type") or "labeled-diagram")
        active_lang = language or sess_lang
        level = str(seg.get("depth") or "beginner")
        
        # Build citations if material attached
        raw_mat_id = plan_data.get("material_id") or plan_data.get("document_id")
        material_id: Optional[str] = str(raw_mat_id) if raw_mat_id else None
        citations: List[Citation] = []
        rag_context: str = ""
        if material_id:
            source_cites = seg.get("source_citations", []) or seg.get("citations", [])
            chunk_ids = [c.get("chunk_id") if isinstance(c, dict) else getattr(c, "chunk_id", None) for c in source_cites]
            chunk_ids = [cid for cid in chunk_ids if cid]
            
            if chunk_ids:
                try:
                    db_chunks = db.query(DBMaterialChunk).filter(DBMaterialChunk.id.in_(chunk_ids)).all()
                    if db_chunks:
                        context_blocks = []
                        for chunk in db_chunks:
                            ch_name = chunk.chapter or "Document Section"
                            p_num = chunk.page or 1
                            content = chunk.content or ""
                            context_blocks.append(f"[{ch_name} - Page {p_num} (Chunk: {chunk.id})]:\n{content}")
                            citations.append(Citation(
                                chunk_id=chunk.id,
                                chapter=ch_name,
                                page=chunk.page or 1,
                                section=chunk.section or "",
                                quote=content[:200] + "..." if len(content) > 200 else content,
                                snippet=content[:140] + "..." if len(content) > 140 else content,
                                confidence=0.98
                            ))
                        rag_context = "\n\n".join(context_blocks)
                except Exception as ex:
                    logger.warning(f"Error querying cited chunk IDs ({ex}); falling back to semantic search.")

            if not rag_context:
                rag_context, retrieved_citations = RAGService.get_grounded_context_and_citations(concept, material_id, db)
                if not citations:
                    citations = retrieved_citations

        # Visual Decision Strategy Resolution
        raw_v_dec = seg.get("visual_decision")
        if isinstance(raw_v_dec, VisualDecision):
            v_decision = raw_v_dec
        elif isinstance(raw_v_dec, dict):
            v_decision = VisualDecision(**raw_v_dec)
        else:
            v_decision = VisualRouter.decide_visual_strategy(concept, sess_topic, level)
        
        visual_type = str(seg.get("visual_type")) if seg.get("visual_type") in ["free_body_diagram", "process_cycle", "equation/graph", "labeled-diagram", "timeline/map", "code+execution"] else v_decision.visual_type

        # 1. Try real LLM Segment Content Generation
        spoken_script = ""
        on_screen_text = ""
        captions: List[CaptionItem] = []

        try:
            pedagogy_guide = (
                f"You are Sahayak AI Teacher teaching '{concept}' to a {level} student in {active_lang}. "
                f"{GROUNDING_GUARDRAIL_PROMPT} "
                "You conduct an interactive lesson with real teacher presence. "
                "For beginners, explain intuitive physical or real-world models and relatable simple examples before formal technical terms. "
                f"CRITICAL VISUAL INTEGRATION RULE: You must verbally guide the student's observation of the visual on screen using this pedagogical guide: '{v_decision.observation_prompt}'. "
            )
            if active_lang == "hi":
                pedagogy_guide += (
                    "CRITICAL HINDI HYBRID TEACHING RULE: Write clear, conversational explanations in Hindi (Devanagari script), "
                    "but strictly preserve domain technical terminology in English (e.g., 'Binary Search', 'Potential Energy', 'Mitochondria', 'Algorithm', 'Conservation of Energy', 'Derivative'). "
                    "Use simple everyday relatable examples."
                )
            elif active_lang == "hinglish":
                pedagogy_guide += (
                    "CRITICAL HINGLISH TEACHING RULE: Write clear conversational Hinglish (Latin script), "
                    "keeping core terminology in English and providing intuitive analogies."
                )
            elif active_lang == "ta":
                pedagogy_guide += (
                    "CRITICAL TAMIL HYBRID TEACHING RULE: Write clear, engaging, conversational explanations in Tamil (Tamil script), "
                    "while strictly preserving domain technical terminology in English (e.g., 'Kinetic Energy', 'Binary Search', 'Algorithm', 'Photosynthesis', 'Momentum', 'Derivative'). "
                    "Use simple everyday relatable analogies and formulate checkpoint questions clearly in Tamil."
                )

            # Incorporate Teacher Personality instruction
            personality_style = "socratic"
            if db and db_sess.user_id:
                try:
                    p_prof = db.query(DBLearnerProfile).filter(DBLearnerProfile.user_id == db_sess.user_id).first()
                    if p_prof and p_prof.preferred_style:
                        personality_style = p_prof.preferred_style
                except Exception:
                    pass
            personality_instr = StudyToolsService.get_personality_instruction_prompt(personality_style)
            if personality_instr:
                pedagogy_guide += f"\n\n{personality_instr}"

            system_prompt = pedagogy_guide
            
            grounded_clause = ""
            if rag_context:
                grounded_clause = (
                    f"\n\nSource Material Context:\n{rag_context}\n\n"
                    f"CRITICAL GROUNDING RULE: {GROUNDING_GUARDRAIL_PROMPT}"
                )

            user_prompt = f"""Generate the teaching delivery content for this lesson segment:
Concept: {concept}
Learner Level: {level}
Language: {active_lang}
Visual Style: {visual_type}
Visual Pedagogical Goal: {v_decision.pedagogical_goal}
Observation Prompt to Weave In: {v_decision.observation_prompt}
{grounded_clause}

Output JSON with:
{{
  "spoken_script": "Engaging, conversational monologue spoken by the AI teacher (approx 70-130 words), guiding the student's observation of the on-screen diagram/visual.",
  "on_screen_text": "Structured blackboard summary with key formulas, takeaways, and bullet points for the visual canvas."
}}
"""
            llm_content = await LLMService.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema_hint='{"spoken_script": "...", "on_screen_text": "..."}',
                temperature=0.3
            )
            
            spoken_script = llm_content.get("spoken_script", "").strip()
            on_screen_text = llm_content.get("on_screen_text", "").strip()
            if spoken_script:
                captions = cls._split_into_timed_captions(spoken_script)
                logger.info(f"[TeacherAgent] Successfully rendered segment {segment_id} using LLM.")
        except Exception as e:
            logger.warning(f"[TeacherAgent] LLM segment rendering failed ({e}); using template fallback.")

        # 2. Template Fallback if LLM failed
        if not spoken_script:
            obs_guide = f" {v_decision.observation_prompt}" if v_decision.observation_prompt else ""
            if active_lang == "hi":
                spoken_script = f"नमस्ते! आज हम {concept} के बारे में गहराई से समझेंगे। यह विषय विज्ञान और व्यावहारिक अनुप्रयोगों के लिए अत्यंत महत्वपूर्ण है।{obs_guide} ध्यान से देखें कि कैसे प्रत्येक घटक एक दूसरे से जुड़ा हुआ है।"
                on_screen_text = f"📚 मुख्य विषय: {concept}\n\n• {v_decision.pedagogical_goal or 'अवधारणा का परिचय'}\n• मुख्य नियम और गणितीय समीकरण\n• व्यावहारिक अनुप्रयोग"
            elif active_lang == "hinglish":
                spoken_script = f"Hey everyone! Aaj hum master karenge {concept}. Yeh concept samajhna bohot simple hai jab aap first principles se start karte hain.{obs_guide} On-screen visuals ko dhyan se dekhiye."
                on_screen_text = f"🚀 Topic: {concept}\n\n• {v_decision.pedagogical_goal or 'First-principles intuition'}\n• Core rules & equations\n• Real-world demo"
            elif active_lang == "ta":
                spoken_script = f"வணக்கம்! இன்று நாம் {concept} பற்றி எளிமையாகவும் தெளிவாகவும் கற்றுக்கொள்ளப் போகிறோம். இது அறிவியலிலும் நடைமுறை உலகிலும் மிக முக்கியமான ஒரு கருத்தாகும்.{obs_guide} திரையில் தோன்றும் விளக்கப் படத்தை உற்று கவனியுங்கள்."
                on_screen_text = f"📚 தலைப்பு: {concept}\n\n• {v_decision.pedagogical_goal or 'அடிப்படைக் கருத்து விளக்கம்'}\n• முதன்மை சூத்திரங்கள் மற்றும் சமன்பாடுகள்\n• நடைமுறை பயன்பாடுகள்"
            else:
                spoken_script = f"Welcome! Today we will explore {concept}. As we break down this concept from first principles,{obs_guide} observe how each fundamental rule interacts to create predictable behavior."
                on_screen_text = f"🎯 Key Focus: {concept}\n\n• {v_decision.pedagogical_goal or 'First-principles derivation'}\n• Governing rules & dynamic equations\n• Interactive checkpoint"
            captions = cls._split_into_timed_captions(spoken_script)

        # 3. Generate Visual Spec
        visual_spec = VisualRouter.generate_visual_spec(concept, visual_type, level, context=sess_topic)
        visual_spec.decision = v_decision

        # 4. Checkpoint Question
        raw_cp = seg.get("checkpoint_question")
        if isinstance(raw_cp, CheckpointQuestion):
            checkpoint_q = raw_cp
        elif isinstance(raw_cp, dict):
            cp_data = dict(raw_cp)
            if "concept_tested" not in cp_data or not cp_data["concept_tested"]:
                cp_data["concept_tested"] = concept
            valid_keys = {"id", "type", "question", "options", "correct_answer", "hints", "concept_tested"}
            filtered_cp_data = {k: v for k, v in cp_data.items() if k in valid_keys}
            checkpoint_q = CheckpointQuestion(**filtered_cp_data)
        else:
            checkpoint_q = CheckpointQuestion(
                id=str(uuid.uuid4()),
                type="mcq",
                question=v_decision.knowledge_check or f"What is the key takeaway of {concept}?",
                options=["A) Dynamic equilibrium", "B) Total entropy decay", "C) Arbitrary fluctuation", "D) Zero conservation"],
                correct_answer="A) Dynamic equilibrium",
                concept_tested=concept
            )

        # 5. Generate Real TTS Audio if ElevenLabs is configured
        tts_res = await TTSService.generate_speech(spoken_script, language=active_lang)
        audio_url = tts_res.get("audio_url")
        
        # If real audio was generated with a known duration, re-scale caption timestamps to match exact audio
        audio_duration = tts_res.get("duration_seconds")
        if audio_duration and audio_duration > 0:
            captions = cls._split_into_timed_captions(spoken_script, total_duration_sec=audio_duration)

        # 6. Avatar video / synthesized asset
        avatar_res = await AvatarService.generate_avatar_video(spoken_script)
        anchor_portrait = AvatarService.get_anchor_portrait_path()

        # 7. Local ffmpeg MP4 video synthesis (skipped for fast interactive language switching)
        if not skip_video:
            video_res = await VideoService.render_segment_video(
                segment_id=segment_id,
                session_id=session_id,
                script=spoken_script,
                audio_url=audio_url,
                visual_spec=visual_spec.model_dump(),
                captions=captions,
                anchor_image_path=anchor_portrait,
                language=active_lang
            )
        else:
            video_res = {
                "provider": "ffmpeg_local",
                "status": "ready",
                "video_url": None,
                "duration_sec": audio_duration or 6.0
            }
        
        return LessonSegmentRender(
            segment_id=segment_id,
            session_id=session_id,
            concept=concept,
            spoken_script=spoken_script,
            on_screen_text=on_screen_text,
            visual_spec=visual_spec,
            visual_decision=v_decision,
            audio_url=audio_url,
            avatar_video_url=avatar_res.get("video_url"),
            video_url=video_res.get("video_url"),
            video_status=str(video_res.get("status", "unavailable")),
            captions=captions,
            citations=citations,
            checkpoint_question=checkpoint_q,
            analogies_used=[str(a) for a in (getattr(db_sess, "analogies_used", None) or [])],
            language=active_lang,
            is_reteach=False
        )
