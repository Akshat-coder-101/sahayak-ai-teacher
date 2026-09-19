import math
import re
from typing import Dict, Any, List, Optional
from .code_sandbox import CodeSandboxService
from ..models.schemas import VisualSpec, VisualDecision

class VisualRouter:
    @classmethod
    def decide_visual_strategy(
        cls, 
        concept: str, 
        context: Optional[str] = None, 
        learner_level: str = "beginner"
    ) -> VisualDecision:
        """
        Intelligently determines the subject, concept type, pedagogical necessity,
        optimal visual representation, observation guidance, and knowledge check.
        """
        concept_l = (concept or "").lower()
        context_l = (context or "").lower()
        combined = f"{concept_l} {context_l}"

        # 1. Subject Classification Heuristic
        if any(w in combined for w in ["force", "gravity", "velocity", "acceleration", "newton", "friction", "momentum", "torque", "kinetic", "potential energy", "wave", "optics", "thermodynamics", "circuit", "ohm", "voltage", "current"]):
            subject = "physics"
        elif any(w in combined for w in ["equation", "calculus", "derivative", "integral", "quadratic", "algebra", "polynomial", "matrix", "geometry", "trigonometry", "function", "parabola", "logarithm", "root"]):
            subject = "mathematics"
        elif any(w in combined for w in ["cell", "mitochondria", "photosynthesis", "dna", "rna", "protein", "organelle", "membrane", "respiration", "enzyme", "neuron", "heart", "organ", "plant", "ecology", "genetics"]):
            subject = "biology"
        elif any(w in combined for w in ["war", "empire", "revolution", "treaty", "century", "dynasty", "historical", "ancient", "medieval", "president", "civilization", "reign", "colony", "timeline"]):
            subject = "history"
        elif any(w in combined for w in ["binary search", "search", "sort", "algorithm", "array", "tree", "graph", "recursion", "loop", "stack", "queue", "dynamic programming", "python", "code", "pointer", "complexity", "big o"]):
            subject = "computer_science"
        else:
            subject = "general"

        # Complexity scaling based on learner level
        complexity = "simple" if learner_level == "beginner" else ("advanced" if learner_level == "advanced" else "intermediate")

        # 2. Subject-Specific Pedagogical Visual Decision
        if subject == "physics":
            if any(w in combined for w in ["force", "newton", "friction", "gravity", "equilibrium", "free body", "tension"]):
                return VisualDecision(
                    subject="physics",
                    concept_type="force_dynamics",
                    pedagogical_goal="Deconstruct interacting vector forces acting on a mass to apply Newton's second law ΣF = ma.",
                    visual_needed="required",
                    visual_type="free_body_diagram",
                    reason="Free-body vector diagrams make direction, magnitude, and net acceleration visually intuitive.",
                    generation_method="svg_diagram",
                    complexity=complexity,
                    observation_prompt="Look at the vector arrows acting on the central mass. Notice the balance between vertical normal force and gravity, and the net horizontal force.",
                    knowledge_check="If the applied force is doubled while opposing friction remains unchanged, what happens to the magnitude of acceleration?"
                )
            else:
                return VisualDecision(
                    subject="physics",
                    concept_type="quantitative_derivation",
                    pedagogical_goal="Plot kinematic or harmonic state trajectory against time.",
                    visual_needed="recommended",
                    visual_type="equation/graph",
                    reason="Coordinate plotting reveals how displacement, velocity, and energy vary dynamically over time.",
                    generation_method="interactive_chart",
                    complexity=complexity,
                    observation_prompt="Observe the curvature of the trajectory and identify where velocity passes through zero.",
                    knowledge_check="At what position along the curve does the system achieve peak kinetic energy?"
                )

        elif subject == "mathematics":
            return VisualDecision(
                subject="mathematics",
                concept_type="algebraic_transformation",
                pedagogical_goal="Step-by-step algebraic solution with corresponding coordinate function graph.",
                visual_needed="required",
                visual_type="equation/graph",
                reason="Combining formal LaTeX transformation steps with coordinate plots connects algebraic symbols with geometric intuition.",
                generation_method="latex_derivation",
                complexity=complexity,
                observation_prompt="Observe each line of the algebraic transformation, then examine how the function curve crosses the horizontal axis.",
                knowledge_check="How do the roots calculated in the algebraic steps match the x-intercepts on the coordinate graph?"
            )

        elif subject == "biology":
            if any(w in combined for w in ["photosynthesis", "respiration", "cycle", "krebs", "calvin", "pathway"]):
                return VisualDecision(
                    subject="biology",
                    concept_type="cellular_process",
                    pedagogical_goal="Trace the sequential biochemical reaction cycle and metabolic inputs/outputs.",
                    visual_needed="required",
                    visual_type="process_cycle",
                    reason="Biochemical cycle diagrams clarify chemical precursors, energy catalysts, and final synthesized products.",
                    generation_method="svg_diagram",
                    complexity=complexity,
                    observation_prompt="Follow the circular reaction pathways from initial chemical inputs (light/water/CO2) to final synthesized energy molecules.",
                    knowledge_check="Which cellular organelle hosts this reaction, and what essential compound is released as a byproduct?"
                )
            else:
                return VisualDecision(
                    subject="biology",
                    concept_type="cellular_structure",
                    pedagogical_goal="Identify structural compartmentalization and organelle functions.",
                    visual_needed="required",
                    visual_type="labeled-diagram",
                    reason="Interactive labeled structural models allow students to inspect organelle roles without cognitive overload.",
                    generation_method="svg_diagram",
                    complexity=complexity,
                    observation_prompt="Notice the highlighted organelles and review the specific metabolic role assigned to each component.",
                    knowledge_check="Which organelle is responsible for generating cellular ATP currency?"
                )

        elif subject == "history":
            return VisualDecision(
                subject="history",
                concept_type="chronological_sequence",
                pedagogical_goal="Map chronological milestone causality and systemic historical triggers.",
                visual_needed="required",
                visual_type="timeline/map",
                reason="Chronological sequencing visually connects underlying social/political tensions with turning points and outcomes.",
                generation_method="timeline_component",
                complexity=complexity,
                observation_prompt="Trace the milestone cards along the timeline, observing how early catalysts precipitated major structural pivots.",
                knowledge_check="Which milestone marked the decisive inflection point in the progression of events?"
            )

        elif subject == "computer_science":
            if any(w in combined for w in ["binary search", "search", "array", "pointer", "index"]):
                return VisualDecision(
                    subject="computer_science",
                    concept_type="algorithmic_procedure",
                    pedagogical_goal="Demonstrate pointer reduction and logarithmic halving of search space.",
                    visual_needed="required",
                    visual_type="code+execution",
                    reason="Displaying active boundary pointers and execution output makes logarithmic time complexity tangible.",
                    generation_method="code_sandbox",
                    complexity=complexity,
                    observation_prompt="Look at the low, mid, and high pointers on the array and observe how the active search range halves at each iteration.",
                    knowledge_check="If target > array[mid], which boundary pointer must be shifted to narrow the search space?"
                )
            else:
                return VisualDecision(
                    subject="computer_science",
                    concept_type="algorithmic_procedure",
                    pedagogical_goal="Verify algorithm logic with live sandboxed Python execution.",
                    visual_needed="recommended",
                    visual_type="code+execution",
                    reason="Live executable code with standard output terminal reinforces syntax, semantics, and invariants.",
                    generation_method="code_sandbox",
                    complexity=complexity,
                    observation_prompt="Review the modular Python function implementation and verify the captured standard output.",
                    knowledge_check="What is the worst-case time complexity of this algorithmic pipeline?"
                )

        # Fallback General
        return VisualDecision(
            subject="general",
            concept_type="conceptual_model",
            pedagogical_goal=f"Provide structured analytical overview for {concept}.",
            visual_needed="recommended",
            visual_type="labeled-diagram",
            reason="Structured diagrams reduce cognitive load by organizing key concepts visually.",
            generation_method="svg_diagram",
            complexity=complexity,
            observation_prompt=f"Observe the relationship between foundational components of {concept}.",
            knowledge_check=f"What is the central governing principle of {concept}?"
        )

    @classmethod
    def generate_visual_spec(
        cls, 
        concept: str, 
        visual_type: str = "labeled-diagram", 
        depth: str = "beginner",
        code_snippet: Optional[str] = None,
        context: Optional[str] = None
    ) -> VisualSpec:
        """
        Generates a validated, domain-accurate VisualSpec accompanied by its VisualDecision.
        """
        decision = cls.decide_visual_strategy(concept, context, depth)
        effective_type = visual_type if visual_type in ["free_body_diagram", "process_cycle", "equation/graph", "labeled-diagram", "timeline/map", "code+execution"] else decision.visual_type

        if effective_type == "free_body_diagram" or (decision.subject == "physics" and decision.concept_type == "force_dynamics"):
            spec = cls._generate_free_body_diagram_spec(concept, depth)
        elif effective_type == "process_cycle" or (decision.subject == "biology" and decision.concept_type == "cellular_process"):
            spec = cls._generate_process_cycle_spec(concept, depth)
        elif "equation" in effective_type or "graph" in effective_type or decision.subject in ["mathematics", "physics"]:
            spec = cls._generate_math_physics_spec(concept, depth)
        elif "diagram" in effective_type or decision.subject == "biology":
            spec = cls._generate_biology_diagram_spec(concept, depth)
        elif "timeline" in effective_type or "map" in effective_type or decision.subject == "history":
            spec = cls._generate_history_timeline_spec(concept, depth)
        else:
            spec = cls._generate_code_execution_spec(concept, depth, code_snippet)

        spec.decision = decision
        return spec

    @staticmethod
    def _generate_free_body_diagram_spec(concept: str, depth: str) -> VisualSpec:
        """Generates physics Free-Body Force Diagram with vectors and ΣF = ma."""
        is_advanced = depth == "advanced"
        f_app = "25 N" if not is_advanced else "F_{app} = 40.0\\text{ N}"
        f_fric = "10 N" if not is_advanced else "f_k = \\mu_k N = 15.0\\text{ N}"
        mass = "5 kg" if not is_advanced else "m = 5.0\\text{ kg}"
        accel = "3 m/s²" if not is_advanced else "a = \\frac{40.0 - 15.0}{5.0} = 5.0\\text{ m/s}^2"

        svg_code = f"""
        <svg viewBox="0 0 600 320" xmlns="http://www.w3.org/2000/svg" className="w-full h-auto">
          <defs>
            <marker id="arrowRed" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#f43f5e" />
            </marker>
            <marker id="arrowBlue" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#38bdf8" />
            </marker>
            <marker id="arrowGreen" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#34d399" />
            </marker>
            <marker id="arrowAmber" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#f59e0b" />
            </marker>
          </defs>
          <rect width="600" height="320" rx="14" fill="#0f172a" stroke="#334155" strokeWidth="2"/>
          
          <!-- Ground Surface line -->
          <line x1="80" y1="230" x2="520" y2="230" stroke="#64748b" strokeWidth="3" />
          <path d="M 80 230 L 70 245 M 140 230 L 130 245 M 200 230 L 190 245 M 260 230 L 250 245 M 320 230 L 310 245 M 380 230 L 370 245 M 440 230 L 430 245 M 500 230 L 490 245" stroke="#475569" strokeWidth="1.5" />

          <!-- Central Object Mass -->
          <rect x="240" y="130" width="120" height="100" rx="8" fill="#1e293b" stroke="#38bdf8" strokeWidth="3" />
          <text x="300" y="185" fill="#f8fafc" fontSize="15" fontWeight="bold" textAnchor="middle">Mass ({mass})</text>

          <!-- Force Normal (Up) -->
          <line x1="300" y1="130" x2="300" y2="40" stroke="#34d399" strokeWidth="3.5" markerEnd="url(#arrowGreen)" />
          <text x="315" y="55" fill="#34d399" fontSize="13" fontWeight="bold">Normal Force (N = mg)</text>

          <!-- Force Gravity (Down) -->
          <line x1="300" y1="230" x2="300" y2="300" stroke="#38bdf8" strokeWidth="3.5" markerEnd="url(#arrowBlue)" />
          <text x="315" y="290" fill="#38bdf8" fontSize="13" fontWeight="bold">Weight (W = mg)</text>

          <!-- Applied Force (Right) -->
          <line x1="360" y1="180" x2="510" y2="180" stroke="#f43f5e" strokeWidth="4" markerEnd="url(#arrowRed)" />
          <text x="440" y="165" fill="#f43f5e" fontSize="13" fontWeight="bold">Applied Force ({f_app})</text>

          <!-- Friction Force (Left) -->
          <line x1="240" y1="225" x2="130" y2="225" stroke="#f59e0b" strokeWidth="3" markerEnd="url(#arrowAmber)" />
          <text x="110" y="215" fill="#f59e0b" fontSize="12" fontWeight="bold">Friction ({f_fric})</text>
        </svg>
        """.strip()

        return VisualSpec(
            type="free_body_diagram",
            title=f"Free-Body Diagram & Force Dynamics: {concept}",
            payload={
                "svg_code": svg_code,
                "equations": [
                    r"\Sigma F_y = N - mg = 0 \implies N = mg",
                    r"\Sigma F_x = F_{app} - f_k = m \cdot a",
                    rf"a = \frac{{\Sigma F_x}}{{m}} = {accel}"
                ],
                "vectors": [
                    {"name": "Applied Force (F_app)", "direction": "Right (+x)", "role": "Driving force causing forward acceleration."},
                    {"name": "Kinetic Friction (f_k)", "direction": "Left (-x)", "role": "Surface resistance opposing velocity."},
                    {"name": "Normal Force (N)", "direction": "Upward (+y)", "role": "Surface reaction force balancing gravity."},
                    {"name": "Gravitational Weight (W)", "direction": "Downward (-y)", "role": "Earth's downward pull (m * g)."}
                ]
            }
        )

    @staticmethod
    def _generate_process_cycle_spec(concept: str, depth: str) -> VisualSpec:
        """Generates biochemical or cellular reaction cycle (e.g. Photosynthesis, Cellular Respiration)."""
        svg_code = """
        <svg viewBox="0 0 600 320" xmlns="http://www.w3.org/2000/svg" className="w-full h-auto">
          <defs>
            <marker id="arrowCycle" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 2 L 8 5 L 0 8 z" fill="#10b981" />
            </marker>
          </defs>
          <rect width="600" height="320" rx="14" fill="#0f172a" stroke="#334155" strokeWidth="2"/>
          
          <!-- Central Chloroplast Organelle -->
          <ellipse cx="300" cy="160" rx="240" ry="115" fill="#064e3b" opacity="0.4" stroke="#10b981" strokeWidth="2.5" strokeDasharray="6 4" />
          <text x="300" y="80" fill="#6ee7b7" fontSize="13" fontWeight="bold" textAnchor="middle">Chloroplast Reaction Chamber (Photosynthesis)</text>

          <!-- Stage 1: Light Reactions -->
          <rect x="100" y="115" width="160" height="90" rx="10" fill="#1e293b" stroke="#38bdf8" strokeWidth="2" />
          <text x="180" y="145" fill="#38bdf8" fontSize="12" fontWeight="bold" textAnchor="middle">1. Light Reactions</text>
          <text x="180" y="165" fill="#94a3b8" fontSize="10" textAnchor="middle">Thylakoid Membrane</text>
          <text x="180" y="185" fill="#fcd34d" fontSize="10" fontWeight="bold" textAnchor="middle">Light + H₂O → ATP + O₂</text>

          <!-- Stage 2: Calvin Cycle -->
          <rect x="340" y="115" width="160" height="90" rx="10" fill="#1e293b" stroke="#f59e0b" strokeWidth="2" />
          <text x="420" y="145" fill="#f59e0b" fontSize="12" fontWeight="bold" textAnchor="middle">2. Calvin Cycle</text>
          <text x="420" y="165" fill="#94a3b8" fontSize="10" textAnchor="middle">Stroma Matrix</text>
          <text x="420" y="185" fill="#34d399" fontSize="10" fontWeight="bold" textAnchor="middle">CO₂ + ATP → C₆H₁₂O₆</text>

          <!-- Cycle Arrow Top: ATP & NADPH -->
          <path d="M 260 140 Q 300 110 340 140" stroke="#10b981" strokeWidth="3" fill="none" markerEnd="url(#arrowCycle)" />
          <text x="300" y="125" fill="#34d399" fontSize="10" fontWeight="bold" textAnchor="middle">ATP + NADPH</text>

          <!-- Cycle Arrow Bottom: ADP + NADP+ -->
          <path d="M 340 180 Q 300 210 260 180" stroke="#94a3b8" strokeWidth="3" fill="none" markerEnd="url(#arrowCycle)" />
          <text x="300" y="208" fill="#94a3b8" fontSize="10" fontWeight="bold" textAnchor="middle">ADP + NADP⁺</text>
        </svg>
        """.strip()

        return VisualSpec(
            type="process_cycle",
            title=f"Biochemical Process Flow: {concept}",
            payload={
                "svg_code": svg_code,
                "chemical_equation": r"6\text{CO}_2 + 6\text{H}_2\text{O} + \text{Photons} \longrightarrow \text{C}_6\text{H}_{12}\text{O}_6 + 6\text{O}_2",
                "stages": [
                    {"stage": "Stage 1: Light-Dependent", "location": "Thylakoid Membrane", "inputs": "Light, H2O", "outputs": "ATP, NADPH, O2 (Byproduct)"},
                    {"stage": "Stage 2: Light-Independent (Calvin Cycle)", "location": "Stroma", "inputs": "CO2, ATP, NADPH", "outputs": "G3P / Glucose"}
                ]
            }
        )

    @staticmethod
    def _generate_math_physics_spec(concept: str, depth: str) -> VisualSpec:
        xs = [round(x * 0.5, 2) for x in range(-10, 11)]
        if "quadratic" in concept.lower() or "parabola" in concept.lower():
            ys = [round(0.5 * (x**2) - 2, 2) for x in xs]
            plot_title = "Quadratic Parabola: f(x) = 0.5x² - 2"
            eqs = [
                r"f(x) = ax^2 + bx + c",
                r"x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}",
                r"\text{Roots at } x = \pm 2.0"
            ]
            steps = [
                "1. Identify coefficients: a = 0.5, b = 0, c = -2.",
                "2. Calculate Discriminant: Δ = b² - 4ac = 0 - 4(0.5)(-2) = 4 > 0 (Two real distinct roots).",
                "3. Compute vertex coordinates at x = -b/(2a) = 0, f(0) = -2 (Global Minimum).",
                "4. Solve roots: 0.5x² - 2 = 0 ⟹ x² = 4 ⟹ x = ±2."
            ]
        elif "wave" in concept.lower() or "oscillation" in concept.lower():
            ys = [round(math.sin(x), 2) for x in xs]
            plot_title = "Harmonic Wave Motion: y(t) = A sin(ωt + φ)"
            eqs = [r"y(t) = A \sin(\omega t + \phi)", r"\omega = 2\pi f", r"v_{wave} = f \cdot \lambda"]
            steps = [
                "1. Amplitude (A) defines the peak displacement from equilibrium.",
                "2. Angular frequency (ω) determines the temporal oscillation rate.",
                "3. Wavelength (λ) corresponds to the spatial distance between successive crests."
            ]
        else:
            ys = [round(2 * x + 1, 2) for x in xs]
            plot_title = f"{concept}: Rate of Change Curve"
            eqs = [r"f(x) = mx + c", r"\frac{df}{dx} = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h} = m"]
            steps = [
                f"1. Establish the domain boundaries and governing relationship for {concept}.",
                "2. Differentiate to identify instantaneous rate of change and critical points.",
                "3. Verify asymptotic limits as independent variable approaches boundary extremes."
            ]

        return VisualSpec(
            type="equation/graph",
            title=f"Mathematical Derivation & Coordinate Model: {concept}",
            payload={
                "equations": eqs,
                "plot_title": plot_title,
                "x_label": "Domain (x)",
                "y_label": "Value f(x)",
                "x_values": xs,
                "y_values": ys,
                "step_by_step": steps
            }
        )

    @staticmethod
    def _generate_biology_diagram_spec(concept: str, depth: str) -> VisualSpec:
        svg_code = """
        <svg viewBox="0 0 600 320" xmlns="http://www.w3.org/2000/svg" className="w-full h-auto">
          <defs>
            <linearGradient id="cellGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#4338ca" stopOpacity="0.8"/>
              <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.8"/>
            </linearGradient>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="6" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>
          <rect width="600" height="320" rx="14" fill="#0f172a" stroke="#334155" strokeWidth="2"/>
          <ellipse cx="300" cy="160" rx="210" ry="110" fill="url(#cellGrad)" opacity="0.35" stroke="#38bdf8" strokeWidth="3" strokeDasharray="6 4"/>
          <circle cx="300" cy="160" r="50" fill="#6366f1" opacity="0.85" filter="url(#glow)"/>
          <circle cx="300" cy="160" r="22" fill="#a855f7"/>
          
          <!-- Organelles -->
          <ellipse cx="180" cy="130" rx="35" ry="18" fill="#10b981" opacity="0.9"/>
          <ellipse cx="420" cy="180" rx="32" ry="16" fill="#f59e0b" opacity="0.9"/>

          <!-- Labels -->
          <line x1="300" y1="110" x2="300" y2="50" stroke="#94a3b8" strokeWidth="2"/>
          <circle cx="300" cy="50" r="4" fill="#38bdf8"/>
          <text x="300" y="38" fill="#f8fafc" fontSize="12" fontWeight="bold" textAnchor="middle">Nucleus & Genomic DNA</text>

          <line x1="180" y1="112" x2="180" y2="70" stroke="#94a3b8" strokeWidth="2"/>
          <circle cx="180" cy="70" r="4" fill="#10b981"/>
          <text x="180" y="58" fill="#6ee7b7" fontSize="11" fontWeight="bold" textAnchor="middle">Mitochondria (ATP)</text>

          <line x1="420" y1="196" x2="420" y2="260" stroke="#94a3b8" strokeWidth="2"/>
          <circle cx="420" cy="260" r="4" fill="#f59e0b"/>
          <text x="420" y="278" fill="#fcd34d" fontSize="11" fontWeight="bold" textAnchor="middle">Endoplasmic Reticulum</text>
        </svg>
        """.strip()

        return VisualSpec(
            type="labeled-diagram",
            title=f"Biological Architecture: {concept}",
            payload={
                "svg_code": svg_code,
                "labels": [
                    {"name": "Core Nucleus", "role": "Master control library containing hereditary DNA and transcription machinery."},
                    {"name": "Mitochondria", "role": "Cellular power plant synthesizing ATP via oxidative phosphorylation."},
                    {"name": "Cell Membrane", "role": "Phospholipid bilayer maintaining homeostasis and selective ion transit."}
                ]
            }
        )

    @staticmethod
    def _generate_history_timeline_spec(concept: str, depth: str) -> VisualSpec:
        is_ww2 = "world war" in concept.lower() or "ww2" in concept.lower() or "wwii" in concept.lower()
        if is_ww2:
            events = [
                {"year": "1939", "title": "Invasion of Poland & Outbreak", "desc": "Blitzkrieg triggers treaty obligations across Britain and France.", "tag": "Trigger"},
                {"year": "1941", "title": "Operation Barbarossa & Pearl Harbor", "desc": "Global expansion as USSR and USA enter the Allied coalition.", "tag": "Turning Point"},
                {"year": "1944", "title": "D-Day Normandy Landings", "desc": "Allied liberation of Western Europe establishing the second front.", "tag": "Decisive Offensive"},
                {"year": "1945", "title": "Treaties & Potsdam Accords", "desc": "Unconditional surrender and foundation of the United Nations system.", "tag": "Resolution"}
            ]
        else:
            events = [
                {"year": "Phase I: Catalysts", "title": "Founding Systemic Pressures", "desc": f"Early institutional friction triggering the rise of {concept}.", "tag": "Origins"},
                {"year": "Phase II: Expansion", "title": "Structural Revolution & Inflection", "desc": "Widespread transformation and socio-political realignment.", "tag": "Turning Point"},
                {"year": "Phase III: Synthesis", "title": "Modern Institutional Paradigm", "desc": "Establishment of modern legal, geographic, and economic equilibrium.", "tag": "Modern Legacy"}
            ]

        return VisualSpec(
            type="timeline/map",
            title=f"Historical Timeline & Milestones: {concept}",
            payload={
                "events": events,
                "geographical_context": {
                    "region": "Global Historical Theatre",
                    "impact_scope": "Socio-political, economic, and institutional balance."
                }
            }
        )

    @classmethod
    def _generate_code_execution_spec(cls, concept: str, depth: str, code_snippet: Optional[str] = None) -> VisualSpec:
        is_binary_search = "binary search" in concept.lower() or "binary" in concept.lower()
        
        if not code_snippet:
            if is_binary_search:
                code_snippet = """# Binary Search: O(log N) Logarithmic Search
def binary_search(arr, target):
    low = 0
    high = len(arr) - 1
    step = 1
    print(f"Initial Array: {arr} (Searching for: {target})")
    
    while low <= high:
        mid = (low + high) // 2
        print(f"Step {step}: low={low}, mid={mid} (val={arr[mid]}), high={high}")
        if arr[mid] == target:
            print(f"✓ Found target {target} at index {mid}!")
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
        step += 1
    print("✗ Target not found.")
    return -1

numbers = [2, 5, 8, 12, 16, 23, 38, 45, 56, 72, 91]
result_idx = binary_search(numbers, 23)
"""
            else:
                code_snippet = f"""# Python Implementation: {concept}
def demonstrate_algorithm():
    data = [12, 45, 68, 90, 102]
    print("Executing pipeline for: {concept}")
    transformed = [x**2 for x in data]
    print("Transformed Data:", transformed)
    print("Computed Average:", sum(transformed) / len(transformed))
    return transformed

demonstrate_algorithm()
"""
        exec_res = CodeSandboxService.execute_python_code(code_snippet)
        
        return VisualSpec(
            type="code+execution",
            title=f"Sandboxed Code Execution: {concept}",
            payload={
                "language": "python",
                "code": code_snippet.strip(),
                "stdout": exec_res.get("stdout", ""),
                "stderr": exec_res.get("stderr", ""),
                "output": exec_res.get("output", ""),
                "success": exec_res.get("success", True),
                "array_trace": [
                    {"step": 1, "low": 0, "mid": 5, "high": 10, "val": 23, "action": "mid=23 == target ⟹ Found!"}
                ] if is_binary_search else [],
                "steps": [
                    "1. Initialize low and high pointers covering the sorted array bounds.",
                    "2. Compute mid = (low + high) // 2 to inspect the central element.",
                    "3. Halve the remaining search interval based on target comparison."
                ]
            }
        )

