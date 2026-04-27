"""
Faz 0.4 — Yerleştirme Görevi (Putaway Task) Migration

Yeni tablo: yerlestirme_gorevleri
Composite index: durum + oncelik + olusturma_tarihi (FIFO görev çekme sorgusunu hızlandırır)
"""

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import get_settings

settings = get_settings()

SQLALCHEMY_DATABASE_URL = settings.sqlalchemy_database_url

engine = create_engine(SQLALCHEMY_DATABASE_URL)

statements = [
    # Ana tablo
    """
    CREATE TABLE IF NOT EXISTS yerlestirme_gorevleri (
        id INT AUTO_INCREMENT PRIMARY KEY,
        palet_id INT NOT NULL,
        mal_kabul_irsaliye_id INT DEFAULT NULL,
        tip VARCHAR(20) NOT NULL DEFAULT 'Yerlestirme',
        kaynak_raf_id INT DEFAULT NULL,
        onerilen_raf_id INT NOT NULL,
        gerceklesen_raf_id INT DEFAULT NULL,
        durum VARCHAR(20) NOT NULL DEFAULT 'Bekliyor',
        oncelik INT NOT NULL DEFAULT 5,
        atanan_kullanici_id INT DEFAULT NULL,
        override_kullanici_id INT DEFAULT NULL,
        override_neden TEXT DEFAULT NULL,
        olusturma_tarihi DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        baslama_tarihi DATETIME DEFAULT NULL,
        tamamlanma_tarihi DATETIME DEFAULT NULL,
        iptal_nedeni TEXT DEFAULT NULL,
        CONSTRAINT fk_yg_palet FOREIGN KEY (palet_id) REFERENCES paletler(id),
        CONSTRAINT fk_yg_mal_kabul FOREIGN KEY (mal_kabul_irsaliye_id) REFERENCES mal_kabul_irsaliyeleri(id),
        CONSTRAINT fk_yg_kaynak_raf FOREIGN KEY (kaynak_raf_id) REFERENCES raflar(id),
        CONSTRAINT fk_yg_onerilen_raf FOREIGN KEY (onerilen_raf_id) REFERENCES raflar(id),
        CONSTRAINT fk_yg_gerceklesen_raf FOREIGN KEY (gerceklesen_raf_id) REFERENCES raflar(id),
        CONSTRAINT fk_yg_atanan_kullanici FOREIGN KEY (atanan_kullanici_id) REFERENCES kullanicilar(id),
        CONSTRAINT fk_yg_override_kullanici FOREIGN KEY (override_kullanici_id) REFERENCES kullanicilar(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
    # Composite index — MySQL 'IF NOT EXISTS' desteklemediği için sadeleştirildi
    """
    CREATE INDEX ix_yg_fifo
    ON yerlestirme_gorevleri (durum, oncelik, olusturma_tarihi);
    """,
]


def tablo_var_mi(conn, tablo_adi: str) -> bool:
    result = conn.execute(
        text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = :t"),
        {"t": tablo_adi},
    )
    return result.scalar() > 0


print("Faz 0.4 — Yerleştirme Görevi Migration başlatılıyor...")

try:
    with engine.begin() as conn:
        if tablo_var_mi(conn, "yerlestirme_gorevleri"):
            print("  Tablo zaten var — atlandı.")
        else:
            for stmt in statements:
                try:
                    conn.execute(text(stmt))
                    print("  OK.")
                except SQLAlchemyError as e:
                    print(f"  Hata: {e}")
                    raise

    print("\nMigration tamamlandı.")
except Exception as e:
    print(f"Bağlantı hatası: {e}")
