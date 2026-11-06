"""Independent Clinic Rule Auditor for NetraCare Appointments.
Checks every appointment in the database against Section 04 of the clinic brief:
- 10-minute start marks
- Inside the doctor's OPD session (status == 'OPD')
- Ends by 1 PM or 6 PM (and respects 1-2 PM lunch break)
- Not on a Sunday or clinic holiday
- Within 30 days of the clinic clock
- Doctor covers the speciality
- No overlapping bookings for the same doctor
- One active booking per patient per speciality
- Follow-up with the doctor who saw the patient
- Doctor not on leave
"""
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models import Appointment, Doctor, WeeklySchedule, Holiday, DoctorLeave

FIXED_CLINIC_NOW = datetime(2026, 11, 2, 10, 0)
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

def audit_appointment(
    appt: Appointment,
    db: Session,
    clinic_now: datetime = FIXED_CLINIC_NOW
) -> List[str]:
    """Audit a single appointment and return a list of rule violation descriptions."""
    violations = []
    
    # Only active or proposed bookings need to be compliant (cancelled appointments do not violate schedule)
    if appt.status not in ["booked", "proposed"]:
        return []

    # 1. 10-minute start mark
    start_t = appt.start_time
    if start_t.minute % 10 != 0 or start_t.second != 0:
        violations.append(f"Appointment {appt.id}: Start time {start_t} is not on a 10-minute boundary.")

    # 2. Duration calculation & Session boundaries
    end_t = appt.end_time
    is_am = time(9, 0) <= start_t < time(13, 0)
    is_pm = time(14, 0) <= start_t < time(18, 0)

    if not (is_am or is_pm):
        violations.append(f"Appointment {appt.id}: Start time {start_t} is outside clinic hours (09:00-13:00, 14:00-18:00).")
    
    # Ends by 1 PM or 6 PM
    if is_am and end_t > time(13, 0):
        violations.append(f"Appointment {appt.id}: AM appointment ends at {end_t}, after 1:00 PM session cutoff.")
    if is_pm and end_t > time(18, 0):
        violations.append(f"Appointment {appt.id}: PM appointment ends at {end_t}, after 6:00 PM session cutoff.")

    # 3. Sunday or Holiday check
    weekday_idx = appt.date.weekday()
    if weekday_idx == 6:
        violations.append(f"Appointment {appt.id}: Date {appt.date} is a Sunday (clinic closed).")
    
    holiday = db.query(Holiday).filter(Holiday.date == appt.date).first()
    if holiday:
        violations.append(f"Appointment {appt.id}: Date {appt.date} is a clinic holiday ({holiday.name}).")

    # 4. Within 30 days of clinic clock
    min_date = clinic_now.date()
    max_date = min_date + timedelta(days=30)
    if appt.date < min_date or appt.date > max_date:
        violations.append(f"Appointment {appt.id}: Date {appt.date} is outside 30-day booking window ({min_date} to {max_date}).")
    elif appt.date == min_date and start_t < clinic_now.time():
        violations.append(f"Appointment {appt.id}: Time {start_t} on {appt.date} is in the past relative to clinic clock ({clinic_now.time()}).")

    # 5. Doctor existence and status
    doctor = db.query(Doctor).filter(Doctor.id == appt.doctor_id).first()
    if not doctor or not doctor.active:
        violations.append(f"Appointment {appt.id}: Doctor {appt.doctor_id} not found or inactive.")
    else:
        # Doctor covers speciality
        doc_specs = [s.strip().lower() for s in doctor.specialities.split(";")]
        if appt.speciality.strip().lower() not in doc_specs:
            violations.append(f"Appointment {appt.id}: Doctor {doctor.name} does not cover speciality {appt.speciality} (covers: {doctor.specialities}).")

        # Doctor weekly schedule (OPD vs SURGERY vs OFF)
        day_str = DAY_NAMES[weekday_idx]
        session_str = "AM" if is_am else "PM"
        ws = db.query(WeeklySchedule).filter(
            WeeklySchedule.doctor_id == doctor.id,
            WeeklySchedule.day == day_str,
            WeeklySchedule.session == session_str
        ).first()

        if not ws:
            violations.append(f"Appointment {appt.id}: No schedule entry for {doctor.name} on {day_str} {session_str}.")
        elif ws.status.upper() != "OPD":
            violations.append(f"Appointment {appt.id}: {doctor.name} is scheduled as {ws.status} (not OPD) on {day_str} {session_str}.")

        # Doctor leave check
        leave = db.query(DoctorLeave).filter(
            DoctorLeave.doctor_id == doctor.id,
            DoctorLeave.date == appt.date
        ).first()
        if leave:
            if leave.session.upper() in ["ALL", "FULL", session_str]:
                violations.append(f"Appointment {appt.id}: {doctor.name} is on leave on {appt.date} ({leave.session}).")

    # 6. Follow-up consistency
    if appt.visit_type.lower() == "follow_up":
        # Must match past doctor who saw patient for this speciality
        past_consult = db.query(Appointment).filter(
            Appointment.patient_id == appt.patient_id,
            Appointment.speciality == appt.speciality,
            Appointment.status == "completed"
        ).first()
        if past_consult and past_consult.doctor_id != appt.doctor_id:
            violations.append(f"Appointment {appt.id}: Follow-up must be with original doctor {past_consult.doctor_id}, not {appt.doctor_id}.")

    return violations


