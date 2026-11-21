"""Automated test suite for NetraCare Iteration 7:
- Feature A: Unified Dual-Mode Chatbot & Session Isolation
- Feature B: Human-in-the-Loop (HITL) Doctor Leave / Surgery Re-routing
- Feature C: Prescription & Referral OCR Intake with Zero-Diagnosis Guardrails
- Feature D: Live Dilation Drop Timer & Waiting Room Stage Lifecycle
"""
import pytest
import io
import json
import base64
from datetime import datetime, date, time
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import init_db, SessionLocal
from app.db.models import Appointment, Patient, Doctor, DoctorLeave, UrgentCase
from app.services.booking import BookingService
from app.services.ocr_service import process_ocr_document, extract_prescription_fields
from app.config import get_clinic_now

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()
    db = SessionLocal()
    # Add a doctor leave fixture for D1 on 2026-11-06 if not present
    existing_leave = db.query(DoctorLeave).filter(DoctorLeave.doctor_id == "D1", DoctorLeave.date == date(2026, 11, 6)).first()
    if not existing_leave:
        db.add(DoctorLeave(doctor_id="D1", date=date(2026, 11, 6), reason="Annual leave"))
        db.commit()
    db.close()

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def get_auth_header(role: str, user_id: str, name: str):
    data = {"role": role, "id": user_id, "name": name}
    token = base64.b64encode(json.dumps(data).encode("utf-8")).decode("utf-8")
    return {"X-Session-Data": token}


# --- 1. HITL Doctor Leave (DOCTOR_OFF) ---
def test_hitl_doctor_leave_options():
    db = SessionLocal()
    try:
        # Requesting Dr. Anand Rao (D1) on Friday Nov 6 when he is on leave
        alts = BookingService.find_alternatives(
            db=db,
            speciality="Cataract",
            requested_doctor_id="D1",
            requested_date=date(2026, 11, 6),
            patient_age=45,
        )
        assert alts["is_paediatric"] is False
        assert len(alts["same_doctor_next_slots"]) > 0
        assert len(alts["same_speciality_alternatives"]) > 0
        
        # Verify doctor in same_speciality_alternatives covers Cataract (e.g. Dr. Meera Iyer D2)
        alt_doc_ids = {s["doctor_id"] for s in alts["same_speciality_alternatives"]}
        assert "D2" in alt_doc_ids
    finally:
        db.close()


# --- 2. HITL Surgery Session (SURGERY_SESSION) ---
def test_hitl_surgery_session_options():
    db = SessionLocal()
    try:
        # Thursday morning (Nov 5) is Dr. Anand Rao's surgery session
        alts = BookingService.find_alternatives(
            db=db,
            speciality="Cataract",
            requested_doctor_id="D1",
            requested_date=date(2026, 11, 5),
            patient_age=50,
        )
        assert len(alts["same_doctor_next_slots"]) > 0
        # Earliest slot for same doctor should not be during surgery session
        for slot in alts["same_doctor_next_slots"]:
            assert not (slot["date"] == "2026-11-05" and slot["start_time"] < "13:00")
    finally:
        db.close()


# --- 3. HITL Paediatric Guard (age < 16) ---
def test_hitl_paediatric_guard_age_under_16():
    db = SessionLocal()
    try:
        # For a 10-year-old child, if Dr. Vikram Menon is unavailable on a particular date,
        # alternatives MUST NOT suggest adult doctors
        alts = BookingService.find_alternatives(
            db=db,
            speciality="Paediatric",
            requested_doctor_id="D5",
            requested_date=date(2026, 11, 5),
            patient_age=10,
        )
        assert alts["is_paediatric"] is True
        # Strictly empty alternative doctors: child cannot switch to adult ophthalmologists
        assert len(alts["same_speciality_alternatives"]) == 0
        # Only Dr. Vikram Menon's next open slots are offered
        assert len(alts["same_doctor_next_slots"]) > 0
        for slot in alts["same_doctor_next_slots"]:
            assert slot["doctor_id"] == "D5"
    finally:
        db.close()


