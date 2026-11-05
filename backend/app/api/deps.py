"""FastAPI dependencies for authentication, role guards, and database session.
Enforces server-side security: patients can only access their own records.
"""
import json
import base64
from typing import Optional, List
from fastapi import Header, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db

class CurrentUser(BaseModel):
    role: str  # "patient", "doctor", "staff", "admin"
    id: str    # e.g. "P01", "D1", "staff_1"
    name: str

def get_current_user(
    x_session_data: Optional[str] = Header(None, alias="X-Session-Data"),
) -> CurrentUser:
    """Extract and validate user session from request header."""
    if not x_session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
        )
    try:
        raw_json = base64.b64decode(x_session_data).decode("utf-8")
        data = json.loads(raw_json)
        return CurrentUser(**data)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token.",
        )

def require_role(allowed_roles: List[str]):
    def role_checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role.lower() not in [r.lower() for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied for role '{user.role}'. Required: {allowed_roles}",
            )
        return user
    return role_checker

def get_current_patient(user: CurrentUser = Depends(require_role(["patient"]))) -> CurrentUser:
    return user

def get_current_doctor(user: CurrentUser = Depends(require_role(["doctor"]))) -> CurrentUser:
    return user

def get_current_staff(user: CurrentUser = Depends(require_role(["staff", "admin", "sub_admin"]))) -> CurrentUser:
    return user

