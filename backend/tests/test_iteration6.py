"""Iteration 6 Comprehensive Verification Tests.
Verifies:
1. NetraCare MCP Server (M01 to M12 in mcp_scenarios.csv)
2. Partner Lab Client & Offline Fallback (LQ01 to LQ09 in lab_questions.csv)
3. Agent Skills Loader, Triggers, & Directory Traversal Security (T01 to T16 in skill_triggers.csv)
"""
import os
import csv
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.db.models import Patient, Appointment, UrgentCase, Doctor
from app.safety.red_flags import EMERGENCY_RESPONSE_TEXT
from mcp_server import find_slots as mcp_find_slots, book_appointment as mcp_book_appointment
from app.agent.skills import load_skill, read_skill_file, AVAILABLE_SKILLS
from app.agent.lab_tool import get_lab_test_info

client = TestClient(app)

def get_patient_token(patient_id: str = "P01") -> str:
    db = SessionLocal()
    try:
        p = db.query(Patient).filter(Patient.id == patient_id).first()
        res = client.post("/api/v1/auth/login", json={"mobile": p.mobile, "name": p.name, "role": "patient"})
        return res.json()["session_token"]
    finally:
        db.close()

def test_mcp_scenarios_m01_to_m12():
    """Verify all 12 rows of mcp_scenarios.csv against NetraCare MCP server functions."""
    db = SessionLocal()
    try:
        db.query(Appointment).filter(Appointment.source == "MCP").delete()
        db.query(Patient).filter(Patient.mobile == "9000000099").delete()
        db.commit()
    finally:
        db.close()

    # M01: find_slots Retina next Monday
    r1 = mcp_find_slots("Retina", "next Monday")
    assert r1.get("count", 0) > 0
    assert any("Shah" in s["doctor_name"] for s in r1["slots"])

    # M02: find_slots Glaucoma next Thursday (Dr. Iyer OFF on Thursday)
    r2 = mcp_find_slots("Glaucoma", "next Thursday")
    assert len(r2["slots"]) == 0
    assert "not at the clinic on Thursdays" in r2["message"]

    # M03: book Ravi Kumar, Cataract, D1, next Monday 10:00
    r3 = mcp_book_appointment(
        patient_name="Ravi Kumar",
        mobile="9000000010",
        speciality="Cataract",
        doctor_name="D1",
        date="next Monday",
        start_time="10:00",
        reason="Distance vision getting misty over the last year",
    )
    assert r3.get("status") == "booked"
    assert r3.get("source") == "MCP"

    # M04: double booking slot from M03
    r4 = mcp_book_appointment(
        patient_name="Neha Joshi",
        mobile="9000000011",
        speciality="Cataract",
        doctor_name="D1",
        date="next Monday",
        start_time="10:00",
        reason="Glare at night",
    )
    assert r4.get("status") == "refused"
    assert r4.get("code") == "DOUBLE_BOOKED"

    # M05: Dr. Iyer on Thursday
    r5 = mcp_book_appointment(
        patient_name="Neha Joshi",
        mobile="9000000011",
        speciality="Glaucoma",
        doctor_name="D2",
        date="next Thursday",
        start_time="10:00",
        reason="Pressure check",
    )
    assert r5.get("status") == "refused"
    assert r5.get("code") == "DOCTOR_OFF"

    # M06: Dr. Rao on Thursday AM is Surgery
    r6 = mcp_book_appointment(
        patient_name="Neha Joshi",
        mobile="9000000011",
        speciality="Cataract",
        doctor_name="D1",
        date="next Thursday",
        start_time="10:00",
        reason="Glare at night",
    )
    assert r6.get("status") == "refused"
    assert r6.get("code") == "SURGERY_SESSION"

    # M07: Dr. Khan (Cornea) does not cover Glaucoma
    r7 = mcp_book_appointment(
        patient_name="Neha Joshi",
        mobile="9000000011",
        speciality="Glaucoma",
        doctor_name="D4",
        date="next Tuesday",
        start_time="15:00",
        reason="Pressure check",
    )
    assert r7.get("status") == "refused"
    assert r7.get("code") == "SPECIALITY_MISMATCH"

    # M08: beyond 30 days
    r8 = mcp_book_appointment(
        patient_name="Neha Joshi",
        mobile="9000000011",
        speciality="General",
        doctor_name="D1",
        date="a Monday more than 30 days from today",
        start_time="10:00",
        reason="Eye test",
    )
    assert r8.get("status") == "refused"
    assert r8.get("code") == "BEYOND_30_DAYS"

    # M09: Ravi Kumar already has Cataract booking from M03
    r9 = mcp_book_appointment(
        patient_name="Ravi Kumar",
        mobile="9000000010",
        speciality="Cataract",
        doctor_name="D2",
        date="next Friday",
        start_time="10:00",
        reason="Second opinion",
    )
    assert r9.get("status") == "refused"
    assert r9.get("code") == "ACTIVE_BOOKING_EXISTS"

    # M10: Mobile 9000000010 belongs to Ravi Kumar, not Rahul Kumar
    r10 = mcp_book_appointment(
        patient_name="Rahul Kumar",
        mobile="9000000010",
        speciality="General",
        doctor_name="D3",
        date="next Monday",
        start_time="11:00",
        reason="Eye test",
    )
    assert r10.get("status") == "refused"
    assert r10.get("code") == "PATIENT_DETAILS_MISMATCH"

    # M11: New mobile 9000000099 creates new patient
    r11 = mcp_book_appointment(
        patient_name="Sameer Khan",
        mobile="9000000099",
        speciality="General",
        doctor_name="D3",
        date="next Monday",
        start_time="11:00",
        reason="New glasses needed",
    )
    assert r11.get("status") == "booked"
    assert r11.get("patient_name") == "Sameer Khan"

    # M12: Red flag ocular emergency
    r12 = mcp_book_appointment(
        patient_name="Neha Joshi",
        mobile="9000000011",
        speciality="Retina",
        doctor_name="D3",
        date="next Monday",
        start_time="12:00",
        reason="Since an hour a dark curtain is coming down over my right eye",
    )
    assert r12.get("status") == "red_flag"
    assert r12.get("code") == "RED_FLAG"
    assert r12.get("message") == EMERGENCY_RESPONSE_TEXT

    # Check urgent case stored with source="MCP"
    db = SessionLocal()
    try:
        urgent = db.query(UrgentCase).filter(UrgentCase.source == "MCP").order_by(UrgentCase.id.desc()).first()
        assert urgent is not None
        assert "curtain" in urgent.summary.lower()
    finally:
        db.close()

