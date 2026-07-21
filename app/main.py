import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.routes.api.facility.me import router as facility_me_router
from app.routes.api.facility.sync import router as facility_sync_router
from app.routes.api.documents.required import router as documents_required_router
from app.routes.api.uploads.other import router as uploads_other_router
from app.routes.api.uploads.document import router as uploads_document_router
from app.routes.api.hooks.send_initial_email import router as send_initial_email_router

load_dotenv()

app = FastAPI()

origins = [o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "").split(",") if o.strip()]
print(f"CORS_ALLOW_ORIGINS resolved to: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(facility_me_router, prefix="/api/facility")
app.include_router(facility_sync_router, prefix="/api/facility")
app.include_router(documents_required_router, prefix="/api/documents")
app.include_router(uploads_other_router, prefix="/api/uploads")
app.include_router(uploads_document_router, prefix="/api/uploads")
app.include_router(send_initial_email_router, prefix="/api/hooks")

@app.get("/")
def read_root():
    return {"message": "API is running"}

# Health check endpoint to wake up the server
@app.get("/status")
def status_check():
    return {"status": "200"}