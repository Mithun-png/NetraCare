# NetraCare data pack 4

Synthetic data for Iteration 4. NetraCare is fictional; no real people or patients.
Keep using data packs 1, 2 and 3. This pack updates one document and adds test scenarios for the booking agent and doctor leave.

## Files
| File | What it holds |
|---|---|
| documents/clinic_policy_faq.md | Replaces the data pack 3 copy. New sections: "Booking through the chat assistant" and "If your doctor is on leave". "Cancelling or changing an appointment" and "What the assistant can and cannot do" are updated |
| agent_scenarios.csv | 24 chat scenarios for the booking agent, with the expected result (stretch goal; iteration 5 reuses it) |
| leave_scenarios.csv | 5 doctor-leave cases with the rebooking your code should propose (stretch goal) |

## The updated document
Copy `documents/clinic_policy_faq.md` over your data pack 3 copy and rebuild your index (`python build_index.py`).
The other two documents are unchanged. The data pack 3 `questions.csv` still works.

## New reason code
| Code | Meaning |
|---|---|
| DOCTOR_ON_LEAVE | The doctor has marked leave for that session |

All the reason codes from data pack 1 still apply. `INSIDE_2_HOURS` now means "sent to Staff for approval" for a patient's cancel or reschedule.

## Stretch goal: scenario files with a fixed clock
Both CSV files use the same fixed clock and seed as the data pack 1 stretch goal, so the expected answers never change:

- Set `CLINIC_NOW = 2026-11-02 10:00` (a Monday).
- Start every scenario from a fresh database: data pack 1, `stretch/appointments_seed.csv` and data pack 2 `past_visits.csv`.
- Log in as the patient in `patient_id`. Do any `setup` step first.

### agent_scenarios.csv
| Column | Meaning |
|---|---|
| scenario_id | AS01 to AS24 |
| patient_id, patient_name | Who is logged in |
| setup | Anything to do before the chat starts (empty means nothing) |
| turns | What the patient does, in order, separated by ` \|\| `. Plain text is a typed chat message. `[confirm]` presses Confirm and `[decline]` presses No on the confirmation card. If no confirmation is waiting, skip that step |
| expected_tools | Tools that must be called, in order. Other tools, such as `my_appointments` or `list_doctors`, may be called as well. Empty means no booking tool should succeed |
| expected_result | `booked`, `rescheduled`, `cancelled`, `to_staff`, `no_change`, `emergency`, `answered` or `idk` |
| expected_appointment | What the database should hold afterwards: `doctor speciality visit_type date start`, or an appointment ID and its state |
| reason_code | The rule the request runs into, if the agent tries it. The agent may spot it from `find_slots` and never call the booking tool; either way the database must not change |
| must_say | What the reply must get across. Wording can differ |

Notes:
- "Today" is Monday 2 November 2026, 10:00. "Tomorrow" is Tuesday 3 November. The 30-day window ends on 2 December.
- Where the patient says "the earliest time", the agent should offer the first free slot.
- AS06 starts at 11:00 today, inside 2 hours, so it goes to Staff. AS07 starts at 12:30, 2.5 hours away, so it is cancelled.
- AS13 and AS14 are red flags. The agent must not book, whatever else the message asks.

### leave_scenarios.csv
Each `leave_id` is one action: the doctor marks leave for `leave_date` and `leave_session` (`AM`, `PM` or `FULL` day).
Every row is one affected appointment and the rebooking your code should propose, using the rules in the handout:

- A new consultation goes to the earliest free slot, at or after the original start time, with any doctor who covers the same speciality.
- A follow-up stays with the same doctor.
- If two doctors are free at the same earliest time, the original doctor wins, then the lower doctor ID.
- Proposals are made in order of the original start time, and each one holds its slot.
