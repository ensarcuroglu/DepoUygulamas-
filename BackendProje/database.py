from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite veritabanı dosyası (proje klasöründe oluşacak)
SQLALCHEMY_DATABASE_URL = "sqlite:///./depo.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite için gerekli
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Dependency: Her API isteğinde veritabanı oturumu açıp kapatır
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
