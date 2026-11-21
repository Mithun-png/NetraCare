"""Intake and OCR router for NetraCare (Iteration 7).
Handles prescription and referral uploads with red-flag emergency screening and zero clinical interpretation.
"""
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.db.models import Appointment, UrgentCase, Patient
from app.api.deps import get_current_user_optional, CurrentUser
from app.services.ocr_service import process_ocr_document
from app.config import get_clinic_now

router = APIRouter(prefix="/intake", tags=["Intake"])

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "application/pdf",
}

@router.post("/ocr")
async def upload_prescription_ocr(
    file: UploadFile = File(...),
    appointment_id: Optional[str] = Form(None),
    user: Optional[CurrentUser] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    # 1. Validate content type
    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_CONTENT_TYPES and not any(file.filename.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".pdf", ".txt"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{content_type}'. Allowed types: JPEG, PNG, WebP, PDF.",
        )

    # 2. Read bytes and check size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds maximum limit of 5 MB.",
        )

    # 3. Process OCR document
    result = process_ocr_document(file_bytes, filename=file.filename)

    # 4. If red flag detected in uploaded document, create UrgentCase record
    if result.get("red_flag"):
        urgent = UrgentCase(
            source="OCR_INTAKE",
            summary=f"Red flag from uploaded referral/prescription: {result['raw_text'][:200]}",
            patient_id=user.id if user and user.role == "patient" else None,
            status="OPEN",
            created_at=get_clinic_now(),
        )
        db.add(urgent)
        db.commit()

        return {
            "ok": False,
            "red_flag": True,
            "emergency_response": result["emergency_response"],
            "raw_text": result["raw_text"],
            "message": "Emergency symptoms detected in document. Please seek immediate medical care.",
        }

    # 5. Optional auto-attachment if appointment_id provided and authorized
    attached = False
    if appointment_id:
        appt = db.query(Appointment).filter(Appointment.id == appointment_id.strip()).first()
        if not appt:
            raise HTTPException(status_code=404, detail=f"Appointment '{appointment_id}' not found.")
        
        # Verify ownership if user is patient
        if user and user.role == "patient" and appt.patient_id != user.id:
            raise HTTPException(status_code=403, detail="You do not have permission to attach documents to this appointment.")

        current_notes = appt.intake_notes or ""
        new_notes = f"{current_notes}\n\n{result['formatted_summary']}".strip()
        appt.intake_notes = new_notes
        db.commit()
        attached = True

    return {
        "ok": True,
        "filename": file.filename,
        "raw_text": result["raw_text"],
        "formatted_summary": result["formatted_summary"],
        "fields": result["fields"],
        "attached": attached,
        "appointment_id": appointment_id if attached else None,
    }
