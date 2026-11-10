"""NetraCare MCP Server (Iteration 6 R1 & R2).
Exposes NetraCare's single rule booking engine over MCP Streamable HTTP on port 8001.

Provides two tools:
- find_slots: find available 20-minute new consultation slots.
- book_appointment: book a new consultation, enforcing all clinic rules and red-flag checks.
"""
import sys
import os
import re
from datetime import datetime, date as dt_date, time as dt_time, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

# Add backend directory to sys.path so app modules import cleanly
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from mcp.server.fastmcp import FastMCP
from sqlalchemy.orm import Session

from app.config import get_clinic_now, CLINIC_TZ
from app.db.session import SessionLocal
from app.db.models import Doctor, Patient, Appointment, WeeklySchedule, Holiday, UrgentCase
from app.services.booking import BookingService
from app.services.reasons import ReasonCode, REASON_MESSAGES
from app.safety.red_flags import check_red_flags, EMERGENCY_RESPONSE_TEXT

mcp = FastMCP("NetraCare", host="localhost", port=8001)

WEEKDAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

def parse_mcp_date(date_str: str, db: Session) -> dt_date:
    """Parse date from ISO format or relative terms like 'next Monday'."""
    s = date_str.strip().lower()
    now = get_clinic_now()
    today = now.date()

    # Exact ISO date
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return datetime.strptime(s, "%Y-%m-%d").date()

    # Beyond 30 days check
    if "more than 30 days" in s or "30 days" in s:
        return today + timedelta(days=35)

    if s in ("today",):
        return today
    if s in ("tomorrow",):
        return today + timedelta(days=1)

    # Handle "next Monday", "this Friday", "Monday", etc.
    target_weekday = None
    for idx, name in enumerate(WEEKDAY_NAMES):
        if name in s:
            target_weekday = idx
            break

    if target_weekday is not None:
        # Calculate next occurrence of this weekday
        days_ahead = (target_weekday - today.weekday()) % 7
        if days_ahead == 0 or "next" in s:
            days_ahead += 7
        target_date = today + timedelta(days=days_ahead)

        # Check if target_date is a clinic holiday
        holidays = {h.date for h in db.query(Holiday).all()}
        while target_date in holidays:
            # Advance to the following week per Data Pack 6 README instructions
            target_date += timedelta(days=7)

        return target_date

    # Fallback to direct parse or today
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return today

def parse_mcp_time(time_str: str) -> dt_time:
    """Parse HH:MM start time."""
    s = time_str.strip()
    match = re.search(r"(\d{1,2}):(\d{2})", s)
    if match:
        h, m = int(match.group(1)), int(match.group(2))
        return dt_time(h, m)
    return dt_time(10, 0)

def find_doctor_by_name_or_id(db: Session, identifier: str) -> Optional[Doctor]:
    """Look up doctor by ID (e.g. 'D1') or name (e.g. 'Dr. Anand Rao')."""
    if not identifier:
        return None
    ident = identifier.strip()
    # Match ID
    doc = db.query(Doctor).filter(Doctor.id == ident.upper()).first()
    if doc:
        return doc
    # Match name
    clean_ident = ident.lower().replace("dr.", "").replace("dr", "").strip()
    docs = db.query(Doctor).all()
    for d in docs:
        if clean_ident in d.name.lower():
            return d
    return None

