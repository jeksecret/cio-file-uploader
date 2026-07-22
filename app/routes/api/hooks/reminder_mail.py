import os
from fastapi import APIRouter, Header, HTTPException
from app.services.hooks.reminder_mail_service import send_due_reminders

router = APIRouter()

def _verify_webhook_secret(x_webhook_secret: str | None) -> None:
    expected = os.getenv("NOTION_WEBHOOK_SECRET")
    if not expected or x_webhook_secret != expected:
        raise HTTPException(status_code=401, detail="Invalid webhook secret.")

@router.get("/reminder-mail")
def reminder_mail(x_webhook_secret: str | None = Header(default=None)):
    _verify_webhook_secret(x_webhook_secret)
    return send_due_reminders()