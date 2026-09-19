import os
from dotenv import load_dotenv

# Load environment variables from current directory or parent directory
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "Sahayak AI Teacher"
    VERSION: str = "1.0.0"
    ENV: str = os.getenv("ENV", os.getenv("ENVIRONMENT", "development"))
    API_PREFIX: str = "/api"
    BACKEND_PORT: int = int(os.getenv("PORT", os.getenv("BACKEND_PORT", "8000")))
    
    # LLM
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-7-sonnet-20250219")
    LLM_PROVIDER_ORDER: str = os.getenv("LLM_PROVIDER_ORDER", "gemini,groq,anthropic")
    
    # Embedding / RAG
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "gemini")  # gemini | deterministic
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
    
    # TTS
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_DEFAULT_VOICE_ID: str = os.getenv("ELEVENLABS_DEFAULT_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    
    # STT
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")
    DEEPGRAM_MODEL: str = os.getenv("DEEPGRAM_MODEL", "nova-2")
    
    # Avatar & Video Generation (Free + Paid Provider Suite)
    # Options: free_avatar | did | heygen | synthesia | tavus | hedra | colossyan | replicate | huggingface
    AVATAR_PROVIDER: str = os.getenv("AVATAR_PROVIDER", "free_avatar")
    
    # Paid Provider API Keys & Settings
    DID_API_KEY: str = os.getenv("DID_API_KEY", "")
    HEYGEN_API_KEY: str = os.getenv("HEYGEN_API_KEY", "")
    SYNTHESIA_API_KEY: str = os.getenv("SYNTHESIA_API_KEY", "")
    TAVUS_API_KEY: str = os.getenv("TAVUS_API_KEY", "")
    TAVUS_REPLICA_ID: str = os.getenv("TAVUS_REPLICA_ID", "r79e1c0369")
    HEDRA_API_KEY: str = os.getenv("HEDRA_API_KEY", "")
    COLOSSYAN_API_KEY: str = os.getenv("COLOSSYAN_API_KEY", "")
    REPLICATE_API_TOKEN: str = os.getenv("REPLICATE_API_TOKEN", "")
    HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY", "")
    
    AVATAR_DEFAULT_ID: str = os.getenv("AVATAR_DEFAULT_ID", "amy-j37u")
    TEACHER_IMAGE_URL: str = os.getenv("TEACHER_IMAGE_URL", "")

    # Database & Vector DB
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sahayak.db').replace(os.sep, '/')}"
    )
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SUPABASE_STORAGE_BUCKET: str = os.getenv("SUPABASE_STORAGE_BUCKET", "lesson-media")
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX: str = os.getenv("PINECONE_INDEX", "ai-teacher-index")
    PINECONE_HOST: str = os.getenv("PINECONE_HOST", "")
    
    # Media & Storage
    MEDIA_DIR: str = os.getenv("MEDIA_DIR", "generated_media")
    DOC_STORAGE_DIR: str = os.getenv("DOC_STORAGE_DIR", "uploaded_docs")
    VIDEO_MODE: str = os.getenv("VIDEO_MODE", "demo")  # "demo" (2-3 min, 3-4 scenes) or "full" (15 min, 10-15 scenes)
    VIDEO_CACHE_DIR: str = os.getenv("VIDEO_CACHE_DIR", "generated_media/cache")
    
    # App & CORS
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "")
    NEXT_PUBLIC_APP_URL: str = os.getenv("NEXT_PUBLIC_APP_URL", "http://localhost:3000")
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "en")
    SUPPORTED_LANGUAGES: str = os.getenv("SUPPORTED_LANGUAGES", "en,hi,hinglish,ta,te,bn,es")
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "25"))
    
    # YouTube Data API (Related Video Grounding)
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
    YOUTUBE_MAX_RESULTS: int = int(os.getenv("YOUTUBE_MAX_RESULTS", "3"))
    YOUTUBE_CACHE_TTL_HOURS: int = int(os.getenv("YOUTUBE_CACHE_TTL_HOURS", "168"))
    
    # JWT & Authentication
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY") or os.getenv("JWT_SECRET") or "sahayak-insecure-secret-key-change-in-production-2026"
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    @property
    def is_postgres(self) -> bool:
        return self.DATABASE_URL.startswith("postgresql") or self.DATABASE_URL.startswith("postgres")

    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

settings = Settings()
