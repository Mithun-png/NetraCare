"""NetraCare FastAPI Application.
Entry point for the backend service.
"""
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.db.session import init_db, SessionLocal
from app.db.seed import seed_db
from app.api.auth import router as auth_router
from app.api.public import router as public_router
from app.api.patient import router as patient_router
from app.api.doctor import router as doctor_router
from app.api.staff import router as staff_router
from app.api.chat import router as chat_router

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
app.include_router(chat_router, prefix="/api/v1")

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "timezone": settings.CLINIC_TIMEZONE,
        "rules_enforced": True,
    }

# Mount React frontend static files when built
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    if (frontend_dist / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.api_route("/", methods=["GET", "HEAD"])
    async def serve_index():
        return FileResponse(str(frontend_dist / "index.html"))

    @app.api_route("/{full_path:path}", methods=["GET", "HEAD"])
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path in ["docs", "openapi.json", "redoc"]:
            raise HTTPException(status_code=404, detail="Not found")
        target_file = frontend_dist / full_path
        if target_file.is_file():
            return FileResponse(str(target_file))
        return FileResponse(str(frontend_dist / "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

