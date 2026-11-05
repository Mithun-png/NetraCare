# NetraCare data pack 3

Synthetic data for Iteration 3. NetraCare is fictional; no real people or patients.
Keep using data packs 1 and 2. This pack adds the clinic documents your patient chat answers from.

## Files
| File | What it holds |
|---|---|
| documents/doctors.md | Doctors and specialities: which speciality sees which problems, and each doctor's specialities and OPD days (brief section 03) |
| documents/procedures.md | 9 tests and procedures: what happens, who does it, time at the clinic, before and after (dos and don'ts), indicative cost |
| documents/clinic_policy_faq.md | Timings, booking, fees, cancelling, what to bring, dilation, children, emergencies, what the assistant can and cannot do |
| questions.csv | 20 patient questions with the expected answer and source. Q16 to Q20 are not covered and should get "I don't know" |
| routing_samples.csv | 20 symptom messages labelled with the right speciality and doctors |

## The documents
- They are Markdown. Every `##` heading is one section. Split on the headings first, so each chunk belongs to one section,
  and keep the file name and the heading on the chunk. Your citations come from them, for example
  `clinic_policy_faq.md > Dilation`.
- Most sections are short. Only split a section further if it is longer than your chunk size.
- Costs are in Indian rupees and are indicative. The assistant shares them as information only; billing is out of scope.
- Do not edit the documents to make a check pass. Fix your chunking, retrieval or prompt instead.

## questions.csv
- `expected_source` is `file > section`. `none` means the documents don't cover it, so the answer is "I don't know".
- `expected_answer` is the gist. Your wording can differ.

## routing_samples.csv
- None of these are red flags. Red flags are checked by your iteration 2 classifier before routing.
- `expected_doctors` are all the doctors with that speciality in doctors.md. The chat should name them.
- Where the `note` gives another acceptable speciality, either answer counts as right.
- R06 and R19 use words that are not in the documents, so keyword search alone may miss them.
- R20 is not an eye problem. The right answer says NetraCare only looks after eyes, with no speciality.
