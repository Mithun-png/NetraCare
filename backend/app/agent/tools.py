"""Agent tools for NetraCare LangGraph booking assistant (Iteration 4 R2 & R5).
Every tool uses the unified BookingService rule engine or knowledge base retriever.
Server-side security: patient ID is strictly retrieved from RunnableConfig, never LLM arguments.
Interrupt is invoked before write actions to render the human-in-the-loop confirmation card.
"""
from datetime import datetime, date as dt_date, time as dt_time, timedelta
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt

from app.config import get_clinic_now, CLINIC_TZ
from app.db.session import SessionLocal
from app.db.models import Doctor, Patient, Appointment, WeeklySchedule, Holiday, Approval
from app.services.booking import BookingService
from app.services.reasons import ReasonCode, REASON_MESSAGES
from app.rag.retriever import get_hybrid_retriever
from app.rag.chat import generate_chat_answer, IDK_RESPONSE

@tool
def search_clinic_docs(query: str) -> Dict[str, Any]:
    """Search clinic policies, FAQs, consultation fees, preparation instructions, and doctors guide."""
    retriever = get_hybrid_retriever()
    scored_chunks = retriever.search(query, top_k=4)
    parsed = generate_chat_answer(rewritten_query=query, chunks=scored_chunks)
    
    # Format sources
    doc_display_names = {
        "clinic_policy_faq.md": "clinic_policy_faq.md",
        "doctors.md": "doctors.md",
        "patient_prep.md": "patient_prep.md",
    }
    sources = []
    if parsed.answered and parsed.source_ids:
        for cid in parsed.source_ids:
            for chunk, _ in scored_chunks:
                if chunk.chunk_id == cid or cid in chunk.chunk_id:
                    fn = doc_display_names.get(chunk.source, chunk.source)
                    sec = chunk.section or "General"
                    s_str = f"{fn} › {sec}"
                    if s_str not in sources:
                        sources.append(s_str)
                    break

    return {
        "answer": parsed.answer,
        "sources": sources,
        "answered": parsed.answered,
    }

@tool
def list_doctors() -> List[Dict[str, Any]]:
    """List all doctors at NetraCare with their IDs, names, specialities, and OPD session days."""
    db = SessionLocal()
    try:
        doctors = db.query(Doctor).filter(Doctor.active == True).all()
        schedules = db.query(WeeklySchedule).all()
        
        sched_map: Dict[str, List[str]] = {}
        for s in schedules:
            if s.status == "OPD":
                sched_map.setdefault(s.doctor_id, []).append(f"{s.day} {s.session}")

        return [
            {
                "doctor_id": d.id,
                "name": d.name,
                "specialities": d.get_speciality_list(),
                "opd_schedule": ", ".join(sched_map.get(d.id, [])),
            }
            for d in doctors
        ]
    finally:
        db.close()

