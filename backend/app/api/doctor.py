"""Doctor endpoints for schedule view, appointment management, and completing visits.
Enforces R2 from Handout 1: completing visits enables follow-up booking.
"""
from datetime import datetime, date as dt_date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_clinic_now
from app.db.session import get_db
from app.db.models import Appointment, Patient, Doctor, WeeklySchedule
from app.api.deps import get_current_doctor, CurrentUser
from app.services.booking import BookingService
from app.assistant.llm import generate_doctor_summary

router = APIRouter(prefix="/doctor", tags=["Doctor"])

class CompleteVisitRequest(BaseModel):
    doctor_note: str

class DoctorAppointmentItem(BaseModel):
    id: str
    patient_id: str
    patient_name: str
    speciality: str
    visit_type: str
    mode: str
    status: str
    date: str
    start_time: str
    end_time: str
    reason: Optional[str]
    doctor_note: Optional[str]

@router.get("/schedule")
def get_doctor_schedule(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (defaults to clinic today)"),
    doctor: CurrentUser = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    now = get_clinic_now()
    if date:
        try:
            target_date = datetime.strptime(date.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    else:
        target_date = now.date()

    day_abbr = BookingService.get_day_abbr(target_date)

    # Weekly schedule status for this day
    schedules = (
        db.query(WeeklySchedule)
        .filter(WeeklySchedule.doctor_id == doctor.id, WeeklySchedule.day == day_abbr)
        .all()
    )
    sched_summary = {s.session: s.status for s in schedules}

    # Appointments booked for this day
    appts = (
        db.query(Appointment)
        .filter(Appointment.doctor_id == doctor.id, Appointment.date == target_date)
        .order_by(Appointment.start_time.asc())
        .all()
    )

    pat_map = {p.id: p.name for p in db.query(Patient).all()}

    appointment_list = [
        DoctorAppointmentItem(
            id=a.id,
            patient_id=a.patient_id,
            patient_name=pat_map.get(a.patient_id, "Unknown Patient"),
            speciality=a.speciality,
            visit_type=a.visit_type,
            mode=a.mode,
            status=a.status,
            date=a.date.isoformat(),
            start_time=a.start_time.strftime("%H:%M"),
            end_time=a.end_time.strftime("%H:%M"),
            reason=a.reason,
            doctor_note=a.doctor_note,
        )
        for a in appts
    ]

    return {
        "ok": True,
        "date": target_date.isoformat(),
        "doctor_id": doctor.id,
        "doctor_name": doctor.name,
        "sessions": sched_summary,
        "appointments": appointment_list,
    }

@router.get("/appointments/{appointment_id}")
def get_appointment_detail(
    appointment_id: str,
    doctor: CurrentUser = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id.strip()).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found.")

    if appt.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Access denied. You can only view your own appointments.")

    pat = db.query(Patient).filter(Patient.id == appt.patient_id).first()

    return {
        "ok": True,
        "appointment": {
            "id": appt.id,
            "patient_id": appt.patient_id,
            "patient_name": pat.name if pat else "Unknown",
            "patient_yob": pat.year_of_birth if pat else None,
            "patient_allergies": pat.allergies if pat else None,
            "patient_chronic": pat.chronic_conditions if pat else None,
            "speciality": appt.speciality,
            "visit_type": appt.visit_type,
            "mode": appt.mode,
            "status": appt.status,
            "date": appt.date.isoformat(),
            "start_time": appt.start_time.strftime("%H:%M"),
            "end_time": appt.end_time.strftime("%H:%M"),
            "reason": appt.reason,
            "doctor_note": appt.doctor_note,
        },
    }

@router.get("/appointments/{appointment_id}/summary")
def get_patient_summary(
    appointment_id: str,
    doctor: CurrentUser = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """Generate a clinical summary of the patient's record for the consulting doctor."""
    appt = db.query(Appointment).filter(Appointment.id == appointment_id.strip()).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found.")

    if appt.doctor_id != doctor.id:
        raise HTTPException(
            status_code=403,
            detail="Access denied. You can only access summaries for your assigned appointments.",
        )

    pat = db.query(Patient).filter(Patient.id == appt.patient_id).first()
    if not pat:
        raise HTTPException(status_code=404, detail="Patient profile not found.")

    # Calculate age from year of birth (relative to 2026)
    age = (2026 - pat.year_of_birth) if pat.year_of_birth else None

    # Fetch past completed visits across all doctors, newest first
    past_appts = (
        db.query(Appointment)
        .filter(Appointment.patient_id == pat.id, Appointment.status == "completed")
        .order_by(Appointment.date.desc(), Appointment.start_time.desc())
        .all()
    )

    doc_map = {d.id: d.name for d in db.query(Doctor).all()}

    past_visits_data = [
        {
            "id": a.id,
            "date": a.date.isoformat(),
            "doctor_id": a.doctor_id,
            "doctor_name": doc_map.get(a.doctor_id, a.doctor_id),
            "speciality": a.speciality,
            "doctor_note": a.doctor_note or "No notes recorded",
            "reason": a.reason,
        }
        for a in past_appts
    ]

    summary_text = generate_doctor_summary(
        patient_name=pat.name,
        age=age,
        general_health=pat.chronic_conditions,
        allergies=pat.allergies,
        todays_reason=appt.reason or "Routine consultation",
        past_visits=past_visits_data,
    )

    return {
        "ok": True,
        "appointment_id": appt.id,
        "patient_id": pat.id,
        "patient_name": pat.name,
        "age": age,
        "general_health": pat.chronic_conditions,
        "allergies": pat.allergies,
        "todays_reason": appt.reason,
        "summary": summary_text,
        "label": "AI summary of recorded notes. Check the notes below.",
        "past_notes": past_visits_data,
    }

@router.post("/appointments/{appointment_id}/complete")
def complete_visit(
    appointment_id: str,
    req: CompleteVisitRequest,
    doctor: CurrentUser = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """Mark an appointment as completed with clinical notes. Fulfills Handout 1 & 2 R2."""
    note_clean = req.doctor_note.strip() if req.doctor_note else ""
    if not note_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A doctor's clinical note is required to mark a visit completed.",
        )

    appt = db.query(Appointment).filter(Appointment.id == appointment_id.strip()).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found.")

    if appt.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Access denied. You can only complete your own visits.")

    appt.status = "completed"
    appt.doctor_note = note_clean
    db.commit()

    return {
        "ok": True,
        "message": f"Appointment {appt.id} marked as completed.",
        "appointment_id": appt.id,
        "status": appt.status,
    }

