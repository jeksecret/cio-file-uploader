import re
from datetime import datetime, timezone
import dropbox
from app.connection import get_supabase
from app.integrations.dropbox_client import get_dropbox, resolve_dropbox_folder_path

def _sanitize(name: str) -> str:
    return re.sub(r'[\/\\:*?"<>|]', "_", name).strip()

def upload_other_files(facility: dict, files: list[tuple[str, bytes]]) -> list[dict]:
    supabase = get_supabase()
    dbx = get_dropbox()

    facility_id = facility["id"]
    facility_name = _sanitize(facility["name"])
    raw_folder = facility.get("dropbox_folder_path")

    if not raw_folder:
        raise ValueError("Facility has no Dropbox folder configured.")
    folder_path = resolve_dropbox_folder_path(raw_folder)

    records = []
    for original_filename, content in files:
        submitted_at = datetime.now(timezone.utc)
        timestamp = submitted_at.strftime("%Y%m%d%H%M%S")
        safe_original = _sanitize(original_filename)
        renamed = f"{facility_name}_その他ファイル_{timestamp}_{safe_original}"
        dropbox_path = f"{folder_path.rstrip('/')}/{renamed}"

        dbx.files_upload(content, dropbox_path, mode=dropbox.files.WriteMode("overwrite"))

        records.append({
            "facility_id": facility_id,
            "submitted_at": submitted_at.isoformat(),
            "dropbox_file_path": dropbox_path,
            "original_filename": original_filename,
        })

    result = supabase.table("facility_other_files").insert(records).execute()
    return result.data