"""Integration tests for FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import init_db, SessionLocal
from app.db.seed import seed_db

@pytest.fixture(scope="module", autouse=True)
def init_test_db():
    init_db()
    db = SessionLocal()
    seed_db(db, load_stretch=False)
    db.close()

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["timezone"] == "Asia/Kolkata"

def test_public_endpoints(client):
    # Clinic info
    res = client.get("/api/v1/public/clinic")
    assert res.status_code == 200
    assert "NetraCare" in res.json()["name"]

    # Doctors list
    res_docs = client.get("/api/v1/public/doctors")
    assert res_docs.status_code == 200
    docs = res_docs.json()
    assert len(docs) == 5
    doc_ids = [d["id"] for d in docs]
    assert "D1" in doc_ids
    assert "D5" in doc_ids

def test_patient_auth_and_isolation(client):
    # Login Asha Verma (P01)
    login_res = client.post("/api/v1/auth/login", json={
        "role": "patient",
        "mobile": "9000000001",
        "name": "Asha Verma",
    })
    assert login_res.status_code == 200
    data = login_res.json()
    token = data["session_token"]
    assert data["user"]["id"] == "P01"

    # Query own appointments
    appts_res = client.get(
        "/api/v1/patient/appointments",
        headers={"X-Session-Data": token},
    )
    assert appts_res.status_code == 200

    # Ensure unauthenticated request is refused with 401
    unauth_res = client.get("/api/v1/patient/appointments")
    assert unauth_res.status_code == 401

def test_doctor_auth(client):
    # Login Dr. Anand Rao (D1)
    login_res = client.post("/api/v1/auth/login", json={
        "role": "doctor",
        "doctor_id": "D1",
    })
    assert login_res.status_code == 200
    token = login_res.json()["session_token"]

    sched_res = client.get(
        "/api/v1/doctor/schedule",
        headers={"X-Session-Data": token},
    )
    assert sched_res.status_code == 200
    assert sched_res.json()["doctor_id"] == "D1"

def test_red_flag_booking_blocked(client):
    # Login patient P01
    login_res = client.post("/api/v1/auth/login", json={
        "role": "patient",
        "mobile": "9000000001",
        "name": "Asha Verma",
    })
    token = login_res.json()["session_token"]

    # Try booking with a red flag symptom on a Thursday morning surgery session (D1)
    book_res = client.post(
        "/api/v1/patient/appointments",
        headers={"X-Session-Data": token},
        json={
            "doctor_id": "D1",
            "speciality": "Cataract",
            "visit_type": "new",
            "date": "2026-11-05",  # Thursday AM
            "start_time": "10:00",
            "reason": "Sudden loss of vision in right eye",
        },
    )
    assert book_res.status_code == 400
    detail = book_res.json()["detail"]
    assert detail["emergency"] is True
    assert "emergency department" in detail["message"]
