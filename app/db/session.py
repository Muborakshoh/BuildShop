from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


# Render PostgreSQL требует SSL в URL
database_url = settings.database_url
if "render.com" in database_url and "sslmode=" not in database_url:
    database_url += ("&" if "?" in database_url else "?") + "sslmode=require"

engine = create_engine(database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

