from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# if we're testing, use in-memory DB
if os.getenv("TESTING"):
    DATABASE_URL = "sqlite:///:memory:"
else:
    BASE_DIR = Path(__file__).resolve().parent.parent  # .../app
    DB_PATH = BASE_DIR / "test.db"
    DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # import models so SQLAlchemy registers them
    from app.models import user, calculation  # noqa: F401

    print("init_db() called")
    Base.metadata.create_all(bind=engine)
    print("Tables after create_all:", Base.metadata.tables.keys())
