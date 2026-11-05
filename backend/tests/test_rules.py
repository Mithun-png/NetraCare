"""Automated Rule Engine Tests.
Runs the complete 38 test cases from data pack 1 stretch/rule_tests.csv
with fixed clock CLINIC_NOW = 2026-11-02 10:00:00.
"""
import csv
from datetime import datetime, date as dt_date, time as dt_time
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db.models import Base
from app.db.seed import seed_db, parse_date, parse_time
from app.services.booking import BookingService

# Fixed test clock per Handout 1 / Data Pack 1 stretch instructions
TEST_CLINIC_NOW = "2026-11-02 10:00:00"

@pytest.fixture(scope="module")
def test_engine():
    # Use in-memory SQLite for test isolation and high speed
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(autouse=True)
def setup_clinic_clock(monkeypatch):
    monkeypatch.setattr(settings, "CLINIC_NOW", TEST_CLINIC_NOW)

def get_rule_tests():
    data_path = Path(__file__).resolve().parent.parent.parent / "data" / "stretch" / "rule_tests.csv"
    tests = []
    with open(data_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tests.append(row)
    return tests

@pytest.mark.parametrize("case", get_rule_tests(), ids=[c["test_id"] for c in get_rule_tests()])
def test_clinic_rule(case, test_engine):
    # Setup a fresh in-memory session with clean seed data for every test
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()
    seed_db(db, load_stretch=True)

    test_id = case["test_id"]
    action = case["action"].strip().lower()
    role = case["role"].strip().lower()
    acting_patient_id = case["acting_patient_id"].strip() if case.get("acting_patient_id") else None
    appointment_id = case["appointment_id"].strip() if case.get("appointment_id") else None
    doctor_id = case["doctor_id"].strip() if case.get("doctor_id") else None
    speciality = case["speciality"].strip() if case.get("speciality") else None
    visit_type = case["visit_type"].strip() if case.get("visit_type") else "new"
    d_str = case["date"].strip() if case.get("date") else None
    t_str = case["start_time"].strip() if case.get("start_time") else None
    expected = case["expected"].strip().lower()
    expected_reason = case["reason_code"].strip() if case.get("reason_code") else None

    date_val = parse_date(d_str) if d_str else None
    start_time = parse_time(t_str) if t_str else None

    if action == "book":
        result = BookingService.book(
            db=db,
            patient_id=acting_patient_id,
            doctor_id=doctor_id,
            speciality=speciality,
            visit_type=visit_type,
            date_val=date_val,
            start_time=start_time,
            role=role,
            source="WEBSITE",
        )
    elif action == "cancel":
        result = BookingService.cancel(
            db=db,
            appointment_id=appointment_id,
            actor_role=role,
            acting_patient_id=acting_patient_id,
        )
    elif action == "reschedule":
        result = BookingService.reschedule(
            db=db,
            appointment_id=appointment_id,
            new_date=date_val,
            new_start_time=start_time,
            new_doctor_id=doctor_id,
            new_speciality=speciality,
            actor_role=role,
            acting_patient_id=acting_patient_id,
        )
    else:
        pytest.fail(f"Unknown action: {action}")

    db.close()

    assert result.expected == expected, (
        f"[{test_id}] Expected status '{expected}', got '{result.expected}' "
        f"(reason={result.reason_code}, msg='{result.message}'). Note: {case.get('note')}"
    )

    if expected_reason:
        assert result.reason_code is not None, (
            f"[{test_id}] Expected reason code '{expected_reason}', but reason_code was None. Note: {case.get('note')}"
        )
        assert result.reason_code.value == expected_reason, (
            f"[{test_id}] Expected reason code '{expected_reason}', got '{result.reason_code.value}'. Note: {case.get('note')}"
        )

