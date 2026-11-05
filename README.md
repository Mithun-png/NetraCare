# NetraCare — AI Front Desk & Care Coordination System

**NetraCare** is a clinical AI front desk and care coordination platform for a 5-doctor ophthalmic clinic. It provides automated triage, slot scheduling, patient self-service, doctor clinical reviews, and front-desk staff coordination—while strictly enforcing non-negotiable medical safety rules (deterministic red-flag emergency detection and 0 diagnosis/treatment advice).

---

## 🏛️ System Architecture

NetraCare follows a **Three-Tier Architecture** centered around a **Single Rule Engine (`BookingService`)**:

```
                 +---------------------------------------------+
                 |            Interaction Channels             |
                 |  React Website  |  Patient Chat (LLM/RAG)   |
                 |  Staff Desk     |  Partner MCP Server       |
                 +----------------------+----------------------+
                                        |
                                        v
                 +---------------------------------------------+
                 |       Deterministic Safety Pre-Filter       |
                 |  red_flags.check_red_flags() -> 100% Triage |
                 |  LangChain Pydantic Parser & Regex Guard    |
                 +----------------------+----------------------+
                                        |
                                        v
                 +---------------------------------------------+
                 |    Single Rule Engine (BookingService)      |
                 |  - 10-Minute Slot Alignment                 |
                 |  - 30-Day Booking Window                    |
                 |  - 20m New / 10m Follow-up Sessions         |
                 |  - Sunday & Holiday Protection              |
                 |  - OPD vs Surgery vs Off Schedules          |
                 |  - Single Active Booking per Speciality     |
                 |  - Follow-up Doctor Continuity              |
                 |  - 2-Hour Cancellation Cutoff to Staff      |
                 |  - Zero Double-Booking Guarantee            |
                 +----------------------+----------------------+
                                        |
                                        v
                 +---------------------------------------------+
                 |              Database Layer                 |
                 |   SQLite (dev/test) / PostgreSQL (prod)     |
                 |   SQLAlchemy 2.0 ORM Models + Seed Loader   |
                 +----------------------+----------------------+
```

---

## 🚀 Quick Start Guide

### 1. Environment Setup

Copy `.env.example` to `.env` and set any required keys:

```powershell
cp .env.example .env
```

### 2. Backend Setup & Run

The backend is built with **Python 3.11+**, **FastAPI**, **LangChain**, **Pydantic v2**, and **SQLAlchemy 2.0**.

```powershell
# Navigate to project root
$env:PYTHONPATH="backend"

# Start FastAPI uvicorn server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- API Base URL: `http://127.0.0.1:8000`
- Interactive Swagger Documentation: `http://127.0.0.1:8000/docs`
- Healthcheck: `http://127.0.0.1:8000/api/v1/health`

### 3. Frontend Setup & Run

The frontend is built with **React**, **Vite**, and **Lucide Icons**.

```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```

- Web Portal: `http://localhost:5173`

---

## 🧪 Automated Test Suite (53 Tests, 100% Passing)

Run the comprehensive pytest suite verifying all clinic scheduling rules, API contracts, safety triage, and Iteration 2 LLM features:

```powershell
$env:PYTHONPATH="backend"
python -m pytest backend/tests -p no:cacheprovider -v
```

### Verified Test Suites:
1. **`backend/tests/test_rules.py` (38 Tests)**: Runs all 38 stretch rule test cases (`stretch/rule_tests.csv`) under a fixed clinic clock (`CLINIC_NOW = 2026-11-02 10:00:00`):
   - Double booking prevention (`DOUBLE_BOOKED`)
   - 10-minute alignment (`INVALID_START_TIME`)
   - Sunday & holiday closure (`CLINIC_CLOSED`, `HOLIDAY`)
   - Lunch break (1-2 PM) and outside hours (`OUTSIDE_SESSION`)
   - Session boundary overflow (`ENDS_AFTER_SESSION`)
   - Doctor schedule adherence (`DOCTOR_OFF`, `SURGERY_SESSION`)
   - Speciality matching (`SPECIALITY_MISMATCH`)
   - One active booking per speciality (`ACTIVE_BOOKING_EXISTS`)
   - Follow-up validation & doctor continuity (`NO_PREVIOUS_VISIT`, `FOLLOW_UP_DIFFERENT_DOCTOR`)
   - 2-Hour cancellation cutoff routing to staff (`INSIDE_2_HOURS` -> `to_staff`)
   - Cross-patient isolation (`NOT_YOUR_APPOINTMENT`)
   - Inactive appointment protection (`NOT_ACTIVE`)
2. **`backend/tests/test_red_flags.py` (1 Test Suite, 35 Cases)**: Evaluates all 35 clinical symptom cases from Data Pack 2 (`reason_samples.csv`):
   - 100% emergency response on red flags across 5 categories
   - Correctly discriminates negations ("no sudden loss", "gradual loss")
3. **`backend/tests/test_api.py` (5 Tests)**: Full HTTP integration tests across public, patient, doctor, and staff endpoints with role guards.
4. **`backend/tests/test_iteration2.py` (9 Tests)**:
   - Fact of the day with refresh & required caveat
   - Mandatory non-empty doctor notes on visit completion
   - Mandatory appointment reasons (up to 300 chars)
   - Red-flag emergency detection & urgent case creation in DB
   - Red flag with invalid slot (e.g. Dr. Rao Thursday surgery session): emergency response returned and urgent case preserved
   - Doctor patient AI summary (<120 words, faithful to recorded notes only, doctor attribution, zero diagnosis/advice)
   - Patient role calling doctor summary returns 403 Forbidden
   - Staff viewing urgent cases and marking seen
   - Summary for patients with no past visits (Aditya Bose P20) states "no previous visits on record" and invents nothing

---

## 👥 Portals & Roles

| Role | Sign-in Method | Capabilities |
|---|---|---|
| **Patient** | Mobile + Name (e.g. `9000000001` / `Asha Verma`) | View doctors & slots, Fact of the Day with Refresh, book appointments with mandatory reason, view own history, cancel/reschedule |
| **Doctor** | Select from Doctor list (D1–D5) | View daily OPD schedule, review patient intake reason, review past doctor notes, view AI clinical summary (<120 words), complete visits with mandatory clinical notes |
| **Staff** | Staff Name | View all doctor appointments, pinned urgent cases banner with "Mark Seen", approval queue (<2hr cancellations), book walk-ins, cancel inside 2 hours |

---

## 📋 Iteration Roadmap

- **Iteration 1 (Completed)**: Clinic website, database models, seed loader, Single Rule Engine (`BookingService`), role-based dashboards, automated rule tests.
- **Iteration 2 (Completed)**: LangChain LLM features (Fact of the Day with refresh & caveat, red-flag emergency classifier with 5 categories & negation handling, urgent cases dashboard, doctor summary chain under 120 words with zero unsolicited diagnosis, mandatory reason and doctor notes).
- **Iteration 3**: RAG patient information chat (hybrid search, citations to clinic docs, "I don't know" threshold), speciality routing.
- **Iteration 4**: LangGraph conversational booking agent, staff approval pauses, doctor leave rebooking workflow.
- **Iteration 5**: Full offline/online evaluation suite (`evals/run_all.py`), safety judge calibration, telemetry traces.
- **Iteration 6**: NetraCare Partner MCP Server, CityCare Lab MCP Client, Agent Skills (`cataract-surgery-care`, `lasik-suitability-intake`, `prepare-for-visit`, `children-visit`).
