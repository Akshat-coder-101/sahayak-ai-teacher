from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..services.tts import TTSService

router = APIRouter(prefix="/media", tags=["Media Generation"])

class TTSRequest(BaseModel):
    text: str
    language: Optional[str] = "en"
    voice_id: Optional[str] = None

@router.post("/tts")
async def generate_tts(req: TTSRequest):
    try:
        res = await TTSService.generate_speech(
            text=req.text,
            language=req.language or "en",
            voice_id=req.voice_id
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")
