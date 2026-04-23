import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/ankidb")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind =engine, autoflush = False, autocommit = False)

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
        
class Base(DeclarativeBase):
    pass