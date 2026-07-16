from fastapi import APIRouter, HTTPException
from app.services.facility.notion_facility_service import upsert_facility_from_notion

router = APIRouter()

@router.post("/sync/{notion_page_id}")
def sync_facility(notion_page_id: str):
    try:
        facility = upsert_facility_from_notion(notion_page_id)
    except KeyError as e:
        print(f"{e}")
        raise HTTPException(
            status_code=502,
            detail=f"Notion page is missing expected property: {e}",
        )
    except Exception as e:
        print(f"{e}")
        raise HTTPException(status_code=502, detail=f"Notion sync failed: {e}")

    return facility