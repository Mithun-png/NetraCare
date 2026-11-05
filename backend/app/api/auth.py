"""Authentication router implementing v1 demo identity.
Patients login via mobile + name (matches data pack 1 / creates new patient).
Doctors pick their name. Staff login with name.
"""
import base64
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Patient, Doctor
from app.services.reasons import ReasonCode, REASON_MESSAGES
from app.api.deps import get_current_user, CurrentUser

router = APIRouter(prefix="/auth", tags=["Auth"])

class LoginRequest(BaseModel):
    role: str  # "patient", "doctor", "staff", "admin"
    mobile: Optional[str] = None
    name: Optional[str] = None
    doctor_id: Optional[str] = None

class LoginResponse(BaseModel):
    ok: bool
    session_token: str
    user: CurrentUser
    message: str

@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    role = req.role.strip().lower()

    if role == "patient":
        if not req.mobile or not req.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mobile number and name are required for patient login.",
            )
        mobile_clean = req.mobile.strip()
        name_clean = req.name.strip()

        # Check existing patient
        existing = db.query(Patient).filter(Patient.mobile == mobile_clean).first()
        if existing:
            # Check name match
            if existing.name.strip().lower() != name_clean.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "reason_code": ReasonCode.PATIENT_DETAILS_MISMATCH.value,
                        "message": REASON_MESSAGES[ReasonCode.PATIENT_DETAILS_MISMATCH],
                    },
                )
            patient = existing
        else:
            # Create new patient
            count = db.query(Patient).count()
            new_id = f"P{count + 1:02d}"
            patient = Patient(
                id=new_id,
                name=name_clean,
                mobile=mobile_clean,
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)

        user = CurrentUser(role="patient", id=patient.id, name=patient.name)

    elif role == "doctor":
        if not req.doctor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Doctor ID is required for doctor login.",
            )
        doc = db.query(Doctor).filter(Doctor.id == req.doctor_id.strip()).first()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Doctor '{req.doctor_id}' not found.",
            )
        user = CurrentUser(role="doctor", id=doc.id, name=doc.name)

    elif role in ["staff", "admin", "sub_admin"]:
        name_clean = req.name.strip() if req.name else "Front Desk Staff"
        user = CurrentUser(role=role, id=f"staff_{name_clean.lower().replace(' ', '_')}", name=name_clean)

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown role '{req.role}'.",
        )

    # Encode user as base64 session token
    session_bytes = json.dumps(user.model_dump()).encode("utf-8")
    session_token = base64.b64encode(session_bytes).decode("utf-8")

    return LoginResponse(
        ok=True,
        session_token=session_token,
        user=user,
        message=f"Welcome {user.name} ({user.role})",
    )

@router.get("/me", response_model=CurrentUser)
def get_me(user: CurrentUser = Depends(get_current_user)):
    return user

@router.post("/logout")
def logout():
    return {"ok": True, "message": "Logged out successfully"}

