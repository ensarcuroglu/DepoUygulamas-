from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()

# MySQL veritabanı bağlantısı
SQLALCHEMY_DATABASE_URL = settings.sqlalchemy_database_url

engine = create_engine(SQLALCHEMY_DATABASE_URL)

alter_statements = [
    "ALTER TABLE stok_hareketleri ADD COLUMN raf_id INT DEFAULT NULL;",
    "ALTER TABLE stok_hareketleri ADD CONSTRAINT fk_stok_raf FOREIGN KEY (raf_id) REFERENCES raflar(id);",
    "ALTER TABLE stok_hareketleri ADD COLUMN siparis_no VARCHAR(100) DEFAULT NULL;",
    "ALTER TABLE stok_hareketleri ADD COLUMN tir_plaka VARCHAR(50) DEFAULT NULL;",
    "ALTER TABLE stok_hareketleri ADD COLUMN depo_kapi VARCHAR(50) DEFAULT NULL;",
    "ALTER TABLE stok_hareketleri ADD COLUMN barkodlar TEXT DEFAULT NULL;",
    # Sevkiyat bilgileri
    "ALTER TABLE stok_hareketleri ADD COLUMN sofor_adi VARCHAR(100) DEFAULT NULL;",
    "ALTER TABLE stok_hareketleri ADD COLUMN tasiyici_firma VARCHAR(100) DEFAULT NULL;",
    # Faz 1d: Kullanıcı depo ataması
    "ALTER TABLE kullanicilar ADD COLUMN depo_id INT DEFAULT NULL;",
    "ALTER TABLE kullanicilar ADD CONSTRAINT fk_kullanici_depo FOREIGN KEY (depo_id) REFERENCES depolar(id);",
    "ALTER TABLE kullanicilar ADD COLUMN depo_erisimi_yok TINYINT(1) NOT NULL DEFAULT 0;",
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
