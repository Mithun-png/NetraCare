"""Patient endpoints for booking, viewing, cancelling, and rescheduling own appointments.
Server-side security: patient ID is strictly derived from the session token.
"""
from datetime import datetime, date as dt_date, time as dt_time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Appointment, Doctor, UrgentCase, Patient
from app.api.deps import get_current_patient, CurrentUser
from app.services.booking import BookingService
from app.assistant.llm import check_red_flags_with_llm
from app.safety.red_flags import check_red_flags

router = APIRouter(prefix="/patient", tags=["Patient"])

class BookAppointmentRequest(BaseModel):
    doctor_id: str
    speciality: str
    visit_type: str = "new"  # "new", "follow_up"
    date: str                # YYYY-MM-DD
    start_time: str          # HH:MM
    mode: str = "IN_PERSON"  # "IN_PERSON", "VIRTUAL"
    reason: str              # Required per Iteration 2 R3 (up to 300 chars)

class RescheduleAppointmentRequest(BaseModel):
    new_date: str
    new_start_time: str
    new_doctor_id: Optional[str] = None
    new_speciality: Optional[str] = None

class CancelAppointmentRequest(BaseModel):
    reason: Optional[str] = None

class AppointmentDetailResponse(BaseModel):
    id: str
    doctor_id: str
    doctor_name: str
    speciality: str
    visit_type: str
    mode: str
    status: str
    date: str
    start_time: str
    end_time: str
    reason: Optional[str]
    doctor_note: Optional[str]
    source: Optional[str] = "WEBSITE"

@router.get("/appointments", response_model=List[AppointmentDetailResponse])
def get_my_appointments(
    patient: CurrentUser = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    appts = (
        db.query(Appointment)
        .filter(Appointment.patient_id == patient.id)
        .order_by(Appointment.date.desc(), Appointment.start_time.desc())
        .all()
    )

    doc_map = {d.id: d.name for d in db.query(Doctor).all()}

    return [
        AppointmentDetailResponse(
            id=a.id,
            doctor_id=a.doctor_id,
            doctor_name=doc_map.get(a.doctor_id, "Unknown Doctor"),
            speciality=a.speciality,
            visit_type=a.visit_type,
            mode=a.mode,
            status=a.status,
            date=a.date.isoformat(),
            start_time=a.start_time.strftime("%H:%M"),
            end_time=a.end_time.strftime("%H:%M"),
            reason=a.reason,
            doctor_note=a.doctor_note,
            source=a.source,
        )
        for a in appts
    ]

@router.post("/appointments")
def book_appointment(
    req: BookAppointmentRequest,
    patient: CurrentUser = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    # 1. Validation: Reason is mandatory (R3, max 300 characters)
    reason_clean = req.reason.strip() if req.reason else ""
    if not reason_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="What is the reason for your visit? A reason is required (up to 300 characters).",
        )
    if len(reason_clean) > 300:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reason must not exceed 300 characters.",
        )

    # 2. Parse date and time
    try:
        date_val = datetime.strptime(req.date.strip(), "%Y-%m-%d").date()
        parts = req.start_time.strip().split(":")
        start_time_val = dt_time(int(parts[0]), int(parts[1]))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date or start_time format. Use YYYY-MM-DD and HH:MM.",
        )

    # 3. Red-Flag Safety Check (R4)
    rf_analysis = check_red_flags_with_llm(reason_clean)
    is_red_flag = rf_analysis.get("red_flag", False)
    emergency_msg = rf_analysis.get("emergency_response")
    cat = rf_analysis.get("category", "unspecified")

    if is_red_flag:
        # Create persistent Urgent Case for staff pinned view
        urgent = UrgentCase(
            source="WEBSITE",
            summary=f"Red flag ({cat}): {reason_clean}",
            patient_id=patient.id,
            draft_context=f'{{"doctor_id":"{req.doctor_id}","speciality":"{req.speciality}","date":"{req.date}","start_time":"{req.start_time}"}}',
            status="OPEN",
        )
        db.add(urgent)
        db.commit()

        # Run normal rules check on the slot per Handout 2 R4
        result = BookingService.book(
            db=db,
            patient_id=patient.id,
            doctor_id=req.doctor_id.strip(),
            speciality=req.speciality.strip(),
            visit_type=req.visit_type.strip(),
            date_val=date_val,
            start_time=start_time_val,
            role="patient",
            source="WEBSITE",
            reason=f"[URGENT] {reason_clean}",
        )

        if not result.ok:
            # Slot breaks clinic rule (e.g. Dr. Rao Thursday morning surgery session)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "ok": False,
                    "reason_code": result.reason_code.value if result.reason_code else "RED_FLAG",
                    "emergency": True,
                    "urgent": True,
                    "message": f"{emergency_msg}\n\n(Booking refused: {result.message})",
                },
            )

        # Slot is valid: appointment is booked with Urgent tag
        return {
            "ok": True,
            "emergency": True,
            "urgent": True,
            "message": emergency_msg,
            "appointment_id": result.appointment.id if result.appointment else None,
        }

    # 4. Normal non-red-flag booking
    result = BookingService.book(
        db=db,
        patient_id=patient.id,
        doctor_id=req.doctor_id.strip(),
        speciality=req.speciality.strip(),
        visit_type=req.visit_type.strip(),
        date_val=date_val,
        start_time=start_time_val,
        role="patient",
        source="WEBSITE",
        reason=reason_clean,
    )

    if not result.ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "ok": False,
                "reason_code": result.reason_code.value if result.reason_code else None,
                "message": result.message,
            },
        )

    return {
        "ok": True,
        "message": result.message,
        "appointment_id": result.appointment.id if result.appointment else None,
    }

