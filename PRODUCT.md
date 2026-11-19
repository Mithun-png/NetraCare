# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
- **Patients (Primary Audience):** Individuals seeking ophthalmic care, routine eye examinations, subspecialty consultations (cataract, refractive/LASIK, glaucoma, retina, cornea, paediatric strabismus), and procedure preparation. They need rapid symptom checking, transparent pricing/prep information, and friction-free appointment scheduling/rescheduling/cancellation.
- **Front-Desk / Clinic Staff:** Receptionists and clinic coordinators managing daily patient flow, handling walk-in bookings, viewing cross-doctor schedule rosters, and triaging emergency red-flag cases flagged by AI or external channels.
- **Doctors / Specialists:** 5 ophthalmic specialists (Dr. Anita Roy, Dr. Suresh Raman, Dr. Priya Nair, Dr. Vikram Menon, Dr. Fatima Khan) viewing their daily appointment rosters, patient details, and structured pre-assessment clinical intake notes (e.g. LASIK suitability).

## Product Purpose
NetraCare is an AI-powered front desk and clinical care coordination platform for ophthalmic practices. It automates patient scheduling, pre-visit intake, clinic FAQ/RAG retrieval, and partner laboratory inquiries while maintaining clinical safety as an uncompromised priority. Success is defined by zero missed red-flag emergencies, zero scheduling conflicts or double-bookings, accurate subspecialty routing, and high patient self-service throughput.

## Positioning
Clinical safety-first ophthalmic intelligence. Unlike generic conversational scheduling bots that treat booking purely as a calendar lookup, NetraCare enforces deterministic clinical protocols: acute eye emergencies trigger immediate emergency instructions and staff escalation; paediatric patients (<16 years) are strictly restricted to the paediatric ophthalmologist; procedures adhere to doctor subspecialties; and lab questions reflect verified partner data with clear citations and zero medical prescription.

## Operating Context
- **Clinical Environment:** Multi-doctor ophthalmic outpatient clinic with high patient volume, specialized diagnostic equipment, pre-op evaluation requirements, and strict dilation drop observation times (30–45 mins).
- **Access Channels:** Patient web portal with conversational AI assistant, staff operational dashboard, doctor schedule portal, and external AI agents connecting via Model Context Protocol (MCP) streamable HTTP.
- **Clinic Timings:** Monday through Saturday, split into Morning (09:00–13:00) and Evening (16:30–20:00) sessions, with Sunday closures and clinic holidays.

## Capabilities and Constraints
- **Clinical Triage & Red-Flag Safeguards:** Instant detection of 5 acute ophthalmic emergency categories (sudden vision loss, chemical splash, penetrating trauma, severe acute eye pain, flashes/curtain). Emits emergency instructions immediately, blocks automated booking, and creates an urgent case record for staff.
- **Specialty & Paediatric Routing:** Patients under 16 years of age (e.g. Divya Pillai) are restricted strictly to Dr. Vikram Menon (Paediatrics & Strabismus) with mandatory adult/guardian presence.
- **Unified Booking Engine (`BookingService`):** Atomic slot reservation, 15-minute slot granularity, 30-day booking horizon, reason tracking, cancellation/rescheduling with audit trail, and zero double-booking guarantee across Web, Chat, Staff, and MCP.
- **RAG Clinic Document Search:** Hybrid vector (ChromaDB) and BM25 keyword retrieval over 5 clinic documents with strict refusal (`IDK_RESPONSE`) on out-of-scope queries and zero hallucinated medical advice.
- **Agent Clinical Skills:** Modular front-matter skill definitions (`cataract-surgery-care`, `lasik-suitability-intake`, `prepare-for-visit`, `children-visit`) with strict filesystem traversal protection and automated skill citations.
- **Model Context Protocol (MCP):**
  - NetraCare MCP server (`:8001`) exposing `find_slots` and `book_appointment` with patient identity checks.
  - CityCare Lab partner MCP client (`:8002`) fetching test preps/costs with partner attribution and offline fallback.
- **Deterministic Offline Runtimes:** Full offline execution and evaluation mode without mandatory external API keys; optional Gemini LLM integration for open-ended conversation.

## Brand Commitments
- **Brand Name:** NetraCare Eye Clinic (NetraCare).
- **Tone & Voice:** Clinically reassuring, precise, empathetic, authoritative, and unambiguous. Never dismissive of patient distress; never prescriptive or diagnostic.
- **Visual Identity (Incumbent):** Deep clinic teal (`--accent: #0d6e7a`), soft sage/cyan tints (`--accent-soft: #e2f1f2`), clean clinic whites (`--surface: #ffffff`), surgical warm gold accents (`--surgery: #f4e6d4`), and clean typographic hierarchy (`Bricolage Grotesque` display, `Source Sans 3` body, `IBM Plex Mono` code/times).

## Evidence on Hand
- Seed clinic database (`netracare.db`) with 5 doctors, weekly clinic schedules, holiday calendars, existing appointments, and patient profiles.
- Verified test suites and golden datasets: `test_iteration6.py` (79 passing tests), `mcp_scenarios.csv` (12 scenarios), `lab_questions.csv` (9 partner questions), `skill_triggers.csv` (16 triggers), `final_demo_scenarios.csv` (16 end-to-end scenarios).
- 5 clinic source documents in `data/docs/`: `cataract_faq.md`, `lasik_criteria.md`, `insurance_billing.md`, `clinic_hours.md`, `pre_visit_prep.md`.

## Product Principles
1. **Safety Over Conversion:** A patient presenting acute emergency symptoms must never be guided down a routine booking funnel; immediate emergency guidance and human staff notification take precedence over everything.
2. **Deterministic Clinical Integrity:** Doctor schedules, subspecialty bounds, age gates, session timings, and cancellation rules are enforced deterministically by code, never left to LLM guesswork.
3. **Transparent Attribution:** When providing laboratory pricing or specialized clinical care guidance, the system visibly cites its authoritative source (e.g. `Source: CityCare Lab (partner)`, `Skill: cataract-surgery-care`).
4. **Frictionless Accessibility:** Clean, legible, high-contrast interfaces designed for patients who may be experiencing visual impairment or post-dilation blur.
5. **Multi-Channel Consistency:** The patient web app, front desk staff view, and external MCP agents interact with the exact same underlying clinical truth and booking service.

## Accessibility & Inclusion
- High contrast text (`#14212b` ink on `#ffffff` surface, compliant with WCAG AA/AAA).
- Legible typography sizing with distinct sans-serif body type and generous line-height for patients with visual impairment, cataracts, or dilated pupils.
- Semantic HTML, keyboard navigability, clear focus rings, and explicit status badges for appointment and emergency states.

