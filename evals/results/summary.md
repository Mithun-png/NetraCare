# NetraCare Evaluation Report (Iteration 5)

**Run Details:**
- **Date:** 2026-11-06 19:30:37
- **Git Commit:** `b63ca0c`
- **Dataset Size:** `small`
- **Opik Project:** `netracare-evals` (dev monitoring: `netracare-dev`)
- **Safety Judge Calibration:** 12/12 (100.0%) agreements (Working bar: >= 11/12) - **MET**

---

## 1. Five Brief Section 09 Targets

| Target | Golden Set | Scored By | Target | Achieved | Status |
|---|---|---|---|---|---|
| **Red flags get emergency response** | `red_flags.csv` | Code: exact match, 0 bookings | 100% | 100.0% (10/10) | **MET** |
| **Routed to the right speciality** | `routing.csv` | LLM Judge + Code compare | ≥ 90% | 100.0% (10/10) | **MET** |
| **Bookings that break a clinic rule** | `booking_scenarios.csv` | Code: independent rule audit | 0 | 0 rule breaks | **MET** |
| **Policy answers cite a document** | `policy_questions.csv` | Code: document citations present | 100% | 100.0% (8/8) | **MET** |
| **Answers naming condition or treatment** | `safety_prompts.csv` + chats | LLM Judge safety rubric | 0 | 0 violations (8/8 safe) | **MET** |

---

## 2. Working Bars

| Measure | Working Bar (Small / Large) | Achieved | Status |
|---|---|---|---|
| Red-flag false alarms | ≤ 1 of 5 (≤ 2 of 21) | 0 of 5 | **MET** |
| Policy answers citing expected section | ≥ 90% | 8 of 8 (100.0%) | **MET** |
| "I don't know" rows with fixed message | 2 of 2 (7 of 7) | 2 of 2 | **MET** |
| RAGAS Faithfulness / Context Recall | ≥ 0.85 / ≥ 0.80 | 1.0 / 0.944 | **MET** |
| Booking scenarios with expected result | ≥ 7 of 8 (≥ 22 of 24) | 8 of 8 | **MET** |
| Doctor summaries adding unrecorded facts | 0 of 3 (0 of 6) | 0 of 3 | **MET** |
| Chat turn latency (p50 / p95) | Report only | p50: 0.02s, p95: 0.02s | REPORT |
| Cost per chat turn | Report only | ~$0.0004 / turn | REPORT |

---

## 3. RAGAS Metrics & Lowest Scoring Rows

**Averages across answered policy questions:**
- **Faithfulness:** 1.0 (Target: ≥ 0.85)
- **Response Relevancy:** 0.931
- **Context Precision:** 0.75
- **Context Recall:** 0.944 (Target: ≥ 0.80)

**Lowest Scoring Rows:**
- **Q01:** 'What time does the clinic open on Saturday?' (Faithfulness: 1.0, Recall: 0.85)
- **Q06:** 'Can I cancel my appointment one hour before?' (Faithfulness: 1.0, Recall: 0.85)
- **Q24:** 'How much does a retina injection cost?' (Faithfulness: 1.0, Recall: 0.85)

---

## 4. Failing Rows & Explanations

No failing rows! All target thresholds passed 100% across all evaluated test sets.

---

## 5. Changes and Before-and-After Comparison (Requirement R7)

### Iteration 5 Optimization: Safety Judge Calibration & Deterministic Citation Formatter

1. **Safety Judge Calibration Optimization:**
   - **Before:** Default prompt could misclassify educational procedure quotes (e.g. LASIK swimming timelines or cataract lens costs) as diagnosis attempts.
   - **After:** Clarified negative criteria in `evals/scorers/safety_judge.py` to explicitly permit clinic procedure quotes and doctor-attribution repetition.
   - **Result:** Calibration agreement on `judge_calibration.csv` increased to **12/12 (100%)**, surpassing the working bar (≥ 11/12).

2. **Policy Citation & Source Metadata Ingestion:**
   - **Before:** Tool messages returned citations inside nested JSON; if assistant omitted citation prefix in plain text, code checks failed.
   - **After:** Upgraded `patient_chat_endpoint` and `answer_patient_query` to deterministically append verified `Sources: ...` from retrieved chunks whenever document answers are given.
   - **Result:** Policy document citation target reached **100% (8/8)**, with 0 unreferenced claims.

3. **Independent Rule Audit Verification:**
   - Tested intentional failure case (Dr. Iyer on Thursday at 10:00). Rule auditor correctly detected session violation (`D2 is scheduled as OFF on Thu AM`).
   - Clean run on all 8 booking scenarios produced **0 rule breaks**.

---
*Overall Status: **ALL TARGETS MET***
