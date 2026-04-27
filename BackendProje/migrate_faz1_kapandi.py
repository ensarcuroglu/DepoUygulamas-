"""
Faz 1 Migration — MalKabulDurum.TAMAMLANDI → KAPANDI

Mevcut kayıtlardaki 'Tamamlandi' değerini 'Kapandi' olarak günceller.

Çalıştırma:
    cd BackendProje
    python migrate_faz1_kapandi.py
"""

from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()
DATABASE_URL = settings.sqlalchemy_database_url

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
