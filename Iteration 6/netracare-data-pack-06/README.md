# NetraCare data pack 6

Synthetic data for Iteration 6. NetraCare, CityCare Hospital and its lab are fictional; no real people, patients or companies.
Keep using data packs 1 to 5. This pack adds test cases for your NetraCare MCP server, a partner lab MCP server your assistant connects to,
three skills for the Patient assistant, and the final demo scenarios.

## Files
| File | What it holds |
|---|---|
| mcp_scenarios.csv | 12 calls to your NetraCare MCP server with the expected result and reason code |
| partner-lab/citycare_lab_mcp.py | A ready-made MCP server for CityCare Hospital Lab, with one tool: `get_lab_test_info` |
| partner-lab/lab_tests.csv | The 7 tests the lab server knows about. It reads this file |
| lab_questions.csv | 9 patient questions about lab tests, with the expected behaviour |
| skills/ | 3 ready-made skills: cataract-surgery-care, lasik-suitability-intake, prepare-for-visit |
| skill_triggers.csv | 16 patient messages with the skill that should load, or `none` |
| final_demo_scenarios.csv | 16 standard scenarios across all six iterations, for the final demo |

## mcp_scenarios.csv
- Dates are relative to today, because your app uses the real clock: "next Monday" means the coming Monday.
  If a date lands on a holiday in holidays.csv, use the following week.
- Run the rows in order. M04 and M09 use the booking made in M03.
- `expected` is `allowed`, `refused` or `red_flag`. Return the `reason_code` exactly as written.
- Reason codes are the ones from data pack 1, plus two new ones:

| Code | Meaning |
|---|---|
| PATIENT_DETAILS_MISMATCH | The mobile belongs to a patient with a different name |
| RED_FLAG | The reason is a red flag. No booking; the emergency response is returned |

## partner-lab/
- You don't build or change this server. It stands in for a partner's system that NetraCare doesn't own.
- Install and run it in its own terminal:
  `pip install "mcp[cli]<2"` then `python citycare_lab_mcp.py`. It serves Streamable HTTP at `http://localhost:8002/mcp`.
- Use MCP version 1.x. `langchain-mcp-adapters` needs it, and in MCP 2.x `FastMCP` was renamed.
- `get_lab_test_info(test)` takes a test name in plain words ("HbA1c", "fasting sugar"). An empty name returns the lab's details and its list of tests.
  A test it doesn't know returns `found: false`; it never makes one up.
- The lab gives information only: no booking, no results.

## lab_questions.csv
- Ask these in the patient chat with the lab server running. LQ06 to LQ09 test what the assistant must not do.

## skills/
- Each skill is a folder with a `SKILL.md` and one extra file. `SKILL.md` starts with YAML front matter (`name`, `description`), then the instructions.
- Copy the `skills/` folder into your project as it is. Add your own `children-visit` skill next to them.
- The skills hold clinic know-how that the three iteration 3 documents don't, such as the day-by-day guide after cataract surgery.
  Treat them as clinic-approved content: answers that use them name the skill as their source.
- Don't edit a skill to make a check pass, except your own. Fix your loader, your tool descriptions or your system prompt.

## skill_triggers.csv
- `patient_id` is who to log in as. For T07 and T08, book an appointment for that patient first.
- `expected_skill` is the skill the assistant should load, or `none`. `also_acceptable` lists another right answer.
- T09 to T11 need the `children-visit` skill you write.
- T16 is a red flag: the emergency response comes first, so no skill should load.

## final_demo_scenarios.csv
- The standard scenarios for the final demo. `iteration` is where the feature was built.
- Rehearse them all in order on a fresh copy of your database, loaded from data packs 1 to 6.
