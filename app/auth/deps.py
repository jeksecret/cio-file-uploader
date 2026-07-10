from fastapi import Header, HTTPException, status
from app.connection import get_supabase

def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header.",
        )
    return authorization.split(" ", 1)[1].strip()

def require_facility_session(authorization: str | None = Header(default=None)) -> dict:
    """
    Verifies the Supabase-issued JWT for a facility user (via Supabase Auth,
    not local JWT decoding) and confirms the authenticated email belongs to
    a registered facility.

    Returns the facility row so route handlers can use it directly
    (facility id, dropbox folder path, etc.) without a second query.
    """
    token = _extract_bearer_token(authorization)
    supabase = get_supabase()

    try:
        user_response = supabase.auth.get_user(token)
    except Exception as e:
        print(f"DEBUG get_user() failed: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="セッションが無効か、有効期限が切れています。",
        )

    user = getattr(user_response, "user", None)
    email = getattr(user, "email", None) if user else None

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="セッションが無効か、有効期限が切れています。",
        )

    result = (
        supabase.table("facilities")
        .select("*")
        .eq("contact_email", email)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="このアカウントは登録済みの施設担当者として認識されていません。",
        )

    return result.data[0]