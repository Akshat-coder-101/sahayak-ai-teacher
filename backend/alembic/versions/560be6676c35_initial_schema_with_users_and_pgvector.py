"""initial_schema_with_users_and_pgvector

Revision ID: 560be6676c35
Revises: 
Create Date: 2026-09-13 23:43:39.057085

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, sqlite

try:
    import pgvector.sqlalchemy
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False

# revision identifiers, used by Alembic.
revision: str = '560be6676c35'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # 1. Enable pgvector extension on Postgres
    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()

    # 2. Create users table
    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("hashed_password", sa.String(), nullable=False),
            sa.Column("role", sa.String(), nullable=False, server_default="student"),
            sa.Column("name", sa.String(), nullable=False, server_default="Learner"),
            sa.Column("cohort", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=True)

    # 3. Create materials table
    if "materials" not in existing_tables:
        op.create_table(
            "materials",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("filename", sa.String(), nullable=False),
            sa.Column("content_type", sa.String(), nullable=True),
            sa.Column("total_sections", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("raw_text", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )

    # 4. Create material_chunks table with pgvector support
    if "material_chunks" not in existing_tables:
        if is_postgres and HAS_PGVECTOR:
            embedding_col = sa.Column("embedding", pgvector.sqlalchemy.Vector(768), nullable=True)
        else:
            embedding_col = sa.Column("embedding", sa.JSON(), nullable=True)

        op.create_table(
            "material_chunks",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("material_id", sa.String(), nullable=True),
            sa.Column("chapter", sa.String(), nullable=True),
            sa.Column("page", sa.Integer(), nullable=True),
            sa.Column("section", sa.String(), nullable=True),
            sa.Column("content", sa.Text(), nullable=False),
            embedding_col,
            sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        )
        op.create_index("ix_material_chunks_material_id", "material_chunks", ["material_id"])

    # 5. Create lesson_sessions table
    if "lesson_sessions" not in existing_tables:
        op.create_table(
            "lesson_sessions",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("topic", sa.String(), nullable=False),
            sa.Column("language", sa.String(), nullable=False, server_default="en"),
            sa.Column("time_budget", sa.Integer(), nullable=False, server_default="20"),
            sa.Column("current_segment_id", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("state", sa.String(), nullable=False, server_default="understand"),
            sa.Column("plan_json", sa.JSON(), nullable=True),
            sa.Column("taught_concepts", sa.JSON(), nullable=False),
            sa.Column("analogies_used", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_lesson_sessions_user_id", "lesson_sessions", ["user_id"])

    # 6. Create checkpoint_attempts table
    if "checkpoint_attempts" not in existing_tables:
        op.create_table(
            "checkpoint_attempts",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("session_id", sa.String(), nullable=True),
            sa.Column("segment_id", sa.Integer(), nullable=True),
            sa.Column("question_text", sa.Text(), nullable=True),
            sa.Column("student_answer", sa.Text(), nullable=True),
            sa.Column("classification", sa.String(), nullable=True),
            sa.Column("feedback", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_checkpoint_attempts_session_id", "checkpoint_attempts", ["session_id"])

    # 7. Create quizzes & quiz_attempts
    if "quizzes" not in existing_tables:
        op.create_table(
            "quizzes",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("session_id", sa.String(), nullable=True),
            sa.Column("topic", sa.String(), nullable=True),
            sa.Column("questions_json", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_quizzes_session_id", "quizzes", ["session_id"])

    if "quiz_attempts" not in existing_tables:
        op.create_table(
            "quiz_attempts",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("session_id", sa.String(), nullable=True),
            sa.Column("score_percentage", sa.Float(), nullable=True),
            sa.Column("details_json", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_quiz_attempts_session_id", "quiz_attempts", ["session_id"])

    # 8. Create learning_reports
    if "learning_reports" not in existing_tables:
        op.create_table(
            "learning_reports",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("session_id", sa.String(), nullable=True, unique=True),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("topic", sa.String(), nullable=True),
            sa.Column("score_percent", sa.Float(), nullable=True),
            sa.Column("time_spent", sa.Integer(), nullable=True),
            sa.Column("report_json", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_learning_reports_session_id", "learning_reports", ["session_id"], unique=True)
        op.create_index("ix_learning_reports_user_id", "learning_reports", ["user_id"])

    # 9. Create learner_profiles
    if "learner_profiles" not in existing_tables:
        op.create_table(
            "learner_profiles",
            sa.Column("user_id", sa.String(), primary_key=True),
            sa.Column("name", sa.String(), nullable=False, server_default="Learner"),
            sa.Column("level", sa.String(), nullable=False, server_default="beginner"),
            sa.Column("goal", sa.String(), nullable=False, server_default="understand_concept"),
            sa.Column("preferred_style", sa.String(), nullable=False, server_default="visual"),
            sa.Column("language", sa.String(), nullable=False, server_default="en"),
            sa.Column("history_json", sa.JSON(), nullable=False),
            sa.Column("mastery_json", sa.JSON(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )

    # 10. Create learning_paths
    if "learning_paths" not in existing_tables:
        op.create_table(
            "learning_paths",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("topic_id", sa.String(), nullable=True),
            sa.Column("title", sa.String(), nullable=True),
            sa.Column("dag_json", sa.JSON(), nullable=True),
            sa.Column("progress_percentage", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_learning_paths_user_id", "learning_paths", ["user_id"])

    # 11. Create youtube_cache
    if "youtube_cache" not in existing_tables:
        op.create_table(
            "youtube_cache",
            sa.Column("key", sa.String(), primary_key=True),
            sa.Column("payload", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )

    # 12. Create export_jobs
    if "export_jobs" not in existing_tables:
        op.create_table(
            "export_jobs",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("session_id", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False, server_default="queued"),
            sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("video_url", sa.String(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_export_jobs_session_id", "export_jobs", ["session_id"])

def downgrade() -> None:
    bind = op.get_bind()
    for tbl in [
        "export_jobs",
        "youtube_cache",
        "learning_paths",
        "learner_profiles",
        "learning_reports",
        "quiz_attempts",
        "quizzes",
        "checkpoint_attempts",
        "lesson_sessions",
        "material_chunks",
        "materials",
        "users"
    ]:
        op.execute(f"DROP TABLE IF EXISTS {tbl}")
