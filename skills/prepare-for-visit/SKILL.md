---
name: prepare-for-visit
description: Builds a personal checklist for a patient's next NetraCare appointment, using their booking and the speciality. Use when a patient asks what to bring, what to do before their appointment, how long it will take, or how to get ready for their visit.
---

# Prepare for your visit

Turns the patient's next booked appointment into a short, personal checklist.

## Steps

1. Call `my_appointments` and pick the patient's next booked appointment.
   If they have more than one, ask which one. If they have none, say so and offer to help book.
2. Read `checklists.md` with `read_skill_file`.
3. Build the checklist in this order:
   - **When and who:** date, time, doctor and speciality. "Please arrive 15 minutes early."
   - **Bring:** the "Every visit" list, plus the items for this speciality.
   - **Before:** the speciality's "Before" lines.
   - **Afterwards:** the speciality's "Afterwards" lines.
   - **Changes:** "You can cancel or change this appointment until 2 hours before it starts. After that, please contact Staff."
4. Keep it to about 10 short lines. Leave out anything that doesn't apply.

## Rules

- Don't guess which tests the doctor will do. Say "if your doctor uses dilating drops" or "if you have", not "you will".
- Don't add anything that isn't in `checklists.md`.
- For a child under 16, include the "Children" lines.
- Give the sources as: Skill: prepare-for-visit, clinic_policy_faq.md.
