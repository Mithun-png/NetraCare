# NetraCare — AI Front Desk & Care Coordination System

**NetraCare** is a clinical AI front desk and care coordination platform for a 5-doctor ophthalmic clinic. It provides automated triage, slot scheduling, patient self-service, doctor clinical reviews, front-desk staff coordination, and a RAG-powered patient chat—while strictly enforcing non-negotiable medical safety rules (deterministic red-flag emergency detection and 0 diagnosis/treatment advice).

---

## 🏛️ System Architecture

NetraCare follows a **Three-Tier Architecture** centered around a **Single Rule Engine (`BookingService`)** and a **Hybrid RAG Pipeline**:

```
                 +---------------------------------------------+
                 |            Interaction Channels             |
                 |  React Website  |  Patient Chat (RAG)       |
                 |  Staff Desk     |  Search Debug Inspector   |
                 +----------------------+----------------------+
                                        |
                                        v
                 +---------------------------------------------+
                 |       Deterministic Safety Pre-Filter       |
                 |  red_flags.check_red_flags() -> 100% Triage |
                 |  Emergency Script + Urgent Case in DB       |
                 +----------------------+----------------------+
                                        |
                                        v
                 +---------------------------------------------+
                 |      Hybrid RAG Knowledge Base Engine       |
                 |  - Chunking on '## ' headers (38 sections)  |
                 |  - BM25 Keyword Search (case/punct clean)   |
                 |  - Chroma Vector Search (Dense Embeddings)  |
                 |  - 50/50 Hybrid Rank Fusion (Top 4 chunks)  |
                 |  - Contextual History Query Rewriter        |
                 |  - Source Citation Formatter                |
                 |  - Zero-Diagnosis & "I don't know" Guard    |
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
                 +---------------------------------------------+
```

---

## 🚀 Quick Start Guide

### 1. Environment & Knowledge Base Setup

```powershell
# Copy environment configuration
cp .env.example .env

# Build or rebuild Knowledge Base index (one command)
python build_index.py
```

### 2. Backend Setup & Run

The backend is built with **Python 3.11+**, **FastAPI**, **LangChain**, **Rank-BM25**, **ChromaDB**, and **SQLAlchemy 2.0**.

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

## 🧪 Automated Test Suite (63 Tests, 100% Passing)

Run the comprehensive pytest suite verifying all clinic scheduling rules, API contracts, safety triage, Iteration 2 LLM summaries, and Iteration 3 RAG patient chat:

```powershell
$env:PYTHONPATH="backend"
python -m pytest backend/tests -p no:cacheprovider -v
```

### Run Benchmark Evals (20 Questions & 20 Routing Samples):
```powershell
$env:PYTHONPATH="backend"
python backend/evals_iteration3.py
```
- **Questions Benchmark (`data/questions.csv`)**: 20/20 (100.0% Pass)
- **Routing Benchmark (`data/routing_samples.csv`)**: 20/20 (100.0% Pass)

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
   - Red flag with invalid slot: emergency response returned and urgent case preserved
   - Doctor patient AI summary (<120 words, faithful to recorded notes only, doctor attribution, zero diagnosis/advice)
   - Patient role calling doctor summary returns 403 Forbidden
   - Staff viewing urgent cases and marking seen
   - Summary for patients with no past visits (Aditya Bose P20) states "no previous visits on record"
5. **`backend/tests/test_iteration3.py` (10 Tests)**:
   - Knowledge base document splitting on `## ` headings into 38+ sections with complete metadata
   - BM25 keyword search ranks `procedures.md > Diabetic eye check` #1 for HbA1c query
   - Dense vector search retrieves `procedures.md > Squint surgery` in top 4 for child straightening surgery query
   - Staff search debug view compares BM25 vs Vector vs Hybrid side-by-side
   - Patient chat returns accurate policy/procedure answers with formatted source citations
   - Follow-up question rewriting using 6-message conversation history
   - Speciality routing from `doctors.md` with doctor attribution and reminder that doctor will assess
   - Non-eye inquiries routed with explanation that NetraCare only looks after eyes
   - Medical guardrails: 0 unsolicited condition diagnoses, 0 treatment advice
   - Uncovered questions trigger exact fixed fallback: "I don't know. Our clinic documents don't cover that. Please ask Staff at the front desk." with 0 sources
   - Booking inquiries point to Book Appointment page
   - Red-flag emergency triage in chat creates `UrgentCase(source="CHAT", ...)` in DB

