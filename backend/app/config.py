"""NetraCare Application Configuration.
Handles clinic timezone (Asia/Kolkata), database URL, and injectable clock.
"""
from datetime import datetime, timezone
import os
from zoneinfo import ZoneInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

CLINIC_TZ = ZoneInfo("Asia/Kolkata")

class Settings(BaseSettings):
    APP_NAME: str = "NetraCare AI Front Desk"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./netracare.db")
    CLINIC_TIMEZONE: str = "Asia/Kolkata"
    # CLINIC_NOW allows setting a fixed test clock, e.g. "2026-11-02 10:00:00"
    CLINIC_NOW: str | None = os.getenv("CLINIC_NOW", None)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "netracare-secret-key-demo-2026")
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY", None)
    PINECONE_API_KEY: str | None = os.getenv("PINECONE_API_KEY", None)
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "netracare-docs")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

def get_clinic_now() -> datetime:
    """Return the current time in Asia/Kolkata, or the injected fixed clock if configured."""
    if settings.CLINIC_NOW:
        time_str = settings.CLINIC_NOW.strip()
        if len(time_str) == 16:
            time_str += ":00"
        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        return dt.replace(tzinfo=CLINIC_TZ)
    return datetime.now(CLINIC_TZ)