def test_lab_questions_lq01_to_lq09():
    """Verify all 9 questions from lab_questions.csv in the patient chat."""
    token = get_patient_token("P01")

    # LQ01: HbA1c fasting
    res1 = client.post("/api/v1/patient/chat", headers={"X-Session-Data": token}, json={"message": "Do I need to fast for an HbA1c test?"})
    d1 = res1.json()
    assert "no fasting" in d1["answer"].lower()
    assert "Source: CityCare Lab (partner)" in d1["answer"]

    # LQ02: Fasting sugar duration
    res2 = client.post("/api/v1/patient/chat", headers={"X-Session-Data": token}, json={"message": "My doctor asked for a fasting sugar test. How long should I not eat?"})
    d2 = res2.json()
    assert "8 to 10 hours" in d2["answer"]
    assert "Source: CityCare Lab (partner)" in d2["answer"]

    # LQ03: Pre-surgery tests
    res3 = client.post("/api/v1/patient/chat", headers={"X-Session-Data": token}, json={"message": "What blood tests are done before eye surgery at CityCare and do I need to fast?"})
    d3 = res3.json()
    assert "pre-surgery" in d3["answer"].lower() or "blood sugar" in d3["answer"].lower()
    assert "Source: CityCare Lab (partner)" in d3["answer"]

    # LQ04: Sunday timings
    res4 = client.post("/api/v1/patient/chat", headers={"X-Session-Data": token}, json={"message": "Is the lab open on Sunday?"})
    d4 = res4.json()
    assert "sunday" in d4["answer"].lower()
    assert "Source: CityCare Lab (partner)" in d4["answer"]

    # LQ05: Home collection
    res5 = client.post("/api/v1/patient/chat", headers={"X-Session-Data": token}, json={"message": "Can someone come home to take my blood sample?"})
    d5 = res5.json()
    assert "100" in d5["answer"] or "home" in d5["answer"].lower()
    assert "Source: CityCare Lab (partner)" in d5["answer"]

    # LQ06: Unknown test (thyroid)
    res6 = client.post("/api/v1/patient/chat", headers={"X-Session-Data": token}, json={"message": "Does CityCare do a thyroid test?"})
    d6 = res6.json()
    assert "doesn't include" in d6["answer"].lower() or "does not include" in d6["answer"].lower()

    # LQ07: Medical safety (no result reading)
    res7 = client.post("/api/v1/patient/chat", headers={"X-Session-Data": token}, json={"message": "My HbA1c came back as 8.2. Is that bad?"})
    d7 = res7.json()
    assert "cannot interpret" in d7["answer"].lower() or "discuss" in d7["answer"].lower()

    # LQ08: Medical safety (no prescribing tests)
    res8 = client.post("/api/v1/patient/chat", headers={"X-Session-Data": token}, json={"message": "Which blood tests do I need for my eyes?"})
    d8 = res8.json()
    assert "cannot advise" in d8["answer"].lower() or "doctor" in d8["answer"].lower()

    # LQ09: No lab bookings
    res9 = client.post("/api/v1/patient/chat", headers={"X-Session-Data": token}, json={"message": "Book me a CBC at CityCare tomorrow morning"})
    d9 = res9.json()
    assert "cannot book" in d9["answer"].lower() or "walk-in" in d9["answer"].lower()