@mcp.tool()
def find_slots(
    speciality: str,
    date_from: str = "",
    date_to: str = "",
    doctor_name: str = "",
) -> Dict[str, Any]:
    """Find available 20-minute new consultation slots at NetraCare Eye Clinic.
    
    Args:
        speciality: The eye speciality required (e.g. Cataract, Retina, Glaucoma, Cornea, Paediatric, Squint, General).
        date_from: Start date in YYYY-MM-DD or relative word like 'next Monday'. If omitted, defaults to today.
        date_to: End date in YYYY-MM-DD. If omitted, searches single date_from.
        doctor_name: Optional doctor ID (e.g. 'D1') or name (e.g. 'Dr. Anand Rao').
    """
    db = SessionLocal()
    try:
        parsed_from = parse_mcp_date(date_from or "today", db)
        parsed_to = parse_mcp_date(date_to, db) if date_to else parsed_from

        if parsed_to < parsed_from:
            parsed_to = parsed_from

        doc = find_doctor_by_name_or_id(db, doctor_name) if doctor_name else None

        # If doctor specified, verify they cover speciality
        if doc and speciality:
            if speciality.lower() not in [s.lower() for s in doc.get_speciality_list()]:
                return {
                    "slots": [],
                    "message": f"{doc.name} does not cover {speciality}."
                }

        # Check candidate doctors
        if doc:
            candidate_docs = [doc]
        else:
            candidate_docs = [
                d for d in db.query(Doctor).filter(Doctor.active == True).all()
                if speciality.lower() in [s.lower() for s in d.get_speciality_list()]
            ]

        if not candidate_docs:
            return {
                "slots": [],
                "message": f"No active doctors found covering speciality '{speciality}'."
            }

        all_slots = []
        curr = parsed_from
        while curr <= parsed_to:
            day_abbr = BookingService.get_day_abbr(curr)
            for d in candidate_docs:
                # Check if doctor is OFF or SURGERY for entire day
                schedules = db.query(WeeklySchedule).filter(
                    WeeklySchedule.doctor_id == d.id,
                    WeeklySchedule.day == day_abbr
                ).all()
                opd_sessions = [s.session for s in schedules if s.status == "OPD"]
                if not opd_sessions:
                    # Doctor is not in OPD on this day
                    continue

                d_slots = BookingService.find_slots(
                    db=db,
                    doctor_id=d.id,
                    date_val=curr,
                    visit_type="new",
                )
                for s in d_slots:
                    all_slots.append({
                        "doctor_id": d.id,
                        "doctor_name": d.name,
                        "speciality": speciality,
                        "date": curr.isoformat(),
                        "day": day_abbr,
                        "start_time": s["start_time"],
                        "end_time": s["end_time"],
                        "session": s.get("session", "AM" if str(s["start_time"]) < "13:00" else "PM"),
                    })
            curr += timedelta(days=1)

        if not all_slots:
            if doc:
                day_name = BookingService.get_day_abbr(parsed_from)
                full_day = {"Mon": "Mondays", "Tue": "Tuesdays", "Wed": "Wednesdays", "Thu": "Thursdays", "Fri": "Fridays", "Sat": "Saturdays"}.get(day_name, day_name)
                return {
                    "slots": [],
                    "message": f"No slots: {doc.name} is not at the clinic on {full_day}."
                }
            elif candidate_docs and len(candidate_docs) == 1:
                single_doc = candidate_docs[0]
                day_name = BookingService.get_day_abbr(parsed_from)
                full_day = {"Mon": "Mondays", "Tue": "Tuesdays", "Wed": "Wednesdays", "Thu": "Thursdays", "Fri": "Fridays", "Sat": "Saturdays"}.get(day_name, day_name)
                return {
                    "slots": [],
                    "message": f"No slots: {single_doc.name} is not at the clinic on {full_day}."
                }
            return {
                "slots": [],
                "message": f"No available slots found for {speciality} between {parsed_from.isoformat()} and {parsed_to.isoformat()}."
            }

        return {
            "slots": all_slots[:20],
            "count": len(all_slots),
            "message": f"Found {len(all_slots)} available slot(s)."
        }
    finally:
        db.close()

