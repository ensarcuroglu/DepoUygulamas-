"""
Faz 1 Migration — MalKabulDurum.TAMAMLANDI → KAPANDI

Mevcut kayıtlardaki 'Tamamlandi' değerini 'Kapandi' olarak günceller.

Çalıştırma:
    cd BackendProje
    python migrate_faz1_kapandi.py
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "depo_db")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

MIGRATION_SQL = """
UPDATE mal_kabul_irsaliyeleri
SET durum = 'Kapandi'
WHERE durum = 'Tamamlandi';
"""

def run():
    with engine.begin() as conn:
        result = conn.execute(text(MIGRATION_SQL))
        print(f"Migration tamamlandı: {result.rowcount} kayıt güncellendi (Tamamlandi → Kapandi).")

if __name__ == "__main__":
    run()
