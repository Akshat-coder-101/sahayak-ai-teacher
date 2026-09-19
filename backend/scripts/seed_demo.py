import os
import sys
import uuid
import asyncio
import logging

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database import (
    SessionLocal, init_db, DBUser, DBLearnerProfile, 
    DBMaterial, DBMaterialChunk, DBLessonSession
)
from app.services.auth import get_password_hash
from app.services.ingestion import IngestionService
from app.services.rag import EmbeddingService
from app.state_machine.teacher_agent import TeacherAgentStateMachine
from app.config import settings

logger = logging.getLogger("sahayak.seed_demo")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DEMO_USER_ID = "user-demo-student"
DEMO_EMAIL = "demo.student@sahayak.edu"
DEMO_PASSWORD = "DemoStudent2026!"
DEMO_SESSION_ID = "session-demo-photosynthesis"
DEMO_DOC_ID = "doc-demo-photosynthesis"

def seed_demo_data():
    """
    Idempotent seeding script for hackathon evaluators and judges:
    1. Creates or verifies demo student account (demo.student@sahayak.edu / DemoStudent2026!).
    2. Parses and ingests public-domain sample science chapter (photosynthesis_chapter.pdf).
    3. Seeds a grounded, pre-synthesized 3-scene lesson session ready for instant playback.
    """
    init_db()
    db = SessionLocal()
    try:
        repo_root = os.path.dirname(backend_dir)
        sample_pdf_path = os.path.join(repo_root, "samples", "photosynthesis_chapter.pdf")

        if not os.path.exists(sample_pdf_path):
            from scripts.generate_sample_pdf import generate_sample_science_pdf
            generate_sample_science_pdf(sample_pdf_path)

        # 1. Seed Demo User & Learner Profile
        user = db.query(DBUser).filter((DBUser.id == DEMO_USER_ID) | (DBUser.email == DEMO_EMAIL)).first()
        if not user:
            user = DBUser(
                id=DEMO_USER_ID,
                email=DEMO_EMAIL,
                hashed_password=get_password_hash(DEMO_PASSWORD),
                role="student",
                name="Judge Demo Student"
            )
            db.add(user)
            logger.info(f"Created demo student account: {DEMO_EMAIL}")
        else:
            user.hashed_password = get_password_hash(DEMO_PASSWORD)
            logger.info(f"Demo student account verified: {DEMO_EMAIL}")

        profile = db.query(DBLearnerProfile).filter(DBLearnerProfile.user_id == DEMO_USER_ID).first()
        if not profile:
            profile = DBLearnerProfile(
                user_id=DEMO_USER_ID,
                name="Judge Demo Student",
                level="intermediate",
                goal="master_concept",
                preferred_style="visual",
                language="en",
                mastery_json={"Photosynthesis": 0.45, "Cellular Respiration": 0.30}
            )
            db.add(profile)
        db.commit()

        # 2. Ingest Sample Document
        doc = db.query(DBMaterial).filter(DBMaterial.id == DEMO_DOC_ID).first()
        if not doc:
            with open(sample_pdf_path, "rb") as f:
                pdf_bytes = f.read()

            pages = IngestionService.parse_pdf(pdf_bytes)
            full_text = "\n\n".join([p["text"] for p in pages])
            key_topics = ["Photosynthesis", "Light Reactions", "Calvin Cycle", "Cellular Respiration", "Chlorophyll"]

            doc = DBMaterial(
                id=DEMO_DOC_ID,
                filename="photosynthesis_chapter.pdf",
                content_type="application/pdf",
                total_sections=len(pages),
                raw_text=full_text
            )
            db.add(doc)

            for p in pages:
                chunk_id = f"chunk-{DEMO_DOC_ID}-p{p['page_number']}"
                existing_chunk = db.query(DBMaterialChunk).filter(DBMaterialChunk.id == chunk_id).first()
                if not existing_chunk:
                    emb = EmbeddingService.get_embedding(p["text"])
                    chunk = DBMaterialChunk(
                        id=chunk_id,
                        material_id=DEMO_DOC_ID,
                        chapter=p.get("title", f"Page {p['page_number']}"),
                        page=p["page_number"],
                        content=p["text"],
                        embedding=emb,
                        token_count=len(p["text"].split())
                    )
                    db.add(chunk)
            db.commit()
            logger.info(f"Ingested sample PDF ({len(pages)} chunks grounded)")
        else:
            logger.info("Sample document already indexed.")

        # 3. Seed Pre-Generated Grounded Lesson Session (VIDEO_MODE=demo)
        session = db.query(DBLessonSession).filter(DBLessonSession.id == DEMO_SESSION_ID).first()
        
        plan_json = {
            "topic": "Photosynthesis & Bioenergetics",
            "document_id": DEMO_DOC_ID,
            "document_filename": "photosynthesis_chapter.pdf",
            "time_budget_minutes": 15,
            "target_audience": "intermediate",
            "language": "en",
            "segments": [
                {
                    "id": 1,
                    "concept": "Light-Dependent Reactions & Chlorophyll Absorption",
                    "learning_objective": "Understand photon capture, photolysis of water, and why plants reflect green light.",
                    "visual_type": "labeled-diagram",
                    "diagram_title": "Chloroplast Thylakoid Membrane & Light Reactions",
                    "teacher_script": (
                        "Welcome to our lesson on Bioenergetics! Today, let's explore how living systems transform solar light "
                        "into biological fuel. Inside the thylakoid membrane, chlorophyll pigments absorb blue and red light. "
                        "Here is a common trap: plants do not look green because they absorb green light. They appear green "
                        "because green wavelengths are reflected right back to our eyes! Photolysis splits water into oxygen, "
                        "generating the initial ATP and NADPH energy carriers."
                    ),
                    "board_visual": {
                        "type": "diagram",
                        "title": "Light Reactions & Thylakoid Electron Transport",
                        "summary": "Photolysis splits H2O -> 2H+ + 1/2 O2 + 2e-. Chlorophyll absorbs red & blue, reflects green.",
                        "labels": ["Photosystem II (P680)", "Electron Transport Chain", "Photosystem I (P700)", "ATP Synthase"]
                    },
                    "checkpoint_question": "Why do plant leaves appear green under white sunlight?",
                    "options": [
                        "They absorb green wavelengths to power photosynthesis",
                        "Chlorophyll cannot absorb green light efficiently, so it is reflected",
                        "Mitochondria emit green luminescence during cellular respiration",
                        "Water photolysis converts green photons into oxygen"
                    ],
                    "correct_answer": "Chlorophyll cannot absorb green light efficiently, so it is reflected",
                    "source_citations": [f"chunk-{DEMO_DOC_ID}-p1"]
                },
                {
                    "id": 2,
                    "concept": "The Calvin Cycle & Carbon Fixation",
                    "learning_objective": "Master how RuBisCO fixes atmospheric CO2 into glucose using ATP and NADPH.",
                    "visual_type": "labeled-diagram",
                    "diagram_title": "The Three Phases of the Calvin Cycle",
                    "teacher_script": (
                        "Now let us move into the chloroplast stroma for the Calvin cycle. Even without direct light, this cycle "
                        "uses the ATP and NADPH generated in Phase 1. The key enzyme RuBisCO fixes carbon dioxide into 3-PGA, "
                        "which is then reduced into high-energy G3P molecules to synthesize glucose."
                    ),
                    "board_visual": {
                        "type": "diagram",
                        "title": "Calvin Cycle: Fixation, Reduction, Regeneration",
                        "summary": "Carbon Fixation (RuBisCO) -> Reduction (3-PGA to G3P) -> Regeneration of RuBP",
                        "labels": ["RuBisCO Enzyme", "3-PGA Intermediate", "G3P Sugar Precursor", "RuBP Acceptor"]
                    },
                    "checkpoint_question": "Which enzyme catalyzes the initial fixation of carbon dioxide in the Calvin cycle?",
                    "options": ["ATP Synthase", "RuBisCO", "DNA Polymerase", "Pyruvate Kinase"],
                    "correct_answer": "RuBisCO",
                    "source_citations": [f"chunk-{DEMO_DOC_ID}-p2"]
                },
                {
                    "id": 3,
                    "concept": "Cellular Respiration & Chemiosmotic ATP Synthesis",
                    "learning_objective": "Compare aerobic glycolysis and mitochondrial oxidative phosphorylation.",
                    "visual_type": "labeled-diagram",
                    "diagram_title": "Cellular Respiration Metabolic Pathway",
                    "teacher_script": (
                        "Finally, while plants produce glucose, all aerobic organisms break down glucose through cellular respiration. "
                        "From glycolysis in the cytoplasm to the Krebs cycle and oxidative phosphorylation in the mitochondria, "
                        "each glucose molecule yields roughly 30 to 32 ATP molecules to power biological life."
                    ),
                    "board_visual": {
                        "type": "diagram",
                        "title": "Cellular Respiration: Glucose to 32 ATP",
                        "summary": "C6H12O6 + 6O2 -> 6CO2 + 6H2O + 30-32 ATP across 4 metabolic stages.",
                        "labels": ["Cytoplasmic Glycolysis", "Pyruvate Oxidation", "Citric Acid Cycle", "Electron Transport Chain"]
                    },
                    "checkpoint_question": "Where does oxidative phosphorylation take place inside eukaryotic cells?",
                    "options": [
                        "Inner mitochondrial membrane",
                        "Chloroplast stroma",
                        "Cell nucleus",
                        "Extracellular fluid"
                    ],
                    "correct_answer": "Inner mitochondrial membrane",
                    "source_citations": [f"chunk-{DEMO_DOC_ID}-p3"]
                }
            ]
        }

        if not session:
            session = DBLessonSession(
                id=DEMO_SESSION_ID,
                user_id=DEMO_USER_ID,
                topic="Photosynthesis & Bioenergetics",
                language="en",
                time_budget=15,
                current_segment_id=1,
                state="explain",
                plan_json=plan_json,
                taught_concepts=["Photosynthesis Overview", "Chlorophyll Absorption Spectrum"],
                analogies_used=["Solar solar-cell battery charging", "Factory assembly line"]
            )
            db.add(session)
            db.commit()
            logger.info(f"Created demo lesson session: {DEMO_SESSION_ID}")
        else:
            session.plan_json = plan_json
            db.commit()
            logger.info(f"Verified and updated demo lesson session: {DEMO_SESSION_ID}")

        print("\n" + "=" * 65)
        print("[OK] ONE-CLICK JUDGE DEMO ENVIRONMENT SEEDED SUCCESSFULLY")
        print("=" * 65)
        print(f"  * Demo Email:      {DEMO_EMAIL}")
        print(f"  * Demo Password:   {DEMO_PASSWORD}")
        print(f"  * Demo Session ID: {DEMO_SESSION_ID}")
        print(f"  * Demo Document:   {sample_pdf_path}")
        print(f"  * Direct Play URL: http://localhost:3000/lesson/{DEMO_SESSION_ID}")
        print("=" * 65 + "\n")

    except Exception as e:
        logger.error(f"Failed to seed demo data: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_data()
