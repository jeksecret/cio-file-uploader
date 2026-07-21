from datetime import datetime, timezone
from app.connection import get_supabase
from app.integrations.email_client import send_email
from app.integrations.notion_client import update_notion_page
from app.services.facility.notion_facility_service import upsert_facility_from_notion
import os

def _build_email_html(facility: dict, uploader_url: str) -> str:
    deadline = facility.get("submission_deadline") or "未定"
    return f"""
    <h2>資料提出のお願い</h2>
    <p>{facility['name']} ご担当者様</p>
    <p>下記アップローダーより、必要書類の提出をお願いいたします。</p>
    <p><a href="{uploader_url}">{uploader_url}</a></p>
    <p>提出期限: {deadline}</p>
    <p>ご不明な点がございましたら、担当者までご連絡ください。</p>
    """

def send_initial_notification(notion_page_id: str) -> dict:
    # Refresh facility data from Notion first, so the email always reflects
    # the latest deadline/contact info rather than a possibly-stale Supabase row.
    facility = upsert_facility_from_notion(notion_page_id)

    uploader_url = f"{os.getenv('FRONTEND_BASE_URL')}/login"
    html = _build_email_html(facility, uploader_url)

    send_email(
        to=[facility["contact_email"]],
        subject=f"【{facility['name']}】資料提出のお願い",
        html=html,
    )

    sent_at = datetime.now(timezone.utc).isoformat()
    supabase = get_supabase()
    result = (
        supabase.table("facilities")
        .update({"initial_email_sent_at": sent_at})
        .eq("id", facility["id"])
        .execute()
    )

    try:
        update_notion_page(notion_page_id, {
            "初回案内メール送信日時": {"date": {"start": sent_at}},
        })
    except Exception as e:
        print(f"WARNING: Notion write-back failed for facility {facility['id']}: {e}")

    return result.data[0]