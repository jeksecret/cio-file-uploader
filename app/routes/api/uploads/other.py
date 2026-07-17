from fastapi import APIRouter, Depends, UploadFile, File
from app.auth.deps import require_facility_session
from app.services.uploads.other_service import upload_other_files

router = APIRouter()

@router.post("/other")
async def upload_other(
    files: list[UploadFile] = File(...),
    facility: dict = Depends(require_facility_session),
):
    file_data = [(f.filename, await f.read()) for f in files]
    return upload_other_files(facility, file_data)