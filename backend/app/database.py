from typing import Optional, Any, List, Dict
from sqlalchemy import create_engine, String, Integer, Float, Text, Boolean, DateTime, JSON, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Mapped, mapped_column
from datetime import datetime, timezone
import json
from .config import settings

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    Vector = None
    HAS_PGVECTOR = False

class Base(DeclarativeBase):
    pass

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

class DBUser(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, default="student", nullable=False)  # "student" | "teacher"
    name: Mapped[str] = mapped_column(String, default="Learner")
    cohort: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)

class DBMaterial(Base):
    __tablename__ = "materials"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    total_sections: Mapped[int] = mapped_column(Integer, default=1)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)

def _get_chunk_embedding_column():
    if settings.is_postgres and HAS_PGVECTOR and Vector is not None:
        return Vector(768)
    return JSON

class DBMaterialChunk(Base):
    __tablename__ = "material_chunks"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    material_id: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    chapter: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    section: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[Any]] = mapped_column(_get_chunk_embedding_column(), nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, default=0)

class DBLessonSession(Base):
    __tablename__ = "lesson_sessions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    topic: Mapped[str] = mapped_column(String, nullable=False)
    language: Mapped[str] = mapped_column(String, default="en")
    time_budget: Mapped[int] = mapped_column(Integer, default=20)
    current_segment_id: Mapped[int] = mapped_column(Integer, default=1)
    state: Mapped[str] = mapped_column(String, default="understand")
    plan_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    taught_concepts: Mapped[List[str]] = mapped_column(JSON, default=list)
    analogies_used: Mapped[List[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now, onupdate=get_utc_now)

class DBCheckpointAttempt(Base):
    __tablename__ = "checkpoint_attempts"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    segment_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    question_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    student_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    classification: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)

class DBQuiz(Base):
    __tablename__ = "quizzes"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    topic: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    questions_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)

class DBQuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    score_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    details_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)

class DBLearningReport(Base):
    __tablename__ = "learning_reports"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[Optional[str]] = mapped_column(String, index=True, unique=True, nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    topic: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    score_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    time_spent: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    report_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)

class DBLearnerProfile(Base):
    __tablename__ = "learner_profiles"
    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, default="Learner")
    level: Mapped[str] = mapped_column(String, default="beginner")
    goal: Mapped[str] = mapped_column(String, default="understand_concept")
    preferred_style: Mapped[str] = mapped_column(String, default="visual")
    language: Mapped[str] = mapped_column(String, default="en")
    history_json: Mapped[List[Any]] = mapped_column(JSON, default=list)
    mastery_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now, onupdate=get_utc_now)

class DBLearningPath(Base):
    __tablename__ = "learning_paths"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    topic_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    dag_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    progress_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now, onupdate=get_utc_now)

class DBYouTubeCache(Base):
    __tablename__ = "youtube_cache"
    key: Mapped[str] = mapped_column(String, primary_key=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)

class DBExportJob(Base):
    __tablename__ = "export_jobs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String, default="queued") # queued, processing, completed, failed
    progress: Mapped[int] = mapped_column(Integer, default=0)
    video_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_now, onupdate=get_utc_now)

# Engine initialization
if settings.is_postgres:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_default_users():
    from .services.auth import get_password_hash
    db = SessionLocal()
    try:
        seeds = [
            ("user-pranjal", "pranjal@sahayak.edu", "Pranjal Mishra", "student", "advanced"),
            ("user-teacher", "teacher@sahayak.edu", "Teacher Master", "teacher", "advanced"),
            ("user-aarav", "aarav.highschool@edu.in", "Aarav Sharma", "student", "beginner"),
            ("user-priya", "priya.research@mit.edu", "Dr. Priya Patel", "student", "intermediate"),
        ]
        for uid, email, name, role, lvl in seeds:
            existing_user = db.query(DBUser).filter((DBUser.id == uid) | (DBUser.email == email)).first()
            if not existing_user:
                u = DBUser(
                    id=uid,
                    email=email,
                    hashed_password=get_password_hash("password123"),
                    role=role,
                    name=name
                )
                db.add(u)
            existing_profile = db.query(DBLearnerProfile).filter(DBLearnerProfile.user_id == uid).first()
            if not existing_profile:
                p = DBLearnerProfile(
                    user_id=uid,
                    name=name,
                    level=lvl,
                    goal="master_concept",
                    preferred_style="visual",
                    language="en"
                )
                db.add(p)
        db.commit()
    except Exception as e:
        import logging
        logging.getLogger("sahayak.db").warning(f"Default user seeding skipped: {e}")
    finally:
        db.close()

def init_db():
    if settings.is_postgres:
        try:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
        except Exception as e:
            import logging
            logging.getLogger("sahayak.db").warning(f"Could not enable pgvector extension: {e}")
    Base.metadata.create_all(bind=engine)
    seed_default_users()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