def test_skill_directory_traversal_guard():
    """Verify read_skill_file rejects directory traversal attempts."""
    res1 = read_skill_file.invoke({"name": "cataract-surgery-care", "file": "../../.env"})
    assert "Access denied" in res1

    res2 = read_skill_file.invoke({"name": "cataract-surgery-care", "file": "../lasik-suitability-intake/questions.md"})
    assert "Access denied" in res2

    # Legitimate read works
    res3 = read_skill_file.invoke({"name": "cataract-surgery-care", "file": "post-op-guide.md"})
    assert "After cataract surgery" in res3

def test_skill_triggers_t01_to_t16():
    """Verify at least 14 of 16 rows from skill_triggers.csv trigger the expected skill or none."""
    db = SessionLocal()
    try:
        pat_map = {p.id: p for p in db.query(Patient).all()}
    finally:
        db.close()

    csv_path = Path("data/skill_triggers.csv")
    if not csv_path.exists():
        csv_path = Path("Iteration 6/netracare-data-pack-06/skill_triggers.csv")

    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    passed = 0
    all_skills = ["cataract-surgery-care", "lasik-suitability-intake", "prepare-for-visit", "children-visit"]

    for r in rows:
        p = pat_map.get(r["patient_id"])
        tok = get_patient_token(p.id)

        res = client.post(
            "/api/v1/patient/chat",
            headers={"X-Session-Data": tok},
            json={"message": r["message"]},
        )
        data = res.json()
        ans = data.get("answer", "")

        detected = "none"
        for sk in all_skills:
            if f"Skill: {sk}" in ans or f"skill: {sk}" in ans.lower():
                detected = sk
                break

        expected = r["expected_skill"]
        also = r["also_acceptable"]

        is_correct = (detected == expected) or (also and detected == also)
        if is_correct:
            passed += 1

    # Requirement R4 check: at least 14 of 16 rows must pass
    assert passed >= 14, f"Only {passed}/16 skill triggers passed. Expected >= 14."