@tool
def find_slots(
    doctor_id: Optional[str] = None,
    speciality: Optional[str] = None,
    visit_type: str = "new",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    session: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Find free available appointment start times for a doctor or speciality, visit type, date range, and optional session.
    Returns at most 10 free slots, sorted earliest first.
    """
    db = SessionLocal()
    try:
        now = get_clinic_now()
        start_date = datetime.strptime(date_from, "%Y-%m-%d").date() if date_from else now.date()
        end_date = datetime.strptime(date_to, "%Y-%m-%d").date() if date_to else (start_date + timedelta(days=14))

        # Enforce max 30-day window
        max_allowed = now.date() + timedelta(days=30)
        if start_date > max_allowed:
            return []
        if end_date > max_allowed:
            end_date = max_allowed

        all_doctors = db.query(Doctor).filter(Doctor.active == True).all()
        doc_map = {d.id: d for d in all_doctors}

        candidate_doctor_ids = []
        if doctor_id:
            candidate_doctor_ids = [doctor_id]
        elif speciality:
            for d in all_doctors:
                if speciality.lower() in [s.lower() for s in d.get_speciality_list()]:
                    candidate_doctor_ids.append(d.id)
        else:
            candidate_doctor_ids = [d.id for d in all_doctors]

        matching_slots = []
        curr_date = start_date
        while curr_date <= end_date and len(matching_slots) < 10:
            # Skip Sundays and holidays
            if curr_date.weekday() == 6:
                curr_date += timedelta(days=1)
                continue
            if db.query(Holiday).filter(Holiday.date == curr_date).first():
                curr_date += timedelta(days=1)
                continue

            day_abbr = BookingService.get_day_abbr(curr_date)
            for d_id in candidate_doctor_ids:
                doc = doc_map.get(d_id)
                slots = BookingService.find_slots(
                    db=db,
                    doctor_id=d_id,
                    date_val=curr_date,
                    visit_type=visit_type,
                )
                for slot in slots:
                    slot_time = datetime.strptime(slot["start_time"], "%H:%M").time()
                    slot_sess = "AM" if slot_time < dt_time(13, 0) else "PM"
                    if session and session.upper() != slot_sess:
                        continue

                    matching_slots.append({
                        "date": curr_date.isoformat(),
                        "day": day_abbr,
                        "start_time": slot["start_time"],
                        "end_time": slot["end_time"],
                        "session": slot_sess,
                        "doctor_id": d_id,
                        "doctor_name": doc.name if doc else d_id,
                        "speciality": speciality or (doc.get_speciality_list()[0] if doc else "General"),
                        "visit_type": visit_type,
                    })
                    if len(matching_slots) >= 10:
                        break
                if len(matching_slots) >= 10:
                    break
            curr_date += timedelta(days=1)

        return matching_slots
    finally:
        db.close()

@tool
def my_appointments(config: RunnableConfig) -> Dict[str, Any]:
    """Get the current logged-in patient's upcoming appointments and any requests waiting for Staff."""
    patient_id = config.get("configurable", {}).get("patient_id")
    if not patient_id:
        return {"error": "Authentication required. No patient is logged in."}

    db = SessionLocal()
    try:
        now = get_clinic_now()
        appts = (
            db.query(Appointment)
            .filter(
                Appointment.patient_id == patient_id,
                Appointment.status.in_(["booked", "pending_staff", "proposed"]),
            )
            .order_by(Appointment.date.asc(), Appointment.start_time.asc())
            .all()
        )
        doc_map = {d.id: d.name for d in db.query(Doctor).all()}

        active_list = []
        for a in appts:
            active_list.append({
                "appointment_id": a.id,
                "doctor_id": a.doctor_id,
                "doctor_name": doc_map.get(a.doctor_id, "Unknown"),
                "speciality": a.speciality,
                "visit_type": a.visit_type,
                "date": a.date.isoformat(),
                "day": BookingService.get_day_abbr(a.date),
                "start_time": a.start_time.strftime("%H:%M"),
                "status": a.status,
                "reason": a.reason,
            })

        return {
            "patient_id": patient_id,
            "upcoming_appointments": active_list,
            "count": len(active_list),
        }
    finally:
        db.close()

@tool
def book_appointment(
    doctor_id: str,
    speciality: str,
    visit_type: str,
    date: str,
    start_time: str,
    reason: str,
    config: RunnableConfig,
) -> Dict[str, Any]:
    """Book an appointment for the current patient.
    Requires: doctor_id, speciality, visit_type ('new' or 'follow_up'), date (YYYY-MM-DD), start_time (HH:MM), and reason.
    """
    patient_id = config.get("configurable", {}).get("patient_id")
    if not patient_id:
        return {"result": "error", "message": "Authentication required. No patient is logged in."}

    db = SessionLocal()
    try:
        doc = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        doc_name = doc.name if doc else doctor_id
        duration = 20 if visit_type.lower() == "new" else 10
        try:
            d_val = datetime.strptime(date.strip(), "%Y-%m-%d").date()
            t_parts = start_time.strip().split(":")
            t_val = dt_time(int(t_parts[0]), int(t_parts[1]))
            day_str = BookingService.get_day_abbr(d_val)
            date_display = d_val.strftime("%a %d %b")
        except Exception:
            return {"result": "refused", "message": "Invalid date or time format. Please use YYYY-MM-DD and HH:MM."}

        # Human-in-the-loop interrupt
        summary = f"Book {doc_name}, {speciality} {visit_type.replace('_', '-')}, {date_display}, {start_time} ({duration} min)?"
        confirmed = interrupt({
            "action": "book",
            "summary": summary,
            "details": {
                "doctor_id": doctor_id,
                "doctor_name": doc_name,
                "speciality": speciality,
                "visit_type": visit_type,
                "date": date,
                "start_time": start_time,
                "duration": duration,
                "reason": reason,
            },
        })

        if not confirmed:
            return {
                "result": "cancelled_by_user",
                "message": "The patient decided not to proceed with this booking.",
            }

        # User confirmed! Call BookingService
        res = BookingService.book(
            db=db,
            patient_id=patient_id,
            doctor_id=doctor_id.strip(),
            speciality=speciality.strip(),
            visit_type=visit_type.strip(),
            date_val=d_val,
            start_time=t_val,
            role="patient",
            source="CHAT",
            reason=reason.strip(),
        )

        if not res.ok:
            return {
                "result": "refused",
                "reason_code": res.reason_code.value if res.reason_code else "REFUSED",
                "message": res.message,
            }

        return {
            "result": "booked",
            "appointment_id": res.appointment.id if res.appointment else None,
            "message": res.message,
            "summary": summary,
        }
    finally:
        db.close()

@tool
def cancel_appointment(
    appointment_id: str,
    reason: Optional[str] = None,
    config: RunnableConfig = None,
) -> Dict[str, Any]:
    """Cancel one of the current patient's upcoming appointments by ID."""
    patient_id = config.get("configurable", {}).get("patient_id") if config else None
    if not patient_id:
        return {"result": "error", "message": "Authentication required. No patient is logged in."}

    db = SessionLocal()
    try:
        appt = db.query(Appointment).filter(Appointment.id == appointment_id.strip()).first()
        if not appt:
            return {
                "result": "refused",
                "reason_code": "NOT_YOUR_APPOINTMENT",
                "message": "Appointment not found or not accessible.",
            }

        # Cross-patient security: verify appointment belongs to current patient
        if appt.patient_id != patient_id:
            return {
                "result": "refused",
                "reason_code": "NOT_YOUR_APPOINTMENT",
                "message": "Patients can only view or modify their own appointments.",
            }

        doc = db.query(Doctor).filter(Doctor.id == appt.doctor_id).first()
        doc_name = doc.name if doc else appt.doctor_id
        day_str = BookingService.get_day_abbr(appt.date)

        summary = f"Cancel your {appt.speciality} appointment with {doc_name} on {day_str} {appt.date.strftime('%d %b')} at {appt.start_time.strftime('%H:%M')}?"
        confirmed = interrupt({
            "action": "cancel",
            "summary": summary,
            "details": {
                "appointment_id": appt.id,
                "doctor_name": doc_name,
                "speciality": appt.speciality,
                "date": appt.date.isoformat(),
                "start_time": appt.start_time.strftime("%H:%M"),
            },
        })

        if not confirmed:
            return {
                "result": "cancelled_by_user",
                "message": "The patient decided not to proceed with cancelling this appointment.",
            }

        res = BookingService.cancel(
            db=db,
            appointment_id=appt.id,
            actor_role="patient",
            acting_patient_id=patient_id,
            reason=reason,
        )

        if not res.ok:
            if res.expected == "to_staff":
                return {
                    "result": "to_staff",
                    "reason_code": "INSIDE_2_HOURS",
                    "message": "Because this appointment starts in less than 2 hours, your cancellation request has been sent to Staff for approval. The appointment remains booked until approved.",
                }
            return {
                "result": "refused",
                "reason_code": res.reason_code.value if res.reason_code else "REFUSED",
                "message": res.message,
            }

        return {
            "result": "cancelled",
            "appointment_id": appt.id,
            "message": "Appointment cancelled successfully.",
        }
    finally:
        db.close()

@tool
def reschedule_appointment(
    appointment_id: str,
    new_date: str,
    new_start_time: str,
    new_doctor_id: Optional[str] = None,
    new_speciality: Optional[str] = None,
    config: RunnableConfig = None,
) -> Dict[str, Any]:
    """Reschedule an existing appointment for the current patient to a new date and time."""
    patient_id = config.get("configurable", {}).get("patient_id") if config else None
    if not patient_id:
        return {"result": "error", "message": "Authentication required. No patient is logged in."}

    db = SessionLocal()
    try:
        appt = db.query(Appointment).filter(Appointment.id == appointment_id.strip()).first()
        if not appt:
            return {
                "result": "refused",
                "reason_code": "NOT_YOUR_APPOINTMENT",
                "message": "Appointment not found or not accessible.",
            }

        # Ownership check
        if appt.patient_id != patient_id:
            return {
                "result": "refused",
                "reason_code": "NOT_YOUR_APPOINTMENT",
                "message": "Patients can only view or modify their own appointments.",
            }

        try:
            new_d_val = datetime.strptime(new_date.strip(), "%Y-%m-%d").date()
            t_parts = new_start_time.strip().split(":")
            new_t_val = dt_time(int(t_parts[0]), int(t_parts[1]))
            day_str = BookingService.get_day_abbr(new_d_val)
        except Exception:
            return {"result": "refused", "message": "Invalid new date or start_time format."}

        target_doc_id = new_doctor_id or appt.doctor_id
        target_spec = new_speciality or appt.speciality
        doc = db.query(Doctor).filter(Doctor.id == target_doc_id).first()
        doc_name = doc.name if doc else target_doc_id
        duration = 20 if appt.visit_type.lower() == "new" else 10

        summary = f"Reschedule your appointment to {doc_name}, {target_spec} {appt.visit_type.replace('_', '-')}, {day_str} {new_d_val.strftime('%d %b')}, {new_start_time} ({duration} min)?"
        confirmed = interrupt({
            "action": "reschedule",
            "summary": summary,
            "details": {
                "appointment_id": appt.id,
                "new_doctor_id": target_doc_id,
                "new_doctor_name": doc_name,
                "new_speciality": target_spec,
                "new_date": new_date,
                "new_start_time": new_start_time,
                "duration": duration,
            },
        })

        if not confirmed:
            return {
                "result": "cancelled_by_user",
                "message": "The patient decided not to proceed with rescheduling.",
            }

        res = BookingService.reschedule(
            db=db,
            appointment_id=appt.id,
            new_date=new_d_val,
            new_start_time=new_t_val,
            new_doctor_id=target_doc_id,
            new_speciality=target_spec,
            actor_role="patient",
            acting_patient_id=patient_id,
        )

        if not res.ok:
            if res.expected == "to_staff":
                return {
                    "result": "to_staff",
                    "reason_code": "INSIDE_2_HOURS",
                    "message": "Because this appointment starts in less than 2 hours, your reschedule request has been sent to Staff for approval.",
                }
            return {
                "result": "refused",
                "reason_code": res.reason_code.value if res.reason_code else "REFUSED",
                "message": res.message,
            }

        return {
            "result": "rescheduled",
            "appointment_id": res.appointment.id if res.appointment else None,
            "message": "Appointment rescheduled successfully.",
            "summary": summary,
        }
    finally:
        db.close()

ALL_TOOLS = [
    search_clinic_docs,
    list_doctors,
    find_slots,
    my_appointments,
    book_appointment,
    cancel_appointment,
    reschedule_appointment,
]
