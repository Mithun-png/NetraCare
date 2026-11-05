---
name: lasik-suitability-intake
description: Collects a patient's answers to NetraCare's LASIK pre-assessment questions before booking a LASIK suitability check with Dr. Fatima Khan. Use when a patient wants LASIK or laser vision correction, or asks whether they are suitable for it.
---

# LASIK suitability intake

Only Dr. Fatima Khan can decide whether someone is suitable for LASIK, at a suitability check.
This skill collects the patient's answers so Dr. Khan has them before the visit. It never decides anything.

## Steps

1. Say that only Dr. Fatima Khan can decide at a suitability check, and that you can ask a few questions to save time at the visit. Ask if they'd like that.
   If they don't, offer to find a Refractive slot with Dr. Khan instead.
2. Read `questions.md` with `read_skill_file`. Ask the questions **one at a time**, in order, in plain words.
   Accept "I don't know" or "skip" for any question and move on.
3. If the patient says they are under 18, stop the questions. Share this line from procedures.md:
   "LASIK at NetraCare is only for adults over 18 whose glasses power has been stable for at least a year."
   Offer a General appointment for their glasses instead (Paediatric if under 16).
4. When the questions are done, read the answers back as a short list and ask the patient to confirm them.
5. Share the preparation the clinic asks for (from clinic_policy_faq.md > Contact lenses and procedures.md > LASIK):
   stop soft contact lenses 1 week before the suitability check and rigid (RGP) lenses 3 weeks before;
   the check takes about 1½ hours; it costs ₹2,000 (indicative).
6. Offer to find a Refractive slot with Dr. Fatima Khan. Pick the date so the patient can stop their lenses in time.
   Book it with `book_appointment`, reason "LASIK suitability check", and the confirmed answers as `intake_notes`.

## Rules

- Never say or hint that the patient is or isn't suitable, is a good or bad candidate, or will or won't be able to have LASIK. That includes "you should be fine" and "that may be a problem".
- Never explain what an answer means. Just record it.
- Record the patient's answers in their own words. Don't add anything.
- Give the source as: Skill: lasik-suitability-intake.
