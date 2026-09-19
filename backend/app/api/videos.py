from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from ..services.youtube import YouTubeService

router = APIRouter(prefix="/videos", tags=["videos"])

@router.get("/recommend")
async def recommend_videos(
    topic: str = Query(..., description="Educational topic or concept to find videos for"),
    language: str = Query("en", description="Target language code (e.g. en, hi, hinglish, ta, te, bn, es)"),
    segment_id: Optional[int] = Query(None, description="Optional current segment id"),
    session_id: Optional[str] = Query(None, description="Optional active session id"),
    context: Optional[str] = Query(None, description="Optional segment pedagogical context or subconcept")
):
    """
    Returns AI-grounded, validated YouTube educational video recommendations.
    Uses real YouTube Data API v3 results and local SQLite caching to prevent hallucination.
    """
    try:
        results = await YouTubeService.find_videos(
            topic=topic,
            language=language,
            segment_context=context
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch video recommendations: {str(e)}")
