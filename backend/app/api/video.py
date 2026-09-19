import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_db, DBExportJob, DBLessonSession
from ..models.schemas import (
    VideoGenerateRequest,
    VideoGenerateResponse,
    VideoStatusResponse,
    VideoStepProgress
)
from ..services.video import VideoService
from ..config import settings

logger = logging.getLogger("sahayak.api.video")

router = APIRouter(prefix="/video", tags=["video"])

@router.post("/generate", response_model=VideoGenerateResponse)
async def generate_video(
    req: VideoGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Asynchronously starts generation for an educational video lecture.
    Supports VIDEO_MODE='demo' (2-3 min, 3-4 scenes) or 'full' (15 min, 10-15 scenes).
    Returns immediately with a job_id and 'processing' status.
    """
    if not req.topic and not req.session_id:
        raise HTTPException(
            status_code=400,
            detail="Either 'topic' or 'session_id' must be provided for video generation."
        )

    target_topic = req.topic or ""
    session_id = req.session_id

    if session_id and not target_topic:
        sess = db.query(DBLessonSession).filter(DBLessonSession.id == session_id).first()
        if not sess:
            raise HTTPException(status_code=404, detail=f"Lesson session '{session_id}' not found.")
        target_topic = sess.topic

    mode = req.mode or getattr(settings, "VIDEO_MODE", "demo")
    job_id = f"vjob_{uuid.uuid4().hex[:12]}"
    effective_session_id = session_id or f"sess_{job_id}"

    # Record job in database
    db_job = DBExportJob(
        id=job_id,
        session_id=effective_session_id,
        status="processing",
        progress=5
    )
    db.add(db_job)
    db.commit()

    # Initialize rich real-time progress cache
    initial_steps = [
        {"name": "Synthesize Lesson Plan", "status": "processing"},
        {"name": "RAG Grounding & Visual Blueprints", "status": "pending"},
        {"name": "Multi-Scene Generation", "status": "pending"},
        {"name": "FFmpeg Stream Composition", "status": "pending"}
    ]
    VideoService.set_job_progress(
        job_id,
        status="processing",
        progress=5,
        current_step="Initializing video synthesis pipeline...",
        steps=initial_steps,
        mode=mode,
        session_id=effective_session_id
    )

    # Spawn background worker
    background_tasks.add_task(
        VideoService.generate_standalone_video,
        job_id=job_id,
        topic=target_topic,
        mode=mode,
        language=req.language or "en",
        visual_type=req.visual_type or "labeled-diagram",
        session_id=effective_session_id
    )

    logger.info(f"[API] Video generation enqueued: job_id={job_id}, mode={mode}, topic='{target_topic}'")
    return VideoGenerateResponse(
        job_id=job_id,
        status="processing",
        mode=mode,
        session_id=effective_session_id,
        message=f"Video lecture generation enqueued in {mode.upper()} mode."
    )

@router.get("/status/{job_id}", response_model=VideoStatusResponse)
def get_video_status(job_id: str, db: Session = Depends(get_db)):
    """
    Returns the real-time processing status, progress percentage,
    granular step checklist, and final video_url for a video job.
    """
    # 1. Check in-memory real-time progress cache
    cached = VideoService.get_job_progress(job_id)
    if cached:
        return VideoStatusResponse(
            job_id=cached["job_id"],
            status=cached["status"],
            progress=cached["progress"],
            mode=cached.get("mode", "demo"),
            current_step=cached.get("current_step"),
            steps=[VideoStepProgress(**s) for s in cached.get("steps", [])],
            video_url=cached.get("video_url"),
            error_message=cached.get("error_message"),
            session_id=cached.get("session_id"),
            duration_sec=cached.get("duration_sec")
        )

    # 2. Database fallback
    job = db.query(DBExportJob).filter(DBExportJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Video generation job '{job_id}' not found.")

    return VideoStatusResponse(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        mode="demo",
        current_step="Completed" if job.status == "completed" else job.status,
        steps=[],
        video_url=job.video_url,
        error_message=job.error_message,
        session_id=job.session_id
    )
