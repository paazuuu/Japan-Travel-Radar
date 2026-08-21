from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import get_settings
from app.db import engine
from app.routers import admin, content, events, planner, rankings, restaurants, search, spots

settings = get_settings()

app = FastAPI(
    title="Japan Travel AI Radar — Backend",
    version="0.1.0",
)

API_PREFIX = "/api/v1"
app.include_router(spots.router, prefix=API_PREFIX)
app.include_router(restaurants.router, prefix=API_PREFIX)
app.include_router(search.router, prefix=API_PREFIX)
app.include_router(rankings.router, prefix=API_PREFIX)
app.include_router(events.router, prefix=API_PREFIX)
app.include_router(planner.router, prefix=API_PREFIX)
app.include_router(content.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    return {"service": "japan-travel-radar-backend", "env": settings.app_env}


@app.get("/health")
def health() -> dict:
    """Liveness + DB/PostGIS readiness check."""
    db_ok = False
    postgis_ok = False
    postgis_version: str | None = None

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_ok = True
            row = conn.execute(text("SELECT PostGIS_Version()")).first()
            if row is not None:
                postgis_ok = True
                postgis_version = str(row[0])
    except Exception:
        # Health endpoint must not raise; report component status instead.
        pass

    status = "ok" if (db_ok and postgis_ok) else "degraded"
    return {
        "status": status,
        "database": db_ok,
        "postgis": postgis_ok,
        "postgis_version": postgis_version,
    }
