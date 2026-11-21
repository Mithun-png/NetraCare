# NetraCare — Iteration 7 Implementation Specification

> **Purpose:** Agent-ready technical specification for implementing Iteration 7 in **NetraCare** (AI Front Desk & Care Coordination System). Follow all existing architectural boundaries, clinical safety rules, and offline-first guarantees.

---

## 1. Project Context & Non-Negotiable Guardrails

Before making any code changes, preserve every existing system invariant:

1. **Deterministic Safety Pre-Filter:** Every user message (whether from the dedicated Chat page, the bottom-right floating widget, or OCR follow-ups) **must** pass through `red_flags.check_red_flags()` first. Acute red-flag emergencies immediately return the emergency script, create an `UrgentCase` record, and block automated booking.
2. **Zero Diagnosis & Zero Treatment Advice:** Neither the chatbot nor the OCR pipeline may diagnose conditions, interpret prescription numbers clinically, or recommend treatments. OCR strictly transcribes text/values.
3. **Single Rule Engine (`BookingService`):** All availability checks, doctor leave/surgery checks, double-booking prevention, 30-day window, 10-minute slot alignment, and paediatric `<16` routing (strictly Dr. Vikram Menon) must execute deterministically inside `BookingService`.
4. **Offline-First Execution:** All new features must work without requiring external LLM API keys (deterministic fallback mode), while optionally enhancing formatting/conversation when Gemini is configured.
5. **Visual Identity & Accessibility:** Follow NetraCare's high-contrast WCAG AA/AAA palette (`--accent: #0d6e7a`, `--accent-soft: #e2f1f2`, `--surface: #ffffff`, `--surgery: #f4e6d4`, `#14212b` ink) and typography (`Bricolage Grotesque`, `Source Sans 3`, `IBM Plex Mono`) suitable for patients with visual impairment or dilated pupils.

---

## 2. Feature Specifications

### Feature A: Unified Dual-Mode Chatbot (Full Page + Bottom-Right Floating Widget)

**Goal:** Patients can interact with the NetraCare Assistant either on the dedicated full-screen Chat page **or** from a persistent floating chatbot widget on the bottom-right corner of every other page—without losing conversation history, pending HITL prompts, or uploaded OCR drafts.

#### Frontend Architecture (`frontend/src/`)
1. **Shared Context (`context/ChatContext.jsx`):**
   - Centralize `messages`, `sessionId`, `isOpen` (widget state), `isLoading`, `pendingAction` (confirmation card or HITL options), and `pendingOcrDraft`.
   - Persist `sessionId` and recent message history in `sessionStorage` so page navigation keeps the conversation intact.
2. **Reusable Component (`components/ChatWindow.jsx`):**
   - Accepts prop `mode="full" | "widget"`.
   - Renders:
     - Message list with source citations (`Source: ...`, `Skill: ...`), emergency alert banners, and structured interactive cards (Booking Confirmation Card, HITL Re-routing Card, OCR Preview Card).
     - Input bar with **Paperclip/Upload button** (for Prescription/Referral OCR) and Send button.
   - Keyboard accessible (Escape closes widget, clear focus rings, high-contrast bubbles).
3. **Floating Widget (`components/FloatingChatWidget.jsx`):**
   - Mounted globally in `App.jsx` inside `<ChatProvider>`.
   - Positioned fixed at `bottom-6 right-6` (`z-50`).
   - Automatically hides the floating launcher when the user is already on the dedicated `/chat` route.
   - Displays an unread/action-needed badge if a HITL prompt or confirmation card is waiting for user input.
   - Includes an "Expand to Full Page" button in the widget header that navigates to `/chat` seamlessly.

---

### Feature B: Human-in-the-Loop (HITL) for Doctor Leave, Surgery, or Double-Booking

**Goal:** When a patient asks in plain language to book a specific doctor (e.g., *"Book Dr. Anita Roy tomorrow morning"*) and `BookingService` reports the doctor is unavailable (`DOCTOR_OFF`, `SURGERY_SESSION`, or `DOUBLE_BOOKED`), the chatbot pauses and explicitly asks the patient whether they want to switch to another specialist in the same department or wait for the doctor's next available slot.

