from fastapi import APIRouter, Query
from app.services.documents.required_service import get_required_documents

router = APIRouter()

@router.get("/required")
def list_required_documents(service_type: str = Query(...)):
    return get_required_documents(service_type)