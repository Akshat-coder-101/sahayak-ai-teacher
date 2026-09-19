import sys
import os
import logging

# Ensure backend directory is in sys.path so 'app' can always be resolved
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if hasattr(sys.stdout, "reconfigure"):
    getattr(sys.stdout, "reconfigure")(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    getattr(sys.stderr, "reconfigure")(encoding="utf-8")

from typing import Any, Optional
from fastapi import FastAPI, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from app.config import settings
from app.database import init_db, SessionLocal, DBUser, DBLearnerProfile
from app.services.auth import get_current_user, get_password_hash
from app.api import ingest, lesson, interact, assess, report, profile, learning_path, media, sandbox, health, videos, documents, study_tools, auth, video

logger = logging.getLogger("sahayak.main")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

def make_canonical_error(code: str, message: str, path: str, status_code: int, details: Any = None) -> JSONResponse:
    """Helper to return uniform JSON error responses across the entire application."""
    content: dict = {
        "error": {
            "code": code,
            "message": message,
            "path": path,
        }
    }
    if details:
        content["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=content)

def seed_default_users():
    """Seeds baseline learner and teacher accounts for immediate demo and test evaluation."""
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
        logger.warning(f"[Main] Default user seeding skipped: {e}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    try:
        init_db()
    except Exception as e:
        logger.error(f"[Lifespan] Database startup initialization warning: {e}")
    
    # Ensure generated media and document storage directories exist
    media_dir = os.path.join(backend_dir, settings.MEDIA_DIR)
    os.makedirs(media_dir, exist_ok=True)
    doc_dir = os.path.join(backend_dir, settings.DOC_STORAGE_DIR)
    os.makedirs(doc_dir, exist_ok=True)
    
    # Startup Provider Diagnostic Report
    print("=" * 65)
    print(f"🚀  {settings.PROJECT_NAME} v{settings.VERSION} — Provider Diagnostics")
    print("=" * 65)
    print(f"  • LLM Providers:      {'✅ Gemini (' + settings.GEMINI_MODEL + ')' if settings.GEMINI_API_KEY else '⚠️ Gemini missing'}")
    print(f"                        {'✅ Groq (' + settings.GROQ_MODEL + ')' if settings.GROQ_API_KEY else '⚠️ Groq missing'}")
    print(f"                        {'✅ Anthropic (' + settings.ANTHROPIC_MODEL + ')' if settings.ANTHROPIC_API_KEY else '⚠️ Anthropic missing'}")
    print(f"                        Order: {settings.LLM_PROVIDER_ORDER}")
    print(f"  • Embedding Provider: {settings.EMBEDDING_PROVIDER.upper()} ({'✅ Active' if settings.GEMINI_API_KEY else '⚠️ SHA-256 fallback'})")
    print(f"  • TTS Voice Engine:   {'✅ ElevenLabs (' + settings.ELEVENLABS_DEFAULT_VOICE_ID + ')' if settings.ELEVENLABS_API_KEY else '⚠️ Browser Web Speech Fallback'}")
    print(f"  • STT Voice Input:    {'✅ Deepgram Nova-2' if settings.DEEPGRAM_API_KEY else '⚠️ Browser STT Fallback'}")
    print(f"  • Avatar Provider:    {settings.AVATAR_PROVIDER.upper()} ({'✅ Colossyan API' if settings.COLOSSYAN_API_KEY else '✅ Interactive Canvas Fallback'})")
    print(f"  • Vector DB:          {'✅ Pinecone (' + settings.PINECONE_INDEX + ')' if settings.PINECONE_API_KEY else '✅ SQLite Local Hybrid'}")
    print(f"  • Database:           {settings.DATABASE_URL}")
    print("=" * 65)
    yield
    print(f"[{settings.PROJECT_NAME}] Shutdown completed.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Human-Like AI Educator Platform for AI Innovation Hackathon 2026",
    lifespan=lifespan
)

# CORS Configuration with configurable allowed origins (Production / Vercel / Railway)
allowed = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    settings.NEXT_PUBLIC_APP_URL.rstrip("/")
]
if settings.FRONTEND_URL and settings.FRONTEND_URL.strip():
    allowed.append(settings.FRONTEND_URL.strip().rstrip("/"))
if settings.CORS_ORIGINS and settings.CORS_ORIGINS.strip():
    for origin in settings.CORS_ORIGINS.split(","):
        cleaned = origin.strip().rstrip("/")
        if cleaned:
            allowed.append(cleaned)

cors_origins = list(set([o for o in allowed if o]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Open Routes (Auth, Health, Media, Learning Path)
for open_router in [auth, health, media, learning_path]:
    app.include_router(open_router.router, prefix=settings.API_PREFIX)
    app.include_router(open_router.router)

# Register Protected API Routers (Protected by JWT Authentication)
protected_routers = [ingest, lesson, interact, assess, report, profile, sandbox, videos, documents, study_tools, video]
for router_module in protected_routers:
    app.include_router(router_module.router, prefix=settings.API_PREFIX, dependencies=[Depends(get_current_user)])
    app.include_router(router_module.router, dependencies=[Depends(get_current_user)])

# ---------------------------------------------------------------------------
# Media File Serving & Traversal Protection (Section G)
# ---------------------------------------------------------------------------
@app.get("/media/{filepath:path}")
async def serve_media_file(filepath: str, request: Request):
    """
    Securely serves generated media files (mp3, mp4, png, webp).
    Guards against directory traversal and returns canonical JSON 404/403.
    """
    resolved_base = os.path.realpath(os.path.join(backend_dir, settings.MEDIA_DIR))
    target_path = os.path.realpath(os.path.join(resolved_base, filepath.lstrip("/")))
    
    # Guard against path traversal
    if not (target_path.startswith(resolved_base + os.sep) or target_path == resolved_base):
        return make_canonical_error(
            code="forbidden",
            message="Access denied: Invalid file path traversal",
            path=request.url.path,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    if not os.path.exists(target_path) or not os.path.isfile(target_path):
        return make_canonical_error(
            code="media_not_found",
            message=f"Media file '{filepath}' was not found.",
            path=request.url.path,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    return FileResponse(target_path)

# ---------------------------------------------------------------------------
# Canonical JSON Exception Handlers (Section G)
# ---------------------------------------------------------------------------
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code_map = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        409: "conflict",
        422: "unprocessable_entity",
        429: "rate_limit_exceeded",
        500: "internal_error",
    }
    code = code_map.get(exc.status_code, "http_error")
    message = exc.detail if exc.detail else "An HTTP error occurred."
    return make_canonical_error(
        code=code,
        message=message,
        path=request.url.path,
        status_code=exc.status_code
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_msgs = []
    for err in exc.errors():
        loc = " -> ".join([str(l) for l in err.get("loc", []) if l != "body"])
        msg = err.get("msg", "Invalid value")
        error_msgs.append(f"{loc}: {msg}" if loc else msg)
    summary = "; ".join(error_msgs) if error_msgs else "Invalid request payload"
    
    return make_canonical_error(
        code="validation_error",
        message=f"Validation failed: {summary}",
        path=request.url.path,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=[{"loc": err.get("loc"), "msg": err.get("msg"), "type": err.get("type")} for err in exc.errors()]
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception on {request.method} {request.url.path}: {exc}")
    return make_canonical_error(
        code="internal_error",
        message="An unexpected internal server error occurred. Please try again later.",
        path=request.url.path,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

@app.get("/")
def root():
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "state_machine": "understand -> plan -> explain -> demonstrate -> question -> evaluate -> adapt -> assess -> report"
    }

@app.get("/health")
@app.get("/api/health")
def health_status():
    return {"status": "healthy", "service": "sahayak-backend"}

@app.get("/health/ready")
@app.get("/api/health/ready")
def health_readiness():
    from sqlalchemy import text
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1;"))
        db_ok = True
    except Exception as e:
        logger.warning(f"[Health] Database readiness check failed: {e}")
        db_ok = False
    finally:
        db.close()
    
    return {
        "status": "ready" if db_ok else "degraded",
        "database": "connected" if db_ok else "unavailable",
        "database_type": "postgresql" if settings.is_postgres else "sqlite"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.BACKEND_PORT, reload=True)
