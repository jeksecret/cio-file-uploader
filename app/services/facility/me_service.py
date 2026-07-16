from app.connection import get_supabase

def get_facility_mypage(facility: dict) -> dict:
    supabase = get_supabase()
    facility_id = facility["id"]
    service_type = facility["service_type"]

    # required documents for this facility's service type
    required = (
        supabase.table("required_documents")
        .select("*")
        .eq("service_type", service_type)
        .eq("is_active", True)
        .order("sort_order")
        .execute()
    ).data

    # existing submission rows for this facility (may be a subset of `required`)
    submissions = (
        supabase.table("facility_submissions")
        .select("*")
        .eq("facility_id", facility_id)
        .execute()
    ).data
    submissions_by_doc_id = {s["required_doc_id"]: s for s in submissions}

    # merge: every required doc gets a status, defaulting to not_submitted
    documents = []
    for doc in required:
        sub = submissions_by_doc_id.get(doc["id"])
        documents.append({
            "required_doc_id": doc["id"],
            "document_name": doc["document_name"],
            "sort_order": doc["sort_order"],
            "status": sub["status"] if sub else "not_submitted",
            "submitted_at": sub["submitted_at"] if sub else None,
        })

    other_files = (
        supabase.table("facility_other_files")
        .select("*")
        .eq("facility_id", facility_id)
        .order("submitted_at", desc=True)
        .execute()
    ).data

    return {
        "id": facility["id"],
        "name": facility["name"],
        "service_type": facility["service_type"],
        "submission_deadline": facility["submission_deadline"],
        "documents": documents,
        "other_files": other_files,
    }