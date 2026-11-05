# NetraCare data pack 2

Synthetic data for Iteration 2. NetraCare is fictional; no real people or patients.
Keep using data pack 1. This pack adds to it and uses the same IDs (doctors D1-D5, patients P01-P25).

## Files
| File | What it holds |
|---|---|
| past_visits.csv | 27 completed visits for 13 patients, across all 5 doctors, each with the reason the patient gave and the doctor's note |
| patient_profiles.csv | General health and allergies for all 25 patients |
| reason_samples.csv | 35 appointment reasons labelled `yes` or `no` for red flag, to check your red-flag classifier |

## past_visits.csv
- Load each row as an appointment with `status = completed`, plus its `reason` and `doctor_note`.
- All dates are in the past, so they never block a new booking. They do count for follow-ups:
  for example, Asha Verma (P01) can book a Retina follow-up with Dr. Shah (D3).
- `visit_type` is `new` (20 min) or `follow_up` (10 min), as in data pack 1.
- Doctor notes are written the way doctors write them, with diagnoses and short forms:
  OD = right eye, OS = left eye, VA = visual acuity, IOP = eye pressure, NPDR = non-proliferative diabetic retinopathy,
  IOL = lens implant, OCT = retinal scan, RGP = rigid contact lens.
- Patients with the most history for testing summaries: P01 Asha Verma, P03 Lakshmi Nair, P13 Fatima Begum (3 visits each, 2 doctors).

## reason_samples.csv
- `expected_red_flag` is `yes` or `no`. For `yes` rows, `category` is the brief's red-flag example it belongs to:
  `sudden_vision_loss`, `curtain_or_shadow`, `floaters_or_flashes`, `chemical_or_injury` or `severe_pain_headache_haloes`.
- 20 rows are red flags and 15 are not.
- S16 and S17 mention red-flag words but are not red flags ("no sudden loss", "gradual").
- S31 to S35 describe red flags in different words from the brief's examples.
- Use these rows for extra testing beyond the handout checks.
- A `no` row flagged as `yes` is a false alarm. It is safe, but tune your prompt to reduce it.
