"""SQLAlchemy models for NetraCare.
Compatible with SQLite and PostgreSQL.
"""
from datetime import datetime, date as dt_date, time as dt_time, timezone
import json
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    Date,
    Time,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def utc_now():
    return datetime.now(timezone.utc)

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(String(10), primary_key=True)  # e.g. D1, D2
    name = Column(String(100), nullable=False)
    specialities = Column(String(255), nullable=False)  # Semicolon-separated, e.g. "Cataract;General"
    active = Column(Boolean, default=True, nullable=False)

    schedules = relationship("WeeklySchedule", back_populates="doctor", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="doctor")

    def get_speciality_list(self) -> list[str]:
        return [s.strip() for s in self.specialities.split(";") if s.strip()]


class WeeklySchedule(Base):
    __tablename__ = "weekly_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doctor_id = Column(String(10), ForeignKey("doctors.id"), nullable=False)
    day = Column(String(3), nullable=False)  # Mon, Tue, Wed, Thu, Fri, Sat
    session = Column(String(2), nullable=False)  # AM, PM
    status = Column(String(10), nullable=False)  # OPD, SURGERY, OFF

    doctor = relationship("Doctor", back_populates="schedules")


class Holiday(Base):
    __tablename__ = "holidays"

    date = Column(Date, primary_key=True)
    name = Column(String(100), nullable=False)


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String(10), primary_key=True)  # e.g. P01
    name = Column(String(100), nullable=False)
    mobile = Column(String(20), unique=True, nullable=False, index=True)
    year_of_birth = Column(Integer, nullable=True)
    allergies = Column(Text, nullable=True)
    chronic_conditions = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    appointments = relationship("Appointment", back_populates="patient")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String(20), primary_key=True)  # e.g. A001, A101
    patient_id = Column(String(10), ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(String(10), ForeignKey("doctors.id"), nullable=False, index=True)
    speciality = Column(String(50), nullable=False)
    visit_type = Column(String(20), nullable=False)  # new, follow_up
    mode = Column(String(20), default="IN_PERSON", nullable=False)  # IN_PERSON, VIRTUAL
    status = Column(String(20), nullable=False)  # booked, pending_staff, cancelled, completed, no_show
    date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    source = Column(String(20), default="WEBSITE", nullable=False)  # WEBSITE, CHAT, STAFF, MCP
    reason = Column(Text, nullable=True)
    doctor_note = Column(Text, nullable=True)
    rescheduled_from = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")


class UrgentCase(Base):
    __tablename__ = "urgent_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(20), default="WEBSITE", nullable=False)
    summary = Column(Text, nullable=False)
    patient_id = Column(String(10), ForeignKey("patients.id"), nullable=True)
    draft_context = Column(Text, nullable=True)  # JSON-encoded draft booking
    status = Column(String(10), default="OPEN", nullable=False)  # OPEN, SEEN
    seen_by = Column(String(50), nullable=True)
    seen_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    kind = Column(String(30), nullable=False)  # LATE_CANCEL, LATE_RESCHEDULE
    appointment_id = Column(String(20), ForeignKey("appointments.id"), nullable=False)
    payload = Column(Text, nullable=False)  # JSON-encoded request info
    status = Column(String(20), default="PENDING", nullable=False)  # PENDING, APPROVED, REJECTED
    decided_by = Column(String(50), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_id = Column(String(50), nullable=True)
    actor_kind = Column(String(20), nullable=False)  # USER, PATIENT, DOCTOR, STAFF, MCP_PARTNER
    action = Column(String(50), nullable=False)
    target = Column(String(100), nullable=False)
    result = Column(String(50), nullable=False)  # allowed, refused, reason code
    override_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