def audit_database(db: Session, clinic_now: datetime = FIXED_CLINIC_NOW) -> Dict[str, Any]:
    """Audit all appointments in the database.
    Checks individual appointment validity, doctor overlaps, and single active booking per speciality.
    """
    appointments = db.query(Appointment).filter(Appointment.status.in_(["booked", "proposed"])).all()
    all_violations = []

    # 1. Audit each appointment
    for appt in appointments:
        violations = audit_appointment(appt, db, clinic_now)
        all_violations.extend(violations)

    # 2. Check for doctor overlaps
    # Group by doctor and date
    doc_date_map: Dict[str, List[Appointment]] = {}
    for appt in appointments:
        key = f"{appt.doctor_id}_{appt.date}"
        doc_date_map.setdefault(key, []).append(appt)

    for key, appts in doc_date_map.items():
        if len(appts) < 2:
            continue
        # Check pairwise
        for i in range(len(appts)):
            for j in range(i + 1, len(appts)):
                a1 = appts[i]
                a2 = appts[j]
                start1 = datetime.combine(a1.date, a1.start_time)
                end1 = datetime.combine(a1.date, a1.end_time)
                start2 = datetime.combine(a2.date, a2.start_time)
                end2 = datetime.combine(a2.date, a2.end_time)

                if max(start1, start2) < min(end1, end2):
                    all_violations.append(
                        f"Doctor overlap: {a1.doctor_id} has overlapping appointments {a1.id} ({a1.start_time}) and {a2.id} ({a2.start_time}) on {a1.date}."
                    )

    # 3. Check single active booking per patient per speciality
    patient_spec_map: Dict[str, List[Appointment]] = {}
    for appt in appointments:
        if appt.status == "booked":
            key = f"{appt.patient_id}_{appt.speciality.lower()}"
            patient_spec_map.setdefault(key, []).append(appt)

    for key, appts in patient_spec_map.items():
        if len(appts) > 1:
            p_id, spec = key.split("_", 1)
            appt_ids = [a.id for a in appts]
            all_violations.append(
                f"Multiple active bookings: Patient {p_id} has {len(appts)} active bookings for {spec}: {appt_ids}."
            )

    return {
        "total_appointments_audited": len(appointments),
        "rule_breaks_count": len(all_violations),
        "rule_breaks": all_violations,
        "passed": len(all_violations) == 0,
    }
