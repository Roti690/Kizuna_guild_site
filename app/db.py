from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def ensure_member_activity_history():
    inspector = inspect(engine)
    if "members" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("members")}
    if "activity_history" in columns:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE members ADD COLUMN activity_history TEXT"))
