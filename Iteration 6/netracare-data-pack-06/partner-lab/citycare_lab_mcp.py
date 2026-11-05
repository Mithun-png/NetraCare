"""CityCare Hospital Lab: a fictional partner MCP server for the NetraCare capstone.

You don't need to change this file. Run it, then connect your Patient assistant to it:
    pip install "mcp[cli]<2"
    python citycare_lab_mcp.py
It serves one read-only tool at http://localhost:8002/mcp (Streamable HTTP).
"""
import csv
from pathlib import Path

from mcp.server.fastmcp import FastMCP

LAB = {
    "lab": "CityCare Hospital Lab (NetraCare's partner lab, fictional)",
    "address": "Ground floor, CityCare Hospital, 2 km from NetraCare",
    "timings": "Monday to Saturday 7 AM to 7 PM; Sunday 7 AM to 12 noon",
    "home_collection": "Available for ₹100 extra. Call 1800-111-1111 (fictional) a day ahead",
    "booking": "No booking needed for walk-in tests. This service gives information only; it cannot book tests",
}

with open(Path(__file__).with_name("lab_tests.csv"), encoding="utf-8") as f:
    TESTS = list(csv.DictReader(f))

mcp = FastMCP("CityCare Lab", host="localhost", port=8002)


def _matches(row: dict, query: str) -> bool:
    names = [row["name"].lower()] + [a.strip().lower() for a in row["also_known_as"].split(";")]
    return any(query == n or query in n or n in query for n in names if n)


@mcp.tool()
def get_lab_test_info(test: str = "") -> dict:
    """Information about a blood or urine test at CityCare Hospital Lab, NetraCare's partner lab.

    Returns fasting rules, sample type, when the report is ready and the indicative price,
    plus the lab's address, timings and home collection. Information only: it cannot book tests,
    read results or say which tests a patient needs.

    Args:
        test: the test name in plain words, for example "HbA1c" or "fasting sugar".
              Leave empty to get the lab's details and the list of tests it offers.
    """
    query = test.strip().lower()
    found = [row for row in TESTS if query and _matches(row, query)]
    if found:
        return {"found": True, "tests": found, **LAB}
    return {
        "found": False,
        "message": "CityCare Lab's list doesn't include that test." if query else "Lab details and tests offered.",
        "tests_offered": [row["name"] for row in TESTS],
        **LAB,
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
