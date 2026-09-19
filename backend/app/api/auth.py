import uuid
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session

from ..database import get_db, DBUser, DBLearnerProfile
from ..services.auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_user
)

router = APIRouter(prefix="/auth", tags=["Authentication & Access Control"])

class RegisterRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=4)
    name: Optional[str] = "Learner"
    role: str = "student"  # "student" | "teacher"
    level: Optional[str] = "intermediate"

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

def _set_auth_cookie(response: Response, token: str):
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in HTTPS/Production environments
        max_age=86400  # 24 hours
    )

@router.post("/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    req: RegisterRequest, 
    response: Response, 
    db: Session = Depends(get_db)
):
    normalized_email = req.email.strip().lower()
    if not normalized_email or "@" not in normalized_email:
        raise HTTPException(status_code=400, detail="Invalid email address.")
    
    if req.role not in ["student", "teacher"]:
        raise HTTPException(status_code=400, detail="Role must be 'student' or 'teacher'.")

    existing = db.query(DBUser).filter(DBUser.email == normalized_email).first()
    if existing:
        raise HTTPException(status_code=409, detail="A user with this email already exists.")

    user_id = f"user-{uuid.uuid4().hex[:12]}"
    hashed_pwd = get_password_hash(req.password)
    new_user = DBUser(
        id=user_id,
        email=normalized_email,
        hashed_password=hashed_pwd,
        role=req.role,
        name=req.name or "Learner"
    )
    db.add(new_user)

    # Initialize learner profile if student
    existing_profile = db.query(DBLearnerProfile).filter(DBLearnerProfile.user_id == user_id).first()
    if not existing_profile:
        new_profile = DBLearnerProfile(
            user_id=user_id,
            name=new_user.name,
            level=req.level or "intermediate",
            goal="master_concept",
            preferred_style="visual",
            language="en"
        )
        db.add(new_profile)

    db.commit()
    db.refresh(new_user)

    token = create_access_token(data={"sub": new_user.id, "email": new_user.email, "role": new_user.role})
    _set_auth_cookie(response, token)

    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=new_user.id,
            email=new_user.email,
            name=new_user.name,
            role=new_user.role
        )
    )

@router.post("/login", response_model=AuthTokenResponse)
def login_user(
    req: LoginRequest, 
    response: Response, 
    db: Session = Depends(get_db)
):
    normalized_email = req.email.strip().lower()
    user = db.query(DBUser).filter(DBUser.email == normalized_email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = create_access_token(data={"sub": user.id, "email": user.email, "role": user.role})
    _set_auth_cookie(response, token)

    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role
        )
    )

@router.post("/logout")
def logout_user(response: Response):
    response.delete_cookie("access_token")
    return {"success": True, "message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: DBUser = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role
    )
