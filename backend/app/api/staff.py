"""Staff endpoints for front desk coordination.
Staff can view all doctors' days, book walk-ins, cancel inside 2 hours,
manage urgent cases, and handle approval queues.
"""
from datetime import datetime, date as dt_date, time as dt_time, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_clinic_now
from app.db.session import get_db
from app.db.models import (
    Appointment,
    Patient,
    Doctor,
    UrgentCase,
    Approval,
    AuditEvent,
)
from app.api.deps import get_current_staff, CurrentUser
from app.services.booking import BookingService
from app.assistant.llm import check_red_flags_with_llm

router = APIRouter(prefix="/staff", tags=["Staff"])

class StaffBookRequest(BaseModel):
    patient_id: str
    doctor_id: str
    speciality: str
    visit_type: str = "new"
    date: str                # YYYY-MM-DD
    start_time: str          # HH:MM
    mode: str = "IN_PERSON"
    reason: str              # Required per Iteration 2 R3
    override_reason: Optional[str] = None

class StaffCancelRequest(BaseModel):
    reason: Optional[str] = "Staff cancellation"

class DecideApprovalRequest(BaseModel):
    decision: str  # "APPROVED" or "REJECTED"
    reason: Optional[str] = None

@router.get("/appointments")
def get_all_appointments(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    doctor_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    staff: CurrentUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    query = db.query(Appointment)
    if date:
        try:
            d_val = datetime.strptime(date.strip(), "%Y-%m-%d").date()
            query = query.filter(Appointment.date == d_val)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format.")
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id.strip())
    if status_filter:
        query = query.filter(Appointment.status == status_filter.strip().lower())

    appts = query.order_by(Appointment.date.asc(), Appointment.start_time.asc()).all()

    pat_map = {p.id: p.name for p in db.query(Patient).all()}
    doc_map = {d.id: d.name for d in db.query(Doctor).all()}

    return [
        {
            "id": a.id,
            "patient_id": a.patient_id,
            "patient_name": pat_map.get(a.patient_id, "Unknown"),
            "doctor_id": a.doctor_id,
            "doctor_name": doc_map.get(a.doctor_id, "Unknown"),
            "speciality": a.speciality,
            "visit_type": a.visit_type,
            "mode": a.mode,
            "status": a.status,
            "date": a.date.isoformat(),
            "start_time": a.start_time.strftime("%H:%M"),
            "end_time": a.end_time.strftime("%H:%M"),
            "source": a.source,
            "reason": a.reason,
            "doctor_note": a.doctor_note,
        }
        for a in appts
    ]

