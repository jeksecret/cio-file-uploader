import os
from datetime import date, datetime, timedelta, timezone
from app.connection import get_supabase
from app.integrations.email_client import send_email
from app.integrations.notion_client import update_notion_page

REMINDER_TEXT = """
<p>提出期限が近づいております。</p>
<p>すでに一部の書類をご提出いただいている場合でも、期限までに残りの書類を可能な範囲で電子提出いただきますようお願いいたします。</p>
"""

def _facility_is_complete(facility_id: int, service_type: str, supabase) -> bool:
    required = (
        supabase.table("required_documents")
        .select("id")
        .eq("service_type", service_type)
        .eq("is_active", True)
        .execute()
    ).data
    if not required:
        return True

    submissions = (
        supabase.table("facility_submissions")
        .select("required_doc_id, status")
        .eq("facility_id", facility_id)
        .eq("status", "submitted")
        .execute()
    ).data
    submitted_ids = {s["required_doc_id"] for s in submissions}
    required_ids = {r["id"] for r in required}

    return required_ids.issubset(submitted_ids)

def send_due_reminders() -> dict:
    days_before = int(os.getenv("REMINDER_DAYS_BEFORE_DEADLINE", "3"))
    today = date.today()
    window_end = today + timedelta(days=days_before)

    supabase = get_supabase()

    facilities = (
        supabase.table("facilities")
        .select("*")
        .not_.is_("submission_deadline", "null")
        .lte("submission_deadline", window_end.isoformat())
        .gte("submission_deadline", today.isoformat())
        .execute()
    ).data

    sent, skipped = [], []

    for facility in facilities:
        facility_id = facility["id"]

        # skip if already reminded today (avoid duplicate sends if cron fires twice)
        last_reminded = facility.get("reminder_sent_at")
        if last_reminded:
            last_reminded_date = datetime.fromisoformat(
                last_reminded.replace("Z", "+00:00")
            ).date()
            if last_reminded_date == today:
                skipped.append({"facility_id": facility_id, "reason": "already reminded today"})
                continue

        if _facility_is_complete(facility_id, facility["service_type"], supabase):
            skipped.append({"facility_id": facility_id, "reason": "already complete"})
            continue

        send_email(
            to=[facility["contact_email"]],
            subject=f"【{facility['name']}】提出期限のお知らせ",
            html=REMINDER_TEXT,
        )

        sent_at = datetime.now(timezone.utc).isoformat()
        supabase.table("facilities").update({"reminder_sent_at": sent_at}).eq("id", facility_id).execute()

        try:
            update_notion_page(facility["notion_page_id"], {
                "リマインダー送信日時": {"date": {"start": sent_at}},
            })
        except Exception as e:
            print(f"WARNING: Notion reminder write-back failed for facility {facility_id}: {e}")

        sent.append(facility_id)

    return {"sent": sent, "skipped": skipped}