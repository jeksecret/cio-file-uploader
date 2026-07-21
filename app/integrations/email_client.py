import os
import requests
from dotenv import load_dotenv

load_dotenv()

RESEND_API_URL = "https://api.resend.com/emails"

def send_email(to: list[str], subject: str, html: str) -> None:
    api_key = os.getenv("RESEND_API_KEY")
    from_address = os.getenv("RESEND_FROM_ADDRESS", "onboarding@resend.dev")

    if not api_key:
        raise RuntimeError("RESEND_API_KEY is not set.")

    response = requests.post(
        RESEND_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "from": from_address,
            "to": to,
            "subject": subject,
            "html": html,
        },
        timeout=10,
    )

    if response.status_code >= 400:
        raise RuntimeError(f"Resend API error ({response.status_code}): {response.text}")