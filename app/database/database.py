"""
app/database/database.py
Database connection using SQLAlchemy ORM.
Supports MySQL/Postgres/SQLite URLs for deployment.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# ----------------------------------------
# DATABASE CONNECTION URL
# Supports: mysql+pymysql://..., postgresql://..., sqlite:///...
# ----------------------------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./legal_ai.db"
)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("postgresql://") and "+" not in DATABASE_URL.split("://", 1)[1]:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

# ----------------------------------------
# ENGINE
# ----------------------------------------

engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,
}

if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
    })

engine = create_engine(DATABASE_URL, **engine_kwargs)

# ----------------------------------------
# SESSION
# ----------------------------------------

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ----------------------------------------
# BASE CLASS FOR ALL MODELS
# ----------------------------------------

Base = declarative_base()


# ----------------------------------------
# DEPENDENCY — FastAPI injection
# ----------------------------------------

def get_db():
    """
    FastAPI dependency for DB session.
    Usage in route:
        db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()