@router.post("/appointments")
def book_for_patient(
    req: StaffBookRequest,
    staff: CurrentUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    reason_clean = req.reason.strip() if req.reason else ""
    if not reason_clean:
        raise HTTPException(status_code=400, detail="A visit reason is required (up to 300 characters).")
    if len(reason_clean) > 300:
        raise HTTPException(status_code=400, detail="Reason must not exceed 300 characters.")

    try:
        date_val = datetime.strptime(req.date.strip(), "%Y-%m-%d").date()
        parts = req.start_time.strip().split(":")
        start_time_val = dt_time(int(parts[0]), int(parts[1]))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date or start_time.")

    # Check red flags
    rf_analysis = check_red_flags_with_llm(reason_clean)
    is_red_flag = rf_analysis.get("red_flag", False)
    emergency_msg = rf_analysis.get("emergency_response")
    cat = rf_analysis.get("category", "unspecified")

    if is_red_flag:
        urgent = UrgentCase(
            source="STAFF",
            summary=f"Red flag ({cat}): {reason_clean}",
            patient_id=req.patient_id.strip(),
            draft_context=f'{{"doctor_id":"{req.doctor_id}","speciality":"{req.speciality}","date":"{req.date}","start_time":"{req.start_time}"}}',
            status="OPEN",
        )
        db.add(urgent)
        db.commit()

        # Run normal rule check on slot
        result = BookingService.book(
            db=db,
            patient_id=req.patient_id.strip(),
            doctor_id=req.doctor_id.strip(),
            speciality=req.speciality.strip(),
            visit_type=req.visit_type.strip(),
            date_val=date_val,
            start_time=start_time_val,
            role="staff",
            source="STAFF",
            reason=f"[URGENT] {reason_clean}",
        )

        if not result.ok:
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

        return {
            "ok": True,
            "emergency": True,
            "urgent": True,
            "message": f"Urgent case created. Appointment booked for patient.",
            "appointment_id": result.appointment.id if result.appointment else None,
        }

    result = BookingService.book(
        db=db,
        patient_id=req.patient_id.strip(),
        doctor_id=req.doctor_id.strip(),
        speciality=req.speciality.strip(),
        visit_type=req.visit_type.strip(),
        date_val=date_val,
        start_time=start_time_val,
        role="staff",
        source="STAFF",
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
def staff_cancel_appointment(
    appointment_id: str,
    req: Optional[StaffCancelRequest] = None,
    staff: CurrentUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    reason_str = req.reason if req else "Staff cancellation"
    result = BookingService.cancel(
        db=db,
        appointment_id=appointment_id.strip(),
        actor_role="staff",
        acting_patient_id=None,
        reason=reason_str,
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

    return {"ok": True, "message": result.message}

@router.get("/urgent")
def get_urgent_cases(
    status_filter: Optional[str] = Query("OPEN"),
    staff: CurrentUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    query = db.query(UrgentCase)
    if status_filter:
        query = query.filter(UrgentCase.status == status_filter.upper())
    cases = query.order_by(UrgentCase.created_at.desc()).all()

    pat_map = {p.id: p.name for p in db.query(Patient).all()}

    return [
        {
            "id": c.id,
            "source": c.source,
            "summary": c.summary,
            "patient_id": c.patient_id,
            "patient_name": pat_map.get(c.patient_id, "Anonymous") if c.patient_id else "Anonymous",
            "draft_context": c.draft_context,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "seen_by": c.seen_by,
            "seen_at": c.seen_at.isoformat() if c.seen_at else None,
        }
        for c in cases
    ]

@router.post("/urgent/{case_id}/seen")
def mark_urgent_seen(
    case_id: int,
    staff: CurrentUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    case = db.query(UrgentCase).filter(UrgentCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Urgent case not found.")

    case.status = "SEEN"
    case.seen_by = staff.name
    case.seen_at = datetime.now(timezone.utc)
    db.commit()

    return {"ok": True, "message": f"Case #{case_id} marked as seen."}

@router.get("/approvals")
def get_approvals(
    status_filter: Optional[str] = Query("PENDING"),
    staff: CurrentUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    query = db.query(Approval)
    if status_filter:
        query = query.filter(Approval.status == status_filter.upper())
    approvals = query.order_by(Approval.created_at.desc()).all()
    
    pat_map = {p.id: p.name for p in db.query(Patient).all()}
    doc_map = {d.id: d.name for d in db.query(Doctor).all()}
    appt_map = {a.id: a for a in db.query(Appointment).all()}

    results = []
    for ap in approvals:
        appt = appt_map.get(ap.appointment_id)
        results.append({
            "id": ap.id,
            "kind": ap.kind,
            "appointment_id": ap.appointment_id,
            "patient_id": appt.patient_id if appt else None,
            "patient_name": pat_map.get(appt.patient_id, "Unknown") if appt else "Unknown",
            "doctor_name": doc_map.get(appt.doctor_id, "Unknown") if appt else "Unknown",
            "date": appt.date.isoformat() if appt else None,
            "start_time": appt.start_time.strftime("%H:%M") if appt else None,
            "payload": ap.payload,
            "status": ap.status,
            "decided_by": ap.decided_by,
            "decided_at": ap.decided_at.isoformat() if ap.decided_at else None,
            "reason": ap.reason,
            "created_at": ap.created_at.isoformat() if ap.created_at else None,
        })
    return results

def _apply_approval_decision(db: Session, appr: Approval, decision: str, staff_name: str, reason: Optional[str] = None):
    import json
    appr.status = decision
    appr.decided_by = staff_name
    appr.decided_at = datetime.now(timezone.utc)
    appr.reason = reason

    appt = db.query(Appointment).filter(Appointment.id == appr.appointment_id).first()
    if appt:
        if decision == "APPROVED":
            if appr.kind == "LATE_CANCEL":
                appt.status = "cancelled"
            elif appr.kind == "LATE_RESCHEDULE":
                # Parse new date and time from payload
                try:
                    payload = json.loads(appr.payload)
                    new_date_val = datetime.strptime(payload["new_date"], "%Y-%m-%d").date()
                    parts = payload["new_start_time"].split(":")
                    new_time_val = dt_time(int(parts[0]), int(parts[1]))
                    new_doc_id = payload.get("new_doctor_id") or appt.doctor_id
                    new_spec = payload.get("new_speciality") or appt.speciality

                    # Perform reschedule as staff
                    BookingService.reschedule(
                        db=db,
                        appointment_id=appt.id,
                        new_date=new_date_val,
                        new_start_time=new_time_val,
                        new_doctor_id=new_doc_id,
                        new_speciality=new_spec,
                        actor_role="staff",
                    )
                except Exception:
                    appt.status = "cancelled"
        else:
            # Reverted back to booked
            appt.status = "booked"
    db.commit()

@router.post("/approvals/{approval_id}/decide")
def decide_approval(
    approval_id: int,
    req: DecideApprovalRequest,
    staff: CurrentUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    appr = db.query(Approval).filter(Approval.id == approval_id).first()
    if not appr:
        raise HTTPException(status_code=404, detail="Approval request not found.")

    decision = req.decision.strip().upper()
    if decision not in ["APPROVED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="Decision must be APPROVED or REJECTED.")

    _apply_approval_decision(db, appr, decision, staff.name, req.reason)
    return {"ok": True, "message": f"Approval #{approval_id} set to {decision}."}

@router.post("/approvals/{approval_id}/approve")
def approve_approval(
    approval_id: int,
    staff: CurrentUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    appr = db.query(Approval).filter(Approval.id == approval_id).first()
    if not appr:
        raise HTTPException(status_code=404, detail="Approval request not found.")
    _apply_approval_decision(db, appr, "APPROVED", staff.name)
    return {"ok": True, "message": f"Approval #{approval_id} approved."}

@router.post("/approvals/{approval_id}/reject")
def reject_approval(
    approval_id: int,
    staff: CurrentUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    appr = db.query(Approval).filter(Approval.id == approval_id).first()
    if not appr:
        raise HTTPException(status_code=404, detail="Approval request not found.")
    _apply_approval_decision(db, appr, "REJECTED", staff.name)
    return {"ok": True, "message": f"Approval #{approval_id} rejected."}

# Doctor Leave Rebookings (R7)
@router.get("/rebookings")
def get_rebookings(
    staff: CurrentUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    """List appointments with proposed status waiting for Staff approval."""
    proposals = (
        db.query(Appointment)
        .filter(Appointment.status == "proposed")
        .order_by(Appointment.date.asc(), Appointment.start_time.asc())
        .all()
    )
    pat_map = {p.id: p.name for p in db.query(Patient).all()}
    doc_map = {d.id: d.name for d in db.query(Doctor).all()}

    return [
        {
            "id": p.id,
            "patient_id": p.patient_id,
            "patient_name": pat_map.get(p.patient_id, "Unknown"),
            "doctor_id": p.doctor_id,
            "doctor_name": doc_map.get(p.doctor_id, "Unknown"),
            "speciality": p.speciality,
            "visit_type": p.visit_type,
            "date": p.date.isoformat(),
            "start_time": p.start_time.strftime("%H:%M"),
            "end_time": p.end_time.strftime("%H:%M"),
            "status": p.status,
            "reason": p.reason,
            "rescheduled_from": p.rescheduled_from,
        }
        for p in proposals
    ]

@router.post("/rebookings/{appointment_id}/approve")
def approve_rebooking(
    appointment_id: str,
    staff: CurrentUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id.strip()).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    if appt.status != "proposed":
        raise HTTPException(status_code=400, detail="Appointment is not in proposed status.")

    appt.status = "booked"
    db.commit()
    return {"ok": True, "message": f"Rebooking {appt.id} approved and booked."}

@router.post("/rebookings/{appointment_id}/reject")
def reject_rebooking(
    appointment_id: str,
    staff: CurrentUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id.strip()).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    if appt.status != "proposed":
        raise HTTPException(status_code=400, detail="Appointment is not in proposed status.")

    appt.status = "cancelled"
    db.commit()
    return {"ok": True, "message": f"Rebooking {appt.id} rejected and cancelled."}


@router.get("/patients")
def search_patients(
    q: Optional[str] = Query(None, description="Search by name or mobile"),
    staff: CurrentUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    query = db.query(Patient)
    if q:
        search = f"%{q.strip()}%"
        query = query.filter((Patient.name.ilike(search)) | (Patient.mobile.ilike(search)))
    patients = query.limit(50).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "mobile": p.mobile,
            "year_of_birth": p.year_of_birth,
            "chronic_conditions": p.chronic_conditions,
            "allergies": p.allergies,
        }
        for p in patients
    ]

@router.get("/audit")
def get_audit_trail(
    limit: int = Query(50),
    staff: CurrentUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    events = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit).all()
    return events
