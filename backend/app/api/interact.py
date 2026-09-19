import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from ..database import get_db, DBLessonSession
from ..models.schemas import StudentAnswerRequest, InteractionResponse
from ..services.evaluator import EvaluatorService
from ..services.stt import STTService
from ..services.tts import TTSService

logger = logging.getLogger("sahayak.interact")

router = APIRouter(prefix="/interact", tags=["Interactivity & Misconception Loop"])

class SimplificationRequest(BaseModel):
    session_id: str
    segment_id: int
    user_query: Optional[str] = "Can you explain this more simply with another analogy?"

@router.post("/answer", response_model=InteractionResponse)
async def evaluate_answer(
    req: StudentAnswerRequest,
    db: Session = Depends(get_db)
):
    try:
        res = await EvaluatorService.evaluate_student_answer(
            session_id=req.session_id,
            segment_id=req.segment_id,
            student_answer=req.student_answer,
            is_demo_mode=req.is_demo_mode,
            force_misconception=req.force_misconception,
            db=db
        )
        return res
    except Exception as e:
        logger.error(f"Interaction evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Interaction evaluation failed: {str(e)}")

@router.post("/voice-answer", response_model=InteractionResponse)
async def evaluate_voice_answer(
    session_id: str = Form(...),
    segment_id: int = Form(...),
    is_demo_mode: bool = Form(False),
    force_misconception: bool = Form(False),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        audio_bytes = await audio.read()
        content_type = audio.content_type or "audio/wav"
        transcript = await STTService.transcribe_audio(audio_bytes, content_type=content_type)
        
        if not transcript:
            transcript = "I would like to explain my understanding orally."

        res = await EvaluatorService.evaluate_student_answer(
            session_id=session_id,
            segment_id=segment_id,
            student_answer=transcript,
            is_demo_mode=is_demo_mode,
            force_misconception=force_misconception,
            db=db
        )
        
        # Synthesize teacher spoken reply audio
        sess = db.query(DBLessonSession).filter(DBLessonSession.id == session_id).first()
        language = sess.language if sess else "en"
        
        reply_audio_url = None
        try:
            # Generate spoken audio of the feedback
            tts_res = await TTSService.generate_speech(res.feedback, language=language)
            reply_audio_url = tts_res.get("audio_url")
        except Exception as tts_err:
            logger.warning(f"[Interact] Voice answer feedback TTS synthesis failed: {tts_err}")

        res.transcript = transcript
        res.answer_text = res.feedback
        res.audio_url = reply_audio_url

        # Prepend transcript badge to feedback text if not already there
        if transcript and "Heard:" not in res.feedback:
            res.feedback = f"🎙️ *Heard: \"{transcript}\"*\n\n" + res.feedback
            
        return res
    except Exception as e:
        logger.error(f"Voice answer evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Voice answer processing failed: {str(e)}")

@router.post("/request-simplification", response_model=InteractionResponse)
async def request_simplification(
    req: SimplificationRequest,
    db: Session = Depends(get_db)
):
    try:
        # Trigger reteach path with deliberate simplification prompt
        res = await EvaluatorService.evaluate_student_answer(
            session_id=req.session_id,
            segment_id=req.segment_id,
            student_answer=req.user_query or "Please simplify this concept.",
            is_demo_mode=False,
            force_misconception=True,
            db=db
        )
        res.feedback = f"✨ *Simplifying concept with a fresh model:*\n\n{res.feedback}"
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simplification failed: {str(e)}")
