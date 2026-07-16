from fastapi import APIRouter, Depends
from app.auth.deps import require_facility_session
from app.services.facility.me_service import get_facility_mypage

router = APIRouter()

@router.get("/me")
def get_me(facility: dict = Depends(require_facility_session)):
    return get_facility_mypage(facility)