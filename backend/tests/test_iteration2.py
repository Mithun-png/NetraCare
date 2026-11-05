"""Comprehensive tests for NetraCare Iteration 2 features.
Verifies:
1. Fact of the Day with Refresh and required caveat
2. Mandatory doctor notes for visit completion
3. Mandatory appointment reasons (up to 300 chars)
4. Red-flag emergency detection and urgent case creation
5. Doctor patient summary with clinical guardrails
6. Patient direct access to summary is forbidden (403)
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import init_db, SessionLocal
from app.db.models import UrgentCase, Appointment, Patient
from app.db.seed import seed_db

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()
    db = SessionLocal()
    seed_db(db, load_stretch=False)
    db.close()

@pytest.fixture(autouse=True)
def clean_booked_appointments():
    db = SessionLocal()
    db.query(Appointment).filter(Appointment.status.in_(["booked", "pending_staff"])).delete()
    db.query(UrgentCase).delete()
    db.commit()
    db.close()

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_fact_of_the_day(client):
    # Initial request
    res = client.get("/api/v1/public/fact-of-the-day")
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert len(data["fact"]) > 10
    assert data["caveat"] == "General information, not medical advice"

    # Refresh with previous
    first_fact = data["fact"]
    res2 = client.get(f"/api/v1/public/fact-of-the-day?previous={first_fact}")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["fact"] != first_fact
    assert data2["caveat"] == "General information, not medical advice"

def test_mandatory_doctor_note(client):
    # Login Dr. Rao (D1)
    login_res = client.post("/api/v1/auth/login", json={"role": "doctor", "doctor_id": "D1"})
    token = login_res.json()["session_token"]

    # Try completing visit with empty note -> Must fail with 400
    res_empty = client.post(
        "/api/v1/doctor/appointments/A001/complete",
        headers={"X-Session-Data": token},
        json={"doctor_note": "   "},
    )
    assert res_empty.status_code == 400
    assert "required" in res_empty.json()["detail"].lower()

def test_mandatory_appointment_reason(client):
    # Login patient P02
    login_res = client.post("/api/v1/auth/login", json={"role": "patient", "mobile": "9000000002", "name": "Rohan Gupta"})
    token = login_res.json()["session_token"]

    # Try booking without reason -> Must fail with 400
    res_no_reason = client.post(
        "/api/v1/patient/appointments",
        headers={"X-Session-Data": token},
        json={
            "doctor_id": "D1",
            "speciality": "General",
            "visit_type": "new",
            "date": "2026-11-04",
            "start_time": "10:00",
            "reason": "",
        },
    )
    assert res_no_reason.status_code == 400
    assert "reason is required" in res_no_reason.json()["detail"].lower()

def test_red_flag_and_negation_bookings(client):
    login_res = client.post("/api/v1/auth/login", json={"role": "patient", "mobile": "9000000005", "name": "Priya Menon"})
    token = login_res.json()["session_token"]

    # 1. Negation: "No sudden loss of vision but I want a check-up" -> Normal booking, NO emergency
    res_neg = client.post(
        "/api/v1/patient/appointments",
        headers={"X-Session-Data": token},
        json={
            "doctor_id": "D1",
            "speciality": "General",
            "visit_type": "new",
            "date": "2026-11-04",
            "start_time": "09:00",
            "reason": "No sudden loss of vision but I want a check-up",
        },
    )
    assert res_neg.status_code == 200
    assert "emergency" not in res_neg.json()

    # 2. Red flag with valid slot: "It feels like a curtain is coming down over my right eye"
    # Login patient P07
    p7_login = client.post("/api/v1/auth/login", json={"role": "patient", "mobile": "9000000007", "name": "Anjali Desai"})
    token7 = p7_login.json()["session_token"]
    res_rf = client.post(
        "/api/v1/patient/appointments",
        headers={"X-Session-Data": token7},
        json={
            "doctor_id": "D5",
            "speciality": "Paediatric",
            "visit_type": "new",
            "date": "2026-11-07",
            "start_time": "09:00",
            "reason": "It feels like a curtain is coming down over my right eye",
        },
    )
    assert res_rf.status_code == 200
    data_rf = res_rf.json()
    assert data_rf.get("emergency") is True
    assert "emergency department" in data_rf.get("message")

    # Verify Urgent Case was saved in DB
    db = SessionLocal()
    case = db.query(UrgentCase).filter(UrgentCase.patient_id == "P07").first()
    assert case is not None
    assert "curtain_or_shadow" in case.summary
    db.close()

def test_red_flag_with_invalid_slot(client):
    # Red flag booked with Dr. Rao on Thursday morning (surgery session)
    # Expected: Emergency response AND booking refused with surgery session!
    p8_login = client.post("/api/v1/auth/login", json={"role": "patient", "mobile": "9000000008", "name": "Kabir Singh"})
    token8 = p8_login.json()["session_token"]

    res_sx = client.post(
        "/api/v1/patient/appointments",
        headers={"X-Session-Data": token8},
        json={
            "doctor_id": "D1",
            "speciality": "Cataract",
            "visit_type": "new",
            "date": "2026-11-05", # Thursday
            "start_time": "10:00", # AM surgery session
            "reason": "Severe eye pain with headache and I feel sick",
        },
    )
    assert res_sx.status_code == 400
    detail = res_sx.json()["detail"]
    assert detail["emergency"] is True
    assert detail["reason_code"] == "SURGERY_SESSION"
    assert "emergency department" in detail["message"]

    # Urgent case still recorded in DB!
    db = SessionLocal()
    case = db.query(UrgentCase).filter(UrgentCase.patient_id == "P08").first()
    assert case is not None
    assert "severe_pain_headache_haloes" in case.summary
    db.close()

def test_doctor_patient_summary(client):
    # Book P03 (Lakshmi Nair) with Dr. Iyer (D2)
    p3_login = client.post("/api/v1/auth/login", json={"role": "patient", "mobile": "9000000003", "name": "Lakshmi Nair"})
    token3 = p3_login.json()["session_token"]
    book_res = client.post(
        "/api/v1/patient/appointments",
        headers={"X-Session-Data": token3},
        json={
            "doctor_id": "D2",
            "speciality": "Glaucoma",
            "visit_type": "follow_up",
            "date": "2026-11-07",
            "start_time": "09:00",
            "reason": "Eye pressure check for glaucoma",
        },
    )
    appt_id = book_res.json()["appointment_id"]

    # 1. As a patient, calling the summary endpoint is forbidden (403)
    p_summary = client.get(
        f"/api/v1/doctor/appointments/{appt_id}/summary",
        headers={"X-Session-Data": token3},
    )
    assert p_summary.status_code == 403

    # 2. As Dr. Iyer (D2), summary succeeds
    d2_login = client.post("/api/v1/auth/login", json={"role": "doctor", "doctor_id": "D2"})
    token_d2 = d2_login.json()["session_token"]

    d_summary = client.get(
        f"/api/v1/doctor/appointments/{appt_id}/summary",
        headers={"X-Session-Data": token_d2},
    )
    assert d_summary.status_code == 200
    data = d_summary.json()
    assert data["ok"] is True
    assert "AI summary of recorded notes" in data["label"]
    assert len(data["past_notes"]) >= 3
    # P03 has Sulfa allergy recorded
    assert "sulfa" in str(data["summary"]).lower() or "sulfa" in str(data["allergies"]).lower()
    # P03 has Glaucoma care with Dr. Iyer and Cataract with Dr. Rao
    assert "glaucoma" in str(data["summary"]).lower()

def test_summary_for_patient_with_no_past_visits(client):
    # Book Aditya Bose (P20) - has no past visits in past_visits.csv
    p20_login = client.post("/api/v1/auth/login", json={"role": "patient", "mobile": "9000000020", "name": "Aditya Bose"})
    token20 = p20_login.json()["session_token"]
    book_res = client.post(
        "/api/v1/patient/appointments",
        headers={"X-Session-Data": token20},
        json={
            "doctor_id": "D1",
            "speciality": "General",
            "visit_type": "new",
            "date": "2026-11-04",
            "start_time": "11:00",
            "reason": "Routine eye test and new glasses",
        },
    )
    appt_id = book_res.json()["appointment_id"]

    # Open as Dr. Rao (D1)
    d1_login = client.post("/api/v1/auth/login", json={"role": "doctor", "doctor_id": "D1"})
    token_d1 = d1_login.json()["session_token"]

    res = client.get(
        f"/api/v1/doctor/appointments/{appt_id}/summary",
        headers={"X-Session-Data": token_d1},
    )
    assert res.status_code == 200
    data = res.json()
    assert "no previous visits" in data["summary"].lower()
    assert len(data["past_notes"]) == 0

def test_staff_urgent_case_marked_seen(client):
    # Book a red flag appointment to generate an urgent case
    p7_login = client.post("/api/v1/auth/login", json={"role": "patient", "mobile": "9000000007", "name": "Anjali Desai"})
    token7 = p7_login.json()["session_token"]
    client.post(
        "/api/v1/patient/appointments",
        headers={"X-Session-Data": token7},
        json={
            "doctor_id": "D5",
            "speciality": "Paediatric",
            "visit_type": "new",
            "date": "2026-11-07",
            "start_time": "09:00",
            "reason": "Sudden flashes of light and curtain over eye",
        },
    )

    # Staff login
    staff_login = client.post("/api/v1/auth/login", json={"role": "staff", "staff_name": "Nurse Maya"})
    staff_token = staff_login.json()["session_token"]

    # Get open urgent cases
    urgent_res = client.get("/api/v1/staff/urgent", headers={"X-Session-Data": staff_token})
    assert urgent_res.status_code == 200
    cases = urgent_res.json()
    assert len(cases) >= 1
    case_id = cases[0]["id"]
    assert cases[0]["status"] == "OPEN"

    # Mark seen
    seen_res = client.post(f"/api/v1/staff/urgent/{case_id}/seen", headers={"X-Session-Data": staff_token})
    assert seen_res.status_code == 200
    assert seen_res.json()["ok"] is True

    # Verify no longer in OPEN filter
    urgent_open = client.get("/api/v1/staff/urgent?status_filter=OPEN", headers={"X-Session-Data": staff_token})
    open_ids = [c["id"] for c in urgent_open.json()]
    assert case_id not in open_ids

def test_sunita_rao_summary_asthma_timolol(client):
    # Sunita Rao (P15) with Dr. Iyer (D2)
    p15_login = client.post("/api/v1/auth/login", json={"role": "patient", "mobile": "9000000015", "name": "Sunita Rao"})
    token15 = p15_login.json()["session_token"]
    book_res = client.post(
        "/api/v1/patient/appointments",
        headers={"X-Session-Data": token15},
        json={
            "doctor_id": "D2",
            "speciality": "Glaucoma",
            "visit_type": "follow_up",
            "date": "2026-11-07",
            "start_time": "10:00",
            "reason": "Follow up glaucoma consultation",
        },
    )
    appt_id = book_res.json()["appointment_id"]

    # Open as Dr. Iyer
    d2_login = client.post("/api/v1/auth/login", json={"role": "doctor", "doctor_id": "D2"})
    token_d2 = d2_login.json()["session_token"]

    res = client.get(
        f"/api/v1/doctor/appointments/{appt_id}/summary",
        headers={"X-Session-Data": token_d2},
    )
    assert res.status_code == 200
    data = res.json()
    summary_lower = data["summary"].lower()
    # Mentions latanoprost and asthma/timolol
    assert "latanoprost" in summary_lower or "glaucoma" in summary_lower
    assert "asthma" in summary_lower or "timolol" in summary_lower

