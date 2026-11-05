"""Public endpoints for clinic info, doctor profiles, and available slots.
No authentication required. Never leaks patient identities.
"""
from datetime import datetime, date as dt_date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Doctor, Holiday
from app.services.booking import BookingService
from app.assistant.llm import get_fact_of_the_day
from app.safety.output_guard import check_patient_facing_output

router = APIRouter(prefix="/public", tags=["Public"])

class DoctorResponse(BaseModel):
    id: str
    name: str
    specialities: List[str]
    active: bool

class ClinicInfoResponse(BaseModel):
    name: str
    hours: str
    lunch_break: str
    sessions: dict
    address: str
    phone: str
    disclaimer: str

@router.get("/clinic", response_model=ClinicInfoResponse)
def get_clinic_info():
    return ClinicInfoResponse(
        name="NetraCare Eye Clinic",
        hours="Monday to Saturday, 9:00 AM – 6:00 PM",
        lunch_break="1:00 PM – 2:00 PM (Closed)",
        sessions={
            "AM": "09:00 – 13:00",
            "PM": "14:00 – 18:00",
        },
        address="104 Netra Enclave, Indiranagar, Bengaluru, Karnataka 560038 [DEMO]",
        phone="+91 80 4000 0000 [DEMO]",
        disclaimer="NetraCare is a synthetic course capstone project. All data and doctors are fictional.",
    )

@router.get("/doctors", response_model=List[DoctorResponse])
def get_doctors(db: Session = Depends(get_db)):
    docs = db.query(Doctor).filter(Doctor.active == True).all()
    return [
        DoctorResponse(
            id=d.id,
            name=d.name,
            specialities=d.get_speciality_list(),
            active=d.active,
        )
        for d in docs
    ]

@router.get("/slots")
def get_slots(
    doctor_id: str = Query(..., description="Doctor ID, e.g. D1"),
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    visit_type: str = Query("new", description="'new' or 'follow_up'"),
    db: Session = Depends(get_db),
):
    try:
        date_val = datetime.strptime(date.strip(), "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    slots = BookingService.find_slots(
        db=db,
        doctor_id=doctor_id.strip(),
        date_val=date_val,
        visit_type=visit_type.strip(),
    )
    return {"ok": True, "date": date, "doctor_id": doctor_id, "slots": slots}

@router.get("/holidays")
def get_holidays(db: Session = Depends(get_db)):
    holidays = db.query(Holiday).order_by(Holiday.date.asc()).all()
    return [
        {"date": h.date.isoformat(), "name": h.name}
        for h in holidays
    ]

@router.get("/fact-of-the-day")
def fact_of_the_day(previous: Optional[str] = Query(None)):
    """Return an educational eye health fact with the mandatory medical caveat."""
    data = get_fact_of_the_day(previous=previous)
    is_safe, sanitized_fact = check_patient_facing_output(data["fact"])
    return {
        "ok": True,
        "fact": sanitized_fact,
        "caveat": data["caveat"],
    }

