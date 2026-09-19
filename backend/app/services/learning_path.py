import uuid
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from ..database import DBLearningPath, DBQuizAttempt, DBLessonSession, DBLearningReport
from ..models.schemas import (
    LearningPath,
    PathNode,
    LearnerProfile,
    LearningRecommendationResult,
    LearningReport
)
from .learner_profile import LearnerProfileService
from .llm import LLMService

logger = logging.getLogger("sahayak.learning_path")

# Specialized curriculum templates for standard subjects & dynamic cognitive synthesis for arbitrary topics
DOMAIN_CURRICULA: Dict[str, Dict[str, Any]] = {
    "machine-learning": {
        "title": "Machine Learning & Statistical Pattern Recognition",
        "description": "Prerequisite-ordered curriculum progressing from Python & mathematical foundations to supervised algorithms, model evaluation, and deep neural architectures.",
        "nodes": [
            {
                "id": "node-1",
                "title": "1. Python Fundamentals & Numerical Arrays",
                "description": "NumPy vectorization, matrix broadcasting, data structures, and algorithmic foundations.",
                "estimated_hours": 1.5,
                "difficulty": "beginner",
                "prerequisites": [],
                "concepts": ["Python Fundamentals", "NumPy", "Vectorization"],
                "objectives": ["Implement vectorized operations", "Master multi-dimensional array slicing"]
            },
            {
                "id": "node-2",
                "title": "2. Mathematics for ML: Linear Algebra & Calculus",
                "description": "Dot products, matrix transformations, eigenvalues, partial derivatives, and gradient vectors.",
                "estimated_hours": 2.5,
                "difficulty": "beginner",
                "prerequisites": ["node-1"],
                "concepts": ["Linear Algebra", "Matrix Multiplication", "Gradients"],
                "objectives": ["Compute gradients of loss functions", "Understand high-dimensional projections"]
            },
            {
                "id": "node-3",
                "title": "3. Data Preprocessing & Feature Engineering",
                "description": "Standardization, missing value imputation, one-hot encoding, and feature correlation matrices.",
                "estimated_hours": 2.0,
                "difficulty": "beginner",
                "prerequisites": ["node-1", "node-2"],
                "concepts": ["Data Processing", "Feature Scaling", "Encoding"],
                "objectives": ["Clean raw datasets", "Engineer predictive features"]
            },
            {
                "id": "node-4",
                "title": "4. Supervised Learning: Regression & Classification",
                "description": "Linear/logistic regression, decision trees, support vector machines, and loss minimization.",
                "estimated_hours": 3.0,
                "difficulty": "intermediate",
                "prerequisites": ["node-3"],
                "concepts": ["Supervised Learning", "Linear Regression", "Classification"],
                "objectives": ["Train supervised classification models", "Minimize mean squared and cross-entropy loss"]
            },
            {
                "id": "node-5",
                "title": "5. Model Evaluation, Validation & Overfitting Diagnostics",
                "description": "K-fold cross-validation, confusion matrices, ROC-AUC, bias-variance tradeoff, and regularization (L1/L2).",
                "estimated_hours": 3.0,
                "difficulty": "intermediate",
                "prerequisites": ["node-4"],
                "concepts": ["Model Evaluation", "Cross-Validation", "Overfitting"],
                "objectives": ["Diagnose overfitting with validation curves", "Evaluate precision, recall, and ROC-AUC"]
            },
            {
                "id": "node-6",
                "title": "6. Deep Neural Networks & Representation Learning",
                "description": "Multi-layer perceptrons, backpropagation chain rule, activation functions, and deep loss optimization.",
                "estimated_hours": 4.5,
                "difficulty": "advanced",
                "prerequisites": ["node-5"],
                "concepts": ["Neural Networks", "Backpropagation", "Deep Learning"],
                "objectives": ["Build multi-layer neural networks", "Compute backpropagation gradients"]
            }
        ]
    },
    "electricity": {
        "title": "Principles of Electricity & Circuit Dynamics",
        "description": "Systematic mastery track covering electric charge, current flow, potential difference, Ohm's law, resistance, and circuit network laws.",
        "nodes": [
            {
                "id": "node-1",
                "title": "1. Electric Charge & Coulomb's Electrostatic Law",
                "description": "Atomic charge carriers, conservation of charge, electrostatic force, and electric field lines.",
                "estimated_hours": 1.5,
                "difficulty": "beginner",
                "prerequisites": [],
                "concepts": ["Electric Charge", "Coulomb's Law", "Electric Field"],
                "objectives": ["Calculate electrostatic forces", "Understand electron mobility"]
            },
            {
                "id": "node-2",
                "title": "2. Electric Current & Potential Difference (Voltage)",
                "description": "Rate of charge flow I = Q/t, electromotive force, potential drop, and battery energy transfer.",
                "estimated_hours": 2.0,
                "difficulty": "beginner",
                "prerequisites": ["node-1"],
                "concepts": ["Electric Current", "Potential Difference", "Voltage"],
                "objectives": ["Define electric current and potential difference", "Measure current and voltage in standard units"]
            },
            {
                "id": "node-3",
                "title": "3. Ohm's Law & Electrical Resistance",
                "description": "Constitutive relationship V = IR, material resistivity, temperature dependence, and microscopic collision model.",
                "estimated_hours": 2.5,
                "difficulty": "intermediate",
                "prerequisites": ["node-2"],
                "concepts": ["Ohm's Law", "Resistance", "Resistivity"],
                "objectives": ["Derive V = IR under constant temperature", "Differentiate opposition to flow from energy consumption"]
            },
            {
                "id": "node-4",
                "title": "4. Series & Parallel Circuit Analysis",
                "description": "Equivalent resistance derivations, current division, voltage sharing, and circuit power calculations.",
                "estimated_hours": 3.0,
                "difficulty": "intermediate",
                "prerequisites": ["node-3"],
                "concepts": ["Series Circuits", "Parallel Circuits", "Equivalent Resistance"],
                "objectives": ["Calculate total resistance in series and parallel networks", "Compute electrical power dissipation"]
            },
            {
                "id": "node-5",
                "title": "5. Kirchhoff's Current & Voltage Laws",
                "description": "Conservation of charge at nodes (KCL) and conservation of energy in loops (KVL) for complex multi-mesh networks.",
                "estimated_hours": 3.5,
                "difficulty": "advanced",
                "prerequisites": ["node-4"],
                "concepts": ["Kirchhoff's Laws", "KCL", "KVL"],
                "objectives": ["Solve multi-loop circuits using nodal and mesh analysis", "Verify conservation principles"]
            }
        ]
    },
    "quantum-computing": {
        "title": "Quantum Computing & Information Mechanics",
        "description": "Bloom's Taxonomy curriculum spanning qubit state spaces, quantum logic gates, Bell states, Shor's and Grover's algorithms.",
        "nodes": [
            {
                "id": "node-1",
                "title": "1. Qubits, Superposition & Hilbert Spaces",
                "description": "Bloch sphere geometric representation, Dirac bra-ket notation, state vectors, and complex probability amplitudes.",
                "estimated_hours": 1.5,
                "difficulty": "beginner",
                "prerequisites": [],
                "concepts": ["Qubits", "Superposition", "Bloch Sphere"],
                "objectives": ["Represent quantum states with Dirac vectors", "Calculate measurement probabilities"]
            },
            {
                "id": "node-2",
                "title": "2. Quantum Logic Gates & Unitary Operators",
                "description": "Pauli-X/Y/Z, Hadamard, Phase Shift, and controlled CNOT matrices maintaining unitary preservation (U†U = I).",
                "estimated_hours": 2.5,
                "difficulty": "beginner",
                "prerequisites": ["node-1"],
                "concepts": ["Quantum Gates", "Hadamard", "CNOT"],
                "objectives": ["Apply unitary gate transformations", "Synthesize superposition states"]
            },
            {
                "id": "node-3",
                "title": "3. Quantum Entanglement & Bell State Teleportation",
                "description": "EPR paradox, non-locality, density matrices, tensor product spaces, and quantum teleportation protocols.",
                "estimated_hours": 3.0,
                "difficulty": "intermediate",
                "prerequisites": ["node-2"],
                "concepts": ["Entanglement", "Bell States", "Teleportation"],
                "objectives": ["Construct Bell states", "Analyze quantum teleportation circuits"]
            },
            {
                "id": "node-4",
                "title": "4. Quantum Algorithms: Deutsch-Jozsa & Grover Search",
                "description": "Phase kickback oracles, amplitude amplification, O(√N) database search complexity, and interference manipulation.",
                "estimated_hours": 3.5,
                "difficulty": "intermediate",
                "prerequisites": ["node-3"],
                "concepts": ["Grover Search", "Quantum Oracles", "Amplitude Amplification"],
                "objectives": ["Implement Grover search iterations", "Demonstrate quadratic quantum speedup"]
            },
            {
                "id": "node-5",
                "title": "5. Quantum Fourier Transform & Shor's Factorization",
                "description": "Discrete log period finding, modular arithmetic circuits, QFT matrix decomposition, and polynomial-time RSA decryption.",
                "estimated_hours": 4.5,
                "difficulty": "advanced",
                "prerequisites": ["node-4"],
                "concepts": ["QFT", "Shor's Algorithm", "Quantum Period Finding"],
                "objectives": ["Decompose quantum Fourier transforms", "Factor integers in polynomial time"]
            }
        ]
    }
}

