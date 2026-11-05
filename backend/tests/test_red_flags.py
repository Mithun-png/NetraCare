"""Tests for red-flag detection using Data Pack 2 reason_samples.csv."""
import csv
from pathlib import Path
from app.safety.red_flags import check_red_flags, EMERGENCY_RESPONSE_TEXT

def test_reason_samples_dataset():
    data_path = Path(__file__).resolve().parent.parent.parent / "data" / "reason_samples.csv"
    with open(data_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample_id = row["sample_id"]
            text = row["reason"]
            expected = row["expected_red_flag"].strip().lower() == "yes"

            is_flag, cat, resp = check_red_flags(text)
            assert is_flag == expected, (
                f"Sample {sample_id} failed: '{text}'. Expected {expected}, got {is_flag} (cat={cat})"
            )
            if expected:
                assert resp == EMERGENCY_RESPONSE_TEXT

