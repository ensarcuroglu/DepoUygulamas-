import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# MySQL veritabanı bağlantısı
SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    "?charset=utf8mb4"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)

alter_statements = [
    "ALTER TABLE stok_hareketleri ADD COLUMN raf_id INT DEFAULT NULL;",
    "ALTER TABLE stok_hareketleri ADD CONSTRAINT fk_stok_raf FOREIGN KEY (raf_id) REFERENCES raflar(id);",
    "ALTER TABLE stok_hareketleri ADD COLUMN siparis_no VARCHAR(100) DEFAULT NULL;",
    "ALTER TABLE stok_hareketleri ADD COLUMN tir_plaka VARCHAR(50) DEFAULT NULL;",
    "ALTER TABLE stok_hareketleri ADD COLUMN depo_kapi VARCHAR(50) DEFAULT NULL;",
    "ALTER TABLE stok_hareketleri ADD COLUMN barkodlar TEXT DEFAULT NULL;"
]

print("Veritabanı migration başlatılıyor...")

try:
    with engine.begin() as conn:
        for stmt in alter_statements:
            try:
                print(f"Executing: {stmt}")
                conn.execute(text(stmt))
                print("Başarılı.")
            except Exception as e:
                # Kolon zaten varsa veya constraint ekliyse hata fırlatır, hata loglanıp devam etsin
                print(f"Hata / Atlandı: {e}")
                pass
    print("Migration tamamlandı.")
except Exception as e:
    print(f"Bağlantı hatası: {e}")