#### Backend / LangGraph Architecture (`backend/app/`)
1. **Availability Helper in `BookingService`:**
   - Add `find_alternatives(speciality, requested_doctor_id, requested_date, patient_age=None)`:
     - **`same_doctor_next_slots`**: Up to 3 earliest open OPD slots for the requested doctor within the 30-day window.
     - **`same_speciality_alternatives`**: Up to 3 earliest open OPD slots with *other* doctors matching the same `speciality`.
     - **Paediatric Gate:** If `patient_age is not None and patient_age < 16`, strictly restrict alternatives to **Dr. Vikram Menon** (do not offer non-paediatric doctors).
2. **LangGraph HITL Node (`doctor_unavailable_hitl`):**
   - Triggered when the booking tool receives `DOCTOR_OFF`, `SURGERY_SESSION`, or `DOUBLE_BOOKED` from `BookingService`.
   - Clearly explains *why* the requested slot isn't available (e.g., *"Dr. Anita Roy is in a surgery session during that time"* or *"Dr. Suresh Raman is on leave on that date"*).
   - Pauses graph execution (HITL interrupt / structured pending state) and returns a structured payload to the frontend:
     ```json
     {
       "type": "HITL_DOCTOR_UNAVAILABLE",
       "reason_code": "SURGERY_SESSION",
       "requested_doctor": "Dr. Anita Roy",
       "message": "Dr. Anita Roy is in a surgery session at that time. Would you like to switch to another Cataract specialist or wait for Dr. Roy's next open slot?",
       "options": [
         {
           "id": "switch_doctor",
           "label": "Switch to another specialist",
           "slots": [{ "doctor_id": "D2", "doctor_name": "...", "date": "...", "start_time": "..." }]
         },
         {
           "id": "wait_next_slot",
           "label": "Wait for Dr. Anita Roy's next slot",
           "slots": [{ "doctor_id": "D1", "doctor_name": "Dr. Anita Roy", "date": "...", "start_time": "..." }]
         }
       ]
     }
     ```
   - **Resume Flow:** When the patient clicks a quick-reply slot button (or replies in text like *"switch doctor"* / *"I'll wait"*), resume the LangGraph state, validate the chosen slot through `BookingService`, and render the standard Booking Confirmation Card before committing.

---

### Feature C: Prescription & Referral OCR Intake → `intake_notes`

**Goal:** Patients can upload a photo of their current glasses prescription or an outside referral letter either inside the Chatbot (full page or widget) or on the Book Appointment form. The system extracts the text via OCR, shows a preview for patient confirmation, and attaches it to `Appointment.intake_notes` for the doctor.

#### Backend Implementation (`backend/app/`)
1. **Endpoint:** `POST /api/v1/intake/ocr`
   - Accepts `multipart/form-data` with `file: UploadFile` (allowed types: `image/jpeg`, `image/png`, `image/webp`, `application/pdf`; max size: `5 MB`).
   - Optional `appointment_id` (if attaching directly to an existing active appointment belonging to the signed-in patient).
2. **Dual-Path OCR Service (`app/services/ocr_service.py`):**
   - **Offline Path (Default):** Use `Pillow` + `pytesseract` to extract raw text from the uploaded image. Parse common ophthalmic prescription markers (`OD`, `OS`, `SPH`, `CYL`, `AXIS`, `ADD`, `PD`) via deterministic regex into a structured summary block.
     - *Fallback:* If `tesseract` binary is not installed in the host environment, return a clean `503` or configurable dev fallback message without crashing the server.
   - **Optional LLM Formatting Path:** If Gemini is enabled, pass *only* the extracted OCR text through a strict formatting prompt that structures fields cleanly while enforcing **zero clinical interpretation, zero diagnosis, and zero treatment advice**.
   - **Safety Check:** Run extracted text through `red_flags.check_red_flags()` (e.g., if a referral letter mentions acute trauma/sudden vision loss, trigger emergency triage).
