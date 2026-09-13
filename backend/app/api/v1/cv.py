from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models import CVParseResponse
from app.services.cv_parser import parse_cv

router = APIRouter(prefix="/cv", tags=["CV"])

@router.post("/upload", response_model=CVParseResponse)
async def upload_cv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only .pdf and .docx are supported.")
    contents = await file.read()
    return await parse_cv(contents, file.filename)