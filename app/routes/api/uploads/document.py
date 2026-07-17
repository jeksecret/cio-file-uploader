from fastapi import APIRouter, Depends, UploadFile, File
from app.auth.deps import require_facility_session
from app.services.uploads.document_service import upload_required_document

router = APIRouter()

@router.post("/{required_doc_id}")
async def upload_document(
    required_doc_id: int,
    files: list[UploadFile] = File(...),
    facility: dict = Depends(require_facility_session),
):
    file_data = [(f.filename, await f.read()) for f in files]
    return upload_required_document(facility, required_doc_id, file_data)