from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db, DBLessonSession, DBUser
from ..models.schemas import LearningReport
from ..services.assessment import AssessmentService
from ..services.auth import get_current_user

router = APIRouter(prefix="/report", tags=["Learning Report"])

@router.get("/{session_id}", response_model=LearningReport)
async def get_session_report(
    session_id: str,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify session access scope
    session = db.query(DBLessonSession).filter(DBLessonSession.id == session_id).first()
    if session and session.user_id and session.user_id not in ("default-user", "user-default"):
        if current_user.role == "student":
            if current_user.id != session.user_id and current_user.email != session.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: You cannot access another student's report."
                )
        elif current_user.role == "teacher" and current_user.cohort:
            target_user = db.query(DBUser).filter(DBUser.id == session.user_id).first()
            if target_user and target_user.cohort and target_user.cohort != current_user.cohort:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: Student report is outside your cohort."
                )

    try:
        report = await AssessmentService.build_learning_report(session_id, db)
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report build failed: {str(e)}")