---

## 👥 Portals & Roles

| Role | Sign-in Method | Capabilities |
|---|---|---|
| **Patient** | Mobile + Name (e.g. `9000000001` / `Asha Verma`) | Interactive RAG Chat with document citations, Fact of the Day with Refresh, view doctors & slots, book appointments with mandatory reason, view own history, cancel/reschedule |
| **Doctor** | Select from Doctor list (D1–D5) | View daily OPD schedule, review patient intake reason, review past doctor notes, view AI clinical summary (<120 words), complete visits with mandatory clinical notes |
| **Staff** | Staff Name | RAG Search Debugger (BM25 vs Vector vs Hybrid), view all doctor appointments, pinned urgent cases banner with "Mark Seen", approval queue (<2hr cancellations), book walk-ins, cancel inside 2 hours |

---

## 🔬 Iteration 5: Evals & Observability

### 1. Opik Tracing & Monitoring Setup
NetraCare uses **Opik** for production tracing, latency, token monitoring, cost tracking, and offline eval experiments:
- **`netracare-dev`**: Live application monitoring dashboard (chat turns, red-flag checks, doctor summaries, facts of the day).
- **`netracare-evals`**: Experiment tracking for automated golden benchmark runs.

To configure Opik, add your API key to `.env` or your terminal session:
```powershell
# In .env or shell:
OPIK_API_KEY="your-opik-api-key"
```
*Note: If `OPIK_API_KEY` is not present or Opik is offline, NetraCare automatically degrades gracefully to zero-overhead local execution without errors.*

### 2. Running Automated Evals

One command executes all six evaluation suites on the golden datasets, runs deterministic and LLM judge scorers, executes an independent rule audit on appointment databases, and writes `evals/results/summary.md`:

```powershell
# Run all 6 suites on small benchmark sets (default)
python run_evals.py

# Run a specific suite
python run_evals.py --suite red_flags
python run_evals.py --suite routing
python run_evals.py --suite policy
python run_evals.py --suite safety
python run_evals.py --suite summary
python run_evals.py --suite booking

# Run on large benchmark datasets
python run_evals.py --large
```

### 3. Five Brief Section 09 Targets (100% Pass)
| Target | Golden Set | Scored By | Target | Achieved | Status |
|---|---|---|---|---|---|
| **Red flags get emergency response** | `red_flags.csv` | Code: exact match, 0 bookings | 100% | 100.0% (10/10) | **MET** |
| **Routed to the right speciality** | `routing.csv` | LLM Judge + Code compare | ≥ 90% | 100.0% (10/10) | **MET** |
| **Bookings that break a clinic rule** | `booking_scenarios.csv` | Code: independent rule audit | 0 | 0 rule breaks | **MET** |
| **Policy answers cite a document** | `policy_questions.csv` | Code: document citations present | 100% | 100.0% (8/8) | **MET** |
| **Answers naming condition or treatment** | `safety_prompts.csv` + chats | LLM Judge safety rubric | 0 | 0 violations (8/8 safe) | **MET** |

---

## 📋 Iteration Roadmap

- **Iteration 1 (Completed)**: Clinic website, database models, seed loader, Single Rule Engine (`BookingService`), role-based dashboards, automated rule tests.
- **Iteration 2 (Completed)**: LangChain LLM features (Fact of the Day with refresh & caveat, red-flag emergency classifier with 5 categories & negation handling, urgent cases dashboard, doctor summary chain under 120 words with zero unsolicited diagnosis, mandatory reason and doctor notes).
- **Iteration 3 (Completed)**: RAG patient information chat (hybrid search BM25 + Vector, citations to clinic docs, "I don't know" threshold, conversation history rewriter, speciality routing, search debug inspector).
- **Iteration 4 (Completed)**: LangGraph conversational booking agent, confirmation cards, staff approvals (<2hr late cancel/reschedule), doctor leave rebooking engine (R7).
- **Iteration 5 (Completed)**: Full offline evaluation suite (`run_evals.py`), Opik observability & tracing (`netracare-dev`, `netracare-evals`), safety judge calibration (12/12), independent rule auditor, RAGAS metrics report (`evals/results/summary.md`).
- **Iteration 6**: NetraCare Partner MCP Server, CityCare Lab MCP Client, Agent Skills (`cataract-surgery-care`, `lasik-suitability-intake`, `prepare-for-visit`, `children-visit`).
