"""
Faz 0.2 — Raf Entity Genişletme Migration

Yeni sütunlar: zon_id, max_agirlik_kg, koridor, kat, goz
Legacy raf kodu dönüşümü: "A-12-01-01" → "GNL-A-12-01-01"
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    "?charset=utf8mb4"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)

alter_statements = [
    # Yeni sütunlar
    "ALTER TABLE raflar ADD COLUMN zon_id INT DEFAULT NULL;",
    "ALTER TABLE raflar ADD CONSTRAINT fk_raf_zon FOREIGN KEY (zon_id) REFERENCES zonlar(id);",
    "ALTER TABLE raflar ADD COLUMN max_agirlik_kg FLOAT DEFAULT NULL;",
    "ALTER TABLE raflar ADD COLUMN koridor VARCHAR(10) DEFAULT '';",
    "ALTER TABLE raflar ADD COLUMN kat INT DEFAULT 0;",
    "ALTER TABLE raflar ADD COLUMN goz INT DEFAULT 0;",
    # kod sütunu genişletilir (20 → 50): yeni format daha uzun
    "ALTER TABLE raflar MODIFY COLUMN kod VARCHAR(50) NOT NULL;",
]

# Legacy raf kodu dönüşümü: 4-parçalı kodları GNL- prefix'i ile genişlet
# Örnek: "A-12-01-01" → "GNL-A-12-01-01"
# 5-parçalı olanlar zaten yeni formatta, dokunma.
legacy_migration_sql = """
UPDATE raflar
SET kod = CONCAT('GNL-', kod)
WHERE LENGTH(kod) - LENGTH(REPLACE(kod, '-', '')) = 3
"""


print("Faz 0.2 — Raf Genişletme Migration başlatılıyor...")

try:
    with engine.begin() as conn:
        for stmt in alter_statements:
            try:
                print(f"  Executing: {stmt[:80]}...")
                conn.execute(text(stmt))
                print("  OK.")
            except Exception as e:
                print(f"  Atlandı (muhtemelen zaten var): {e}")

        # Legacy kod dönüşümü
        print("  Legacy raf kodu dönüşümü...")
        result = conn.execute(text(legacy_migration_sql))
        print(f"  {result.rowcount} raf kodu güncellendi (4-parça → 5-parça).")

    print("\nMigration tamamlandı.")
except Exception as e:
    print(f"Bağlantı hatası: {e}")
