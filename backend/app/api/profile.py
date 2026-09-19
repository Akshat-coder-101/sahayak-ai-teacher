from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..database import get_db, DBLearnerProfile, DBUser
from ..models.schemas import LearnerProfile, LearnerProfileCreate
from ..services.learner_profile import LearnerProfileService
from ..services.auth import get_current_user

router = APIRouter(prefix="/profile", tags=["Learner Profile & History"])

def check_profile_access(current_user: DBUser, target_user_id: str, db: Session):
    # Teacher has access
    if current_user.role == "teacher":
        if current_user.cohort:
            target_user = db.query(DBUser).filter(DBUser.id == target_user_id).first()
            if target_user and target_user.cohort and target_user.cohort != current_user.cohort:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="Forbidden: Student is not in your cohort."
                )
        return

    # Student can only access their own profile
    if current_user.id != target_user_id and current_user.email != target_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You cannot access another student's profile."
        )

@router.get("/{user_id}", response_model=LearnerProfile)
def get_profile(
    user_id: str, 
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_profile_access(current_user, user_id, db)
    try:
        return LearnerProfileService.get_full_learner_profile(user_id, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch profile: {str(e)}")

@router.post("/{user_id}", response_model=LearnerProfile)
def update_profile(
    user_id: str,
    update_data: LearnerProfileCreate,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_profile_access(current_user, user_id, db)
    try:
        p = LearnerProfileService.get_or_create_profile(user_id, db)
        p.name = update_data.name
        p.level = update_data.level
        p.goal = update_data.goal
        p.preferred_style = update_data.preferred_style
        p.language = update_data.language
        db.commit()

        return LearnerProfileService.get_full_learner_profile(user_id, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")

@router.get("/{user_id}/learning-history", response_model=List[Dict[str, Any]])
def get_learning_history(
    user_id: str, 
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_profile_access(current_user, user_id, db)
    try:
        return LearnerProfileService.get_learning_history(user_id, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch learning history: {str(e)}")
