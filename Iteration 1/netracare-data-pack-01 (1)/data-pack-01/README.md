# NetraCare data pack 1

Synthetic data for Handout 1. NetraCare is fictional; no real people or patients.

## How to use
Load the four files below into your database when the app starts. Bookings are made through your app, using today's real date and time.

## Files
| File | What it holds |
|---|---|
| doctors.csv | 5 doctors. `specialities` is separated by `;` |
| weekly_schedule.csv | One row per doctor, day and session (AM 09:00-13:00, PM 14:00-18:00). `status` is OPD (bookable), SURGERY or OFF |
| holidays.csv | Clinic holidays up to the end of 2027. No bookings on these dates |
| patients.csv | 25 patients. Patients log in with mobile + name |

## Stretch goal: automated rule tests (folder `stretch/`)
Only if you want to go further. These files use a fixed date so everyone's tests give the same answers:
set `CLINIC_NOW = 2026-11-02 10:00` in your config (a Monday) and use it instead of the real clock while testing.

| File | What it holds |
|---|---|
| stretch/appointments_seed.csv | Past visits (`completed`), a `cancelled` one and upcoming `booked` ones. `visit_type` is `new` (20 min) or `follow_up` (10 min) |
| stretch/rule_tests.csv | 38 actions with the expected result |

### Running rule_tests.csv
- Start every test from a fresh copy of the seed data. Tests do not depend on each other.
- Each test breaks at most one rule, so the reason is never ambiguous.
- `action` is book, cancel or reschedule. `role` is patient or staff. `acting_patient_id` is the logged-in patient.
- `expected` is `allowed`, `refused` or `to_staff`. `to_staff` means the request goes to Staff for approval; if you did not build the Staff approval queue, treat it as refused with "Please contact Staff".
- Return the `reason_code` exactly as written, so your tests can compare it.

## Reason codes (for the stretch goal)
| Code | Meaning |
|---|---|
| INVALID_START_TIME | Start time not on a 10-minute mark |
| IN_PAST | Before the clinic clock |
| BEYOND_30_DAYS | More than 30 days ahead |
| CLINIC_CLOSED | Sunday |
| HOLIDAY | Listed in holidays.csv |
| OUTSIDE_SESSION | Before 9 AM, during lunch 1-2 PM, or after 6 PM |
| ENDS_AFTER_SESSION | Would finish after 1 PM (AM) or 6 PM (PM) |
| DOCTOR_OFF | Doctor not at the clinic that session |
| SURGERY_SESSION | Doctor is operating that session |
| SPECIALITY_MISMATCH | Doctor does not cover that speciality |
| DOUBLE_BOOKED | Overlaps another booked appointment with that doctor |
| ACTIVE_BOOKING_EXISTS | Patient already has a booked appointment in that speciality |
| NO_PREVIOUS_VISIT | Follow-up asked for, but the patient has no completed visit in that speciality |
| FOLLOW_UP_DIFFERENT_DOCTOR | Follow-up must be with the doctor who saw the patient last in that speciality |
| INSIDE_2_HOURS | Patient cancel or reschedule less than 2 hours before the appointment; goes to Staff |
| NOT_YOUR_APPOINTMENT | A patient acting on someone else's appointment |
| NOT_ACTIVE | Appointment is already cancelled or completed |
