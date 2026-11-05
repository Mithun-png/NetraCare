# NetraCare — Architecture and Implementation Plan

**Project:** NetraCare — AI Front Desk and Care Coordination (fictional eye clinic)
**Purpose:** Course capstone and portfolio project
**Time budget:** 2–3 days
**Document status:** Design baseline. Nothing here is implemented yet. Items marked **[VERIFY]** must be checked against the supplied data packs and handouts, which were not available when this document was written.

---

## 1. Decisions Log

These decisions come from the project owner and drive everything below.

| # | Topic | Decision |
|---|---|---|
| 1 | Goal | Course capstone, published in portfolio |
| 2 | Time | 2–3 days total |
| 3 | Frontend | React (separate `frontend/` folder) |
| 4 | Backend | Python, FastAPI, Pydantic (separate `backend/` folder) |
| 5 | Database | PostgreSQL |
| 6 | LLM | Google Gemini |
| 7 | Vector database | Pinecone |
| 8 | Identity (v1) | Use the supplied datasets and the mobile + name identity flow. Real password accounts and public signup are deferred to a later update |
| 9 | Video (v1) | Free developer option if one fits, otherwise a mock room |
| 10 | Notifications | Deferred to the later update (with real accounts) |
| 11 | Admin model | Admin creates staff accounts. A sub-admin moderates staff |
| 12 | Reschedule inside 2-hour window | Original slot stays held until staff decide |
| 13 | Doctor rule | One active booking per patient per doctor at a time, even when the doctor has several specialties |
| 14 | Red flag during booking | Draft booking is preserved and attached to the urgent case for staff |
| 15 | Timezone | India Standard Time (`Asia/Kolkata`, UTC+05:30, no daylight saving) |

### Interaction between rule 13 and the README rules

The README already says "one active booking per specialty". Decision 13 adds a second, separate limit: one active booking per doctor. Both apply together. Example: a patient with an active Cataract booking with Dr. Iyer cannot also book Glaucoma with Dr. Iyer, and cannot book Cataract with any other doctor.

---

## 2. Scope Strategy for 2–3 Days

The full brief (six iterations plus video) is more than most people can finish in three days. The plan below protects the parts that matter most for the grading targets and for a portfolio.

| Priority | Scope | Why |
|---|---|---|
| **Must have** | Iteration 1 (site, rules, roles), safety gate, urgent cases | Zero rule-breaking bookings and 100% red-flag response are hard targets |
| **Must have** | Iteration 3 (RAG chat with citations, routing) | The most visible AI feature |
| **Should have** | Iteration 2 (visit summary), Iteration 4 (assistant booking) | Core agent behaviour |
| **Should have** | Iteration 5 (evaluation scripts with real numbers) | Proves targets honestly |
| **Could have** | Iteration 6 (MCP server, lab MCP, skills) | Valuable but depends on stable services |
| **Could have** | Virtual consultation (mock room first) | Adds scope; keep modular |
| **Later update** | Real accounts, signup, notifications | Explicitly deferred |

If time runs short, cut from the bottom of this table upward. Anything cut must be stated in the final README as "not done", not hidden. The brief requires being clear about any target not met.

---

## 3. Assumptions to Verify Against the Data Packs

1. **[VERIFY]** Exact reason codes. This document uses placeholder names. Replace them with the codes in the data pack README files.
2. **[VERIFY]** Doctor and staff demo credentials. If the packs contain none, seed fictional demo accounts.
3. **[VERIFY]** Seed file formats (CSV or JSON), column names, and the weekly schedule representation.
4. **[VERIFY]** How "follow-up" is determined: from visit history in data pack 2, or chosen by the patient.
5. **[VERIFY]** What the 16 demo scenarios exactly require, and the routing test set format.
6. **[VERIFY]** Whether the lab MCP server is a runnable Python process and which port it uses.
7. **[VERIFY]** The documented local endpoint for the NetraCare MCP server.

---

## 4. System Context

```
                    +----------------------------+
                    |   Users                    |
                    | Patient | Doctor | Staff   |
                    | Admin / Sub-admin          |
                    +-------------+--------------+
                                  |
                          React frontend (SPA)
                                  |  HTTPS / JSON
                                  v
   +--------------------------------------------------------------+
   |                      FastAPI backend                          |
   |                                                              |
   |  API layer: auth, RBAC, validation, rate limiting            |
   |      |                                                       |
   |      +--> Safety gate (deterministic red-flag detection)     |
   |      |                                                       |
   |      +--> Application services                               |
   |      |      booking | schedule | leave | urgent cases        |
   |      |      audit | video | identity | approvals             |
   |      |                                                       |
   |      +--> Assistant layer                                    |
   |             Gemini | LangGraph | RAG | skills | tool wrappers |
   +-------+---------------+-----------------+--------------------+
           |               |                 |
           v               v                 v
      PostgreSQL        Pinecone       External/optional
   (system of record)  (vectors +      Video provider / mock room
                        metadata)      NetraCare MCP server (port TBD)
                                       CityCare Lab MCP server
```

### Core principle: four channels, one rule engine

Website, assistant, staff dashboard, and MCP all call the **same** `BookingService`. No channel contains its own booking rules. Contract tests (section 14) run the same scenarios through all four channels to prove they cannot diverge.

---

## 5. Repository Structure

