import re
from datetime import datetime, timezone
import dropbox
from app.connection import get_supabase
from app.integrations.dropbox_client import get_dropbox, resolve_dropbox_folder_path

def _sanitize(name: str) -> str:
    return re.sub(r'[\/\\:*?"<>|]', "_", name).strip()

def upload_required_document(
    facility: dict,
    required_doc_id: int,
    files: list[tuple[str, bytes]],
) -> dict:
    supabase = get_supabase()
    dbx = get_dropbox()

    facility_id = facility["id"]
    facility_name = _sanitize(facility["name"])
    raw_folder = facility.get("dropbox_folder_path")

    if not raw_folder:
        raise ValueError("Facility has no Dropbox folder configured.")
    folder_path = resolve_dropbox_folder_path(raw_folder)

    doc_result = (
        supabase.table("required_documents")
        .select("*")
        .eq("id", required_doc_id)
        .limit(1)
        .execute()
    )
    if not doc_result.data:
        raise ValueError("Required document not found.")
    document_name = _sanitize(doc_result.data[0]["document_name"])

    submitted_at = datetime.now(timezone.utc)
    timestamp = submitted_at.strftime("%Y%m%d%H%M%S")

    uploaded_paths, uploaded_names = [], []

    for original_filename, content in files:
        safe_original = _sanitize(original_filename)
        renamed = f"{facility_name}_{document_name}_{timestamp}_{safe_original}"
        dropbox_path = f"{folder_path.rstrip('/')}/{renamed}"

        dbx.files_upload(content, dropbox_path, mode=dropbox.files.WriteMode("overwrite"))

        uploaded_paths.append(dropbox_path)
        uploaded_names.append(original_filename)

    submission = {
        "facility_id": facility_id,
        "required_doc_id": required_doc_id,
        "status": "submitted",
        "submitted_at": submitted_at.isoformat(),
        "dropbox_file_path": ", ".join(uploaded_paths),
        "original_filename": ", ".join(uploaded_names),
    }

    result = (
        supabase.table("facility_submissions")
        .upsert(submission, on_conflict="facility_id,required_doc_id")
        .execute()
    )
    return result.data[0]