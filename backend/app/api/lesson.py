import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Body, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from ..config import settings
from ..database import get_db, DBLessonSession, DBExportJob
from ..models.schemas import (
    LessonPlan, 
    LessonPlanRequest, 
    LessonSegmentRender, 
    LanguageSwitchRequest,
    ExportJobResponse,
    ExportJobStatusResponse
)
from ..state_machine.teacher_agent import TeacherAgentStateMachine
from ..services.llm import LLMService
from ..services.video import VideoService

router = APIRouter(prefix="/lesson", tags=["Lesson Planning & Rendering"])

class SegmentRenderPayload(BaseModel):
    session_id: Optional[str] = None
    language: Optional[str] = None

@router.post("/plan", response_model=LessonPlan)
async def create_lesson_plan(
    req: LessonPlanRequest,
    db: Session = Depends(get_db)
):
    try:
        plan = await TeacherAgentStateMachine.generate_lesson_plan(
            topic=req.topic,
            material_id=req.material_id or req.document_id,
            profile=req.learner_profile,
            time_budget_minutes=req.time_budget_minutes or 20,
            language=req.language or "en",
            instruction=req.instruction,
            target_chapter=req.target_chapter,
            db=db
        )
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lesson planning failed: {str(e)}")

@router.get("/plan/{session_id}", response_model=LessonPlan)
@router.get("/plan", response_model=LessonPlan)
def get_lesson_plan(
    session_id: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    if not session_id:
        # Fetch the latest session as fallback
        sess = db.query(DBLessonSession).order_by(DBLessonSession.created_at.desc()).first()
    else:
        sess = db.query(DBLessonSession).filter(DBLessonSession.id == session_id).first()

    if not sess or not sess.plan_json:
        raise HTTPException(status_code=404, detail="Session not found")
    
    plan_data = sess.plan_json
    if isinstance(plan_data, str):
        import json
        try:
            plan_data = json.loads(plan_data)
        except Exception:
            pass
            
    return LessonPlan.model_validate(plan_data)

@router.api_route("/segment/{segment_id}/render", methods=["GET", "POST"], response_model=LessonSegmentRender)
async def render_segment(
    segment_id: int,
    session_id: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    body: Optional[SegmentRenderPayload] = Body(None),
    db: Session = Depends(get_db)
):
    try:
        # Extract session_id from query or body
        effective_session_id = session_id or (body.session_id if body else None)
        effective_lang = language or (body.language if body else None)

        if not effective_session_id:
            # Fallback to latest session in DB
            sess = db.query(DBLessonSession).order_by(DBLessonSession.created_at.desc()).first()
            if sess:
                effective_session_id = sess.id
            else:
                # Create a demo session on the fly
                plan = await TeacherAgentStateMachine.generate_lesson_plan(
                    topic="Newton's Laws and Mechanical Energy",
                    material_id=None,
                    profile=None,
                    time_budget_minutes=20,
                    language="en",
                    db=db
                )
                effective_session_id = plan.session_id

        segment_payload = await TeacherAgentStateMachine.render_segment(
            session_id=effective_session_id,
            segment_id=segment_id,
            language=effective_lang,
            db=db
        )
        return segment_payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Segment rendering failed: {str(e)}")

@router.post("/language-switch", response_model=LessonSegmentRender)
async def switch_language(
    req: LanguageSwitchRequest,
    db: Session = Depends(get_db)
):
    sess = db.query(DBLessonSession).filter(DBLessonSession.id == req.session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    sess.language = req.target_language
    db.commit()

    # Regenerate current segment without losing progress or analogies
    segment_payload = await TeacherAgentStateMachine.render_segment(
        session_id=req.session_id,
        segment_id=req.current_segment_id,
        language=req.target_language,
        db=db
    )
    return segment_payload

@router.api_route("/segment/{segment_id}/stream", methods=["GET", "POST"])
async def stream_segment_explanation(
    segment_id: int,
    session_id: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    body: Optional[SegmentRenderPayload] = Body(None),
    db: Session = Depends(get_db)
):
    effective_session_id = session_id or (body.session_id if body else None)
    effective_lang = language or (body.language if body else None) or "en"
    
    concept = "Educational Principle"
    if effective_session_id:
        sess = db.query(DBLessonSession).filter(DBLessonSession.id == effective_session_id).first()
        if sess and sess.plan_json:
            segments = sess.plan_json.get("segments", []) if isinstance(sess.plan_json, dict) else []
            seg = next((s for s in segments if s.get("id") == segment_id), None)
            if seg:
                concept = seg.get("concept", sess.topic)
            else:
                concept = sess.topic

    system_prompt = f"You are Sahayak AI Teacher explaining '{concept}' in {effective_lang}. Deliver clear, engaging, intuitive pedagogical explanations."
    user_prompt = f"Explain the core mechanics and intuition of {concept}."

    async def event_generator():
        try:
            async for token in LLMService.stream_response(system_prompt, user_prompt, temperature=0.3):
                yield f"data: {token}\n\n"
        except Exception as e:
            yield f"data: {str(e)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/{session_id}/export", response_model=ExportJobResponse)
async def export_lesson_video(
    session_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Spawns an asynchronous rendering job to stitch all lesson segments into an MP4 export.
    Returns the job_id immediately so frontend can monitor progress without blocking.
    """
    sess = db.query(DBLessonSession).filter(DBLessonSession.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Lesson session not found")

    job_id = str(uuid.uuid4())
    job = DBExportJob(
        id=job_id,
        session_id=session_id,
        status="queued",
        progress=0
    )
    db.add(job)
    db.commit()

    # Enqueue background export task
    background_tasks.add_task(VideoService.export_full_lesson_video, job_id=job_id, session_id=session_id)

    return ExportJobResponse(
        job_id=job_id,
        session_id=session_id,
        status="queued",
        progress=0
    )


@router.get("/export/{job_id}/status", response_model=ExportJobStatusResponse)
def get_export_job_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns current rendering progress and status for an export job.
    """
    job = db.query(DBExportJob).filter(DBExportJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")

    return ExportJobStatusResponse(
        job_id=job.id,
        session_id=job.session_id,
        status=job.status,
        progress=job.progress,
        video_url=job.video_url,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at
    )


@router.get("/export/{job_id}/download")
def download_exported_lesson_video(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Serves the completed exported lesson MP4 file with attachment download headers.
    """
    job = db.query(DBExportJob).filter(DBExportJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")

    if job.status != "completed" or not job.video_url:
        raise HTTPException(status_code=400, detail=f"Export job is in status '{job.status}'; video is not ready.")

    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    filename = os.path.basename(job.video_url)
    file_path = os.path.join(backend_dir, settings.MEDIA_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Exported video file not found on disk")

    sess = db.query(DBLessonSession).filter(DBLessonSession.id == job.session_id).first()
    safe_topic = (sess.topic if sess else "lesson").replace(" ", "_").replace("/", "_")[:30]
    download_name = f"Sahayak_Lesson_{safe_topic}.mp4"

    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=download_name
    )

