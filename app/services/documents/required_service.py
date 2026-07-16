from app.connection import get_supabase

def get_required_documents(service_type: str) -> list[dict]:
    supabase = get_supabase()

    result = (
        supabase.table("required_documents")
        .select("*")
        .eq("service_type", service_type)
        .eq("is_active", True)
        .order("sort_order")
        .execute()
    )

    return result.data