"""System prompt builder for NetraCare LangGraph booking agent (Iteration 4 R3).
Constructs dynamic context:
1. Clinic clock and next 30 days calendar (with open/holiday status).
2. Patient profile (name, age, upcoming appointments, past completed visits).
3. Routing, booking rules, and safety guardrails.
"""
from datetime import datetime, date as dt_date, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.config import get_clinic_now
from app.db.models import Patient, Doctor, Appointment, Holiday, WeeklySchedule
from app.services.booking import BookingService

def build_system_prompt(patient_id: str, db: Session) -> str:
    """Build the comprehensive, grounded system prompt for the booking agent."""
    now = get_clinic_now()
    today_date = now.date()
    today_day = BookingService.get_day_abbr(today_date)
    today_time = now.strftime("%H:%M")

    # 1. Next 30 days calendar
    calendar_lines = []
    holidays = {h.date: h.name for h in db.query(Holiday).all()}
    
    for i in range(31):
        d = today_date + timedelta(days=i)
        day_abbr = BookingService.get_day_abbr(d)
        if d.weekday() == 6:
            status_desc = "closed (Sunday)"
        elif d in holidays:
            status_desc = f"holiday ({holidays[d]})"
        else:
            status_desc = "open"
        calendar_lines.append(f"- {d.isoformat()} ({day_abbr}): {status_desc}")
    calendar_text = "\n".join(calendar_lines)

    # 2. Patient Context
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if patient:
        age_str = f"{today_date.year - patient.year_of_birth}" if patient.year_of_birth else "unknown"
        patient_info = f"Name: {patient.name}, Age: {age_str} (Patient ID: {patient.id})"
        is_paediatric = bool(patient.year_of_birth and (today_date.year - patient.year_of_birth < 16))
    else:
        patient_info = f"Patient ID: {patient_id}"
        is_paediatric = False

    # Upcoming appointments
    active_appts = (
        db.query(Appointment)
        .filter(
            Appointment.patient_id == patient_id,
            Appointment.status.in_(["booked", "pending_staff", "proposed"]),
        )
        .order_by(Appointment.date.asc(), Appointment.start_time.asc())
        .all()
    )
    doc_map = {d.id: d.name for d in db.query(Doctor).all()}
    
    upcoming_lines = []
    for a in active_appts:
        d_abbr = BookingService.get_day_abbr(a.date)
        upcoming_lines.append(
            f"- Appointment {a.id}: {d_abbr} {a.date.isoformat()} at {a.start_time.strftime('%H:%M')} "
            f"with {doc_map.get(a.doctor_id, a.doctor_id)} ({a.speciality}, {a.visit_type}, status: {a.status})"
        )
    upcoming_text = "\n".join(upcoming_lines) if upcoming_lines else "None"

    # Past completed visits
    past_appts = (
        db.query(Appointment)
        .filter(
            Appointment.patient_id == patient_id,
            Appointment.status == "completed",
        )
        .order_by(Appointment.date.desc())
        .all()
    )
    past_lines = []
    for a in past_appts:
        past_lines.append(
            f"- {a.date.isoformat()}: {doc_map.get(a.doctor_id, a.doctor_id)} ({a.speciality}, {a.visit_type})"
        )
    past_text = "\n".join(past_lines) if past_lines else "None"

    # 3. Assemble prompt
    prompt = f"""You are the NetraCare Eye Clinic AI Front Desk Assistant.
You help patients find appointment times, book, cancel, reschedule, check their appointments, and answer questions about clinic policies.

CLINIC CLOCK AND CALENDAR:
- Today is: {today_day} {today_date.isoformat()} at {today_time}.
- Next 30 days calendar (use this to identify weekdays, open days, holidays, and Sundays):
{calendar_text}

LOGGED-IN PATIENT CONTEXT:
- {patient_info}
{"- SPECIAL NOTICE: This patient is UNDER 16 years old. ALL bookings for this patient MUST be Paediatric (Dr. Vikram Menon), regardless of the eye complaint." if is_paediatric else ""}
- Current upcoming appointments:
{upcoming_text}
- Past completed visits:
{past_text}

CLINICAL AND BOOKING RULES:
1. ALWAYS find free slots using the `find_slots` tool before offering any times to the patient. NEVER invent, assume, or offer any appointment time that was not returned by `find_slots`.
2. A reason for the visit is MANDATORY before calling `book_appointment`. If the patient hasn't given a reason, ask for it before booking.
3. Speciality selection and Doctor attribution:
   - If patient is under 16: ALWAYS Paediatric with Dr. Vikram Menon.
   - If the patient describes symptoms instead of naming a speciality:
     * Cloudy vision, blurriness, glare -> Cataract (Dr. Anand Rao, Dr. Meera Iyer)
     * Eye pressure, halos, loss of peripheral vision, glaucoma family history -> Glaucoma (Dr. Meera Iyer)
     * Diabetic eye check, floaters, retina check -> Retina (Dr. Kiran Shah)
     * Dry, gritty, itchy eyes, redness, tear film -> Cornea & Refractive (Dr. Fatima Khan)
     * Squint, lazy eye, double vision, child vision -> Paediatric & Strabismus (Dr. Vikram Menon)
     * General eye check, routine test, glasses prescription -> General OPD (Dr. Anand Rao, Dr. Kiran Shah, Dr. Vikram Menon)
4. Follow-up vs. New Consultation:
   - A follow-up consultation MUST be booked with the doctor who saw the patient last in that speciality (see Past completed visits). Duration: 10 minutes.
   - If the patient has no previous completed visit in that speciality, politely explain that they must book a new consultation (20 minutes).
5. Explain refusals in plain words:
   - If doctor is not at the clinic (e.g. Dr. Iyer on Thursdays): explain clearly ("Dr. Iyer is not at the clinic on Thursdays") and offer their available days.
   - If surgery session (e.g. Dr. Khan on Monday afternoon): explain they are in surgery and offer their next OPD times.
   - If active booking exists in that speciality: explain they already have an appointment and offer to change it instead.
   - If beyond 30 days: explain bookings only open up to 30 days ahead and offer dates within the window.
6. Cancelling and Rescheduling:
   - When asked to move or change an appointment, use `reschedule_appointment`.
   - When asked to cancel, use `cancel_appointment`.
   - Never show or modify appointments belonging to other patients.
7. Clinic Information & Policy:
   - If asked about fees, preparation, parking, dilation, laser procedures, or policies, call `search_clinic_docs`.
   - If the documents do not cover the question, repeat the "I don't know" response word for word.
8. MEDICAL SAFETY GUARDRAILS:
   - NEVER name a diagnosis or likely medical condition.
   - NEVER suggest or prescribe treatments, medications, or eye drops.
   - You only represent NetraCare Eye Clinic.
"""
    return prompt
