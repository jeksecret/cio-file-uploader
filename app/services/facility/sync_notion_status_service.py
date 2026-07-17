from datetime import datetime
from app.connection import get_supabase
from app.integrations.notion_client import update_notion_page

def _format_status_line(doc: dict) -> str:
    if doc["status"] == "submitted" and doc["submitted_at"]:
        dt = datetime.fromisoformat(doc["submitted_at"].replace("Z", "+00:00"))
        formatted = dt.strftime("%Y-%m-%d %H:%M")
        return f"{doc['document_name']}: 提出済み({formatted})"
    return f"{doc['document_name']}: 未提出"

def sync_notion_submission_status(facility_id: int, other_file_submitted_at: str | None = None) -> None:
    """
    Pushes current submission status (per document) and, optionally, the
    latest other-file submission timestamp back to the facility's Notion page.
    Called after every successful upload (required doc or other file).
    """
    supabase = get_supabase()

    facility_result = (
        supabase.table("facilities")
        .select("*")
        .eq("id", facility_id)
        .limit(1)
        .execute()
    )
    if not facility_result.data:
        return
    facility = facility_result.data[0]
    notion_page_id = facility["notion_page_id"]
    service_type = facility["service_type"]

    required = (
        supabase.table("required_documents")
        .select("*")
        .eq("service_type", service_type)
        .eq("is_active", True)
        .order("sort_order")
        .execute()
    ).data

    submissions = (
        supabase.table("facility_submissions")
        .select("*")
        .eq("facility_id", facility_id)
        .execute()
    ).data
    submissions_by_doc_id = {s["required_doc_id"]: s for s in submissions}

    status_lines = []
    for doc in required:
        sub = submissions_by_doc_id.get(doc["id"])
        status_lines.append(_format_status_line({
            "document_name": doc["document_name"],
            "status": sub["status"] if sub else "not_submitted",
            "submitted_at": sub["submitted_at"] if sub else None,
        }))
    status_text = " / ".join(status_lines)

    properties = {
        "提出状況": {"rich_text": [{"text": {"content": status_text}}]},
    }

    if other_file_submitted_at:
        properties["その他ファイル提出日時"] = {
            "date": {"start": other_file_submitted_at}
        }

    update_notion_page(notion_page_id, properties)