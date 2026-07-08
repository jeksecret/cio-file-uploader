# CIO Facility Data Uploader — Technical Design & Implementation Plan

## 1. Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Frontend | React (Vite) | SPA served as static assets |
| Backend | Python FastAPI | Route/service split for maintainability |
| Package manager | `uv` | `pyproject.toml` + `uv.lock` |
| Database | Supabase (Postgres) | Facility master, documents master, submission status |
| Auth | Supabase Auth — **Email OTP** | Facilities have no Google account, so a passwordless email-code flow is used instead of OAuth |
| File storage | Dropbox API | Files are saved to a facility's pre-registered Dropbox folder |
| PM / source of truth | Notion (`notion-client`) | Facility info, service type, deadlines, Dropbox folder, send button |
| Email sending | Resend (primary) / Gmail via Make (fallback) | See §7 |
| Hosting | Render | `Procfile` + `gunicorn -k uvicorn.workers.UvicornWorker` |

---

## 2. System Architecture

```
Notion (facility DB)
   │  facility name / service type / contact / deadline / dropbox folder
   │  "Send" button (Notion automation → webhook)
   ▼
POST /api/hooks/send-initial-email
   │  builds payload from Notion, resolves Dropbox folder
   ▼
Email Service (Resend / Make+Gmail)
   │  sends uploader URL + deadline to facility contact
   ▼
Facility opens uploader URL
   │
   ▼
Frontend (React) — Email OTP login
   │  1. enter email → POST /api/auth/otp/request
   │  2. enter code  → verifyOtp (Supabase client)
   ▼
Facility My Page  (GET /api/facility/me)
   │  - facility name / service type / deadline
   │  - required documents (from Required Documents Master, filtered by service type)
   │  - submission status per document
   │  - "Other Files" uploader
   ▼
POST /api/uploads/{document_id}   (or /api/uploads/other)
   │  1. upload file(s) to backend
   │  2. rename per convention, push to Dropbox folder (from Notion)
   │  3. record submission status + timestamp in Supabase
   │  4. mirror status back to Notion (facility row)
   ▼
Dropbox (facility folder)          Notion (submission status columns)

Reminder job (scheduled) ──▶ GET /api/hooks/reminder-mail ──▶ Email Service
Admin Dashboard (internal, Google OAuth) ──▶ Required Documents Master CRUD
```

---

## 3. Data Model (Supabase)

```sql
-- Facilities pulled from / synced with Notion
facilities (
  id                    bigint pk,
  notion_page_id        text unique,
  name                  text,
  service_type          text,          -- e.g. "Licensed Daycare Center"
  contact_name          text,
  contact_email         text,
  submission_deadline   date,
  dropbox_folder_path   text,          -- pre-registered folder from Notion
  initial_email_sent_at timestamptz,
  reminder_sent_at      timestamptz,
  created_at            timestamptz default now()
)

-- Required Documents Master (admin-managed, per service type)
required_documents (
  id            bigint pk,
  service_type  text,
  document_name text,
  sort_order    int,
  is_active     boolean default true
)

-- Per-facility, per-document submission status
facility_submissions (
  id                bigint pk,
  facility_id       bigint references facilities(id),
  required_doc_id   bigint references required_documents(id),
  status            text check (status in ('not_submitted','submitted')) default 'not_submitted',
  submitted_at      timestamptz,
  dropbox_file_path text,
  original_filename text,
  unique (facility_id, required_doc_id)
)

-- "Other Files" — not tied to a required-doc row, multiple per facility
facility_other_files (
  id                bigint pk,
  facility_id       bigint references facilities(id),
  submitted_at      timestamptz default now(),
  dropbox_file_path text,
  original_filename text
)

-- OTP login sessions are handled entirely by Supabase Auth (auth.users),
-- keyed by the facility's contact_email — no separate table needed.
```

No resubmission history, no comments, no per-document approval — matches spec §17 exclusions.

---

## 4. Backend Structure

