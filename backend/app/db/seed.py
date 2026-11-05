"""Database seeding utility.
Loads synthetic data from CSV files into SQLite/PostgreSQL.
"""
import csv
from datetime import datetime, date as dt_date, time as dt_time
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.models import Doctor, WeeklySchedule, Holiday, Patient, Appointment
from app.db.session import SessionLocal, init_db

def find_data_dir() -> Path:
    """Locate the data directory across possible working directories."""
    candidates = [
        Path("data"),
        Path("../data"),
        Path(__file__).resolve().parent.parent.parent / "data",
        Path(__file__).resolve().parent.parent.parent.parent / "data",
    ]
    for c in candidates:
        if c.exists() and (c / "doctors.csv").exists():
            return c.resolve()
    raise FileNotFoundError("Could not locate NetraCare 'data' directory containing doctors.csv")

def parse_time(t_str: str) -> dt_time:
    t_str = t_str.strip()
    parts = t_str.split(":")
    return dt_time(int(parts[0]), int(parts[1]))

def parse_date(d_str: str) -> dt_date:
    return datetime.strptime(d_str.strip(), "%Y-%m-%d").date()

def seed_db(db: Session, load_stretch: bool = False, reset_appointments: bool = False):
    """Seed the database with all core CSV records."""
    data_dir = find_data_dir()

    # 1. Doctors
    with open(data_dir / "doctors.csv", mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc_id = row["doctor_id"].strip()
            existing = db.query(Doctor).filter(Doctor.id == doc_id).first()
            if not existing:
                doc = Doctor(
                    id=doc_id,
                    name=row["name"].strip(),
                    specialities=row["specialities"].strip(),
                    active=True,
                )
                db.add(doc)
            else:
                existing.name = row["name"].strip()
                existing.specialities = row["specialities"].strip()
    db.commit()

    # 2. Weekly Schedules
    with open(data_dir / "weekly_schedule.csv", mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Clear existing weekly schedules to avoid duplicates
        db.query(WeeklySchedule).delete()
        for row in reader:
            ws = WeeklySchedule(
                doctor_id=row["doctor_id"].strip(),
                day=row["day"].strip(),
                session=row["session"].strip(),
                status=row["status"].strip(),
            )
            db.add(ws)
    db.commit()

    # 3. Holidays
    with open(data_dir / "holidays.csv", mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            h_date = parse_date(row["date"])
            existing = db.query(Holiday).filter(Holiday.date == h_date).first()
            if not existing:
                h = Holiday(
                    date=h_date,
                    name=row["name"].strip(),
                )
                db.add(h)
    db.commit()

    # 4. Patients
    patient_profiles = {}
    profiles_path = data_dir / "patient_profiles.csv"
    if profiles_path.exists():
        with open(profiles_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                p_id = row["patient_id"].strip()
                patient_profiles[p_id] = {
                    "chronic_conditions": row.get("general_health", "").strip(),
                    "allergies": row.get("allergies", "").strip(),
                }

    with open(data_dir / "patients.csv", mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            p_id = row["patient_id"].strip()
            profile = patient_profiles.get(p_id, {})
            yob = int(row["year_of_birth"].strip()) if row.get("year_of_birth") else None
            existing = db.query(Patient).filter(Patient.id == p_id).first()
            if not existing:
                pat = Patient(
                    id=p_id,
                    name=row["name"].strip(),
                    mobile=row["mobile"].strip(),
                    year_of_birth=yob,
                    chronic_conditions=profile.get("chronic_conditions"),
                    allergies=profile.get("allergies"),
                )
                db.add(pat)
            else:
                existing.name = row["name"].strip()
                existing.mobile = row["mobile"].strip()
                existing.year_of_birth = yob
                if profile:
                    existing.chronic_conditions = profile.get("chronic_conditions")
                    existing.allergies = profile.get("allergies")
    db.commit()

    # 5. Past Visits (data pack 2)
    past_visits_path = data_dir / "past_visits.csv"
    if past_visits_path.exists():
        with open(past_visits_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                v_id = row.get("visit_id") or row.get("appointment_id")
                v_id = v_id.strip()
                existing = db.query(Appointment).filter(Appointment.id == v_id).first()
                if not existing:
                    appt = Appointment(
                        id=v_id,
                        patient_id=row["patient_id"].strip(),
                        doctor_id=row["doctor_id"].strip(),
                        speciality=row["speciality"].strip(),
                        visit_type=row["visit_type"].strip(),
                        mode="IN_PERSON",
                        status="completed",
                        date=parse_date(row["date"]),
                        start_time=parse_time(row["start_time"]),
                        end_time=parse_time(row["end_time"]),
                        source="WEBSITE",
                        reason=row.get("reason", "").strip(),
                        doctor_note=row.get("doctor_note", "").strip(),
                    )
                    db.add(appt)
    db.commit()

    # 6. Optional: Stretch appointments seed
    if load_stretch:
        stretch_path = data_dir / "stretch" / "appointments_seed.csv"
        if stretch_path.exists():
            with open(stretch_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    a_id = row["appointment_id"].strip()
                    existing = db.query(Appointment).filter(Appointment.id == a_id).first()
                    if not existing:
                        appt = Appointment(
                            id=a_id,
                            patient_id=row["patient_id"].strip(),
                            doctor_id=row["doctor_id"].strip(),
                            speciality=row["speciality"].strip(),
                            visit_type=row["visit_type"].strip(),
                            mode="IN_PERSON",
                            status=row["status"].strip(),
                            date=parse_date(row["date"]),
                            start_time=parse_time(row["start_time"]),
                            end_time=parse_time(row["end_time"]),
                            source="WEBSITE",
                        )
                        db.add(appt)
                    else:
                        existing.status = row["status"].strip()
                        existing.date = parse_date(row["date"])
                        existing.start_time = parse_time(row["start_time"])
                        existing.end_time = parse_time(row["end_time"])
            db.commit()

if __name__ == "__main__":
    init_db()
    db = SessionLocal()
    seed_db(db, load_stretch=True)
    db.close()
    print("Database initialized and seeded successfully.")

