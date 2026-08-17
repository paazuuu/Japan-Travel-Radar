from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.config import get_settings


def _normalized_url(url: str) -> str:
    """Ensure SQLAlchemy uses the psycopg (v3) driver."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def make_engine() -> Engine:
    settings = get_settings()
    return create_engine(
        _normalized_url(settings.database_url),
        pool_pre_ping=True,
        future=True,
    )


engine: Engine = make_engine()