```
app/
  main.py
  db.py                              # get_supabase() client factory
  auth/
    deps.py                          # require_facility_session (OTP-based) + require_allowed_user (admin)
  security/
    domain_policy.py                 # domain allowlist for the internal admin dashboard
  integrations/
    dropbox_client.py                # get_dropbox() client factory
    notion_client.py                 # Notion page fetch/property extraction
    email_client.py                  # Resend + Make/Gmail fallback
  routes/api/
    auth/
      otp.py                         # POST /request, POST /verify (or delegate fully to Supabase)
    facility/
      me.py                          # GET  /api/facility/me
    documents/
      required.py                    # GET  /api/documents/required?service_type=
    uploads/
      document.py                    # POST /api/uploads/{required_doc_id}
      other.py                       # POST /api/uploads/other
    hooks/
      send_initial_email.py          # POST — called from Notion "Send" button automation
      reminder_mail.py                # GET  — polled by scheduler
      sync_notion_status.py           # internal — pushes status back to Notion
    admin/
      required_documents.py          # CRUD for Required Documents Master (Google-OAuth gated)
  services/
    facility/
      me_service.py
    documents/
      required_service.py
    uploads/
      document_service.py             # rename + Dropbox upload + status update
      other_service.py
    hooks/
      send_initial_email_service.py
      reminder_mail_service.py
      sync_notion_status_service.py
    admin/
      required_documents_service.py
```

`app/main.py` mounts routers with two dependency groups:

```python
facility_deps = [Depends(require_facility_session)]   # OTP-authenticated facility users
admin_deps    = [Depends(require_allowed_user)]        # Google-OAuth internal staff

app.include_router(facility_me_router,     prefix="/api/facility", dependencies=facility_deps)
app.include_router(required_docs_router,   prefix="/api/documents", dependencies=facility_deps)
app.include_router(uploads_router,         prefix="/api/uploads",   dependencies=facility_deps)
app.include_router(admin_docs_router,      prefix="/api/admin",     dependencies=admin_deps)
app.include_router(hooks_router,           prefix="/api/hooks")     # webhook-authenticated separately
```

---

## 5. Authentication — Email OTP

Supabase Auth natively supports passwordless email OTP, so no custom OTP code needs to be
written server-side:

- Frontend: `supabase.auth.signInWithOtp({ email })` → Supabase emails a 6-digit code.
- Frontend: `supabase.auth.verifyOtp({ email, token, type: 'email' })` → returns a session (JWT).
- Backend: `require_facility_session` verifies the Supabase JWT (HS256 + `SUPABASE_JWT_SECRET`)
  and checks the email against the `facilities` table — only emails that exist as a
  `contact_email` on some `facilities` row may pass.
- Rate limiting on OTP requests is handled via Supabase Auth's built-in settings.

The internal Admin Dashboard keeps a separate Google-OAuth login for staff, gated by a
company-domain allowlist, since admins are internal staff rather than facilities.

---

## 6. Notion Integration

- Facility rows are read via the Notion API: `service_type`, `submission_deadline`,
  `dropbox_folder_path`, `initial_email_sent_at`, `reminder_sent_at`, contact info.
- After each upload, `sync_notion_status_service.py` writes the per-document status +
  timestamp back to the Notion row, and the "other files" timestamp.
- The Notion **"Send" button** is implemented as a Notion button-property automation that calls
  `POST /api/hooks/send-initial-email` with the page ID — no polling needed for the initial send;
  reminders are polled on a schedule (see §8).
- Notion stays the source of truth; Supabase is the fast-read cache the app queries.

---

## 7. Email Service

Two interchangeable backends behind one interface (`app/integrations/email_client.py`):

```python
def send_email(to: list[str], subject: str, html: str) -> None: ...
```

- **Resend** (primary): direct API call, simplest, no external automation dependency.
- **Gmail via Make** (fallback): POST a JSON payload to a Make scenario that sends via the
  Gmail module.

Selection via env var `EMAIL_PROVIDER=resend|make`. Both the initial-notification hook and the
reminder hook call the same `send_email()` — the provider is swappable without touching route
code, so the team can pick per-environment.

Reminder emails (spec §15) query for facilities whose `submission_deadline` is approaching and
whose submissions are not fully complete.

---

## 8. Dropbox Integration

- `app/integrations/dropbox_client.py` — wraps the official `dropbox` Python SDK, authenticated
  via a long-lived refresh token (`DROPBOX_APP_KEY`, `DROPBOX_APP_SECRET`, `DROPBOX_REFRESH_TOKEN`).