```
netracare/
├── README.md
├── docs/
│   ├── NetraCare-Architecture.md
│   ├── evaluation-results.md
│   └── demo-script.md
├── data/                      # copied from the supplied packs (synthetic only)
│   ├── pack1/ ... pack6/
├── backend/
│   ├── pyproject.toml
│   ├── .env.example
│   ├── alembic/               # migrations
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py          # settings from environment
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   ├── models.py
│   │   │   └── seed.py
│   │   ├── api/
│   │   │   ├── deps.py        # current user, role guards
│   │   │   ├── auth.py
│   │   │   ├── public.py
│   │   │   ├── patient.py
│   │   │   ├── doctor.py
│   │   │   ├── staff.py
│   │   │   ├── admin.py
│   │   │   ├── assistant.py
│   │   │   └── video.py
│   │   ├── services/
│   │   │   ├── booking.py     # THE rule engine
│   │   │   ├── reasons.py     # reason codes (enum)
│   │   │   ├── schedule.py
│   │   │   ├── leave.py
│   │   │   ├── urgent.py
│   │   │   ├── identity.py
│   │   │   ├── audit.py
│   │   │   ├── approvals.py
│   │   │   └── video.py       # provider interface + implementations
│   │   ├── safety/
│   │   │   ├── red_flags.py
│   │   │   └── output_guard.py  # blocks diagnosis/treatment language
│   │   ├── assistant/
│   │   │   ├── llm.py         # Gemini client wrapper
│   │   │   ├── rag/
│   │   │   │   ├── ingest.py
│   │   │   │   ├── retrieve.py
│   │   │   │   └── answer.py
│   │   │   ├── routing.py     # specialty routing
│   │   │   ├── summary.py     # visit summary
│   │   │   ├── graph.py       # LangGraph booking workflow
│   │   │   ├── tools.py       # tool wrappers around services
│   │   │   └── skills/loader.py
│   │   ├── mcp/
│   │   │   ├── server.py      # NetraCare MCP server
│   │   │   └── lab_client.py
│   │   └── observability/tracing.py
│   ├── skills/                # SKILL.md folders
│   │   ├── cataract-surgery-care/
│   │   ├── lasik-suitability-intake/
│   │   ├── prepare-for-visit/
│   │   └── children-visit/
│   ├── evals/
│   │   ├── red_flags.py
│   │   ├── routing.py
│   │   ├── policy_citations.py
│   │   ├── booking_rules.py
│   │   ├── no_diagnosis.py
│   │   └── run_all.py
│   └── tests/
│       ├── unit/
│       ├── contract/          # same scenarios through all channels
│       └── security/
└── frontend/
    ├── package.json
    ├── .env.example
    └── src/
        ├── main.jsx
        ├── api/               # typed API client
        ├── auth/              # session context, route guards
        ├── pages/
        │   ├── public/        # Home, Doctors, Services, Contact, Login
        │   ├── patient/
        │   ├── doctor/
        │   └── staff/
        ├── components/
        │   ├── BookingWizard/
        │   ├── SlotPicker/
        │   ├── AssistantChat/
        │   ├── UrgentBanner/
        │   └── VideoJoin/
        └── styles/
```

---

## 6. Technology Stack

| Layer | Choice | Notes |
|---|---|---|
| Frontend | React with Vite, React Router | Role-based route guards for UX only. Server enforces security |
| Backend | Python 3.11+, FastAPI, Pydantic v2 | Typed request/response models |
| ORM and migrations | SQLAlchemy 2.x, Alembic | Migrations from day one |
| Database | PostgreSQL | Needed for the overlap-prevention constraint (section 8) |
| LLM | Gemini API | Model name in an environment variable so it can be changed |
| Embeddings | Gemini embedding model | Pinecone index dimension must match the model **[VERIFY]** |
| Vector store | Pinecone | Check current free-tier limits before indexing **[VERIFY]** |
| Orchestration | LangGraph with Postgres checkpointer | Persisted state for approval pauses |
| MCP | Official Python MCP SDK 1.x, Streamable HTTP | Per the Iteration 6 handout |
| Auth (v1) | Demo identity, signed session cookie | Upgraded in the later update |
| Testing | pytest, Playwright (optional) | Contract and security tests are the priority |
| Config | `.env` (ignored) plus `.env.example` | Names and placeholders only |

---

## 7. Time Handling (Indian Timezone)

- Store all instants as `timestamptz` (PostgreSQL stores UTC internally).
- Interpret clinic rules in `Asia/Kolkata`. Define `CLINIC_TZ = ZoneInfo("Asia/Kolkata")` in one module and never hard-code offsets elsewhere.
- Convert inputs to clinic time before checking hours, sessions, Sundays, and holidays.
- "30 days ahead" and "two hours before" are computed from the current time in `Asia/Kolkata`. Make `now()` injectable so tests can fix the clock.
- Store holidays and schedules as **dates** (no time component) in clinic local time.

---

## 8. Data Architecture (PostgreSQL)

### 8.1 Entity overview

```
users ──1:0..1── patients
users ──1:0..1── doctors ──< doctor_specialties
doctors ──< schedules (date + session + status)
holidays
patients ──< appointments >── doctors
appointments ──0..1── video_rooms
urgent_cases ──> patients? / users?
approvals ──> appointments?
leave_requests ──< leave_effects
audit_events
knowledge_sources
```

### 8.2 Schema (reference DDL)

Types and names are a starting point. Align column names with the seed files **[VERIFY]**.

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TYPE user_role AS ENUM ('patient','doctor','staff','sub_admin','admin');
CREATE TYPE session_kind AS ENUM ('AM','PM');
CREATE TYPE session_status AS ENUM ('OPD','SURGERY','OFF');
CREATE TYPE visit_type AS ENUM ('NEW','FOLLOW_UP');
CREATE TYPE appt_mode AS ENUM ('IN_PERSON','VIRTUAL');
CREATE TYPE appt_status AS ENUM
  ('BOOKED','PENDING_STAFF','CANCELLED','COMPLETED','NO_SHOW');
CREATE TYPE booking_source AS ENUM ('WEBSITE','CHAT','STAFF','MCP');