3. **Attachment Endpoint / Integration:**
   - `POST /api/v1/appointments/{appointment_id}/attach-ocr` (with patient ownership check) OR pass `ocr_intake_text` in the `POST /api/v1/appointments` booking payload.
   - Appends to `Appointment.intake_notes` formatted as:
     ```text
     [OCR Prescription/Referral Attached — 2026-11-02 10:15]
     <verified extracted text>
     ```
   - Never overwrites existing `intake_notes` (e.g., LASIK intake answers); always appends cleanly.

#### Frontend Implementation (`frontend/src/`)
1. **In `<ChatWindow />`:** Paperclip upload button opens file picker → uploads to `/api/v1/intake/ocr` → renders an **OCR Preview Card** inside chat showing the extracted text (editable textarea so the patient can fix any OCR typo) with **"Attach to Booking"** and **"Discard"** buttons.
2. **In Book Appointment Form:** Add an optional **"Upload Glasses Prescription / Referral Letter"** dropzone that populates a reviewable preview and submits the verified text with the booking request.
3. **In Doctor Portal:** Display attached `[OCR Prescription/Referral Attached]` notes clearly inside the patient's appointment intake panel (alongside existing `intake_notes`).

---

### Feature D: Live Dilation Drop Timer & Waiting-Room Tracker

**Goal:** Operationalize NetraCare's 30–45 minute dilation drop observation window across Staff, Patient, and Doctor portals with zero heavy backend polling.

#### Database Schema Update (`backend/app/models.py`)
Extend the `Appointment` SQLAlchemy model (and update seed loader / DB migration script):
- `visit_stage`: `String`, default `"SCHEDULED"`
  - Allowed values: `"SCHEDULED"`, `"CHECKED_IN"`, `"DILATING"`, `"READY_FOR_DOCTOR"`, `"COMPLETED"`
- `dilation_started_at`: `DateTime`, nullable `True`
- `dilation_duration_mins`: `Integer`, default `35` (validated between `15` and `60`)

#### Backend Endpoints (`backend/app/routers/`)
1. **`PATCH /api/v1/staff/appointments/{appointment_id}/stage`** (Staff role guard):
   - Body: `{ "visit_stage": "CHECKED_IN" | "DILATING" | "READY_FOR_DOCTOR", "dilation_duration_mins": 35 }`
   - When `visit_stage == "DILATING"`, sets `dilation_started_at = clinic_now()` (respecting fixed `CLINIC_NOW` in tests).
   - Validates transitions (cannot dilate a cancelled or completed appointment).
2. **Read Support:**
   - Include `visit_stage`, `dilation_started_at`, `dilation_duration_mins`, and server `server_now` timestamp in existing Patient, Staff, and Doctor appointment response schemas.

#### Frontend Implementation (`frontend/src/`)
1. **Client-Side Countdown Hook (`hooks/useDilationTimer.js`):**
   - Computes remaining seconds locally every 1 second using `dilation_started_at + dilation_duration_mins - currentTime` (offset by `server_now` to avoid client clock skew).
   - Returns `{ remainingSeconds, formattedTime, progressPercent, isReady }`.
2. **Staff Desk:**
   - Add stage action buttons on today's active appointments:
     - `SCHEDULED` → **"Check In"**
     - `CHECKED_IN` → **"Start Dilation (35m)"** (with optional 30/35/45m quick selector)
     - `DILATING` → Live countdown badge (`24:12 left`) + **"Mark Ready Now"** override button.
3. **Patient Portal:**
   - When the signed-in patient has an appointment in `CHECKED_IN`, `DILATING`, or `READY_FOR_DOCTOR`, render a prominent, high-contrast **Live Visit Status Card** (extra-large typography for blurred vision):
     - Shows progress bar, live countdown (`MM:SS remaining`), and safety note: *"Your pupils are dilating. Vision may be temporarily blurred—please avoid driving and stay in the waiting area."*
     - Switches to **"Ready for Dr. [Name]"** in clinic teal when the timer completes.
