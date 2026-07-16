from app.connection import get_supabase
from app.integrations.notion_client import get_notion

def _extract_title(prop: dict) -> str | None:
    items = prop.get("title", [])
    return items[0]["plain_text"] if items else None

def _extract_rich_text(prop: dict) -> str | None:
    items = prop.get("rich_text", [])
    return items[0]["plain_text"] if items else None

def _extract_select(prop: dict) -> str | None:
    select = prop.get("select")
    return select["name"] if select else None

def _extract_date(prop: dict) -> str | None:
    date = prop.get("date")
    return date["start"] if date else None

def _extract_url(prop: dict) -> str | None:
    return prop.get("url")

def fetch_facility_from_notion(page_id: str) -> dict:
    notion = get_notion()
    page = notion.pages.retrieve(page_id=page_id)
    props = page["properties"]

    return {
        "notion_page_id": page["id"],
        "name": _extract_title(props["facility name"]),
        "service_type": _extract_select(props["サービス種別"]),
        "contact_name": _extract_rich_text(props["担当者名"]),
        "contact_email": _extract_rich_text(props["Mail"]),
        "submission_deadline": _extract_date(props["提出期限"]),
        "dropbox_folder_path": _extract_url(props["Dropbox"]),
    }

def upsert_facility_from_notion(page_id: str) -> dict:
    """
    Fetches the facility page from Notion and upserts it into the
    `facilities` table, keyed on notion_page_id.
    """
    data = fetch_facility_from_notion(page_id)
    supabase = get_supabase()

    result = (
        supabase.table("facilities")
        .upsert(data, on_conflict="notion_page_id")
        .execute()
    )

    return result.data[0]