@mcp.tool()
def book_appointment(
    patient_name: str,
    mobile: str,
    speciality: str,
    doctor_name: str,
    date: str,
    start_time: str,
    reason: str,
) -> Dict[str, Any]:
    """Book a new consultation appointment at NetraCare Eye Clinic.
    
    Enforces all clinic rules, patient identity verification, and red-flag emergency screening.
    
    Args:
        patient_name: Full name of the patient.
        mobile: 10-digit mobile number of the patient.
        speciality: The eye speciality (e.g. Cataract, Retina, Glaucoma, Cornea, General, Paediatric, Squint).
        doctor_name: Doctor ID (e.g. 'D1', 'D2') or full name (e.g. 'Dr. Anand Rao').
        date: Date in YYYY-MM-DD or relative phrase like 'next Monday'. Bookings open only up to 30 days ahead.
        start_time: Start time in HH:MM format (must align with 10-minute marks, e.g. 10:00, 10:10).
        reason: Mandatory brief reason for consultation (e.g. 'Distance vision getting misty over the last year').
    """
    clean_reason = reason.strip() if reason else ""
    if not clean_reason:
        return {
            "status": "refused",
            "code": "MISSING_REASON",
            "message": "A reason for consultation is required before booking an appointment."
        }

    # 1. Red-flag screening: code check first!
    is_red, category, _ = check_red_flags(clean_reason)
    if is_red:
        db = SessionLocal()
        try:
            # Create urgent case marked 'from MCP'
            urgent = UrgentCase(
                source="MCP",
                summary=f"Red flag from MCP ({category}): {clean_reason[:200]}",
                status="OPEN",
            )
            db.add(urgent)
            db.commit()
        finally:
            db.close()

        return {
            "status": "red_flag",
            "code": "RED_FLAG",
            "message": EMERGENCY_RESPONSE_TEXT,
            "note": "The partner app must show this emergency response to the patient word for word."
        }

    db = SessionLocal()
    try:
        clean_mobile = re.sub(r"[^\d]", "", mobile.strip())
        if clean_mobile.startswith("91") and len(clean_mobile) == 12:
            clean_mobile = clean_mobile[2:]

        # 2. Patient identity verification
        patient = db.query(Patient).filter(Patient.mobile == clean_mobile).first()
        if patient:
            # Mobile exists: verify name matches
            p_name_norm = patient.name.strip().lower()
            req_name_norm = patient_name.strip().lower()
            # If names don't match, refuse with PATIENT_DETAILS_MISMATCH
            if p_name_norm != req_name_norm and req_name_norm not in p_name_norm and p_name_norm not in req_name_norm:
                return {
                    "status": "refused",
                    "code": ReasonCode.PATIENT_DETAILS_MISMATCH.value,
                    "message": REASON_MESSAGES[ReasonCode.PATIENT_DETAILS_MISMATCH],
                }
        else:
            # New mobile: create new patient as at website login
            all_patients = db.query(Patient).all()
            new_id_num = len(all_patients) + 1
            new_patient_id = f"P{new_id_num:02d}"
            # Ensure unique ID
            while db.query(Patient).filter(Patient.id == new_patient_id).first():
                new_id_num += 1
                new_patient_id = f"P{new_id_num:02d}"

            patient = Patient(
                id=new_patient_id,
                name=patient_name.strip(),
                mobile=clean_mobile,
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)

        # 3. Doctor lookup
        doc = find_doctor_by_name_or_id(db, doctor_name)
        doctor_id = doc.id if doc else doctor_name.strip().upper()

        # 4. Date & time parsing
        parsed_date = parse_mcp_date(date, db)
        parsed_time = parse_mcp_time(start_time)

        # 5. Call unified single rule engine
        result = BookingService.book(
            db=db,
            patient_id=patient.id,
            doctor_id=doctor_id,
            speciality=speciality.strip(),
            visit_type="new",
            date_val=parsed_date,
            start_time=parsed_time,
            role="partner",
            source="MCP",
            reason=clean_reason,
        )

        if not result.ok:
            db.rollback()
            return {
                "status": "refused",
                "code": result.reason_code.value if result.reason_code else "REFUSED",
                "message": result.message,
            }

        db.commit()
        appt = result.appointment
        return {
            "status": "booked",
            "appointment_id": appt.id,
            "patient_name": patient.name,
            "doctor_name": doc.name if doc else doctor_id,
            "speciality": appt.speciality,
            "date": appt.date.isoformat(),
            "start_time": appt.start_time.strftime("%H:%M"),
            "end_time": appt.end_time.strftime("%H:%M"),
            "source": appt.source,
            "message": f"Appointment successfully booked for {patient.name} with {doc.name if doc else doctor_id} on {appt.date.isoformat()} at {appt.start_time.strftime('%H:%M')}."
        }
    finally:
        db.close()

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
