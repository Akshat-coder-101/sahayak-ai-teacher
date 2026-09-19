from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.schemas import (
    TeacherPersonalityConfig,
    FlashcardSet,
    FlashcardReviewRequest,
    StudyNotes,
    HomeworkAssignment,
    ExamPrepPlan,
    ExamPrepRequest,
    StudyPlan,
    StudyPlanRequest,
    StudyPlanRecalculateRequest,
    LearningAnalyticsData,
    RevisionSessionRequest
)
from ..services.study_tools import StudyToolsService
from ..services.learner_profile import LearnerProfileService

router = APIRouter(prefix="/study-tools", tags=["Advanced Study Tools & Analytics"])

# 1. Teacher Personalities
@router.get("/personalities", response_model=List[TeacherPersonalityConfig])
def get_teacher_personalities():
    return StudyToolsService.get_personalities()

@router.post("/personalities/select")
def set_teacher_personality(
    user_id: str = Query(default="default-user"),
    personality: str = Query(default="socratic"),
    db: Session = Depends(get_db)
):
    try:
        p = LearnerProfileService.get_or_create_profile(user_id, db)
        p.preferred_style = personality # align preferred style / personality
        db.commit()
        return {
            "user_id": user_id,
            "teacher_personality": personality,
            "config": StudyToolsService.get_personality_config(personality)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set teacher personality: {str(e)}")

# 2. Revision Mode
@router.post("/revision-session")
def create_revision_session(
    request: RevisionSessionRequest,
    db: Session = Depends(get_db)
):
    try:
        return StudyToolsService.generate_revision_lesson_plan(
            user_id=request.user_id,
            topic=request.topic,
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate revision session: {str(e)}")

# 3. Flashcards
@router.post("/flashcards/generate", response_model=FlashcardSet)
async def generate_flashcards(
    topic: str = Query(...),
    user_id: str = Query(default="default-user"),
    session_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    try:
        return await StudyToolsService.generate_flashcards(
            user_id=user_id,
            topic=topic,
            session_id=session_id,
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate flashcards: {str(e)}")

@router.post("/flashcards/review")
def review_flashcard(
    review: FlashcardReviewRequest,
    db: Session = Depends(get_db)
):
    try:
        return StudyToolsService.record_flashcard_review(
            user_id=review.user_id,
            card_id=review.card_id,
            concept=review.concept,
            result=review.result,
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record flashcard review: {str(e)}")

# 4. Automatic Notes
@router.post("/notes/generate", response_model=StudyNotes)
async def generate_study_notes(
    topic: str = Query(...),
    user_id: str = Query(default="default-user"),
    session_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    try:
        return await StudyToolsService.generate_notes(
            user_id=user_id,
            topic=topic,
            session_id=session_id,
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate study notes: {str(e)}")

# 5. Personalized Homework
@router.post("/homework/generate", response_model=HomeworkAssignment)
def generate_homework(
    topic: str = Query(...),
    user_id: str = Query(default="default-user"),
    session_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    try:
        return StudyToolsService.generate_personalized_homework(
            user_id=user_id,
            topic=topic,
            session_id=session_id,
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate homework: {str(e)}")

# 6. Exam Preparation Mode
@router.post("/exam-prep/generate", response_model=ExamPrepPlan)
def generate_exam_prep(
    request: ExamPrepRequest,
    db: Session = Depends(get_db)
):
    try:
        return StudyToolsService.generate_exam_prep(
            user_id=request.user_id,
            subject=request.subject,
            days_until_exam=request.days_until_exam,
            target_score_percent=request.target_score_percent,
            daily_study_hours=request.daily_study_hours,
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate exam prep plan: {str(e)}")

# 7. Automatic Study Planner
@router.post("/study-plan/generate", response_model=StudyPlan)
def generate_study_plan(
    request: StudyPlanRequest,
    db: Session = Depends(get_db)
):
    try:
        return StudyToolsService.generate_study_plan(
            user_id=request.user_id,
            topic_id=request.topic_id,
            daily_minutes=request.daily_minutes,
            target_days=request.target_days,
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate study plan: {str(e)}")

@router.post("/study-plan/recalculate", response_model=StudyPlan)
def recalculate_study_plan(
    request: StudyPlanRecalculateRequest,
    db: Session = Depends(get_db)
):
    try:
        return StudyToolsService.recalculate_study_plan(
            user_id=request.user_id,
            topic_id=request.topic_id,
            missed_up_to_day=request.missed_up_to_day,
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recalculate study plan: {str(e)}")

# 8. Learning Analytics
@router.get("/analytics/{user_id}", response_model=LearningAnalyticsData)
def get_learning_analytics(
    user_id: str,
    db: Session = Depends(get_db)
):
    try:
        return StudyToolsService.get_learning_analytics(user_id=user_id, db=db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch learning analytics: {str(e)}")
