from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.ingestion import IngestionService
from ..models.schemas import IngestResponse

router = APIRouter(prefix="/ingest", tags=["Ingestion & RAG"])

@router.post("", response_model=IngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
            
        result = IngestionService.process_file(file.filename or "uploaded_doc.txt", content, db)
        return IngestResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