@router.post("/appointments/{appointment_id}/cancel")
def cancel_appointment(
    appointment_id: str,
    req: Optional[CancelAppointmentRequest] = None,
    patient: CurrentUser = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    reason_str = req.reason if req else None
    result = BookingService.cancel(
        db=db,
        appointment_id=appointment_id.strip(),
        actor_role="patient",
        acting_patient_id=patient.id,
        reason=reason_str,
    )

    if not result.ok:
        if result.expected == "to_staff":
            return {
                "ok": False,
                "expected": "to_staff",
                "reason_code": result.reason_code.value if result.reason_code else None,
                "message": result.message,
            }
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "ok": False,
                "reason_code": result.reason_code.value if result.reason_code else None,
                "message": result.message,
            },
        )

    return {"ok": True, "message": result.message}

@router.post("/appointments/{appointment_id}/reschedule")
def reschedule_appointment(
    appointment_id: str,
    req: RescheduleAppointmentRequest,
    patient: CurrentUser = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    try:
        new_date_val = datetime.strptime(req.new_date.strip(), "%Y-%m-%d").date()
        parts = req.new_start_time.strip().split(":")
        new_time_val = dt_time(int(parts[0]), int(parts[1]))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date or start_time format. Use YYYY-MM-DD and HH:MM.",
        )

    result = BookingService.reschedule(
        db=db,
        appointment_id=appointment_id.strip(),
        new_date=new_date_val,
        new_start_time=new_time_val,
        new_doctor_id=req.new_doctor_id.strip() if req.new_doctor_id else None,
        new_speciality=req.new_speciality.strip() if req.new_speciality else None,
        actor_role="patient",
        acting_patient_id=patient.id,
    )

    if not result.ok:
        if result.expected == "to_staff":
            return {
                "ok": False,
                "expected": "to_staff",
                "reason_code": result.reason_code.value if result.reason_code else None,
                "message": result.message,
            }
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "ok": False,
                "reason_code": result.reason_code.value if result.reason_code else None,
                "message": result.message,
            },
        )

    return {
        "ok": True,
        "message": result.message,
        "appointment_id": result.appointment.id if result.appointment else None,
    }

@router.get("/profile")
def get_patient_profile(
    patient: CurrentUser = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    p = db.query(Patient).filter(Patient.id == patient.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient profile not found.")
    return {
        "id": p.id,
        "name": p.name,
        "mobile": p.mobile,
        "year_of_birth": p.year_of_birth,
        "chronic_conditions": p.chronic_conditions,
        "allergies": p.allergies,
    }

