import pytest
from app.config import settings

@pytest.fixture(autouse=True)
def default_clinic_now(monkeypatch):
    """Ensure clinic now defaults to the standard test clock 2026-11-02 10:00:00."""
    monkeypatch.setattr(settings, "CLINIC_NOW", "2026-11-02 10:00:00")