CREATE TABLE users (
  id            BIGSERIAL PRIMARY KEY,
  role          user_role NOT NULL,
  email         TEXT UNIQUE,            -- used in the later update
  password_hash TEXT,                   -- NULL in v1 demo identity
  status        TEXT NOT NULL DEFAULT 'ACTIVE',
  created_by    BIGINT REFERENCES users(id),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE patients (
  id         BIGSERIAL PRIMARY KEY,
  user_id    BIGINT UNIQUE REFERENCES users(id),
  mobile     TEXT NOT NULL UNIQUE,
  full_name  TEXT NOT NULL,
  profile    JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE doctors (
  id        BIGSERIAL PRIMARY KEY,
  user_id   BIGINT UNIQUE REFERENCES users(id),
  full_name TEXT NOT NULL,
  active    BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE doctor_specialties (
  doctor_id BIGINT NOT NULL REFERENCES doctors(id),
  specialty TEXT NOT NULL,
  PRIMARY KEY (doctor_id, specialty)
);

CREATE TABLE schedules (
  id        BIGSERIAL PRIMARY KEY,
  doctor_id BIGINT NOT NULL REFERENCES doctors(id),
  day       DATE NOT NULL,
  session   session_kind NOT NULL,
  status    session_status NOT NULL,
  UNIQUE (doctor_id, day, session)
);

CREATE TABLE holidays (
  day  DATE PRIMARY KEY,
  name TEXT NOT NULL
);

CREATE TABLE appointments (
  id            BIGSERIAL PRIMARY KEY,
  patient_id    BIGINT NOT NULL REFERENCES patients(id),
  doctor_id     BIGINT NOT NULL REFERENCES doctors(id),
  specialty     TEXT NOT NULL,
  visit_type    visit_type NOT NULL,
  mode          appt_mode NOT NULL DEFAULT 'IN_PERSON',
  status        appt_status NOT NULL,
  start_at      TIMESTAMPTZ NOT NULL,
  end_at        TIMESTAMPTZ NOT NULL,
  source        booking_source NOT NULL,
  intake_notes  TEXT,
  rescheduled_from BIGINT REFERENCES appointments(id),
  created_by    BIGINT REFERENCES users(id),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (end_at > start_at),

  -- A doctor cannot have two active appointments that overlap
  CONSTRAINT no_doctor_overlap EXCLUDE USING gist (
    doctor_id WITH =,
    tstzrange(start_at, end_at) WITH &&
  ) WHERE (status IN ('BOOKED','PENDING_STAFF'))
);

-- One active booking per patient per specialty
CREATE UNIQUE INDEX one_active_per_specialty
  ON appointments (patient_id, specialty)
  WHERE status IN ('BOOKED','PENDING_STAFF');

-- One active booking per patient per doctor (decision 13)
CREATE UNIQUE INDEX one_active_per_doctor
  ON appointments (patient_id, doctor_id)
  WHERE status IN ('BOOKED','PENDING_STAFF');

CREATE TABLE video_rooms (
  id             BIGSERIAL PRIMARY KEY,
  appointment_id BIGINT NOT NULL UNIQUE REFERENCES appointments(id),
  provider       TEXT NOT NULL,          -- 'mock' | 'jitsi' | ...
  room_ref       TEXT NOT NULL,          -- random, unguessable
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE urgent_cases (
  id          BIGSERIAL PRIMARY KEY,
  source      booking_source NOT NULL,    -- WEBSITE/CHAT/STAFF/MCP
  summary     TEXT NOT NULL,
  patient_id  BIGINT REFERENCES patients(id),
  user_id     BIGINT REFERENCES users(id),
  draft_context JSONB,                    -- preserved draft booking (decision 14)
  status      TEXT NOT NULL DEFAULT 'OPEN', -- OPEN | SEEN
  seen_by     BIGINT REFERENCES users(id),
  seen_at     TIMESTAMPTZ,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE approvals (
  id             BIGSERIAL PRIMARY KEY,
  kind           TEXT NOT NULL,           -- LATE_CANCEL | LATE_RESCHEDULE | ...
  appointment_id BIGINT REFERENCES appointments(id),
  payload        JSONB NOT NULL,
  status         TEXT NOT NULL DEFAULT 'PENDING', -- PENDING|APPROVED|REJECTED
  decided_by     BIGINT REFERENCES users(id),
  decided_at     TIMESTAMPTZ,
  reason         TEXT,
  graph_thread_id TEXT,                   -- LangGraph resume handle
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE leave_requests (
  id         BIGSERIAL PRIMARY KEY,
  doctor_id  BIGINT NOT NULL REFERENCES doctors(id),
  from_day   DATE NOT NULL,
  to_day     DATE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE audit_events (
  id         BIGSERIAL PRIMARY KEY,
  actor_id   BIGINT REFERENCES users(id),
  actor_kind TEXT NOT NULL,               -- USER | SYSTEM | MCP_PARTNER
  action     TEXT NOT NULL,
  target     TEXT NOT NULL,
  result     TEXT NOT NULL,               -- reason code
  override_reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE knowledge_sources (
  id        TEXT PRIMARY KEY,             -- document or skill id
  kind      TEXT NOT NULL,                -- DOCUMENT | SKILL | PARTNER
  title     TEXT NOT NULL,
  path      TEXT NOT NULL
);
```

### 8.3 Why these constraints matter

- **`no_doctor_overlap`** makes double booking impossible even if two requests arrive at the same instant. The application check gives a friendly reason code. The constraint is the safety net that guarantees "0 rule-breaking bookings".
- **Partial unique indexes** enforce the per-specialty and per-doctor limits at the database level.
- A slot "becomes available again" automatically when an appointment moves to `CANCELLED`, because the constraints only apply to `BOOKED` and `PENDING_STAFF`.
- `PENDING_STAFF` holds the original slot during a late reschedule (decision 12).

---

## 9. The Booking Service (Rule Engine)

### 9.1 Contract

```python
class BookingService:
    def find_slots(self, specialty, *, doctor_id=None, mode, from_day, to_day,
                   visit_type, patient_ref) -> SlotResult: ...
    def book(self, request: BookingRequest, actor: Actor) -> BookingResult: ...
    def cancel(self, appointment_id, actor: Actor) -> CancelResult: ...
    def reschedule(self, appointment_id, new_request, actor: Actor) -> BookingResult: ...
    def staff_override(self, request, actor: Actor, reason: str) -> BookingResult: ...
```

Every result carries `ok: bool`, a `reason_code`, and a human-readable message. Services never raise for rule violations; they return reason codes.

### 9.2 Validation chain (ordered)

The order puts cheap and safety checks first, and database-bound checks last.

| Step | Check | Placeholder reason code |
|---|---|---|
| 0 | Safety gate already passed by caller | (caller responsibility) |
| 1 | Actor allowed to act on this patient | `FORBIDDEN` |
| 2 | Identity match: known mobile with different name is rejected | `IDENTITY_MISMATCH` |
| 3 | Date within the next 30 days and not in the past | `OUT_OF_RANGE` |
| 4 | Not Sunday | `CLINIC_CLOSED` |
| 5 | Not a listed holiday | `HOLIDAY` |
| 6 | Doctor covers the specialty | `SPECIALTY_MISMATCH` |
| 7 | Doctor session status is OPD (not surgery or off) | `NOT_OPD` |
| 8 | Start on a 10-minute mark | `BAD_SLOT_ALIGNMENT` |
| 9 | Within clinic hours and not in lunch | `OUTSIDE_HOURS` |
| 10 | Duration by visit type (20 new, 10 follow-up) finishes inside its session | `EXCEEDS_SESSION` |
| 11 | Follow-up is with the doctor who saw the patient for that specialty | `FOLLOWUP_WRONG_DOCTOR` |
| 12 | One active booking per specialty | `ACTIVE_BOOKING_EXISTS` |
| 13 | One active booking per doctor | `ACTIVE_WITH_DOCTOR_EXISTS` |
| 14 | No doctor overlap (application check) | `SLOT_TAKEN` |
| 15 | Insert in a transaction. Database constraint violation maps to `SLOT_TAKEN` or the matching code | same |

**[VERIFY]** Replace the placeholder codes with the codes from the data pack README files.

### 9.3 Cancel and reschedule

```
cancel(appointment):
    if actor is patient and now > start_at - 2 hours:
        create approval(LATE_CANCEL), set status PENDING_STAFF
        return reason TOO_LATE_ROUTED_TO_STAFF
    else: set CANCELLED, audit

reschedule(appointment, new_request):
    run the full validation chain for the NEW slot first
    if outside the 2-hour window:
        in ONE transaction: cancel old + insert new   (all or nothing)
    else:
        create approval(LATE_RESCHEDULE), keep ORIGINAL slot held
        (status PENDING_STAFF) until staff decide      # decision 12
```

Two details to get right:
- The rule 12 and rule 13 unique indexes would block the new booking while the old one is still active. Perform cancel and insert inside one transaction, with the old row cancelled first.
- Validate the new slot before touching the old appointment, so a failed reschedule never loses the patient's existing booking.

### 9.4 Doctor leave

```
mark_leave(doctor, from_day, to_day):
    1. Set schedules for those dates to OFF.
    2. Find affected active appointments.
    3. For each: cancel, then search replacement:
         a. another doctor with the same specialty (or overlapping specialty),
            next free slot within 30 days
         b. else same doctor's next free slot within 30 days
         c. else record "no slot within 30 days" and tell the patient clearly
    4. Create approvals/offers; patient or staff confirms the offered slot
       (the offer itself passes the full validation chain when accepted).
    5. Audit everything.
```

Whether leave rebooking is automatic or offered for confirmation should follow the Iteration 4 handout **[VERIFY]**. The safer default is to offer, then book on confirmation.

### 9.5 Staff overrides

- Only `staff` and above, never the assistant or MCP.
- Requires a non-empty `reason`.
- Writes an `audit_events` row with actor, action, target, and reason.
- An override may bypass specific soft rules (for example the 2-hour window). It must never bypass the database overlap constraint or the safety gate.

---

## 10. Safety Architecture

### 10.1 Red-flag gate

```
any inbound text (chat, intake notes, booking free text, MCP request)
                     |
                     v
        +--------------------------+
        |  red_flags.detect(text)  |   deterministic, runs FIRST
        +------------+-------------+
          flag found |            | no flag
                     v            v
   return exact emergency     continue to assistant /
   text, stop all booking,    booking / skill logic
   create urgent case
   (source channel kept,
    draft booking preserved)
```

Rules:
- Runs in code on **every** channel before any model call, tool call, or skill load.
- Emergency text is a single constant, returned **word for word**:
  > “What you describe needs urgent attention. Please come to the clinic now or go to the nearest emergency department. Our staff have been notified.”
- Detection covers: sudden vision loss; curtain or shadow across vision; sudden shower of floaters or flashes; chemical splash or eye injury; severe eye pain with headache, nausea, or haloes.
- Method: keyword and phrase patterns with normalization (case, spacing, common spellings), plus an optional second-opinion Gemini classifier. The classifier may only **add** triggers, never remove one.
- Tuning direction: prefer false positives to false negatives. Measure against the red-flag test set (Iteration 5).
- Each trigger creates an `urgent_cases` row. Staff view shows it at the top until marked seen.
- For MCP partner bookings, the urgent case is created but no appointment detail is returned to the partner.

### 10.2 Output guard

A second code check on every assistant response before it reaches the user:
- Blocks naming a likely condition, treatment or medication advice, test interpretation, and lab-test recommendations.
- On a block: replace with a safe refusal ("A doctor will assess this") and log the event.
- Measured by the "0 diagnosis or treatment statements" target.

### 10.3 Skills cannot weaken safety

Skills are loaded after the safety gate and only add knowledge. No skill file can disable the gate, change reason codes, or call booking logic directly.

---

## 11. Authentication, Roles, and Access Control

### 11.1 v1: demo identity (now)

| Role | v1 sign-in |
|---|---|
| Patient | Mobile + name matched against the supplied patient data. Known mobile with a different name is rejected |
| Doctor | Seeded demo account, selected on the same Log in screen |
| Staff | Seeded demo account |
| Admin / Sub-admin | Seeded demo accounts |

The single **Log in** button opens one screen. After sign-in, the server returns the role and the frontend routes to the right area.

Important honesty note for the README: mobile + name is **not** secure authentication. It is the course's synthetic-data convention. State this clearly.

Session: a signed, `HttpOnly`, `SameSite` cookie containing a session ID mapped to `user_id` and `role` on the server.

### 11.2 Later update: real accounts

An `AuthProvider` interface keeps this a drop-in change:

```python
class AuthProvider(Protocol):
    def authenticate(self, credentials) -> AuthenticatedUser | None: ...
```

- `DemoIdentityProvider` (v1)
- `PasswordProvider` (later): email, password hash (argon2 or bcrypt), patient self-signup, verified mobile linking to a synthetic patient record
- Notifications (email or simulated SMS) added at the same time

### 11.3 Role and permission matrix

| Capability | Patient | Doctor | Staff | Sub-admin | Admin |
|---|:--:|:--:|:--:|:--:|:--:|
| View own appointments | ✔ | | | | |
| Book, cancel, reschedule own | ✔ (rules apply) | | ✔ (any patient) | | |
| View own schedule and intake notes | | ✔ | | | |
| Mark leave | | ✔ | ✔ (on behalf) | | |
| Urgent cases, approvals | | | ✔ | ✔ | ✔ |
| Handle walk-ins, manage holidays, doctors | | | ✔ | ✔ | ✔ |
| Authorized override (with reason) | | | ✔ | ✔ | ✔ |
| Create staff accounts | | | | | ✔ |
| Moderate staff (suspend, review audit) | | | | ✔ | ✔ |
| View audit trail | | | ✔ (own actions) | ✔ | ✔ |

The README only names Patient, Doctor, and Staff. Admin and Sub-admin come from decision 11.

### 11.4 Enforcement rules

1. Authorization is checked **on the server**, in a FastAPI dependency per route, and again at the **query level** (every query for appointments includes the owner filter).
2. A patient endpoint never accepts `patient_id` from the client. The patient ID is derived from the session.
3. A doctor endpoint filters by the doctor linked to the session.
4. Security tests (section 14) try cross-patient access and must fail closed.

---

## 12. API Design

All paths are prefixed `/api/v1`. Responses use a common envelope containing `ok`, `reason_code`, `message`, and `data`.

### Public

| Method | Path | Purpose |
|---|---|---|
| GET | `/public/clinic` | Intro, hours, location (demo values labelled as demo) |
| GET | `/public/doctors` | Doctors and specialties |
| GET | `/public/services` | Services/procedures from approved documents |
| GET | `/public/slots` | Available slots (no personal data) |
| POST | `/auth/login` | v1 demo identity, returns role |
| POST | `/auth/logout` | End session |
| GET | `/auth/me` | Current user and role |

### Patient (`role=patient`)

| Method | Path | Purpose |
|---|---|---|
| GET | `/patient/appointments` | Own upcoming and past |
| POST | `/patient/appointments` | Book (mode, specialty, slot) |
| POST | `/patient/appointments/{id}/cancel` | Cancel |
| POST | `/patient/appointments/{id}/reschedule` | Reschedule |
| POST | `/patient/appointments/{id}/join` | Get video join info (assigned patient only) |
| POST | `/assistant/chat` | Assistant message |

### Doctor (`role=doctor`)

| Method | Path | Purpose |
|---|---|---|
| GET | `/doctor/schedule` | Own schedule |
| GET | `/doctor/appointments/{id}` | Details and intake summary |
| POST | `/doctor/leave` | Mark leave |
| POST | `/doctor/appointments/{id}/join` | Video join (assigned doctor only) |

### Staff (`role=staff` or higher)

| Method | Path | Purpose |
|---|---|---|
| GET | `/staff/today` | Today's appointments with filters (doctor, mode, source) |
| GET | `/staff/urgent` | Open urgent cases (pinned first) |
| POST | `/staff/urgent/{id}/seen` | Mark seen |
| GET | `/staff/approvals` | Approval queue |
| POST | `/staff/approvals/{id}/decide` | Approve or reject (resumes graph if linked) |
| GET | `/staff/patients?q=` | Search |
| POST | `/staff/appointments` | Book on behalf, walk-in, or override (reason required) |
| POST | `/staff/leave/{id}/rebook` | Leave rebooking workflow |
| CRUD | `/staff/holidays`, `/staff/doctors` | Management |
| GET | `/staff/audit` | Audit trail |
| GET | `/staff/appointments/{id}/video` | See mode and join status for help |

### Admin

| Method | Path | Purpose |
|---|---|---|
| POST | `/admin/staff` | Create staff account |
| PATCH | `/admin/staff/{id}` | Suspend or reactivate (sub-admin allowed) |

---

## 13. Assistant Architecture

### 13.1 Request pipeline

```
user message
   |
   v
[1] Safety gate (deterministic)  --flag--> emergency response + urgent case
   |
   v
[2] Intent classification (Gemini or rules)
   |-- policy/info question  --> RAG answer (section 13.2)
   |-- symptom description   --> specialty routing (13.3)
   |-- booking/cancel/resched--> LangGraph workflow (13.5)
   |-- skill topic           --> skill load (13.6)
   |-- lab question          --> lab MCP client (13.7)
   |-- anything else         --> polite scope message
   |
   v
[3] Output guard (no diagnosis/treatment) --> response with citations
```

### 13.2 RAG with citations (Iteration 3)

**Ingestion** (offline script):
1. Parse the clinic documents from pack 3.
2. Chunk by section with overlap. Attach metadata: `doc_id`, `title`, `section`, `source_path`.
3. Embed with the Gemini embedding model and upsert to Pinecone.
4. Mirror document metadata into `knowledge_sources`.

**Retrieval:**
1. Vector search in Pinecone (top K).
2. Keyword search over chunk text (for example Postgres full-text search or BM25) for exact terms like costs.
3. Merge the two lists (reciprocal rank fusion), then optionally rerank.
4. If the best score is below a threshold, return **"This information is not available in the clinic documents"** without calling the model to guess.

**Generation:**
- Prompt contains only the retrieved chunks and instructions to answer from them.
- The response schema requires a `citations` list of `doc_id`s. A post-check rejects any policy answer without a citation, and rejects citations not in the retrieved set.

### 13.3 Specialty routing

- Input: the patient's description. Output: a specialty and a short neutral explanation ("A doctor will assess this"). Never a condition name.
- Method: Gemini classifier with few-shot examples from the routing sample set, constrained to the clinic's specialty list.
- Evaluated on the routing test set; target 90% or better.

### 13.4 Visit summary (Iteration 2)

- Input: intake text and visit history.
- Output schema: `patient_reported`, `inferred`, `missing`. Inferred items are clearly labelled.
- Output guard blocks diagnosis or treatment language.
- Read by doctors only for their own appointments.

### 13.5 Booking agent (Iteration 4, LangGraph)

```
START
  -> safety_gate --flag--> urgent_case -> END
  -> classify_intent
  -> collect_details  (loop until specialty, mode, patient, preferred time known)
  -> find_slots       (calls BookingService.find_slots)
  -> propose          (show the proposed appointment, ask for confirmation)
  -> await_confirm
  -> execute          (calls BookingService.book / cancel / reschedule)
        |-- ok ----------> confirmation message
        |-- needs staff -> create approval -> INTERRUPT (human in the loop)
        |                       staff decides -> resume -> notify patient
        '-- refused -----> explain reason code in plain language, offer next options
```

Design rules:
- **Tools are thin wrappers** over services. The model never writes SQL and never decides rules.
- The safety gate runs again on each new user message inside the graph, not only at the start.
- State is checkpointed in PostgreSQL, so approval pauses survive restarts.
- If a red flag appears mid-booking, the draft (collected details) is saved in `urgent_cases.draft_context` and the graph ends (decision 14).

### 13.6 Skills (Iteration 6)

- At startup, the loader reads only the front matter (`name`, `description`) of each `SKILL.md`.
- The assistant selects a skill by description; only then is the full file loaded.
- **Path safety:** resolve the real path and require it to stay inside that skill's own folder. Reject `..`, absolute paths, and symlinks that escape.
- Skills in scope: cataract surgery care, LASIK suitability intake (one question at a time, never decides suitability), prepare-for-visit, and the project-created children-visit skill (routes to Dr. Vikram Menon, documented preparation only).
- Skill answers carry the skill identifier as a citation.

### 13.7 MCP

**NetraCare MCP server**
- Tools: `find_slots` and `book_appointment`, with typed (Pydantic) inputs and clear descriptions.
- Calls `BookingService` directly. No duplicated rules.
- Runs the same safety gate and identity matching.
- Records `source = MCP` and an audit event.
- Returns only slot data and a booking result code to the partner. No appointment details are exposed through the partner server.

**CityCare Lab MCP client**
- Used for general test logistics only.
- Response is tagged with a partner source label.
- Timeouts and a circuit breaker. If the lab server is down, the assistant continues and says the lab information is currently unavailable.
- No interpretation of results, no "you need this test", no lab booking.

---

## 14. Virtual Consultation Design

### 14.1 Data model fit

Virtual is an attribute of the same appointment (`mode = VIRTUAL`) plus one `video_rooms` row. It uses the identical booking rules (README section 2).

### 14.2 Provider interface

```python
class VideoProvider(Protocol):
    def create_room(self, appointment_id: int) -> RoomRef: ...
    def join_info(self, room: RoomRef, role: str, user_id: int) -> JoinInfo: ...
```

| Implementation | Description | When |
|---|---|---|
| `MockRoomProvider` | An in-app "demo call" page with a placeholder panel, timer, and join/leave buttons | Default for the demo. Always works |
| `JitsiProvider` | Opens a meeting room on a free Jitsi server using a random room name stored server-side | Optional, if the free service works for the demo |

**[VERIFY]** Before relying on Jitsi: the free public server's terms, and whether it currently lets anyone start a meeting without signing in. If the current behaviour does not suit a smooth demo, stay with the mock room.

Honest limitation to state in the README: on a free public video server, anyone who knows the room name could join. The protection here is an unguessable random name delivered only through authenticated endpoints. A production deployment would use a provider with signed tokens and per-room access control. This is acceptable for a synthetic-data demo, and it is exactly the kind of limitation the brief asks you to be clear about.

### 14.3 Access flow

```
Patient/Doctor clicks "Join" on their dashboard
   -> POST /…/appointments/{id}/join
   -> server checks: session user is the assigned patient OR assigned doctor,
      appointment is VIRTUAL and BOOKED, current time is inside the allowed
      window (for example 15 min before start until end)
   -> returns short-lived join info (never the permanent room reference to others)
```

- Staff see the mode and a "help join" panel, not the join link itself unless required for support.
- No recordings are stored. No meeting tokens appear in logs or in public responses.

---

## 15. Frontend Architecture

### 15.1 Routes

```
/                       Home
/doctors                Doctors and specialties
/services               Services and procedures
/contact                Clinic information
/book                   Appointment type choice and booking entry
/login                  Single login (v1 demo identity)
/patient/*              Patient area            (guard: patient)
/doctor/*               Doctor dashboard        (guard: doctor)
/staff/*                Staff dashboard         (guard: staff+)
/admin/*                Account management      (guard: admin, sub-admin)
```

After login the app reads the role from `/auth/me` and redirects. Route guards are for user experience only.

### 15.2 Key components

| Component | Responsibility |
|---|---|
| `BookingWizard` | Mode (in-person/virtual) → specialty → doctor/slot → confirm. Shows reason-code messages |
| `SlotPicker` | Calendar plus 10-minute grid within OPD sessions only |
| `AssistantChat` | Messages, citations list, visible emergency banner |
| `UrgentBanner` | Staff view, pinned top, mark-seen action |
| `ApprovalQueue` | Approve or reject flagged actions |
| `VideoJoin` | Join action with time-window state |
| `AuditTable` | Filter by actor, action, source |

### 15.3 UI rules

- Demo values (address, phone) carry a visible "demo" label.
- Emergency text is shown exactly as specified when returned by the API.
- Source label "Booked via" (Website, Chat, Staff, MCP) appears in the staff views.
- Never compute rules in the browser. The UI only displays what the API returns.

### 15.4 Frontend state

- A small API client with typed response shapes.
- React Query (or a similar cache) for server data, and a session context for the role.

---

## 16. Security and Privacy Checklist

- [ ] Secrets only in `.env`; `.env.example` has names only; `.env` is gitignored
- [ ] Gemini and Pinecone keys server-side only
- [ ] Every route has an explicit role dependency; default deny
- [ ] Every patient query filtered by session patient ID
- [ ] Intake notes visible only to the assigned doctor and staff
- [ ] Input validation with Pydantic on every endpoint
- [ ] Rate limiting on login and chat endpoints
- [ ] CORS limited to the frontend origin
- [ ] Logs exclude message text, intake notes, tokens, and join links
- [ ] Synthetic data only; README states this prominently
- [ ] v1 identity limitation documented honestly

---

## 17. Observability and Evaluation (Iteration 5)

### 17.1 Tracing

Capture per request: request ID, channel, safety-gate result, retrieved source IDs, tool calls and outcomes, refusals, reason codes, latency, and token/cost estimates. Store identifiers and codes rather than raw sensitive text.

Tooling options named by the handouts: LangSmith, Opik, RAGAS. Pick one tracing tool (do not set up all of them) given the time budget.

### 17.2 Evaluation sets and targets

| Target | Eval script | How it is measured |
|---|---|---|
| Red-flag messages trigger emergency response: 100% | `evals/red_flags.py` | Run the full red-flag set through all channels; response must equal the exact constant |
| Routing accuracy ≥ 90% | `evals/routing.py` | Compare to the routing test set labels |
| Bookings that break clinic rules: 0 | `evals/booking_rules.py` | Generated and scenario requests; verify with an independent rule checker |
| Policy answers cite a clinic document: 100% | `evals/policy_citations.py` | Citation present and present in retrieved set |
| Answers naming a condition or suggesting treatment: 0 | `evals/no_diagnosis.py` | Rule-based check plus a calibrated judge on adversarial prompts |

Rules for reporting:
- Report real numbers, including misses. Do not present an unmeasured target as achieved.
- Calibrate any LLM judge against hand-labelled examples before trusting it.
- `evals/run_all.py` runs against a fresh synthetic database and writes `docs/evaluation-results.md`.

### 17.3 Contract tests

The same scenario list is executed through the website API, the assistant tools, the staff API, and the MCP tools. All four must return the same reason code for the same input. This is the strongest proof that rules cannot diverge.

---

## 18. Iteration Plan in Detail

Each iteration lists deliverables, tasks, and an exit test. Iterations are cumulative.

### Iteration 1: Website and scheduling foundation

**Deliverables**
- PostgreSQL schema, migrations, seed loader for data pack 1
- `BookingService`, `reasons.py`, audit, urgent-case table (empty use for now)
- Demo identity login with role redirect and server-side guards
- Public pages and the three role dashboards (minimal but real)
- Staff route for actions inside the 2-hour window

**Tasks**
1. Inspect data pack 1 and fix the schema **[VERIFY]**
2. Alembic migration and seed script (idempotent, runs on a fresh DB)
3. Implement the validation chain with unit tests per rule
4. Auth, session, and role dependencies
5. Patient, doctor, and staff endpoints
6. React pages and routing

**Exit test**
- Table-driven tests: one case per rule code, all pass
- Concurrency test: two simultaneous bookings for one slot yield one success
- Patient A cannot read patient B's appointment (HTTP 403 or 404)

### Iteration 2: First LLM features

**Deliverables**
- Safety gate (`red_flags.py`) wired in front of every endpoint that accepts free text
- Urgent case creation and the staff pinned banner with "mark seen"
- Visit summary workflow
- Eye-fact banner
- Output guard v1

**Tasks**
1. Build red-flag patterns and test set from the data pack 2 examples
2. Urgent case service (source channel kept)
3. Gemini wrapper with structured output
4. Summary schema (reported/inferred/missing) and prompts
5. Doctor view of intake summary

**Exit test**
- Every red-flag example returns the exact emergency text and creates an urgent case
- Summaries label inferred items and never contain a diagnosis (checked by the output guard)

### Iteration 3: Patient information chat and retrieval

**Deliverables**
- Ingestion script, Pinecone index, hybrid retrieval, citations
- Specialty routing
- `AssistantChat` component with citation display

**Tasks**
1. Chunk and index pack 3 documents
2. Retrieval with threshold and fusion
3. Answer generation with citation schema and post-check
4. Routing classifier with few-shot examples
5. Frontend chat

**Exit test**
- Questions with known answers return the right citation
- Questions the documents do not answer return the "not available" message
- Routing set accuracy measured and recorded

### Iteration 4: Booking assistant and staff in the loop

**Deliverables**
- LangGraph workflow with Postgres checkpointer
- Approval queue and resume
- Leave workflow and affected-patient rebooking
- Intake summary attached to bookings

**Tasks**
1. Tool wrappers over `BookingService`
2. Graph nodes and confirmation step
3. Approval interrupt and resume path
4. Leave service and staff rebook screen
5. Pack 4 scenarios as automated tests

**Exit test**
- Assistant bookings produce identical reason codes to the website for the same inputs
- A late cancellation pauses for approval and completes after staff decide
- Red flag mid-conversation stops booking and preserves the draft

### Iteration 5: Evaluations and observability

**Deliverables**
- All five eval scripts, `run_all.py`, results document
- Tracing in place
- Contract tests across channels

**Exit test**
- A single command regenerates the results on a fresh database
- Results are reported honestly against each target

### Iteration 6: MCP and skills

**Deliverables**
- NetraCare MCP server (`find_slots`, `book_appointment`)
- "Booked via" labels and audit entries
- Lab MCP client with fallback
- Skill loader with path restrictions and four skills

**Exit test**
- Partner booking creates urgent cases for red flags and exposes no appointment details
- Lab server stopped: the assistant still works and says lab information is unavailable
- Path traversal attempts on skill reads are rejected

### Parallel track: Virtual consultation

**Deliverables:** `mode` field, `VideoProvider` interface, `MockRoomProvider`, join endpoints, join UI, staff mode visibility.
**Exit test:** only the assigned patient and doctor can obtain join info; a different patient and an unauthenticated user cannot.

---

## 19. Suggested Schedule (2–3 Days)

### Day 1: Foundation (Iteration 1 plus start of safety)
- Morning: read data packs, finalize schema, migrations, seed
- Midday: `BookingService` with full rule tests
- Afternoon: auth, role guards, core endpoints
- Evening: React shell, public pages, login, minimal dashboards

### Day 2: AI core (Iterations 2, 3, and 4)
- Morning: safety gate, urgent cases, staff banner
- Midday: RAG ingestion and cited chat, routing
- Afternoon: LangGraph booking flow and approvals
- Evening: leave workflow

### Day 3: Proof and extras (Iterations 5, 6, and video)
- Morning: eval scripts and contract tests, fix failures
- Midday: MCP server, lab client, skills (as far as time allows)
- Afternoon: mock-room virtual consultation
- Evening: demo rehearsal on a fresh database, README, results document

**Cut line if behind:** drop in this order: Jitsi provider, lab MCP, skills, MCP server, visit summary polish. Never cut: booking rules, safety gate, urgent cases, citations, evaluation reporting.

---

## 20. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Scope too large for 3 days | Unfinished demo | Priority table in section 2; cut line in section 19 |
| Double booking under concurrency | Violates 0-rule-break target | Exclusion constraint plus transactional insert |
| Rule drift across channels | Inconsistent behaviour | One `BookingService`; contract tests |
| Red-flag false negatives | Safety failure | Broad patterns, test set, tune toward over-triggering |
| Hallucinated policy answers | Wrong information | Threshold, citation post-check, "not available" path |
| Cross-patient data leak | Privacy failure | Session-derived IDs, query-level filters, security tests |
| Gemini or Pinecone limits and outages | Broken chat | Check free-tier limits early; cache; clear error messages |
| Timezone mistakes | Wrong slots | Single timezone module, injectable clock, tests around midnight and session edges |
| Video free service changes | Broken demo | Mock provider as default |
| Reason codes differ from handouts | Failing checks | Replace placeholders after reading the packs |

---

## 21. Final Demo Checklist

Run against a **fresh** synthetic database.

- [ ] Website booking (in-person)
- [ ] Virtual booking and join as patient and doctor (mock room)
- [ ] Rule refusals with clear reason codes
- [ ] Late cancel routed to staff, held slot, staff decision
- [ ] Red-flag escalation on website, chat, and MCP; staff see urgent case at top, source shown
- [ ] Policy answer with citation, and an unanswerable question with "not available"
- [ ] Symptom routing to a specialty without naming a condition
- [ ] Lab question answered with partner label, and again with lab server stopped
- [ ] Cataract, LASIK (one question at a time), prepare-for-visit, and children skills
- [ ] Partner MCP booking with "Booked via MCP" and no detail exposure
- [ ] Skill path traversal attempt rejected
- [ ] Doctor leave and patient rebooking
- [ ] Evaluation results shown, with any missed target stated plainly
- [ ] Admin creates staff; sub-admin moderates

---

## 22. Open Items

1. Reason codes, seed formats, and scenario details from the data packs (section 3).
2. Final choice of free video option after checking current terms, or stay with the mock room.
3. Which tracing tool to use for Iteration 5.
4. Whether leave rebooking is automatic or offered for confirmation, per the Iteration 4 handout.
5. Later update plan: real accounts, patient self-signup, verified mobile linking, and notifications.
