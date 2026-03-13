"""
SQLAlchemy engine, session ve Base konfigürasyonu.

Mevcut BackendProje/database.py ile aynı bağlantıyı kullanır;
Clean Architecture geçişi tamamlanınca tek kaynak burası olacak.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
import os

load_dotenv()

SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    "?charset=utf8mb4"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency: Her API isteğinde veritabanı oturumu açıp kapatır."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
