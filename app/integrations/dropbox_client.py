import os
from functools import lru_cache
from urllib.parse import urlparse, unquote
from dotenv import load_dotenv
import dropbox

load_dotenv()

@lru_cache(maxsize=1)
def get_dropbox() -> dropbox.Dropbox:
    app_key = os.getenv("DROPBOX_APP_KEY")
    app_secret = os.getenv("DROPBOX_APP_SECRET")
    refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")

    if not all([app_key, app_secret, refresh_token]):
        raise RuntimeError(
            "DROPBOX_APP_KEY, DROPBOX_APP_SECRET, and DROPBOX_REFRESH_TOKEN must all be set."
        )

    return dropbox.Dropbox(
        app_key=app_key,
        app_secret=app_secret,
        oauth2_refresh_token=refresh_token,
    )

def resolve_dropbox_folder_path(raw: str) -> str:
    if raw.startswith("http://") or raw.startswith("https://"):
        path = unquote(urlparse(raw).path)
        if path.startswith("/home"):
            path = path[len("/home"):]
        return path or "/"
    return raw