"""NetraCare FastAPI Application.
Entry point for the backend service.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.session import init_db, SessionLocal
from app.db.seed import seed_db
from app.api.auth import router as auth_router
from app.api.public import router as public_router
from app.api.patient import router as patient_router
from app.api.doctor import router as doctor_router
from app.api.staff import router as staff_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and seed foundational data
    init_db()
    db = SessionLocal()
    try:
        seed_db(db, load_stretch=False)
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="AI Front Desk and Care Coordination for NetraCare Eye Clinic",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS setup for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits localhost:5173, etc.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers under /api/v1
app.include_router(public_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(patient_router, prefix="/api/v1")
app.include_router(doctor_router, prefix="/api/v1")
app.include_router(staff_router, prefix="/api/v1")

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "timezone": settings.CLINIC_TIMEZONE,
        "rules_enforced": True,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

