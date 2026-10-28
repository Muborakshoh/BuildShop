from sqlalchemy import create_engine, make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


# Render PostgreSQL требует SSL
url = make_url(settings.database_url)
if "render.com" in str(url) and "sslmode" not in url.query:
    url = url.update_query_dict({"sslmode": "require"})

engine = create_engine(url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