# --- 4. OCR Extraction & Safe Attachment to intake_notes ---
def test_ocr_extraction_and_attachment(client):
    headers_p01 = get_auth_header("patient", "P01", "Asha Verma")
    prescription_sample = (
        "DR. CLINICAL EYE CLINIC\n"
        "Patient: Asha Verma\n"
        "OD: SPH -2.50 CYL -0.75 AXIS 180\n"
        "OS: SPH -2.25 CYL -0.50 AXIS 175\n"
        "PD: 63 mm\n"
        "Advice: Wear glasses for distance."
    )

    # 1. Test parser directly
    ocr_res = process_ocr_document(prescription_sample.encode("utf-8"), filename="rx.txt")
    assert ocr_res["ok"] is True
    assert ocr_res["red_flag"] is False
    assert ocr_res["fields"]["od"]["sph"] == "-2.50"
    assert ocr_res["fields"]["os"]["sph"] == "-2.25"
    assert "Transcribed text only" in ocr_res["formatted_summary"]

    # 2. Test upload endpoint
    file_payload = ("prescription.txt", io.BytesIO(prescription_sample.encode("utf-8")), "text/plain")
    res = client.post(
        "/api/v1/intake/ocr",
        headers=headers_p01,
        files={"file": file_payload},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert "[OCR Prescription/Referral Attached" in data["formatted_summary"]

    # 3. Test attachment to appointment
    db = SessionLocal()
    try:
        appt = db.query(Appointment).filter(Appointment.patient_id == "P01").first()
        assert appt is not None
        appt_id = appt.id
        initial_notes = appt.intake_notes or ""
    finally:
        db.close()

    attach_res = client.post(
        f"/api/v1/patient/appointments/{appt_id}/attach-ocr",
        headers=headers_p01,
        json={"ocr_text": data["formatted_summary"]},
    )
    assert attach_res.status_code == 200
    assert "[OCR Prescription/Referral Attached" in attach_res.json()["intake_notes"]
    if initial_notes:
        assert initial_notes in attach_res.json()["intake_notes"]


# --- 5. OCR File Validation & Cross-Patient Isolation ---
def test_ocr_file_validation_and_cross_patient_isolation(client):
    headers_p01 = get_auth_header("patient", "P01", "Asha Verma")
    headers_p02 = get_auth_header("patient", "P02", "Rohan Gupta")

    # A. Unsupported file type (.exe)
    invalid_file = ("malicious.exe", io.BytesIO(b"binary content"), "application/x-msdownload")
    res_inv = client.post("/api/v1/intake/ocr", headers=headers_p01, files={"file": invalid_file})
    assert res_inv.status_code == 400

    # B. Cross-Patient Isolation: Patient P02 cannot attach notes to Patient P01's appointment
    db = SessionLocal()
    try:
        appt_p01 = db.query(Appointment).filter(Appointment.patient_id == "P01").first()
        target_id = appt_p01.id
    finally:
        db.close()

    res_cross = client.post(
        f"/api/v1/patient/appointments/{target_id}/attach-ocr",
        headers=headers_p02,
        json={"ocr_text": "Attempted cross-patient note injection"},
    )
    assert res_cross.status_code == 403


# --- 6. OCR Red-Flag Emergency Triage ---
def test_ocr_red_flag_emergency_triage(client):
    headers_p01 = get_auth_header("patient", "P01", "Asha Verma")
    emergency_referral = (
        "URGENT HOSPITAL REFERRAL\n"
        "Patient presenting with sudden vision loss in the right eye since this morning.\n"
        "Dark curtain falling across sight. Immediate retinal evaluation required."
    )
    file_payload = ("emergency_referral.txt", io.BytesIO(emergency_referral.encode("utf-8")), "text/plain")
    res = client.post("/api/v1/intake/ocr", headers=headers_p01, files={"file": file_payload})
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is False
    assert data["red_flag"] is True
    assert "emergency" in data["emergency_response"].lower() or "hospital" in data["emergency_response"].lower()

    # Verify UrgentCase record created in DB
    db = SessionLocal()
    try:
        urgent = db.query(UrgentCase).filter(UrgentCase.source == "OCR_INTAKE").order_by(UrgentCase.id.desc()).first()
        assert urgent is not None
        assert "sudden vision loss" in urgent.summary.lower()
    finally:
        db.close()


# --- 7. Live Dilation Timer & Stage Lifecycle ---
def test_live_dilation_timer_lifecycle(client):
    headers_staff = get_auth_header("staff", "staff_front_desk", "Front Desk")
    headers_patient = get_auth_header("patient", "P01", "Asha Verma")

    db = SessionLocal()
    try:
        # Find an active booked appointment
        appt = db.query(Appointment).filter(Appointment.status == "booked").first()
        assert appt is not None
        appt_id = appt.id
    finally:
        db.close()

    # 1. Non-staff role cannot update stage (403 Forbidden)
    res_forbidden = client.patch(
        f"/api/v1/staff/appointments/{appt_id}/stage",
        headers=headers_patient,
        json={"visit_stage": "CHECKED_IN"},
    )
    assert res_forbidden.status_code == 403

    # 2. Staff: SCHEDULED -> CHECKED_IN
    res_checkin = client.patch(
        f"/api/v1/staff/appointments/{appt_id}/stage",
        headers=headers_staff,
        json={"visit_stage": "CHECKED_IN"},
    )
    assert res_checkin.status_code == 200
    assert res_checkin.json()["visit_stage"] == "CHECKED_IN"

    # 3. Staff: CHECKED_IN -> DILATING (starts dilation timer)
    res_dilate = client.patch(
        f"/api/v1/staff/appointments/{appt_id}/stage",
        headers=headers_staff,
        json={"visit_stage": "DILATING", "dilation_duration_mins": 35},
    )
    assert res_dilate.status_code == 200
    d_data = res_dilate.json()
    assert d_data["visit_stage"] == "DILATING"
    assert d_data["dilation_started_at"] is not None
    assert d_data["dilation_duration_mins"] == 35

    # 4. Staff: DILATING -> READY_FOR_DOCTOR
    res_ready = client.patch(
        f"/api/v1/staff/appointments/{appt_id}/stage",
        headers=headers_staff,
        json={"visit_stage": "READY_FOR_DOCTOR"},
    )
    assert res_ready.status_code == 200
    assert res_ready.json()["visit_stage"] == "READY_FOR_DOCTOR"

    # 5. Clean up: reset stage back to SCHEDULED
    client.patch(
        f"/api/v1/staff/appointments/{appt_id}/stage",
        headers=headers_staff,
        json={"visit_stage": "SCHEDULED"},
    )


# --- 8. Patient and Doctor Dilation Views ---
def test_patient_and_doctor_dilation_views(client):
    headers_staff = get_auth_header("staff", "staff_front_desk", "Front Desk")

    db = SessionLocal()
    try:
        appt = db.query(Appointment).filter(Appointment.patient_id == "P01", Appointment.status == "booked").first()
        if not appt:
            appt = db.query(Appointment).filter(Appointment.status == "booked").first()
        appt_id = appt.id
        appt_date = appt.date.isoformat()
        doctor_id = appt.doctor_id
        patient_id = appt.patient_id
    finally:
        db.close()

    headers_doctor = get_auth_header("doctor", doctor_id, "Doctor")
    headers_patient = get_auth_header("patient", patient_id, "Patient")

    # Set to DILATING
    patch_res = client.patch(
        f"/api/v1/staff/appointments/{appt_id}/stage",
        headers=headers_staff,
        json={"visit_stage": "DILATING", "dilation_duration_mins": 35},
    )
    assert patch_res.status_code == 200

    # Patient View: appointments response includes stage & timestamps
    p_res = client.get("/api/v1/patient/appointments", headers=headers_patient)
    assert p_res.status_code == 200
    my_appts = p_res.json()
    matching = next((a for a in my_appts if a["id"] == appt_id), None)
    assert matching is not None
    assert matching["visit_stage"] == "DILATING"
    assert matching["dilation_started_at"] is not None
    assert matching["server_now"] is not None

    # Doctor View: doctor schedule includes stage & timestamps
    d_res = client.get(f"/api/v1/doctor/schedule?date={appt_date}", headers=headers_doctor)
    assert d_res.status_code == 200
    doc_appts = d_res.json()["appointments"]
    matching_doc = next((a for a in doc_appts if a["id"] == appt_id), None)
    if matching_doc:
        assert matching_doc["visit_stage"] == "DILATING"
        assert matching_doc["server_now"] is not None

    # Clean up
    client.patch(
        f"/api/v1/staff/appointments/{appt_id}/stage",
        headers=headers_staff,
        json={"visit_stage": "SCHEDULED"},
    )
