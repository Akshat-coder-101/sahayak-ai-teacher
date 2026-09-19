import uuid
import random
import logging
import asyncio
import re
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session
from ..database import DBLessonSession, DBCheckpointAttempt
from ..models.schemas import (
    InteractionResponse, 
    CheckpointQuestion, 
    LessonSegmentRender, 
    CaptionItem,
    TeachingDecisionState
)
from .visual_router import VisualRouter
from .tts import TTSService
from .avatar import AvatarService
from .llm import LLMService, LLMUnavailable

logger = logging.getLogger("sahayak.evaluator")

class EvaluatorService:
    ANALOGIES_BANK = {
        "networking": [
            ("A city postal highway with local mail vans, distribution postal hubs, and interstate trucks delivering sealed envelopes by zip codes.", "Think of computer networking like postal delivery: your host terminal writes the destination IP address on an envelope, the local switch directs it to your building's mailbox, and the gateway router sends it across the national highway."),
            ("A central airport air-traffic control and luggage sorting terminal routing tagged suitcases to designated flight gates.", "Like airport luggage sorting: suitcases are tagged with destination codes (IP/MAC), conveyor belts (switches) sort them to the right carousel, and international flights (routers) carry them across continents."),
            ("A secure office telephone switchboard connecting extension numbers to outside world lines.", "Think of a company PBX switchboard: local extension calls stay inside the building via the switch, while external numbers get forwarded through the gateway trunk line.")
        ],
        "physics": [
            ("A roller coaster cart on a steep hill exchanging potential gravitational energy into kinetic speed.", "Imagine a roller coaster at the crest: pure potential energy, converted into rushing kinetic speed as it plunges."),
            ("A compressed spring storing mechanical strain until released to push a block.", "Think of a tightly coiled mattress spring: pushing on it stores potential energy that snaps into motion."),
            ("A water reservoir behind a high dam spinning a turbine as water cascades down.", "Think of a hydroelectric dam holding a mountain reservoir: height creates water pressure that spins turbines into electrical work."),
            ("Stretching a rubber band between two fingers before letting it snap forward.", "Like drawing a slingshot band: muscular work becomes elastic potential energy that hurls the stone.")
        ],
        "biology": [
            ("A bustling city airport where security gates regulate passport entry.", "Consider a cell membrane like an international airport gate with biometric passports filtering authorized travelers."),
            ("A smart modern factory with a central blueprint library and assembly conveyor lines.", "Think of the nucleus as the head architect's blueprint vault, with ribosomes serving as precision assembly robots."),
            ("A rechargeable battery dock recharging mobile power banks for night shifts.", "The mitochondrion functions like a solar-charged power station synthesizing ATP currency for cellular work."),
            ("A fortress castle surrounded by a moat with drawbridges checking cargo wagons.", "Picture a castle wall with specialized drawbridges that open only when specific heraldic keys arrive.")
        ],
        "programming": [
            ("A kitchen chef following a precise recipe card with measurable ingredients.", "Think of an algorithm like a master chef's numbered recipe where each step must be executed in exact sequential order."),
            ("A post office filing cabinet sorting mail envelopes into indexed cubbies.", "Consider arrays and hash maps like labeled cubbies in a sorting room where postal codes instantly locate packages."),
            ("An assembly line conveyor belt where each station performs one deterministic transformation.", "Imagine a factory belt: raw parts enter, each station does one specific transformation, and finished goods emerge."),
            ("A library catalog index card pointing readers directly to shelf numbers.", "Pointers and references act like library catalog numbers: they don't hold the book itself, but tell you exactly where it lives.")
        ],
        "general": [
            ("A traffic roundabout managing smooth multi-lane vehicle flow without collisions.", "Like a well-designed roundabout where traffic smoothly self-regulates through yield rules."),
            ("A balance scale where adding weight on one pan requires matching weight on the other.", "Like an old-fashioned balance beam: every action on one side requires a balancing force on the other."),
            ("A musical symphony where each instrument plays its part to create harmonious melody.", "Think of an orchestra where rhythm, pitch, and timbre must coordinate synchronously to produce harmony.")
        ]
    }

    @classmethod
    def _detect_domain(cls, concept: str) -> str:
        c = concept.lower()
        if any(w in c for w in [
            "network", "packet", "router", "switch", "cisco", "tracer", "topology", 
            "ip", "tcp", "udp", "protocol", "ethernet", "lan", "wan", "vlan", "port", 
            "socket", "subnet", "dhcp", "dns", "http", "lab manual", "simulation"
        ]):
            return "networking"
        elif any(w in c for w in ["force", "newton", "gravity", "energy", "velocity", "wave", "quantum", "thermo"]):
            return "physics"
        elif any(w in c for w in ["cell", "dna", "bio", "organ", "plant", "heart", "mitochondria", "enzyme"]):
            return "biology"
        elif any(w in c for w in ["code", "python", "algorithm", "data", "tree", "loop", "function", "variable"]):
            return "programming"
        return "general"

    @classmethod
    def get_fresh_analogy(cls, concept: str, used_analogies: List[str]) -> Tuple[str, str]:
        domain = cls._detect_domain(concept)
        available = [item for item in cls.ANALOGIES_BANK.get(domain, cls.ANALOGIES_BANK["general"]) if item[0] not in used_analogies]
        if not available:
            available = [item for item in cls.ANALOGIES_BANK["general"] if item[0] not in used_analogies]
        if not available:
            return (f"A dynamic self-balancing feedback loop in {concept}", f"Think of a precision thermostat: any divergence from the setpoint triggers an immediate restorative correction in {concept}.")
        return random.choice(available)

    @classmethod
    def _get_distinct_visual_type(cls, prev_visual_type: str, concept: str) -> str:
        """Ensures the retry visual type is completely different from the initial slide."""
        prev = (prev_visual_type or "labeled-diagram").lower()
        domain = cls._detect_domain(concept)
        
        if "diagram" in prev or "topology" in prev:
            return "equation/graph" if domain in ["physics", "general"] else ("code+execution" if domain in ["programming", "networking"] else "timeline/map")
        elif "equation" in prev or "graph" in prev:
            return "code+execution" if domain in ["programming", "networking"] else "labeled-diagram"
        elif "code" in prev:
            return "network-topology" if domain == "networking" else "equation/graph"
        elif "timeline" in prev or "map" in prev:
            return "labeled-diagram"
        return "equation/graph"

    @classmethod
    async def evaluate_student_answer(
        cls,
        session_id: str,
        segment_id: int,
        student_answer: str,
        is_demo_mode: bool,
        force_misconception: bool,
        db: Session
    ) -> InteractionResponse:
        session = db.query(DBLessonSession).filter(DBLessonSession.id == session_id).first()
        topic = session.topic if session else "The concept"
        plan_json = session.plan_json if session and session.plan_json else {}
        segments = plan_json.get("segments", []) if isinstance(plan_json, dict) else []
        
        current_segment = next((s for s in segments if s.get("id") == segment_id), None)
        concept = current_segment.get("concept", topic) if current_segment else topic
        level = current_segment.get("depth", "beginner") if current_segment else "beginner"
        prev_visual_type = current_segment.get("visual_type", "labeled-diagram") if current_segment else "labeled-diagram"
        question_data = current_segment.get("checkpoint_question", {}) if current_segment else {}
        question_text = question_data.get("question", "")
        correct_answer = question_data.get("correct_answer", "")
        used_analogies = list(session.analogies_used or []) if session else []
        language = session.language if session else "en"

        # 1. Check deliberate judging/demo triggers
        trigger_demo_reteach = force_misconception or (is_demo_mode and "correct" not in student_answer.lower())

        # 2. FAST-PATH: Deterministic Checkpoint Answer Matching (< 20ms response time)
        # Evaluates MCQ options and direct keyword answers instantly without waiting for external LLM timeouts
        ans_clean = student_answer.strip().lower()
        corr_clean = (correct_answer or "").strip().lower()

        is_direct_match = False
        if corr_clean:
            if ans_clean == corr_clean:
                is_direct_match = True
            elif len(ans_clean) >= 3 and ans_clean in corr_clean:
                is_direct_match = True
            elif len(corr_clean) >= 3 and corr_clean in ans_clean:
                is_direct_match = True
            else:
                # Strip MCQ prefix (e.g. "b) cisco packet tracer..." -> "cisco packet tracer...")
                clean_a = re.sub(r'^[a-d]\s*[\)\.\:\-]\s*', '', ans_clean).strip()
                clean_c = re.sub(r'^[a-d]\s*[\)\.\:\-]\s*', '', corr_clean).strip()
                if clean_a and clean_c and (clean_a == clean_c or clean_a in clean_c or clean_c in clean_a):
                    is_direct_match = True
                
                # Check option letter match (e.g. "B" matching "B) ...")
                a_letter = ans_clean[0] if (len(ans_clean) >= 2 and ans_clean[1] in [')', '.', ':', ' ']) else (ans_clean if len(ans_clean) == 1 else "")
                c_letter = corr_clean[0] if (len(corr_clean) >= 2 and corr_clean[1] in [')', '.', ':', ' ']) else (corr_clean if len(corr_clean) == 1 else "")
                if a_letter and c_letter and a_letter == c_letter:
                    is_direct_match = True

        if is_direct_match and not trigger_demo_reteach:
            feedback = f"Correct! Excellent work. You selected the right answer: **{student_answer}**."
            db_attempt = DBCheckpointAttempt(
                id=str(uuid.uuid4()),
                session_id=session_id,
                segment_id=segment_id,
                question_text=question_text,
                student_answer=student_answer,
                classification="correct",
                feedback=feedback
            )
            db.add(db_attempt)
            db.commit()

            decision_state = TeachingDecisionState(
                current_concept=concept,
                student_understanding="mastery",
                confidence=0.95,
                action="advance",
                reason="Student demonstrated clear conceptual understanding by selecting the correct grounded option.",
                next_step="next_concept" if segment_id < len(segments) else "final_assessment",
                remaining_time_minutes=max(1, (len(segments) - segment_id) * 4)
            )

            return InteractionResponse(
                action="advance",
                classification="correct",
                feedback=feedback,
                next_segment_id=segment_id + 1 if segment_id < len(segments) else None,
                decision_state=decision_state
            )

        # 3. LLM Diagnostic Evaluation (Bounded with strict 4.0s timeout for open-ended or wrong answers)
        try:
            system_prompt = (
                "You are an expert diagnostic cognitive evaluator in an AI teaching system. "
                "Analyze student answers with pedagogical precision. "
                "Classify understanding into: 'correct', 'partially_correct', 'misconception', or 'no_understanding'. "
                "If there is a misconception, pinpoint the exact underlying cognitive fault (misconception_name specific to this answer) "
                "and provide a brand new, unused intuitive analogy and concrete real-world example to remediate it."
            )

            user_prompt = f"""Evaluate this student checkpoint response:
Concept Taught: {concept}
Learner Level: {level}
Language: {language}
Question Asked: {question_text}
Correct Answer: {correct_answer}
Student's Actual Answer: "{student_answer}"
Previously Used Analogies (DO NOT REPEAT): {used_analogies}

Output JSON schema:
{{
  "classification": "correct | partially_correct | misconception | no_understanding",
  "feedback": "Encouraging, pedagogical response directly addressing the student's answer.",
  "misconception_name": "Precise name of this specific misunderstanding, or empty if correct",
  "why_wrong": "Explanation of why the student's reasoning failed, or empty if correct",
  "remediation_explanation": "First-principles intuitive clarification to resolve the misunderstanding",
  "new_analogy": "Brand new, creative analogy explaining the concept without repeating previous analogies",
  "new_example": "Concrete everyday scenario demonstrating the correct intuition",
  "followup_question": {{
    "question": "A fresh checkpoint question testing the corrected intuition?",
    "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "correct_answer": "A) The exact text of the correct option",
    "hints": ["Helpful hint"]
  }}
}}
"""
            llm_eval = await asyncio.wait_for(
                LLMService.generate_json(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    schema_hint="Diagnostic evaluation JSON with classification, feedback, misconception_name, new_analogy, followup_question",
                    temperature=0.2
                ),
                timeout=4.5
            )

            classification = llm_eval.get("classification", "misconception").lower()
            
            # If classified as correct or partially_correct (when acceptable)
            if classification in ["correct", "partially_correct"] and not force_misconception:
                feedback = llm_eval.get("feedback", f"Excellent work! Your understanding of **{concept}** is correct.")
                
                db_attempt = DBCheckpointAttempt(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    segment_id=segment_id,
                    question_text=question_text,
                    student_answer=student_answer,
                    classification=classification,
                    feedback=feedback
                )
                db.add(db_attempt)
                db.commit()

                decision_state = TeachingDecisionState(
                    current_concept=concept,
                    student_understanding="mastery",
                    confidence=0.92,
                    action="advance",
                    reason="Student demonstrated clear conceptual understanding of the principles.",
                    next_step="next_concept" if segment_id < len(segments) else "final_assessment",
                    remaining_time_minutes=max(1, (len(segments) - segment_id) * 4)
                )

                return InteractionResponse(
                    action="advance",
                    classification="correct",
                    feedback=feedback,
                    next_segment_id=segment_id + 1 if segment_id < len(segments) else None,
                    decision_state=decision_state
                )
            
            # Misconception path with LLM data
            misconception_name = llm_eval.get("misconception_name") or f"Misunderstanding governing dynamics in {concept}"
            feedback = llm_eval.get("feedback") or f"Great try! You touched upon an interesting nuance in **{concept}**. Let's examine this from a fresh angle."
            new_analogy = llm_eval.get("new_analogy") or f"Think of {concept} like a regulated feedback circuit."
            new_example = llm_eval.get("new_example") or f"Notice how balancing forces prevents runaway deviation."
            remediation = llm_eval.get("remediation_explanation") or new_analogy

            # Append analogy to session dedup list
            if new_analogy not in used_analogies:
                used_analogies.append(new_analogy[:60])
            if session:
                session.analogies_used = list(set(used_analogies))
                db.commit()

            fq = llm_eval.get("followup_question") or {}
            fq_options = fq.get("options", [
                f"A) {concept} responds proportionally to maintain equilibrium",
                f"B) {concept} completely halts all energy conversion",
                f"C) Fluctuations grow without upper bounds",
                f"D) Internal parameters are non-deterministic"
            ])
            fq_correct = fq.get("correct_answer") or fq_options[0]

            new_checkpoint_q = CheckpointQuestion(
                type="mcq",
                question=fq.get("question", f"Applying our new insight, how does {concept} maintain stability?"),
                options=fq_options,
                correct_answer=fq_correct,
                hints=fq.get("hints", ["Think about the balanced feedback principle."]),
                concept_tested=concept
            )

            spoken_script = f"Let's look at {concept} with a fresh model. {remediation} {new_example} Notice how this resolves the edge case."
            on_screen_text = f"💡 Reteach Focus: {concept}\n\n• Diagnosed: {misconception_name}\n• Insight: {new_analogy[:80]}\n• Concrete Case: {new_example[:80]}"
            
            # Switch to a VISIBLY DIFFERENT visual type on retry
            new_visual_type = cls._get_distinct_visual_type(prev_visual_type, concept)
            visual_spec = VisualRouter.generate_visual_spec(f"[Adaptive Reteach] {concept}", new_visual_type, level)

            audio_url = None
            try:
                tts_res = await asyncio.wait_for(
                    TTSService.generate_speech(spoken_script, language=language),
                    timeout=2.0
                )
                audio_url = tts_res.get("audio_url")
            except Exception as tts_err:
                logger.warning(f"[EvaluatorService] Reteach TTS timed out or skipped: {tts_err}")
            
            # Split captions
            sentences = [s.strip() for s in spoken_script.split(".") if s.strip()]
            captions = [
                CaptionItem(start_sec=0.0, end_sec=4.0, text=sentences[0] if len(sentences) > 0 else f"Let's look at {concept}."),
                CaptionItem(start_sec=4.0, end_sec=8.5, text=sentences[1] if len(sentences) > 1 else new_analogy[:70]),
                CaptionItem(start_sec=8.5, end_sec=13.0, text=sentences[2] if len(sentences) > 2 else new_example[:70])
            ]

            reteach_segment = LessonSegmentRender(
                segment_id=segment_id,
                session_id=session_id,
                concept=concept,
                spoken_script=spoken_script,
                on_screen_text=on_screen_text,
                visual_spec=visual_spec,
                audio_url=audio_url,
                captions=captions,
                checkpoint_question=new_checkpoint_q,
                analogies_used=used_analogies,
                language=language,
                is_reteach=True
            )

            db_attempt = DBCheckpointAttempt(
                id=str(uuid.uuid4()),
                session_id=session_id,
                segment_id=segment_id,
                question_text=question_text,
                student_answer=student_answer,
                classification="misconception",
                feedback=feedback
            )
            db.add(db_attempt)
            db.commit()

            decision_state = TeachingDecisionState(
                current_concept=concept,
                student_understanding="misconception",
                confidence=0.78,
                action="simplify",
                reason=misconception_name,
                next_step="explain_with_analogy",
                remaining_time_minutes=max(1, (len(segments) - segment_id + 1) * 4)
            )

            return InteractionResponse(
                action="reteach",
                classification="misconception",
                feedback=feedback,
                misconception_name=misconception_name,
                new_analogy=new_analogy,
                new_example=new_example,
                new_checkpoint_question=new_checkpoint_q,
                reteach_segment=reteach_segment,
                next_segment_id=segment_id,
                decision_state=decision_state
            )

        except Exception as e:
            logger.warning(f"[EvaluatorService] LLM evaluation failed ({e}); switching to heuristic evaluation.")

        # 3. Rule-Based Fallback (Offline / Demo Mode)
        ans_lower = student_answer.strip().lower()
        corr_lower = (correct_answer or "").strip().lower()

        is_exact_or_substring = False
        if corr_lower:
            if ans_lower == corr_lower:
                is_exact_or_substring = True
            elif len(ans_lower) >= 4 and ans_lower in corr_lower:
                is_exact_or_substring = True
            elif len(corr_lower) >= 4 and corr_lower in ans_lower:
                is_exact_or_substring = True
            elif len(ans_lower) <= 2 and corr_lower.startswith(ans_lower):
                is_exact_or_substring = True
            elif ans_lower in ["yes", "correct"] and corr_lower in ["yes", "correct", "true"]:
                is_exact_or_substring = True

        if is_exact_or_substring and not trigger_demo_reteach:
            feedback = f"Outstanding work! Your understanding of **{concept}** is spot on. You correctly recognized the underlying principles."
            db_attempt = DBCheckpointAttempt(
                id=str(uuid.uuid4()),
                session_id=session_id,
                segment_id=segment_id,
                question_text=question_text,
                student_answer=student_answer,
                classification="correct",
                feedback=feedback
            )
            db.add(db_attempt)
            db.commit()

            decision_state = TeachingDecisionState(
                current_concept=concept,
                student_understanding="mastery",
                confidence=0.90,
                action="advance",
                reason="Student selected the correct grounded definition.",
                next_step="next_concept" if segment_id < len(segments) else "final_assessment",
                remaining_time_minutes=max(1, (len(segments) - segment_id) * 4)
            )

            return InteractionResponse(
                action="advance",
                classification="correct",
                feedback=feedback,
                next_segment_id=segment_id + 1 if segment_id < len(segments) else None,
                decision_state=decision_state
            )

        # Fallback Reteach with curated analogies bank
        misconception_name = f"Confusing Static Equilibrium with Dynamic Flux in {concept}"
        analogy_title, analogy_text = cls.get_fresh_analogy(concept, used_analogies)
        used_analogies.append(analogy_title)
        if session:
            session.analogies_used = list(set(used_analogies))
            db.commit()

        new_example = f"Consider a real-world case: pedaling a bicycle on flat asphalt versus uphill. On flat road, momentum carries you forward; uphill requires continuous force application."
        feedback = f"Great try! You hit a very common nuance in **{concept}**. Let's unpack this with a fresh perspective."

        new_checkpoint_q = CheckpointQuestion(
            type="mcq",
            question=f"Based on our new model ({analogy_title}), what happens when driving forces temporarily double?",
            options=[
                "A) The rate of response scales proportionally",
                "B) The system immediately reaches infinite potential",
                "C) Nothing changes because capacity is fixed",
                "D) The energy is completely lost to heat"
            ],
            correct_answer="A) The rate of response scales proportionally",
            hints=["Think of the linear proportionality discussed in the fresh analogy."],
            concept_tested=concept
        )

        spoken_script = f"Let's look at {concept} with a fresh perspective. {analogy_text} {new_example} Notice how the relationship holds true across all conditions."
        on_screen_text = f"💡 Reteach Focus: {concept}\n\n• New Model: {analogy_title}\n• Key Insight: Dynamic response scales directly with driving stimulus."
        
        # Switch to a VISIBLY DIFFERENT visual type on retry
        new_visual_type = cls._get_distinct_visual_type(prev_visual_type, concept)
        visual_spec = VisualRouter.generate_visual_spec(f"[Remediation Blackboard] {concept}", new_visual_type, "beginner")
        
        reteach_segment = LessonSegmentRender(
            segment_id=segment_id,
            session_id=session_id,
            concept=concept,
            spoken_script=spoken_script,
            on_screen_text=on_screen_text,
            visual_spec=visual_spec,
            captions=[
                CaptionItem(start_sec=0.0, end_sec=3.5, text=f"Let's look at {concept} with a fresh analogy."),
                CaptionItem(start_sec=3.5, end_sec=8.0, text=analogy_text[:70] + "..."),
                CaptionItem(start_sec=8.0, end_sec=12.0, text=new_example[:70] + "...")
            ],
            checkpoint_question=new_checkpoint_q,
            analogies_used=used_analogies,
            language=session.language if session else "en",
            is_reteach=True
        )

        db_attempt = DBCheckpointAttempt(
            id=str(uuid.uuid4()),
            session_id=session_id,
            segment_id=segment_id,
            question_text=question_text,
            student_answer=student_answer,
            classification="misconception",
            feedback=feedback
        )
        db.add(db_attempt)
        db.commit()

        decision_state = TeachingDecisionState(
            current_concept=concept,
            student_understanding="misconception",
            confidence=0.75,
            action="simplify",
            reason=misconception_name,
            next_step="explain_with_analogy",
            remaining_time_minutes=max(1, (len(segments) - segment_id + 1) * 4)
        )

        return InteractionResponse(
            action="reteach",
            classification="misconception",
            feedback=feedback,
            misconception_name=misconception_name,
            new_analogy=analogy_text,
            new_example=new_example,
            new_checkpoint_question=new_checkpoint_q,
            reteach_segment=reteach_segment,
            next_segment_id=segment_id,
            decision_state=decision_state
        )