- Upload flow in `uploads/document_service.py`:
  1. Read `dropbox_folder_path` from the facility's Supabase row (synced from Notion).
  2. Rename file: `{facility_name}_{document_name}_{submitted_at:%Y%m%d%H%M%S}_{original_filename}`.
  3. Upload via `files_upload` (chunked upload for files > 150MB, per Dropbox SDK guidance).
  4. On success, write `facility_submissions.status='submitted'` + `submitted_at` + `dropbox_file_path`.
- "Other Files" uses the same service with the `その他ファイル` naming convention from spec §13.

---

## 9. Admin Dashboard

- Gated by internal Google-OAuth auth (company-domain allowlist) — admins are internal staff,
  not facilities.
- CRUD screens for the Required Documents Master: add service type, add/remove documents,
  reorder, toggle active.

---

## 10. Environment Variables

```
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_JWT_SECRET=
NOTION_API_TOKEN=
DROPBOX_APP_KEY=
DROPBOX_APP_SECRET=
DROPBOX_REFRESH_TOKEN=
EMAIL_PROVIDER=resend            # or "make"
RESEND_API_KEY=                  # if EMAIL_PROVIDER=resend
MAKE_SEND_FACILITY_EMAIL=        # if EMAIL_PROVIDER=make
MAKE_REMINDER_EMAIL=             # if EMAIL_PROVIDER=make
CORS_ALLOW_ORIGINS=
VITE_API_URL=
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
```

---

## 11. Implementation Phases

### Phase 0 — Project Scaffolding
- `uv init`, `pyproject.toml` with FastAPI, Supabase, Notion client, Dropbox SDK, Resend.
- Vite + React frontend scaffold, Tailwind, `@supabase/supabase-js`, `react-router-dom`.
- Supabase project: create tables from §3, enable Email OTP provider.
- Render service + `Procfile`.
- `.env.example` with all vars from §10.

### Phase 1 — Auth (Email OTP)
- Frontend: Login page (email input → OTP input → verify), auth context using
  `signInWithOtp` / `verifyOtp`.
- Backend: `require_facility_session` dependency, `facilities`-table email check.
- Private-route guard checks for a valid session/token before rendering My Page.

### Phase 2 — Notion Read Integration
- Notion client wrapper: fetch facility row by page ID (name, service type, deadline,
  Dropbox folder path).
- Sync job / on-demand fetch to populate `facilities` table in Supabase.

### Phase 3 — Required Documents Master + Facility My Page
- `required_documents` table + `GET /api/documents/required?service_type=`.
- `GET /api/facility/me` — facility info + required docs list + status + other-files list.
- Frontend "My Page": facility header, submission deadline, per-document status rows.

### Phase 4 — File Upload + Dropbox
- `dropbox_client.py`, upload endpoints for required documents and "Other Files".
- Multi-file select + drag-and-drop UI component (reusable across both upload types).
- Rename-and-store logic per spec §13.
- Update `facility_submissions` / `facility_other_files` on success.

### Phase 5 — Notion Write-back
- `sync_notion_status_service.py` — push submission status + timestamps back to the Notion row
  after each successful upload.

### Phase 6 — Initial Notification Email
- Notion "Send" button → `POST /api/hooks/send-initial-email`.
- Build uploader URL + deadline + request text, send via `email_client.py`.
- Record `initial_email_sent_at` in both Supabase and Notion.

### Phase 7 — Reminder Emails
- `GET /api/hooks/reminder-mail` — due-reminder query (deadline approaching, not fully submitted).
- Scheduled trigger (Render Cron Job or external scheduler) hits this endpoint daily.
- Record `reminder_sent_at`.

### Phase 8 — Admin Dashboard
- `/api/admin/required-documents` CRUD, gated by internal Google-OAuth auth.
- React admin pages: add service type, add/remove/reorder/toggle documents.

### Phase 9 — Hardening & Launch
- Rate-limit OTP requests, file-size/type validation, error states (upload failure, Dropbox
  auth expiry), empty/loading states on My Page.
- End-to-end test: Notion send → email → OTP login → upload → Dropbox file appears → Notion
  status updates → reminder fires for facilities with an approaching deadline.
- Deploy to Render, point `VITE_API_URL` / `CORS_ALLOW_ORIGINS` at production.

---

## 12. Explicit Non-Goals (per spec §17)

Google Forms submission, Google Account auth for facilities, file preview, resubmission
tracking, comments, per-document approval workflow, version control — none of these are built.