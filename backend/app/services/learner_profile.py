import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ..database import (
    DBLearnerProfile,
    DBLearningPath,
    DBLessonSession,
    DBQuizAttempt,
    DBLearningReport,
    DBCheckpointAttempt
)
from ..models.schemas import (
    LearnerProfile,
    LearnerProfileCreate,
    RelevantLearnerContext,
    LearningReport,
    ConceptMasteryItem
)

logger = logging.getLogger("sahayak.learner_profile")

class LearnerProfileService:
    @classmethod
    def get_or_create_profile(cls, user_id: str, db: Session) -> DBLearnerProfile:
        """
        Retrieves existing learner profile or creates a clean new profile.
        """
        p = db.query(DBLearnerProfile).filter(DBLearnerProfile.user_id == user_id).first()
        if not p:
            name = user_id.replace("user-", "").replace("-", " ").title() if user_id.startswith("user-") else "Learner"
            p = DBLearnerProfile(
                user_id=user_id,
                name=name,
                level="beginner",
                goal="understand_concept",
                preferred_style="visual",
                language="en",
                history_json=[],
                mastery_json={}
            )
            db.add(p)
            db.commit()
            db.refresh(p)
        return p

    @classmethod
    def get_full_learner_profile(cls, user_id: str, db: Session) -> LearnerProfile:
        """
        Aggregates granular concept-level mastery, active curriculum paths,
        learning history, and next recommended actions into a unified LearnerProfile.
        """
        p = cls.get_or_create_profile(user_id, db)
        
        history: List[Dict[str, Any]] = list(p.history_json) if isinstance(p.history_json, list) else []
        mastery_map: Dict[str, Dict[str, Any]] = dict(p.mastery_json) if isinstance(p.mastery_json, dict) else {}

        # 1. Classify concepts by granular mastery state
        strong_concepts: List[str] = []
        weak_concepts: List[str] = []
        misunderstood_concepts: List[str] = []
        concepts_studied: List[str] = list(mastery_map.keys())

        for concept, data in mastery_map.items():
            if isinstance(data, dict):
                m_state = data.get("mastery", "developing")
                misconceptions = data.get("misconceptions", [])
                
                if m_state == "misunderstood" or (misconceptions and len(misconceptions) > 0):
                    if concept not in misunderstood_concepts:
                        misunderstood_concepts.append(concept)
                
                if m_state in ["mastered", "strong"]:
                    if concept not in strong_concepts:
                        strong_concepts.append(concept)
                elif m_state in ["weak", "misunderstood"]:
                    if concept not in weak_concepts:
                        weak_concepts.append(concept)

        # Also incorporate score history if mastery map is sparse
        topics_studied: List[str] = []
        for h in history:
            t = h.get("topic")
            if t and t not in topics_studied:
                topics_studied.append(t)
            score = h.get("score", 0)
            if score >= 85 and t and t not in strong_concepts:
                strong_concepts.append(t)
            elif score < 70 and t and t not in weak_concepts:
                weak_concepts.append(t)

        # 2. Retrieve active learning paths
        active_db_paths = db.query(DBLearningPath).filter(DBLearningPath.user_id == user_id).all()
        active_paths_list: List[Dict[str, Any]] = []
        completed_topics: List[str] = []
        in_progress_topics: List[str] = []
        current_topic: Optional[str] = None
        current_path_id: Optional[str] = None
        recommended_next_topic: Optional[str] = None
        recommended_action: Optional[str] = None
        prerequisite_gaps: List[Dict[str, Any]] = []

        for lp in active_db_paths:
            dag = lp.dag_json if isinstance(lp.dag_json, dict) else {}
            nodes = dag.get("nodes", []) if isinstance(dag, dict) else []
            completed_nodes = [n.get("title") for n in nodes if isinstance(n, dict) and n.get("completed")]
            in_prog_nodes = [n.get("title") for n in nodes if isinstance(n, dict) and not n.get("completed")]
            
            active_paths_list.append({
                "topic_id": lp.topic_id,
                "title": lp.title,
                "progress_percentage": lp.progress_percentage,
                "total_nodes": len(nodes),
                "completed_nodes": len(completed_nodes)
            })

            if lp.progress_percentage >= 100.0:
                completed_topics.append(lp.title or lp.topic_id)
            else:
                in_progress_topics.append(lp.title or lp.topic_id)
                if not current_topic and in_prog_nodes:
                    current_topic = in_prog_nodes[0]
                    current_path_id = lp.topic_id

        # 3. Determine next recommended action
        if weak_concepts or misunderstood_concepts:
            target_weak = misunderstood_concepts[0] if misunderstood_concepts else weak_concepts[0]
            recommended_action = "REVISE_CONCEPT"
            recommended_next_topic = f"Revision: {target_weak}"
            prerequisite_gaps.append({
                "concept": target_weak,
                "status": "misunderstood" if target_weak in misunderstood_concepts else "weak",
                "recommended_action": f"Revisit foundational concepts and practice targeted problems for {target_weak}."
            })
        elif current_topic:
            recommended_action = "CONTINUE_CURRENT_TOPIC"
            recommended_next_topic = current_topic
        elif strong_concepts:
            recommended_action = "MOVE_TO_NEXT_TOPIC"
            recommended_next_topic = f"Advanced Applications of {strong_concepts[-1]}"
        else:
            recommended_action = "MOVE_TO_NEXT_TOPIC"
            recommended_next_topic = "Foundational Principles"

        return LearnerProfile(
            user_id=p.user_id,
            name=p.name or "Learner",
            level=p.level or "beginner",
            goal=p.goal or "understand_concept",
            preferred_style=p.preferred_style or "visual",
            language=p.language or "en",
            time_budget_minutes=20,
            depth="standard",
            topics_studied=topics_studied,
            concepts_studied=concepts_studied,
            scores_history=history,
            strong_concepts=strong_concepts,
            weak_concepts=weak_concepts,
            misunderstood_concepts=misunderstood_concepts,
            concept_masteries=mastery_map,
            current_learning_path_id=current_path_id,
            current_topic=current_topic,
            completed_topics=completed_topics,
            in_progress_topics=in_progress_topics,
            recommended_next_topic=recommended_next_topic,
            recommended_action=recommended_action,
            prerequisite_gaps=prerequisite_gaps,
            active_paths=active_paths_list
        )

    @classmethod
    def update_profile_from_assessment(
        cls,
        user_id: str,
        report: LearningReport,
        db: Session
    ) -> LearnerProfile:
        """
        Updates the persistent learner model with multi-source evidence from
        checkpoint logs, diagnostic grading, concept mastery, and identified misconceptions.
        """
        p = cls.get_or_create_profile(user_id, db)
        
        # 1. Update History
        hist = list(p.history_json) if isinstance(p.history_json, list) else []
        hist.append({
            "session_id": report.session_id,
            "topic": report.topic,
            "score": report.score_percent,
            "date": report.generated_at.isoformat() if hasattr(report.generated_at, "isoformat") else str(report.generated_at),
            "concepts_mastered": [cm.concept for cm in report.concept_masteries if cm.mastery in ["mastered", "strong"]],
            "concepts_weak": [cm.concept for cm in report.concept_masteries if cm.mastery in ["weak", "misunderstood"]],
            "misconceptions": report.misconceptions_encountered
        })
        p.history_json = hist

        # 2. Update Granular Concept Mastery Map
        mastery_map = dict(p.mastery_json) if isinstance(p.mastery_json, dict) else {}
        for cm in report.concept_masteries:
            existing = mastery_map.get(cm.concept, {})
            attempts = existing.get("attempts", 0) + 1
            
            mastery_map[cm.concept] = {
                "concept": cm.concept,
                "mastery": cm.mastery,
                "confidence": cm.confidence,
                "assessment_score": cm.score_percent,
                "attempts": attempts,
                "last_assessed_at": report.generated_at.isoformat() if hasattr(report.generated_at, "isoformat") else str(report.generated_at),
                "misconceptions": cm.misconceptions,
                "evidence": cm.evidence or [f"Assessed on {report.topic} ({report.score_percent}%)"]
            }
        
        p.mastery_json = mastery_map
        db.commit()
        db.refresh(p)

        logger.info(f"[LearnerProfileService] Updated profile for {user_id}: {len(report.concept_masteries)} concepts recorded.")
        return cls.get_full_learner_profile(user_id, db)

    @classmethod
    def get_relevant_learner_context(
        cls,
        user_id: str,
        target_topic: str,
        db: Session
    ) -> RelevantLearnerContext:
        """
        Synthesizes a compact, actionable learner context for the AI Teacher lesson planner.
        Extracts prerequisite mastery, prior misconceptions, and tailored pedagogical instructions.
        """
        profile = cls.get_full_learner_profile(user_id, db)
        
        pedagogical_instructions: List[str] = []
        prerequisite_status: Dict[str, str] = {}

        # Scan for target topic or related concept misconceptions
        topic_lower = target_topic.lower()
        matched_misconceptions: List[str] = []
        for concept, data in profile.concept_masteries.items():
            c_low = concept.lower()
            if c_low in topic_lower or topic_lower in c_low or any(w in topic_lower for w in c_low.split()):
                prerequisite_status[concept] = data.get("mastery", "developing")
                for m in data.get("misconceptions", []):
                    if m not in matched_misconceptions:
                        matched_misconceptions.append(m)

        # Generate targeted pedagogical adaptations
        if matched_misconceptions:
            pedagogical_instructions.append(
                f"PRIOR MISCONCEPTION ALERT: The student previously struggled with: {'; '.join(matched_misconceptions)}. "
                "Explicitly clarify this distinction using a simple analogy (e.g. water pipe flow vs pressure) and verify understanding with a checkpoint question."
            )

        if profile.level == "advanced" or (len(profile.strong_concepts) >= 3 and any(s.lower() in topic_lower for s in profile.strong_concepts)):
            pedagogical_instructions.append(
                "ADVANCED LEARNER DETECTED: Student has demonstrated mastery of core foundations. "
                "Skip elementary definitions; compress basic segments and focus immediately on rigorous derivations, edge-case analysis, and practical applications."
            )
        elif profile.level == "beginner":
            pedagogical_instructions.append(
                "BEGINNER LEARNER DETECTED: Ground each concept with intuitive real-world analogies before mathematical formulations."
            )

        recent_perf: Dict[str, Any] = {}
        if profile.scores_history:
            recent_perf = profile.scores_history[-1]

        return RelevantLearnerContext(
            user_id=user_id,
            student_level=profile.level,
            target_topic=target_topic,
            goal=profile.goal,
            preferred_style=profile.preferred_style,
            strong_concepts=profile.strong_concepts,
            weak_concepts=profile.weak_concepts,
            misconceptions=matched_misconceptions or profile.misunderstood_concepts,
            prerequisite_status=prerequisite_status,
            recent_performance=recent_perf,
            pedagogical_instructions=pedagogical_instructions
        )

    @classmethod
    def get_learning_history(cls, user_id: str, db: Session) -> List[Dict[str, Any]]:
        """
        Returns full chronological learning trajectory with scores and evidence details.
        """
        profile = cls.get_or_create_profile(user_id, db)
        history: List[Dict[str, Any]] = list(profile.history_json) if isinstance(profile.history_json, list) else []
        return sorted(history, key=lambda x: x.get("date", ""), reverse=True)
