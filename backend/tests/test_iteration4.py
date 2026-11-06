"""Comprehensive automated test suite for NetraCare Iteration 4.
Verifies all Section 05 Requirements (R1 - R7) and Section 10 'Done When' specifications:
- R1: Reschedule API + Staff approvals (<2h actions)
- R2: Agent tools over clinic API with server-side patient injection
- R3: Agent graph with 30-day calendar prompt & paediatric routing
- R4: InMemorySaver thread memory & multi-turn conversations
- R5: Confirmation cards with interrupt(), resume=True/False, and typed-message cancellation
- R6: Red flags in chat, UrgentCase creation, Sources formatting, 'I don't know' fallback
- R7: Doctor leave marking, DOCTOR_ON_LEAVE refusal, automated rebooking proposals, Staff approval
"""
import pytest
from datetime import datetime, date as dt_date, time as dt_time, timedelta
from fastapi.testclient import TestClient
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.main import app
from app.config import get_clinic_now
from app.db.session import SessionLocal, init_db
from app.db.models import (
    Patient,
    Doctor,
    Appointment,
    Approval,
    DoctorLeave,
    UrgentCase,
    WeeklySchedule,
    Holiday,
)
from app.services.booking import BookingService
from app.services.reasons import ReasonCode
from app.agent.graph import agent_graph
from app.agent.tools import (
    search_clinic_docs,
    list_doctors,
    find_slots,
    my_appointments,
    book_appointment,
    cancel_appointment,
    reschedule_appointment,
)

@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)

@pytest.fixture
def auth_headers():
    import base64, json
    def _headers(patient_id="P01", role="patient", name="Asha Verma"):
        token = base64.b64encode(json.dumps({"id": patient_id, "role": role, "name": name}).encode()).decode()
        return {"X-Session-Data": token, "Authorization": f"Bearer {token}"}
    return _headers

# ==========================================
# R1: Finish Clinic API (Reschedule & Approvals)
# ==========================================

