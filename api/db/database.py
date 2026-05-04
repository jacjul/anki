import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool

from api.core.settings import settings


engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind =engine, autoflush = False, autocommit = False)

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
        
class Base(DeclarativeBase):
    pass