class LearningPathService:
    @classmethod
    async def generate_or_get_learning_path(
        cls,
        topic_id: str,
        user_id: str,
        db: Session,
        goal: Optional[str] = "understand_concept",
        learner_level: Optional[str] = "beginner",
        force_regenerate: bool = False
    ) -> LearningPath:
        """
        Generates or retrieves a personalized learning path DAG tailored to the student's
        existing mastery profile, skipping mastered fundamentals where appropriate,
        and setting dynamic prerequisite lock states.
        """
        profile = LearnerProfileService.get_full_learner_profile(user_id, db)
        effective_level = learner_level or profile.level
        effective_goal = goal or profile.goal

        # Check if existing path in DB for this user unless forced regeneration
        if not force_regenerate:
            db_path = db.query(DBLearningPath).filter(
                DBLearningPath.topic_id == topic_id,
                DBLearningPath.user_id == user_id
            ).first()

            if db_path and db_path.dag_json:
                path = LearningPath.model_validate(db_path.dag_json)
                return cls.evaluate_path_prerequisites(path, profile)

        clean_topic = topic_id.replace("-", " ").title()
        
        # Check domain curated templates
        normalized_key = topic_id.lower().strip()
        matched_spec = None
        for key in DOMAIN_CURRICULA:
            if key == normalized_key or key in normalized_key or normalized_key in key:
                matched_spec = DOMAIN_CURRICULA[key]
                break

        if matched_spec:
            spec_nodes: List[Dict[str, Any]] = list(matched_spec.get("nodes", []))
            title = str(matched_spec.get("title", clean_topic))
            description = str(matched_spec.get("description", ""))
            
            # Personalization: If returning student already has verified mastery of early nodes
            final_nodes: List[PathNode] = []
            for n in spec_nodes:
                node_concepts = n.get("concepts", [n.get("title", "")])
                is_already_mastered = any(
                    profile.concept_masteries.get(c, {}).get("mastery") in ["mastered", "strong"]
                    for c in node_concepts
                ) or (n.get("title") in profile.completed_topics)
                
                status = "mastered" if is_already_mastered else "available"
                score = 95.0 if is_already_mastered else None
                completed = is_already_mastered

                final_nodes.append(PathNode(
                    id=n["id"],
                    title=n["title"],
                    description=n["description"],
                    estimated_hours=float(n.get("estimated_hours", 2.0)),
                    difficulty=n.get("difficulty", "beginner"),
                    prerequisites=n.get("prerequisites", []),
                    completed=completed,
                    score=score,
                    status=status,
                    concepts=node_concepts,
                    objectives=n.get("objectives", [])
                ))

            # Build Edges
            edges = []
            for n in final_nodes:
                for p in n.prerequisites:
                    edges.append({"from": p, "to": n.id})
            if not edges:
                for i in range(len(final_nodes) - 1):
                    edges.append({"from": final_nodes[i].id, "to": final_nodes[i+1].id})
        else:
            # Dynamic synthesis via LLM with Bloom's Taxonomy fallback
            final_nodes = []
            edges = []
            title = f"Comprehensive Mastery Path: {clean_topic}"
            description = f"Prerequisite-ordered curriculum DAG for {clean_topic} moving progressively from intuition to advanced synthesis."

            try:
                system_prompt = (
                    "You are an elite curriculum architect and cognitive learning designer. "
                    "Synthesize a prerequisite-ordered curriculum DAG (5 to 6 nodes) for the subject. "
                    "Each node MUST have: id, title, description, estimated_hours (float), difficulty ('beginner', 'intermediate', 'advanced'), concepts (list of strings), objectives (list of strings), prerequisites (list of earlier node IDs)."
                )
                user_prompt = f"""Generate a personalized learning curriculum DAG for:
Topic: {clean_topic}
Student Level: {effective_level}
Goal: {effective_goal}
Known Strong Concepts to build upon: {', '.join(profile.strong_concepts) if profile.strong_concepts else 'None'}

JSON Output Format:
{{
  "title": "{title}",
  "description": "{description}",
  "nodes": [
    {{
      "id": "node-1",
      "title": "1. Foundational Concepts & Intuition",
      "description": "Core terminology and intuitions",
      "estimated_hours": 1.5,
      "difficulty": "beginner",
      "prerequisites": [],
      "concepts": ["Concept 1", "Concept 2"],
      "objectives": ["Objective 1"]
    }}
  ]
}}
"""
                llm_dag = await LLMService.generate_json(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    schema_hint='{"title": "...", "description": "...", "nodes": [{"id": "node-1", "title": "...", "description": "...", "estimated_hours": 1.5, "difficulty": "beginner", "prerequisites": [], "concepts": [], "objectives": []}]}',
                    temperature=0.3
                )
                raw_nodes = llm_dag.get("nodes", []) if isinstance(llm_dag, dict) else []
                if raw_nodes and len(raw_nodes) >= 3:
                    for i, n in enumerate(raw_nodes):
                        if isinstance(n, dict):
                            final_nodes.append(PathNode(
                                id=str(n.get("id") or f"node-{i+1}"),
                                title=str(n.get("title") or f"Module {i+1}"),
                                description=str(n.get("description") or ""),
                                estimated_hours=float(n.get("estimated_hours") or 2.0),
                                difficulty=str(n.get("difficulty") or "beginner"),
                                prerequisites=[str(p) for p in (n.get("prerequisites") or []) if p],
                                completed=False,
                                score=None,
                                status="available",
                                concepts=[str(c) for c in n.get("concepts", [])],
                                objectives=[str(o) for o in n.get("objectives", [])]
                            ))
                    title = llm_dag.get("title", title)
                    description = llm_dag.get("description", description)
                    
                    for n in final_nodes:
                        for p in n.prerequisites:
                            edges.append({"from": p, "to": n.id})
                    if not edges:
                        for i in range(len(final_nodes) - 1):
                            edges.append({"from": final_nodes[i].id, "to": final_nodes[i+1].id})
            except Exception as e:
                logger.warning(f"[LearningPathService] LLM DAG synthesis failed ({e}); falling back to Bloom's template.")

            if not final_nodes:
                stages: List[Dict[str, Any]] = [
                    {"id": "node-1", "title": f"1. Foundations & Intuitive Models of {clean_topic}", "difficulty": "beginner", "prerequisites": [], "concepts": [f"{clean_topic} Basics"]},
                    {"id": "node-2", "title": f"2. Governing Principles & Structural Formulation", "difficulty": "beginner", "prerequisites": ["node-1"], "concepts": [f"{clean_topic} Principles"]},
                    {"id": "node-3", "title": f"3. Applied Problem Solving & Standard Methods", "difficulty": "intermediate", "prerequisites": ["node-2"], "concepts": [f"{clean_topic} Applications"]},
                    {"id": "node-4", "title": f"4. Experimental Diagnostics & Edge Cases", "difficulty": "intermediate", "prerequisites": ["node-3"], "concepts": [f"{clean_topic} Diagnostics"]},
                    {"id": "node-5", "title": f"5. Advanced Theory & High-Order Synthesis", "difficulty": "advanced", "prerequisites": ["node-4"], "concepts": [f"{clean_topic} Advanced Theory"]}
                ]
                for st in stages:
                    final_nodes.append(PathNode(
                        id=str(st["id"]),
                        title=str(st["title"]),
                        description=f"Pedagogical unit covering {st['title']}",
                        estimated_hours=2.5,
                        difficulty=str(st["difficulty"]),
                        prerequisites=[str(p) for p in st.get("prerequisites", [])],
                        completed=False,
                        score=None,
                        status="available",
                        concepts=[str(c) for c in st.get("concepts", [])],
                        objectives=[f"Master {st['title']}"]
                    ))
                for i in range(len(final_nodes) - 1):
                    edges.append({"from": final_nodes[i].id, "to": final_nodes[i+1].id})

        path = LearningPath(
            topic_id=topic_id,
            user_id=user_id,
            subject=clean_topic,
            goal=effective_goal,
            title=title,
            description=description,
            nodes=final_nodes,
            edges=edges,
            completion_percentage=0.0
        )

        # Apply prerequisite locks and recommendations
        evaluated_path = cls.evaluate_path_prerequisites(path, profile)

        # Persist / update in database
        existing_db_path = db.query(DBLearningPath).filter(
            DBLearningPath.topic_id == topic_id,
            DBLearningPath.user_id == user_id
        ).first()

        if existing_db_path:
            existing_db_path.dag_json = evaluated_path.model_dump(mode="json")
            existing_db_path.progress_percentage = evaluated_path.completion_percentage
            existing_db_path.title = evaluated_path.title
            db.commit()
        else:
            new_db_path = DBLearningPath(
                id=str(uuid.uuid4()),
                user_id=user_id,
                topic_id=topic_id,
                title=evaluated_path.title,
                dag_json=evaluated_path.model_dump(mode="json"),
                progress_percentage=evaluated_path.completion_percentage
            )
            db.add(new_db_path)
            db.commit()

        return evaluated_path

    @classmethod
    def evaluate_path_prerequisites(cls, path: LearningPath, profile: LearnerProfile) -> LearningPath:
        """
        Deterministic DAG solver: Evaluates every node's prerequisite dependencies against
        both prior node completion status and the student's persistent concept mastery map.
        Sets node status: locked | available | in_progress | completed | mastered | needs_revision.
        """
        node_map = {n.id: n for n in path.nodes}
        completed_ids = set()
        mastered_ids = set()
        needs_revision_ids = set()
        prerequisite_gaps = []

        # 1. First pass: Evaluate individual node completion and concept mastery
        for n in path.nodes:
            # Check concept mastery in profile for this node's concepts
            has_weak_concept = False
            has_misconception = False
            has_mastered_concept = False
            
            for c in n.concepts:
                m_info = profile.concept_masteries.get(c, {})
                m_state = m_info.get("mastery")
                if m_state in ["weak", "misunderstood"]:
                    has_weak_concept = True
                if m_state == "misunderstood" or (m_info.get("misconceptions") and len(m_info.get("misconceptions")) > 0):
                    has_misconception = True
                if m_state in ["mastered", "strong"]:
                    has_mastered_concept = True

            # If node has been assessed or has misconceptions
            if n.status == "needs_revision" or (n.score is not None and n.score < 70.0) or (has_weak_concept and n.score is not None) or (has_misconception and n.score is not None):
                n.status = "needs_revision"
                n.recommended_action = f"Targeted revision needed for {n.concepts[0] if n.concepts else n.title}"
                needs_revision_ids.add(n.id)
            elif n.completed:
                if has_mastered_concept or (n.score is not None and n.score >= 85.0):
                    n.status = "mastered"
                    mastered_ids.add(n.id)
                    completed_ids.add(n.id)
                else:
                    n.status = "completed"
                    completed_ids.add(n.id)
            else:
                n.status = "available"

        # 2. Second pass: Propagate prerequisite dependency locks
        for n in path.nodes:
            if n.status in ["mastered", "completed", "needs_revision"]:
                continue

            unmet_prereqs = []
            for prereq_id in n.prerequisites:
                prereq_node = node_map.get(prereq_id)
                if not prereq_node:
                    continue

                if prereq_id in needs_revision_ids or prereq_node.status == "needs_revision":
                    unmet_prereqs.append(f"{prereq_node.title} (Needs Revision)")
                    prerequisite_gaps.append(f"{n.title} blocked by {prereq_node.title}")
                elif prereq_id not in completed_ids and prereq_node.status != "mastered":
                    unmet_prereqs.append(f"{prereq_node.title} (Incomplete)")
                    prerequisite_gaps.append(f"{n.title} requires completion of {prereq_node.title}")

            if unmet_prereqs:
                n.status = "locked"
                n.prerequisite_reason = f"Locked: Requires mastery of {'; '.join(unmet_prereqs)}"
                n.recommended_action = "Complete prerequisite modules before attempting this unit."
            else:
                n.status = "available"
                n.prerequisite_reason = None

        # 3. Calculate completion percentage
        comp_count = sum(1 for n in path.nodes if n.status in ["completed", "mastered"])
        path.completion_percentage = round((comp_count / len(path.nodes)) * 100, 1) if path.nodes else 0.0
        path.prerequisite_gaps = prerequisite_gaps

        # 4. Generate structured next recommendation
        recommendation = cls._determine_next_recommendation(path, profile)
        path.recommendation = recommendation
        path.recommended_next_node_id = recommendation.node_id

        # Mark the active in-progress node
        for n in path.nodes:
            if n.id == recommendation.node_id and n.status == "available":
                n.status = "in_progress"
                path.current_node_id = n.id
                break

        return path

    @classmethod
    def _determine_next_recommendation(
        cls,
        path: LearningPath,
        profile: LearnerProfile
    ) -> LearningRecommendationResult:
        """
        Determines the next learning action with explainability and evidence.
        """
        # Case A: A prerequisite node needs revision
        revision_nodes = [n for n in path.nodes if n.status == "needs_revision"]
        if revision_nodes:
            target = revision_nodes[0]
            return LearningRecommendationResult(
                action="REVISE_CONCEPT",
                topic_id=path.topic_id,
                node_id=target.id,
                node_title=target.title,
                reason=f"Assessment revealed conceptual gaps in {target.title}.",
                evidence=[f"Recent score below threshold ({target.score or 65}%) in {target.title}"],
                prerequisite_gap=f"Prerequisite module {target.title} requires revision before proceeding.",
                explanation=f"We recommend spending 10 minutes strengthening {target.title} before advancing to downstream topics."
            )

        # Case B: Next available node
        available_nodes = [n for n in path.nodes if n.status in ["available", "in_progress"]]
        if available_nodes:
            target = available_nodes[0]
            prereq_titles = [path.nodes[i].title for i, n in enumerate(path.nodes) if n.id in target.prerequisites]
            return LearningRecommendationResult(
                action="MOVE_TO_NEXT_TOPIC",
                topic_id=path.topic_id,
                node_id=target.id,
                node_title=target.title,
                reason=f"All prerequisites for {target.title} have been satisfied.",
                evidence=[f"Completed prior modules: {', '.join(prereq_titles) if prereq_titles else 'Foundations satisfied'}"],
                prerequisite_gap=None,
                explanation=f"{target.title} is ready. Launch the interactive AI lesson to continue your learning path."
            )

        # Case C: All nodes completed or mastered
        return LearningRecommendationResult(
            action="MOVE_TO_NEXT_TOPIC",
            topic_id=path.topic_id,
            node_id=None,
            node_title=f"Advanced Capstone in {path.title}",
            reason=f"You have completed all {len(path.nodes)} modules in {path.title} with high mastery.",
            evidence=[f"Curriculum completion: 100%"],
            prerequisite_gap=None,
            explanation="Congratulations! You have mastered this entire curriculum. Advance to specialized research topics or capstone projects."
        )

    @classmethod
    def get_next_topic_recommendation(
        cls,
        topic_id: str,
        user_id: str,
        db: Session
    ) -> LearningRecommendationResult:
        """
        Public API helper to get the current recommendation for a learning path.
        """
        path = db.query(DBLearningPath).filter(
            DBLearningPath.topic_id == topic_id,
            DBLearningPath.user_id == user_id
        ).first()

        profile = LearnerProfileService.get_full_learner_profile(user_id, db)

        if not path or not path.dag_json:
            return LearningRecommendationResult(
                action="CONTINUE_CURRENT_TOPIC",
                topic_id=topic_id,
                reason="Generate learning path to begin structured curriculum.",
                explanation="Start learning by initializing your customized curriculum DAG."
            )

        lp_obj = LearningPath.model_validate(path.dag_json)
        evaluated = cls.evaluate_path_prerequisites(lp_obj, profile)
        return evaluated.recommendation or cls._determine_next_recommendation(evaluated, profile)

    @classmethod
    async def toggle_node_completion(
        cls,
        topic_id: str,
        user_id: str,
        node_id: str,
        db: Session
    ) -> LearningPath:
        """
        Toggles node completion, updates persistent learner state, re-evaluates prerequisites,
        and saves updated DAG.
        """
        db_path = db.query(DBLearningPath).filter(
            DBLearningPath.topic_id == topic_id,
            DBLearningPath.user_id == user_id
        ).first()

        if not db_path:
            await cls.generate_or_get_learning_path(topic_id, user_id, db)
            db_path = db.query(DBLearningPath).filter(
                DBLearningPath.topic_id == topic_id,
                DBLearningPath.user_id == user_id
            ).first()

        if not db_path or not db_path.dag_json:
            return await cls.generate_or_get_learning_path(topic_id, user_id, db)

        data = dict(db_path.dag_json) if isinstance(db_path.dag_json, dict) else {}
        nodes: List[Dict[str, Any]] = list(data.get("nodes", []))
        
        for n in nodes:
            if isinstance(n, dict) and n.get("id") == node_id:
                n["completed"] = not bool(n.get("completed", False))
                if n["completed"] and not n.get("score"):
                    n["score"] = 90.0
                elif not n["completed"]:
                    n["score"] = None
                break

        lp_obj = LearningPath.model_validate(data)
        profile = LearnerProfileService.get_full_learner_profile(user_id, db)
        evaluated = cls.evaluate_path_prerequisites(lp_obj, profile)

        db_path.dag_json = evaluated.model_dump(mode="json")
        db_path.progress_percentage = evaluated.completion_percentage
        db.commit()

        return evaluated

    @classmethod
    def update_path_from_assessment(
        cls,
        user_id: str,
        topic_id: str,
        report: LearningReport,
        db: Session
    ) -> Optional[LearningPath]:
        """
        Adapts the student's active learning path in response to an assessment event.
        Updates node mastery, sets revision requirements, or unlocks downstream nodes.
        """
        db_path = db.query(DBLearningPath).filter(
            DBLearningPath.user_id == user_id,
            DBLearningPath.topic_id == topic_id
        ).first()

        if not db_path:
            # Check by matching title or topic keyword
            all_user_paths = db.query(DBLearningPath).filter(DBLearningPath.user_id == user_id).all()
            for p in all_user_paths:
                if (p.topic_id and p.topic_id in topic_id.lower()) or (p.title and report.topic.lower() in p.title.lower()):
                    db_path = p
                    break

        if not db_path or not db_path.dag_json:
            return None

        data = dict(db_path.dag_json) if isinstance(db_path.dag_json, dict) else {}
        nodes: List[Dict[str, Any]] = list(data.get("nodes", []))

        # Check if report maps to a specific node
        for n in nodes:
            n_title = str(n.get("title", "")).lower()
            n_concepts = [c.lower() for c in n.get("concepts", [])]
            report_topic_low = report.topic.lower()

            matches = report_topic_low in n_title or n_title in report_topic_low or any(c in report_topic_low for c in n_concepts)
            if matches:
                n["score"] = report.score_percent
                n["completed"] = report.score_percent >= 70.0
                if report.score_percent < 70.0:
                    n["status"] = "needs_revision"
                elif report.score_percent >= 85.0:
                    n["status"] = "mastered"
                else:
                    n["status"] = "completed"
                break

        lp_obj = LearningPath.model_validate(data)
        profile = LearnerProfileService.get_full_learner_profile(user_id, db)
        evaluated = cls.evaluate_path_prerequisites(lp_obj, profile)

        db_path.dag_json = evaluated.model_dump(mode="json")
        db_path.progress_percentage = evaluated.completion_percentage
        db.commit()

        logger.info(f"[LearningPathService] Adapted learning path {db_path.topic_id} for user {user_id} post-assessment.")
        return evaluated