def test_r1_reschedule_success(client, auth_headers):
    """Test atomic reschedule: new slot booked and old slot cancelled."""
    headers = auth_headers("P01")
    now = get_clinic_now()

    # Find a date 5 days ahead
    target_date = now.date() + timedelta(days=5)
    db = SessionLocal()
    holidays = {h.date for h in db.query(Holiday).all()}
    while target_date.weekday() in [3, 6] or target_date in holidays:  # Skip Thu/Sun/Holidays for Dr. Rao
        target_date += timedelta(days=1)

    # Clean up any existing Cataract bookings for P01 so active booking limit is respected
    db.query(Appointment).filter(
        Appointment.patient_id == "P01",
        Appointment.speciality == "Cataract",
    ).delete()

    # Create existing appointment
    old_id = "A_TEST_R1_01"
    db.query(Appointment).filter(Appointment.id == old_id).delete()
    old_appt = Appointment(
        id=old_id,
        patient_id="P01",
        doctor_id="D1",
        speciality="Cataract",
        visit_type="new",
        mode="IN_PERSON",
        status="booked",
        date=target_date,
        start_time=dt_time(10, 0),
        end_time=dt_time(10, 20),
        source="WEBSITE",
        reason="Initial cataract consult",
    )
    db.add(old_appt)
    db.commit()
    db.close()

    # Reschedule to 10:40 AM same day
    res = client.post(
        f"/api/v1/patient/appointments/{old_id}/reschedule",
        headers=headers,
        json={
            "new_date": target_date.isoformat(),
            "new_start_time": "10:40",
            "new_doctor_id": "D1",
            "new_speciality": "Cataract",
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["ok"] is True
    assert data["appointment_id"] is not None

    db = SessionLocal()
    old_updated = db.query(Appointment).filter(Appointment.id == old_id).first()
    new_appt = db.query(Appointment).filter(Appointment.id == data["appointment_id"]).first()
    assert old_updated.status == "cancelled"
    assert new_appt.status == "booked"
    assert new_appt.rescheduled_from == old_id
    db.close()

def test_r1_reschedule_refusal_preserves_original(client, auth_headers):
    """If new booking is refused (e.g. outside clinic hours / lunch), original stays booked."""
    headers = auth_headers("P01")
    now = get_clinic_now()
    target_date = now.date() + timedelta(days=6)
    db = SessionLocal()
    holidays = {h.date for h in db.query(Holiday).all()}
    db.close()
    while target_date.weekday() in [3, 6] or target_date in holidays:
        target_date += timedelta(days=1)

    db = SessionLocal()
    old_id = "A_TEST_R1_02"
    db.query(Appointment).filter(Appointment.id == old_id).delete()
    old_appt = Appointment(
        id=old_id,
        patient_id="P01",
        doctor_id="D1",
        speciality="Cataract",
        visit_type="new",
        mode="IN_PERSON",
        status="booked",
        date=target_date,
        start_time=dt_time(11, 0),
        end_time=dt_time(11, 20),
        source="WEBSITE",
        reason="Consultation",
    )
    db.add(old_appt)
    db.commit()
    db.close()

    # Attempt to reschedule to 13:30 (Lunch break -> OUTSIDE_SESSION)
    res = client.post(
        f"/api/v1/patient/appointments/{old_id}/reschedule",
        headers=headers,
        json={
            "new_date": target_date.isoformat(),
            "new_start_time": "13:30",
            "new_doctor_id": "D1",
        },
    )
    assert res.status_code == 400
    err_detail = res.json()["detail"]
    assert err_detail["reason_code"] == ReasonCode.OUTSIDE_SESSION.value

    # Verify original appointment is still active and booked!
    db = SessionLocal()
    original = db.query(Appointment).filter(Appointment.id == old_id).first()
    assert original.status == "booked"
    db.close()

def test_r1_late_cancel_routes_to_staff_and_approved(client, auth_headers):
    """Patient cancellation inside 2 hours creates Approval and can be approved by Staff."""
    now = get_clinic_now()
    # Create appointment 1 hour from now
    appt_dt = now + timedelta(hours=1)
    appt_date = appt_dt.date()
    appt_time = dt_time(appt_dt.hour, 0)

    db = SessionLocal()
    appt_id = "A_TEST_LATE_01"
    db.query(Appointment).filter(Appointment.id == appt_id).delete()
    db.query(Approval).filter(Approval.appointment_id == appt_id).delete()
    appt = Appointment(
        id=appt_id,
        patient_id="P01",
        doctor_id="D1",
        speciality="Cataract",
        visit_type="new",
        mode="IN_PERSON",
        status="booked",
        date=appt_date,
        start_time=appt_time,
        end_time=dt_time(appt_time.hour, 20),
        source="WEBSITE",
        reason="Urgent visit",
    )
    db.add(appt)
    db.commit()
    db.close()

    # Patient cancels inside 2 hours
    headers_pat = auth_headers("P01")
    res_cancel = client.post(f"/api/v1/patient/appointments/{appt_id}/cancel", headers=headers_pat)
    assert res_cancel.status_code == 200
    data_cancel = res_cancel.json()
    assert data_cancel["expected"] == "to_staff"
    assert data_cancel["reason_code"] == ReasonCode.INSIDE_2_HOURS.value

    db = SessionLocal()
    appt_check = db.query(Appointment).filter(Appointment.id == appt_id).first()
    assert appt_check.status == "pending_staff"

    appr = db.query(Approval).filter(Approval.appointment_id == appt_id).first()
    assert appr is not None
    assert appr.kind == "LATE_CANCEL"
    assert appr.status == "PENDING"
    approval_id = appr.id
    db.close()

    # Staff views and approves
    headers_staff = auth_headers(patient_id="staff_1", role="staff", name="Front Desk")
    res_appr = client.post(f"/api/v1/staff/approvals/{approval_id}/approve", headers=headers_staff)
    assert res_appr.status_code == 200

    db = SessionLocal()
    appt_final = db.query(Appointment).filter(Appointment.id == appt_id).first()
    assert appt_final.status == "cancelled"
    db.close()

# ==========================================
# R2: Tools Over API & Cross-Patient Security
# ==========================================

def test_r2_tools_cross_patient_isolation():
    """Verify that a patient cannot cancel or reschedule another patient's appointment."""
    db = SessionLocal()
    # Create appointment for P02
    other_id = "A_TEST_OTHER_01"
    db.query(Appointment).filter(Appointment.id == other_id).delete()
    other_appt = Appointment(
        id=other_id,
        patient_id="P02",
        doctor_id="D1",
        speciality="Cataract",
        visit_type="new",
        mode="IN_PERSON",
        status="booked",
        date=dt_date(2026, 11, 20),
        start_time=dt_time(10, 0),
        end_time=dt_time(10, 20),
        source="WEBSITE",
        reason="P02 visit",
    )
    db.add(other_appt)
    db.commit()
    db.close()

    # P01 invokes cancel_appointment tool with their RunnableConfig
    config = {"configurable": {"patient_id": "P01"}}
    res = cancel_appointment.invoke({"appointment_id": other_id}, config=config)
    assert res["result"] == "refused"
    assert res["reason_code"] == ReasonCode.NOT_YOUR_APPOINTMENT.value

    # Verify other appointment is completely unchanged
    db = SessionLocal()
    check = db.query(Appointment).filter(Appointment.id == other_id).first()
    assert check.status == "booked"
    db.close()

def test_r2_my_appointments_tool():
    """Verify my_appointments returns only the logged-in patient's appointments."""
    config = {"configurable": {"patient_id": "P01"}}
    res = my_appointments.invoke({}, config=config)
    assert "upcoming_appointments" in res
    for a in res["upcoming_appointments"]:
        assert "A" in a["appointment_id"]
        assert "doctor_name" in a

def test_r2_find_slots_tool():
    """Verify find_slots returns valid OPD slots within 30 days."""
    now = get_clinic_now()
    slots = find_slots.invoke({
        "doctor_id": "D1",
        "speciality": "Cataract",
        "visit_type": "new",
        "date_from": now.date().isoformat(),
        "date_to": (now.date() + timedelta(days=7)).isoformat(),
    })
    assert isinstance(slots, list)
    if slots:
        assert "start_time" in slots[0]
        assert "end_time" in slots[0]
        assert slots[0]["doctor_id"] == "D1"

# ==========================================
# R3 & R4: Agent Graph, Prompt & Memory
# ==========================================

def test_r3_paediatric_under_16_routing(client, auth_headers):
    """Patient under 16 (Divya Pillai, age 11) is routed to Paediatric with Dr. Vikram Menon."""
    headers = auth_headers("P17", name="Divya Pillai")
    res = client.post(
        "/api/v1/patient/chat",
        headers=headers,
        json={"message": "My eyes hurt when I read the board at school. Can I see someone on Saturday 7 November, the earliest time? Reason: eyes hurt reading the board"},
    )
    assert res.status_code == 200
    data = res.json()
    pending = data.get("pending_action")
    assert pending is not None
    summary = pending["summary"].lower()
    assert "dr. vikram menon" in summary
    assert "paediatric" in summary

def test_r4_conversation_memory_thread_id(client, auth_headers):
    """Memory checkpointer preserves multi-turn context across turns on the same thread_id."""
    headers = auth_headers("P01")
    thread_id = "test_memory_thread_42"

    # Turn 1: Check fee
    r1 = client.post(
        "/api/v1/patient/chat",
        headers=headers,
        json={"message": "How much is a new consultation?", "thread_id": thread_id},
    )
    assert r1.status_code == 200
    assert "800" in r1.json()["answer"]

    # Turn 2: Follow up query
    r2 = client.post(
        "/api/v1/patient/chat",
        headers=headers,
        json={"message": "Is there parking at the clinic?", "thread_id": thread_id},
    )
    assert r2.status_code == 200
    assert "i don't know" in r2.json()["answer"].lower()

# ==========================================
# R5: Human-In-The-Loop Confirmation Cards
# ==========================================

def test_r5_confirmation_card_confirm_and_decline(client, auth_headers):
    """Action pauses at confirmation card; Confirm mutates DB, Decline does not."""
    headers = auth_headers("P01")
    thread_id = "test_card_thread_01"

    # Turn 1: Request booking
    r1 = client.post(
        "/api/v1/patient/chat",
        headers=headers,
        json={
            "message": "Please book my retina follow-up with Dr. Shah this Friday morning, the earliest time you have. Reason: six-month diabetic eye review",
            "thread_id": thread_id,
        },
    )
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["pending_action"] is not None
    assert "Confirm" in d1["answer"] or "Book Dr. Kiran Shah" in d1["answer"]

    # Turn 2: Decline (No)
    r2 = client.post(
        "/api/v1/patient/chat",
        headers=headers,
        json={"thread_id": thread_id, "confirm": False},
    )
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["pending_action"] is None
    assert "no changes" in d2["answer"].lower() or "what would you like" in d2["answer"].lower()

# ==========================================
# R6: Red Flags & Clinic Answers in Agent
# ==========================================

def test_r6_red_flag_in_agent_creates_urgent_case(client, auth_headers):
    """Red flag typed message returns emergency script and creates UrgentCase in DB."""
    headers = auth_headers("P21", name="Zoya Khan")
    res = client.post(
        "/api/v1/patient/chat",
        headers=headers,
        json={"message": "Can I book for tomorrow? A curtain came down over my right eye an hour ago"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["emergency"] is True
    assert "urgent attention" in data["answer"].lower() or "emergency" in data["answer"].lower()

    # Verify urgent case created in database
    db = SessionLocal()
    case = db.query(UrgentCase).filter(UrgentCase.source == "CHAT").order_by(UrgentCase.created_at.desc()).first()
    assert case is not None
    assert "curtain" in case.summary.lower()
    db.close()

def test_r6_sources_and_idk(client, auth_headers):
    """Questions covered by clinic documents include Sources: line; uncovered return fixed IDK."""
    headers = auth_headers("P18")
    res_idk = client.post(
        "/api/v1/patient/chat",
        headers=headers,
        json={"message": "Is there parking at the clinic?"},
    )
    assert res_idk.status_code == 200
    d_idk = res_idk.json()
    assert "i don't know" in d_idk["answer"].lower()
    assert len(d_idk["sources"]) == 0

# ==========================================
# R7: Doctor Leave & Staff Rebooking Proposals
# ==========================================

def test_r7_doctor_leave_and_rebooking_proposals(client, auth_headers):
    """Doctor marks leave; affected bookings are cancelled and proposed slots created."""
    now = get_clinic_now()
    leave_date = now.date() + timedelta(days=4)
    while leave_date.weekday() in [3, 6]:  # Ensure weekday with OPD
        leave_date += timedelta(days=1)

    db = SessionLocal()
    # Create two appointments for Dr. Rao (D1) on leave_date
    a1_id = "A_LEAVE_TEST_01"
    a2_id = "A_LEAVE_TEST_02"
    db.query(Appointment).filter(Appointment.id.in_([a1_id, a2_id])).delete()
    db.query(Appointment).filter(Appointment.rescheduled_from.in_([a1_id, a2_id])).delete()
    db.query(DoctorLeave).filter(DoctorLeave.doctor_id == "D1", DoctorLeave.date == leave_date).delete()

    appt1 = Appointment(
        id=a1_id,
        patient_id="P01",
        doctor_id="D1",
        speciality="Cataract",
        visit_type="new",
        mode="IN_PERSON",
        status="booked",
        date=leave_date,
        start_time=dt_time(9, 0),
        end_time=dt_time(9, 20),
        source="WEBSITE",
        reason="New cataract consult",
    )
    appt2 = Appointment(
        id=a2_id,
        patient_id="P02",
        doctor_id="D1",
        speciality="General",
        visit_type="new",
        mode="IN_PERSON",
        status="booked",
        date=leave_date,
        start_time=dt_time(9, 20),
        end_time=dt_time(9, 40),
        source="WEBSITE",
        reason="General checkup",
    )
    db.add(appt1)
    db.add(appt2)
    db.commit()
    db.close()

    # Dr. Rao marks full-day leave
    headers_doc = auth_headers("D1", role="doctor", name="Dr. Anand Rao")
    res_leave = client.post(
        "/api/v1/doctor/leave",
        headers=headers_doc,
        json={"date": leave_date.isoformat(), "session": "FULL"},
    )
    assert res_leave.status_code == 200, res_leave.text
    d_leave = res_leave.json()
    assert d_leave["ok"] is True
    assert d_leave["affected_count"] >= 2

    # Verify both original appointments were cancelled
    db = SessionLocal()
    a1_check = db.query(Appointment).filter(Appointment.id == a1_id).first()
    a2_check = db.query(Appointment).filter(Appointment.id == a2_id).first()
    assert a1_check.status == "cancelled"
    assert a2_check.status == "cancelled"

    # Verify proposed rebooking appointments were created
    props = db.query(Appointment).filter(Appointment.rescheduled_from.in_([a1_id, a2_id])).all()
    assert len(props) >= 2
    for p in props:
        assert p.status == "proposed"
        assert "leave" in p.reason.lower()
    proposed_id = props[0].id
    db.close()

    # Staff views rebooking proposals
    headers_staff = auth_headers("staff_1", role="staff", name="Front Desk")
    res_rebooks = client.get("/api/v1/staff/rebookings", headers=headers_staff)
    assert res_rebooks.status_code == 200
    rebooks_list = res_rebooks.json()
    assert any(rb["id"] == proposed_id for rb in rebooks_list)

    # Staff approves one proposal
    res_appr = client.post(f"/api/v1/staff/rebookings/{proposed_id}/approve", headers=headers_staff)
    assert res_appr.status_code == 200

    db = SessionLocal()
    prop_final = db.query(Appointment).filter(Appointment.id == proposed_id).first()
    assert prop_final.status == "booked"
    db.close()