4. **Doctor OPD Roster:**
   - Displays live stage badges (`Waiting`, `Dilating: 18m left`, **`Ready for Exam`**).
   - Automatically highlights patients as **Ready for Examination** when `isReady === true` or `visit_stage === "READY_FOR_DOCTOR"`.

---

## 3. Recommended Execution Order (For Antigravity Agent)

Execute in 4 clean, testable slices:

1. **Slice 1 — Database & Live Dilation Timer:**
   - Update `Appointment` model (`visit_stage`, `dilation_started_at`, `dilation_duration_mins`), schema responses, and Staff stage endpoint.
   - Build `useDilationTimer.js` and wire Staff, Patient, and Doctor UI badges/cards.
   - Add pytest coverage.
2. **Slice 2 — Prescription & Referral OCR Intake:**
   - Add `ocr_service.py`, `POST /api/v1/intake/ocr`, and `attach-ocr` / booking payload integration appending to `intake_notes`.
   - Wire OCR upload & editable preview into Booking Form and Doctor intake view.
   - Add pytest coverage (mocking Tesseract output for deterministic CI).
3. **Slice 3 — LangGraph HITL Leave/Surgery Re-routing:**
   - Add `BookingService.find_alternatives()` respecting all clinic rules + paediatric `<16` restriction.
   - Add `doctor_unavailable_hitl` LangGraph node & resume handler.
   - Add pytest coverage for `DOCTOR_OFF`, `SURGERY_SESSION`, `DOUBLE_BOOKED`, and paediatric edge cases.
4. **Slice 4 — Unified Full-Page + Bottom-Right Floating Chatbot:**
   - Extract `ChatContext.jsx` and `<ChatWindow mode="full" | "widget" />`.
   - Mount `<FloatingChatWidget />` globally, wire OCR upload button and HITL quick-reply cards inside both modes.
   - Verify full regression suite passes.

---

## 4. Automated Test Plan (`backend/tests/test_iteration7.py`)

All new tests must run deterministically under the existing fixed clinic clock (`CLINIC_NOW = 2026-11-02 10:00:00`) and pass alongside the existing 63+ tests:

1. **HITL Doctor Leave (`DOCTOR_OFF`):** Requesting a doctor on leave returns `HITL_DOCTOR_UNAVAILABLE` with both `switch_doctor` and `wait_next_slot` options; selecting an option completes booking via `BookingService` with 0 rule breaks.
2. **HITL Surgery Session (`SURGERY_SESSION`):** Requesting a doctor during surgery triggers HITL options instead of a dead-end error.
3. **HITL Paediatric Guard (`age < 16`):** When Dr. Vikram Menon is unavailable for a child patient, `switch_doctor` does **not** suggest non-paediatric doctors; only Dr. Vikram Menon's next open slots are offered.
4. **OCR Extraction & Attachment:** Uploading a sample glasses prescription image extracts text, preserves zero-diagnosis guardrails, and appends `[OCR Prescription/Referral Attached]` to `Appointment.intake_notes` without overwriting existing notes.
5. **OCR File Validation & Cross-Patient Isolation:** Rejects invalid file types/oversized files (`400`/`413`) and prevents Patient A from attaching OCR notes to Patient B's appointment (`403`).
6. **OCR Red-Flag Triage:** An uploaded referral containing acute red-flag text (e.g., *"sudden vision loss right eye"*) triggers the deterministic emergency response and creates an `UrgentCase`.
7. **Live Dilation Timer Lifecycle:** Staff transitions an appointment `SCHEDULED` → `CHECKED_IN` → `DILATING` (sets `dilation_started_at`) → `READY_FOR_DOCTOR`; non-staff roles calling the stage endpoint receive `403 Forbidden`.
8. **Regression Check:** Run full `pytest backend/tests` and `python run_evals.py` to confirm 100% pass rate across Iterations 1–7.