"""Reason codes and error messages for NetraCare appointment booking rules.
Canonical codes matching Handout 1, data pack 1 stretch rules, data pack 4, and data pack 6.
"""
from enum import Enum

class ReasonCode(str, Enum):
    INVALID_START_TIME = "INVALID_START_TIME"
    IN_PAST = "IN_PAST"
    BEYOND_30_DAYS = "BEYOND_30_DAYS"
    CLINIC_CLOSED = "CLINIC_CLOSED"
    HOLIDAY = "HOLIDAY"
    OUTSIDE_SESSION = "OUTSIDE_SESSION"
    ENDS_AFTER_SESSION = "ENDS_AFTER_SESSION"
    DOCTOR_OFF = "DOCTOR_OFF"
    SURGERY_SESSION = "SURGERY_SESSION"
    SPECIALITY_MISMATCH = "SPECIALITY_MISMATCH"
    DOUBLE_BOOKED = "DOUBLE_BOOKED"
    ACTIVE_BOOKING_EXISTS = "ACTIVE_BOOKING_EXISTS"
    NO_PREVIOUS_VISIT = "NO_PREVIOUS_VISIT"
    FOLLOW_UP_DIFFERENT_DOCTOR = "FOLLOW_UP_DIFFERENT_DOCTOR"
    INSIDE_2_HOURS = "INSIDE_2_HOURS"
    NOT_YOUR_APPOINTMENT = "NOT_YOUR_APPOINTMENT"
    NOT_ACTIVE = "NOT_ACTIVE"
    DOCTOR_ON_LEAVE = "DOCTOR_ON_LEAVE"
    PATIENT_DETAILS_MISMATCH = "PATIENT_DETAILS_MISMATCH"
    RED_FLAG = "RED_FLAG"
    ACTIVE_WITH_DOCTOR_EXISTS = "ACTIVE_WITH_DOCTOR_EXISTS"

REASON_MESSAGES = {
    ReasonCode.INVALID_START_TIME: "Appointment start times must be on a 10-minute mark.",
    ReasonCode.IN_PAST: "Cannot book or reschedule to a date or time in the past.",
    ReasonCode.BEYOND_30_DAYS: "Bookings open only up to 30 days ahead.",
    ReasonCode.CLINIC_CLOSED: "The clinic is closed on Sundays.",
    ReasonCode.HOLIDAY: "The clinic is closed on this scheduled holiday.",
    ReasonCode.OUTSIDE_SESSION: "Outside clinic hours (AM session: 9 AM–1 PM, PM session: 2 PM–6 PM, closed 1–2 PM).",
    ReasonCode.ENDS_AFTER_SESSION: "Appointment duration would finish after the session ends (1 PM or 6 PM).",
    ReasonCode.DOCTOR_OFF: "The doctor is not scheduled at the clinic during this session.",
    ReasonCode.SURGERY_SESSION: "The doctor is scheduled for surgery during this session and is not taking OPD appointments.",
    ReasonCode.SPECIALITY_MISMATCH: "The selected doctor does not cover this speciality.",
    ReasonCode.DOUBLE_BOOKED: "The doctor already has an active appointment in this time slot.",
    ReasonCode.ACTIVE_BOOKING_EXISTS: "The patient already has an active booking in this speciality.",
    ReasonCode.NO_PREVIOUS_VISIT: "A follow-up requires a previous completed visit in this speciality.",
    ReasonCode.FOLLOW_UP_DIFFERENT_DOCTOR: "A follow-up consultation must be booked with the doctor who saw the patient last in this speciality.",
    ReasonCode.INSIDE_2_HOURS: "Cancellations or changes within 2 hours of the appointment must be handled by clinic staff.",
    ReasonCode.NOT_YOUR_APPOINTMENT: "Patients can only view or modify their own appointments.",
    ReasonCode.NOT_ACTIVE: "This appointment is already completed or cancelled.",
    ReasonCode.DOCTOR_ON_LEAVE: "The doctor is on approved leave for this session.",
    ReasonCode.PATIENT_DETAILS_MISMATCH: "The provided mobile number is already registered under a different name.",
    ReasonCode.RED_FLAG: "Urgent red-flag symptom detected. Emergency assistance required.",
    ReasonCode.ACTIVE_WITH_DOCTOR_EXISTS: "The patient already has an active booking with this doctor.",
}

