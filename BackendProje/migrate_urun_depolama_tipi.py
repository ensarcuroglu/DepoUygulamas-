"""
Faz 0.3 — Ürün Depolama Tipi Migration

Yeni sütun: depolama_tipi (VARCHAR 20, default 'Kuru')
Tüm mevcut ürünler varsayılan olarak 'Kuru' alır — legacy uyumluluk sağlanır.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import get_settings

settings = get_settings()

SQLALCHEMY_DATABASE_URL = settings.sqlalchemy_database_url

engine = create_engine(SQLALCHEMY_DATABASE_URL)

alter_statements = [
    "ALTER TABLE urunler ADD COLUMN depolama_tipi VARCHAR(20) NOT NULL DEFAULT 'Kuru';",
]


def duplicate_column_hatasi_mi(exc: SQLAlchemyError) -> bool:
    """Sadece 'column already exists' durumunu tespit eder."""
    orig = getattr(exc, "orig", None)
    if orig is None:
        return False

    # MySQL duplicate column hata kodu
    args = getattr(orig, "args", ())
    if args and args[0] == 1060:
        return True

    mesaj = str(orig).lower()
    return "duplicate column name" in mesaj or "already exists" in mesaj

print("Faz 0.3 — Ürün Depolama Tipi Migration başlatılıyor...")

try:
    with engine.begin() as conn:
        for stmt in alter_statements:
            try:
                print(f"  Executing: {stmt}")
                conn.execute(text(stmt))
                print("  OK.")
            except SQLAlchemyError as e:
                if duplicate_column_hatasi_mi(e):
                    print(f"  Atlandı (sütun zaten var): {e}")
                    continue
                raise

    print("\nMigration tamamlandı. Tüm mevcut ürünler 'Kuru' depolama tipiyle işaretlendi.")
except Exception as e:
    print(f"Bağlantı hatası: {e}")
