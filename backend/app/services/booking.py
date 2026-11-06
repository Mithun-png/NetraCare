"""Booking Service for NetraCare.
Implements the Single Rule Engine for all 4 channels (Web, Chat, Staff, MCP).
Strictly enforces the 16 clinic rules in deterministic priority order.
"""
from dataclasses import dataclass
from datetime import datetime, date as dt_date, time as dt_time, timedelta, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import CLINIC_TZ, get_clinic_now
from app.db.models import (
    Doctor,
    WeeklySchedule,
    Holiday,
    Patient,
    Appointment,
    Approval,
    DoctorLeave,
    AuditEvent,
)
from app.services.reasons import ReasonCode, REASON_MESSAGES

@dataclass
class BookingResult:
    ok: bool
    expected: str  # "allowed", "refused", "to_staff"
    reason_code: Optional[ReasonCode] = None
    message: str = ""
    appointment: Optional[Appointment] = None

@dataclass
class CancelResult:
    ok: bool
    expected: str  # "allowed", "refused", "to_staff"
    reason_code: Optional[ReasonCode] = None
    message: str = ""
    appointment: Optional[Appointment] = None

class BookingService:

    @staticmethod
    def get_day_abbr(d: dt_date) -> str:
        abbrs = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return abbrs[d.weekday()]

    @staticmethod
    def get_duration_minutes(visit_type: str) -> int:
        return 20 if visit_type.lower() == "new" else 10

    @staticmethod
    def add_minutes(t: dt_time, mins: int) -> dt_time:
        total = t.hour * 60 + t.minute + mins
        return dt_time(total // 60, total % 60)

    @classmethod
    def find_slots(
        cls,
        db: Session,
        doctor_id: str,
        date_val: dt_date,
        visit_type: str = "new",
        patient_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return all bookable start times for doctor, date, and visit_type."""
        now = get_clinic_now()

        # Clinic closed on Sunday
        if date_val.weekday() == 6:
            return []

        # Holiday check
        if db.query(Holiday).filter(Holiday.date == date_val).first():
            return []

        # Date range check: not in the past, within 30 days
        if date_val < now.date() or (date_val - now.date()).days > 30:
            return []

        day_abbr = cls.get_day_abbr(date_val)
        duration = cls.get_duration_minutes(visit_type)

        # Doctor leave check: if leave on this date, skip affected sessions
        doctor_leaves = (
            db.query(DoctorLeave)
            .filter(DoctorLeave.doctor_id == doctor_id, DoctorLeave.date == date_val)
            .all()
        )
        leave_sessions = {lv.session for lv in doctor_leaves}
        if "FULL" in leave_sessions:
            return []

        # Get schedules for this doctor on this weekday
        schedules = (
            db.query(WeeklySchedule)
            .filter(WeeklySchedule.doctor_id == doctor_id, WeeklySchedule.day == day_abbr)
            .all()
        )

        active_appts = (
            db.query(Appointment)
            .filter(
                Appointment.doctor_id == doctor_id,
                Appointment.date == date_val,
                Appointment.status.in_(["booked", "pending_staff", "proposed"]),
            )
            .all()
        )

        slots = []
        for sched in schedules:
            if sched.status != "OPD":
                continue
            if sched.session in leave_sessions:
                continue

            if sched.session == "AM":
                sess_start = dt_time(9, 0)
                sess_end = dt_time(13, 0)
            else:
                sess_start = dt_time(14, 0)
                sess_end = dt_time(18, 0)

            curr_m = sess_start.hour * 60 + sess_start.minute
            end_m = sess_end.hour * 60 + sess_end.minute

            while curr_m + duration <= end_m:
                cand_start = dt_time(curr_m // 60, curr_m % 60)
                cand_end = cls.add_minutes(cand_start, duration)

                # Skip if in past today
                cand_dt = datetime.combine(date_val, cand_start, tzinfo=CLINIC_TZ)
                if cand_dt < now:
                    curr_m += 10
                    continue

                # Overlap check with active appointments
                overlap = False
                for app in active_appts:
                    if cand_start < app.end_time and cand_end > app.start_time:
                        overlap = True
                        break

                if not overlap:
                    slots.append({
                        "start_time": cand_start.strftime("%H:%M"),
                        "end_time": cand_end.strftime("%H:%M"),
                        "doctor_id": doctor_id,
                        "date": date_val.isoformat(),
                        "visit_type": visit_type,
                    })

                curr_m += 10

        return slots

    @classmethod
    def book(
        cls,
        db: Session,
        patient_id: str,
        doctor_id: str,
        speciality: str,
        visit_type: str,
        date_val: dt_date,
        start_time: dt_time,
        role: str = "patient",
        source: str = "WEBSITE",
        reason: Optional[str] = None,
        ignore_appointment_id: Optional[str] = None,
    ) -> BookingResult:
        """Validate and book an appointment through the unified rule engine."""
        now = get_clinic_now()
        visit_type = visit_type.lower()

        # 1. Start time alignment: must be on a 10-minute mark
        if start_time.minute % 10 != 0 or start_time.second != 0:
            return BookingResult(
                ok=False,
                expected="refused",
                reason_code=ReasonCode.INVALID_START_TIME,
                message=REASON_MESSAGES[ReasonCode.INVALID_START_TIME],
            )

        # 2. In past check
        slot_dt = datetime.combine(date_val, start_time, tzinfo=CLINIC_TZ)
        if slot_dt < now:
            return BookingResult(
                ok=False,
                expected="refused",
                reason_code=ReasonCode.IN_PAST,
                message=REASON_MESSAGES[ReasonCode.IN_PAST],
            )

        # 3. Beyond 30 days check
        if (date_val - now.date()).days > 30:
            return BookingResult(
                ok=False,
                expected="refused",
                reason_code=ReasonCode.BEYOND_30_DAYS,
                message=REASON_MESSAGES[ReasonCode.BEYOND_30_DAYS],
            )

        # 4. Clinic closed (Sunday)
        if date_val.weekday() == 6:
            return BookingResult(
                ok=False,
                expected="refused",
                reason_code=ReasonCode.CLINIC_CLOSED,
                message=REASON_MESSAGES[ReasonCode.CLINIC_CLOSED],
            )

        # 5. Holiday check
        if db.query(Holiday).filter(Holiday.date == date_val).first():
            return BookingResult(
                ok=False,
                expected="refused",
                reason_code=ReasonCode.HOLIDAY,
                message=REASON_MESSAGES[ReasonCode.HOLIDAY],
            )

        # 6. Outside clinic hours / lunch check (AM: 9-13, Lunch: 13-14, PM: 14-18)
        is_am = dt_time(9, 0) <= start_time < dt_time(13, 0)
        is_pm = dt_time(14, 0) <= start_time < dt_time(18, 0)
        if not (is_am or is_pm):
            return BookingResult(
                ok=False,
                expected="refused",
                reason_code=ReasonCode.OUTSIDE_SESSION,
                message=REASON_MESSAGES[ReasonCode.OUTSIDE_SESSION],
            )

        # 7. Session duration and boundary check
        duration = cls.get_duration_minutes(visit_type)
        end_time = cls.add_minutes(start_time, duration)

        if is_am and end_time > dt_time(13, 0):
            return BookingResult(
                ok=False,
                expected="refused",
                reason_code=ReasonCode.ENDS_AFTER_SESSION,
                message=REASON_MESSAGES[ReasonCode.ENDS_AFTER_SESSION],
            )
        if is_pm and end_time > dt_time(18, 0):
            return BookingResult(
                ok=False,
                expected="refused",
                reason_code=ReasonCode.ENDS_AFTER_SESSION,
                message=REASON_MESSAGES[ReasonCode.ENDS_AFTER_SESSION],
            )

        # 8. Doctor weekly schedule check
        day_abbr = cls.get_day_abbr(date_val)
        session_kind = "AM" if is_am else "PM"
        sched = (
            db.query(WeeklySchedule)
            .filter(
                WeeklySchedule.doctor_id == doctor_id,
                WeeklySchedule.day == day_abbr,
                WeeklySchedule.session == session_kind,
            )
            .first()
        )
        if not sched or sched.status == "OFF":
            return BookingResult(
                ok=False,
                expected="refused",
                reason_code=ReasonCode.DOCTOR_OFF,
                message=REASON_MESSAGES[ReasonCode.DOCTOR_OFF],
            )
        if sched.status == "SURGERY":
            return BookingResult(
                ok=False,
                expected="refused",
                reason_code=ReasonCode.SURGERY_SESSION,
                message=REASON_MESSAGES[ReasonCode.SURGERY_SESSION],
            )

        # 8b. Doctor leave check
        doctor_leaves = (
            db.query(DoctorLeave)
            .filter(DoctorLeave.doctor_id == doctor_id, DoctorLeave.date == date_val)
            .all()
        )
        for lv in doctor_leaves:
            if lv.session == "FULL" or lv.session == session_kind:
                return BookingResult(
                    ok=False,
                    expected="refused",
                    reason_code=ReasonCode.DOCTOR_ON_LEAVE,
                    message=REASON_MESSAGES[ReasonCode.DOCTOR_ON_LEAVE],
                )

        # 9. Doctor speciality match
        doc = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc:
            return BookingResult(
                ok=False,
                expected="refused",
                reason_code=ReasonCode.SPECIALITY_MISMATCH,
                message=REASON_MESSAGES[ReasonCode.SPECIALITY_MISMATCH],
            )
        doc_specialities = [s.lower() for s in doc.get_speciality_list()]
        if speciality.lower() not in doc_specialities:
            return BookingResult(
                ok=False,
                expected="refused",
                reason_code=ReasonCode.SPECIALITY_MISMATCH,
                message=REASON_MESSAGES[ReasonCode.SPECIALITY_MISMATCH],
            )

        # 10. Patient active booking limit per speciality
        active_query = db.query(Appointment).filter(
            Appointment.patient_id == patient_id,
            func.lower(Appointment.speciality) == speciality.lower(),
            Appointment.status.in_(["booked", "pending_staff", "proposed"]),
        )
        if ignore_appointment_id:
            active_query = active_query.filter(Appointment.id != ignore_appointment_id)
        if active_query.first():
            return BookingResult(
                ok=False,
                expected="refused",
                reason_code=ReasonCode.ACTIVE_BOOKING_EXISTS,
                message=REASON_MESSAGES[ReasonCode.ACTIVE_BOOKING_EXISTS],
            )

        # 11. Follow-up rules
        if visit_type == "follow_up":
            completed_visits = (
                db.query(Appointment)
                .filter(
                    Appointment.patient_id == patient_id,
                    func.lower(Appointment.speciality) == speciality.lower(),
                    Appointment.status == "completed",
                )
                .order_by(Appointment.date.desc(), Appointment.start_time.desc())
                .all()
            )
            if not completed_visits:
                return BookingResult(
                    ok=False,
                    expected="refused",
                    reason_code=ReasonCode.NO_PREVIOUS_VISIT,
                    message=REASON_MESSAGES[ReasonCode.NO_PREVIOUS_VISIT],
                )
            last_visit = completed_visits[0]
            if last_visit.doctor_id != doctor_id:
                return BookingResult(
                    ok=False,
                    expected="refused",
                    reason_code=ReasonCode.FOLLOW_UP_DIFFERENT_DOCTOR,
                    message=REASON_MESSAGES[ReasonCode.FOLLOW_UP_DIFFERENT_DOCTOR],
                )

        # 12. Doctor double-booking / slot overlap check
        overlap_query = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.date == date_val,
            Appointment.status.in_(["booked", "pending_staff", "proposed"]),
        )
        if ignore_appointment_id:
            overlap_query = overlap_query.filter(Appointment.id != ignore_appointment_id)

        for app in overlap_query.all():
            if start_time < app.end_time and end_time > app.start_time:
                return BookingResult(
                    ok=False,
                    expected="refused",
                    reason_code=ReasonCode.DOUBLE_BOOKED,
                    message=REASON_MESSAGES[ReasonCode.DOUBLE_BOOKED],
                )

        # All checks passed! Create the appointment
        appt_id = f"A{int(datetime.now(timezone.utc).timestamp() * 1000) % 1000000:06d}"
        new_appt = Appointment(
            id=appt_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
            speciality=speciality,
            visit_type=visit_type,
            mode="IN_PERSON",
            status="booked",
            date=date_val,
            start_time=start_time,
            end_time=end_time,
            source=source,
            reason=reason,
        )
        db.add(new_appt)

        # Audit event
        audit = AuditEvent(
            actor_id=patient_id if role == "patient" else "STAFF",
            actor_kind=role.upper(),
            action="BOOK",
            target=f"Appointment {appt_id}",
            result="allowed",
        )
        db.add(audit)
        db.commit()
        db.refresh(new_appt)

        return BookingResult(
            ok=True,
            expected="allowed",
            reason_code=None,
            message="Appointment booked successfully.",
            appointment=new_appt,
        )

    @classmethod
    def cancel(
        cls,
        db: Session,
        appointment_id: str,
        actor_role: str = "patient",
        acting_patient_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> CancelResult:
        """Cancel an appointment according to the 2-hour window and role rules."""
        now = get_clinic_now()
        appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt:
            return CancelResult(
                ok=False,
                expected="refused",
                reason_code=ReasonCode.NOT_ACTIVE,
                message="Appointment not found.",
            )

        # 1. Status check: must not be already cancelled or completed
        if appt.status in ["cancelled", "completed"]:
            return CancelResult(
                ok=False,
                expected="refused",
                reason_code=ReasonCode.NOT_ACTIVE,
                message=REASON_MESSAGES[ReasonCode.NOT_ACTIVE],
            )

        # 2. Ownership check
        if actor_role == "patient" and acting_patient_id and appt.patient_id != acting_patient_id:
            return CancelResult(
                ok=False,
                expected="refused",
                reason_code=ReasonCode.NOT_YOUR_APPOINTMENT,
                message=REASON_MESSAGES[ReasonCode.NOT_YOUR_APPOINTMENT],
            )

        # 3. 2-hour window check
        appt_dt = datetime.combine(appt.date, appt.start_time, tzinfo=CLINIC_TZ)
        time_diff = (appt_dt - now).total_seconds()

        if time_diff < 2 * 3600:
            if actor_role == "patient":
                # Routed to staff for approval
                approval = Approval(
                    kind="LATE_CANCEL",
                    appointment_id=appt.id,
                    payload=f'{{"reason": "{reason or ""}"}}',
                    status="PENDING",
                )
                db.add(approval)
                appt.status = "pending_staff"
                db.commit()
                return CancelResult(
                    ok=False,
                    expected="to_staff",
                    reason_code=ReasonCode.INSIDE_2_HOURS,
                    message=REASON_MESSAGES[ReasonCode.INSIDE_2_HOURS],
                    appointment=appt,
                )
            else:
                # Staff can cancel inside 2 hours
                appt.status = "cancelled"
                audit = AuditEvent(
                    actor_id="STAFF",
                    actor_kind="STAFF",
                    action="CANCEL",
                    target=f"Appointment {appt.id}",
                    result="allowed",
                    override_reason=reason or "Staff override inside 2 hours",
                )
                db.add(audit)
                db.commit()
                return CancelResult(
                    ok=True,
                    expected="allowed",
                    reason_code=None,
                    message="Appointment cancelled by staff.",
                    appointment=appt,
                )
        else:
            # Outside 2 hours: cancelled immediately
            appt.status = "cancelled"
            audit = AuditEvent(
                actor_id=acting_patient_id if actor_role == "patient" else "STAFF",
                actor_kind=actor_role.upper(),
                action="CANCEL",
                target=f"Appointment {appt.id}",
                result="allowed",
            )
            db.add(audit)
            db.commit()
            return CancelResult(
                ok=True,
                expected="allowed",
                reason_code=None,
                message="Appointment cancelled successfully.",
                appointment=appt,
            )

    @classmethod
    def reschedule(
        cls,
        db: Session,
        appointment_id: str,
        new_date: dt_date,
        new_start_time: dt_time,
        new_doctor_id: Optional[str] = None,
        new_speciality: Optional[str] = None,
        actor_role: str = "patient",
        acting_patient_id: Optional[str] = None,
    ) -> BookingResult:
        """Reschedule an existing appointment: cancel old + book new in one atomic transaction."""
        now = get_clinic_now()
        appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appt or appt.status in ["cancelled", "completed"]:
            return BookingResult(
                ok=False,
                expected="refused",
                reason_code=ReasonCode.NOT_ACTIVE,
                message=REASON_MESSAGES[ReasonCode.NOT_ACTIVE],
            )

        if actor_role == "patient" and acting_patient_id and appt.patient_id != acting_patient_id:
            return BookingResult(
                ok=False,
                expected="refused",
                reason_code=ReasonCode.NOT_YOUR_APPOINTMENT,
                message=REASON_MESSAGES[ReasonCode.NOT_YOUR_APPOINTMENT],
            )

        # Check 2-hour window on old appointment
        appt_dt = datetime.combine(appt.date, appt.start_time, tzinfo=CLINIC_TZ)
        time_diff = (appt_dt - now).total_seconds()
        if time_diff < 2 * 3600 and actor_role == "patient":
            approval = Approval(
                kind="LATE_RESCHEDULE",
                appointment_id=appt.id,
                payload=f'{{"new_date": "{new_date}", "new_start_time": "{new_start_time}"}}',
                status="PENDING",
            )
            db.add(approval)
            appt.status = "pending_staff"
            db.commit()
            return BookingResult(
                ok=False,
                expected="to_staff",
                reason_code=ReasonCode.INSIDE_2_HOURS,
                message=REASON_MESSAGES[ReasonCode.INSIDE_2_HOURS],
                appointment=appt,
            )

        # Validate the new slot first, ignoring the current appointment for overlap and active booking checks
        target_doctor_id = new_doctor_id or appt.doctor_id
        target_speciality = new_speciality or appt.speciality

        val_result = cls.book(
            db=db,
            patient_id=appt.patient_id,
            doctor_id=target_doctor_id,
            speciality=target_speciality,
            visit_type=appt.visit_type,
            date_val=new_date,
            start_time=new_start_time,
            role=actor_role,
            source=appt.source,
            ignore_appointment_id=appt.id,
        )

        if not val_result.ok:
            # New slot is invalid; old appointment remains unchanged!
            return val_result

        # Success! In one transaction: cancel old appointment and link new one
        appt.status = "cancelled"
        if val_result.appointment:
            val_result.appointment.rescheduled_from = appt.id

        db.commit()
        return val_result

    @classmethod
    def apply_doctor_leave(
        cls,
        db: Session,
        doctor_id: str,
        date_val: dt_date,
        session_kind: str = "FULL",  # "AM", "PM", "FULL"
    ) -> Dict[str, Any]:
        """Apply doctor leave, cancel affected appointments, and propose rebookings per R7."""
        doc = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doc:
            raise ValueError(f"Doctor {doctor_id} not found.")

        # Save leave
        leave = DoctorLeave(
            doctor_id=doctor_id,
            date=date_val,
            session=session_kind,
        )
        db.add(leave)
        db.flush()

        # Find affected active appointments
        query = (
            db.query(Appointment)
            .filter(
                Appointment.doctor_id == doctor_id,
                Appointment.date == date_val,
                Appointment.status.in_(["booked", "pending_staff"]),
            )
        )
        if session_kind == "AM":
            query = query.filter(Appointment.start_time < dt_time(13, 0))
        elif session_kind == "PM":
            query = query.filter(Appointment.start_time >= dt_time(14, 0))

        affected_appts = query.order_by(Appointment.start_time.asc()).all()

        all_doctors = db.query(Doctor).all()
        proposals = []

        for appt in affected_appts:
            # 1. Cancel original appointment
            appt.status = "cancelled"
            appt.doctor_note = f"Moved because Dr. {doc.name} is on leave"

            # 2. Find replacement slot
            # Rule for 'new': earliest free slot at or after original start time, across all doctors who cover that speciality
            # Tie: original doctor first, then lower doctor ID
            # Rule for 'follow_up': same doctor, next free slot
            if appt.visit_type == "new":
                candidate_docs = [
                    d for d in all_doctors
                    if appt.speciality.lower() in [s.lower() for s in d.get_speciality_list()]
                ]
            else:
                candidate_docs = [doc]

            # Search from date_val up to date_val + 30 days
            found_proposal = None
            for day_offset in range(31):
                target_date = date_val + timedelta(days=day_offset)
                # Check Sunday or holiday
                if target_date.weekday() == 6:
                    continue
                if db.query(Holiday).filter(Holiday.date == target_date).first():
                    continue

                # Collect available slots across candidate doctors on this date
                day_candidates = []
                for c_doc in candidate_docs:
                    slots = cls.find_slots(
                        db=db,
                        doctor_id=c_doc.id,
                        date_val=target_date,
                        visit_type=appt.visit_type,
                        patient_id=appt.patient_id,
                    )
                    for slot in slots:
                        slot_start = datetime.strptime(slot["start_time"], "%H:%M").time()
                        if target_date == date_val and slot_start < appt.start_time:
                            continue
                        day_candidates.append({
                            "doctor": c_doc,
                            "date": target_date,
                            "start_time": slot_start,
                            "end_time": datetime.strptime(slot["end_time"], "%H:%M").time(),
                        })

                if day_candidates:
                    # Sort candidates by:
                    # 1. start_time asc
                    # 2. is_original_doctor desc (0 for original, 1 for others)
                    # 3. doctor.id asc
                    day_candidates.sort(
                        key=lambda x: (
                            x["start_time"],
                            0 if x["doctor"].id == appt.doctor_id else 1,
                            x["doctor"].id,
                        )
                    )
                    best = day_candidates[0]
                    # Create proposal appointment holding the slot
                    prop_id = f"A{int(datetime.now(timezone.utc).timestamp() * 1000) % 1000000:06d}"
                    prop_appt = Appointment(
                        id=prop_id,
                        patient_id=appt.patient_id,
                        doctor_id=best["doctor"].id,
                        speciality=appt.speciality,
                        visit_type=appt.visit_type,
                        mode=appt.mode,
                        status="proposed",
                        date=best["date"],
                        start_time=best["start_time"],
                        end_time=best["end_time"],
                        source="STAFF",
                        reason=f"Moved because Dr. {doc.name} is on leave",
                        rescheduled_from=appt.id,
                    )
                    db.add(prop_appt)
                    db.flush()
                    found_proposal = prop_appt
                    proposals.append({
                        "original_appointment_id": appt.id,
                        "proposed_appointment_id": prop_id,
                        "patient_id": appt.patient_id,
                        "doctor_id": best["doctor"].id,
                        "doctor_name": best["doctor"].name,
                        "speciality": appt.speciality,
                        "visit_type": appt.visit_type,
                        "date": best["date"].isoformat(),
                        "start_time": best["start_time"].strftime("%H:%M"),
                        "end_time": best["end_time"].strftime("%H:%M"),
                    })
                    break

            if not found_proposal:
                proposals.append({
                    "original_appointment_id": appt.id,
                    "proposed_appointment_id": None,
                    "patient_id": appt.patient_id,
                    "note": "No slot: call the patient",
                })

        db.commit()
        return {
            "doctor_id": doctor_id,
            "date": date_val.isoformat(),
            "session": session_kind,
            "affected_count": len(affected_appts),
            "proposals": proposals,
        }
