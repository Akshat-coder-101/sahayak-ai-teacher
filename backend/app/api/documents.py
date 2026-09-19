import logging
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from ..database import get_db, DBMaterial, DBMaterialChunk
from ..services.ingestion import IngestionService
from ..models.schemas import (
    DocumentUploadResponse, 
    LessonPlan, 
    LearnerProfileCreate,
    ParsedStudentInstruction
)
from ..state_machine.teacher_agent import TeacherAgentStateMachine

logger = logging.getLogger("sahayak.documents")

router = APIRouter(prefix="/documents", tags=["Documents & RAG Grounding"])

class DocumentPlanRequest(BaseModel):
    time_budget_minutes: Optional[int] = 20
    language: Optional[str] = "en"
    learner_profile: Optional[LearnerProfileCreate] = None
    instruction: Optional[str] = None
    target_chapter: Optional[str] = None

class ParseInstructionRequest(BaseModel):
    instruction: str

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and ingest PDF, DOCX, PPTX, or TXT documents.
    Enforces maximum upload size (25MB), file type restrictions, non-empty content,
    and safe disk persistence before chunking, embedding, and extracting key topics.
    """
    filename = getattr(file, "filename", None) or "uploaded_document.txt"
    try:
        content = await file.read()
        
        # Validation and ingestion pipeline
        result = await IngestionService.process_document_upload(
            filename=filename,
            content=content,
            db=db
        )
        return DocumentUploadResponse(**result)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Document ingestion failed for filename=%s", filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document ingestion failed. Please check the file and try again."
        )

@router.post("/{document_id}/parse-instruction", response_model=ParsedStudentInstruction)
async def parse_instruction_for_document(
    document_id: str,
    req: ParseInstructionRequest,
    db: Session = Depends(get_db)
):
    """
    Parses natural student instruction into structured pedagogical parameters.
    """
    try:
        db_mat = db.query(DBMaterial).filter(DBMaterial.id == document_id).first()
        if not db_mat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{document_id}' not found."
            )
        filename = db_mat.filename or "Uploaded Document"
        chunks = db.query(DBMaterialChunk).filter(DBMaterialChunk.material_id == document_id).all()
        avail_chapters = list(dict.fromkeys([c.chapter for c in chunks if c.chapter]))[:15]
        
        parsed = await TeacherAgentStateMachine.parse_student_instruction(
            instruction=req.instruction,
            filename=filename,
            available_chapters=avail_chapters
        )
        return parsed
    except HTTPException:
        raise
    except Exception:
        logger.exception("Instruction parsing failed for document_id=%s", document_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Instruction parsing failed. Please try again."
        )

@router.post("/{document_id}/plan", response_model=LessonPlan)
async def plan_lesson_from_document(
    document_id: str,
    req: DocumentPlanRequest = DocumentPlanRequest(),
    db: Session = Depends(get_db)
):
    """
    Generate a strictly grounded adaptive lesson plan from an ingested document and instruction.
    Segments cover representative chunks across the document/chapter and contain source citations.
    """
    try:
        db_mat = db.query(DBMaterial).filter(DBMaterial.id == document_id).first()
        if not db_mat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{document_id}' not found."
            )
        plan = await TeacherAgentStateMachine.plan_from_document(
            document_id=document_id,
            time_budget_minutes=req.time_budget_minutes or 20,
            language=req.language or "en",
            learner_profile=req.learner_profile,
            instruction=req.instruction,
            target_chapter=req.target_chapter,
            db=db
        )
        return plan
    except HTTPException:
        raise
    except Exception:
        logger.exception("Grounded lesson planning failed for document_id=%s", document_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Grounded lesson planning failed. Please try again."
        )
