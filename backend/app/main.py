from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.limiter import limiter
from app.routers import admin, auth, events

app = FastAPI(
    title="Event Workshop Portal API",
    description="API for event management, workshop registrations, and authentication",
    version="1.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def _allowed_origins() -> list[str]:
    origins = set(settings.cors_origins)
    # In development, localhost and 127.0.0.1 are different origins to the browser,
    # so allow both for the Vite dev server (a common cause of "Failed to fetch").
    if settings.app_env != "production":
        for port in (5173, 3000):
            origins.add(f"http://localhost:{port}")
            origins.add(f"http://127.0.0.1:{port}")
    return sorted(origins)


app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Event Workshop Portal API is running", "status": "ok"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/api/health/db")
def health_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={"status": "error", "database": "unavailable"})
    return {"status": "ok", "database": "connected"}


app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
