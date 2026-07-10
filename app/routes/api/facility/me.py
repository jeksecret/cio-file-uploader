from fastapi import APIRouter, Depends
from app.auth.deps import require_facility_session

router = APIRouter()

@router.get("/me")
def get_me(facility: dict = Depends(require_facility_session)):
    return {
        "id": facility["id"],
        "name": facility["name"],
        "service_type": facility["service_type"],
        "submission_deadline": facility["submission_deadline"],
    }