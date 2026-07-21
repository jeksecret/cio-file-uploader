import os
from fastapi import APIRouter, Header, HTTPException, Body
from app.services.hooks.send_initial_email_service import send_initial_notification

router = APIRouter()

def _verify_webhook_secret(x_webhook_secret: str | None) -> None:
    expected = os.getenv("NOTION_WEBHOOK_SECRET")
    if not expected or x_webhook_secret != expected:
        raise HTTPException(status_code=401, detail="Invalid webhook secret.")

@router.post("/send-initial-email")
def send_initial_email(
    payload: dict = Body(...),
    x_webhook_secret: str | None = Header(default=None),
):
    _verify_webhook_secret(x_webhook_secret)

    data = payload.get("data", {})
    notion_page_id = data.get("id")

    if not notion_page_id:
        raise HTTPException(status_code=400, detail="Missing page id in webhook payload.")

    return send_initial_notification(notion_page_id)