from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services.code_sandbox import CodeSandboxService

router = APIRouter(prefix="/sandbox", tags=["Code Sandbox Execution"])

class PythonRunRequest(BaseModel):
    code: str
    timeout_seconds: int = 5

@router.post("/run")
def run_python_code(req: PythonRunRequest):
    try:
        res = CodeSandboxService.execute_python_code(req.code, timeout_seconds=req.timeout_seconds)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")
