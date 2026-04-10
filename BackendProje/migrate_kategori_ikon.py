import sys
import logging
from sqlalchemy import text
from database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_kategori_ikon():
    logger.info("Veritabanına bağlanılıyor...")
    
    try:
        with engine.connect() as conn:
            # Önce sütunun var olup olmadığını kontrol edelim
            check_sql = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='kategoriler' AND column_name='ikon';
            """)
            result = conn.execute(check_sql).fetchone()
            
            if result:
                logger.info("'ikon' kolonu 'kategoriler' tablosunda zaten mevcut.")
            else:
                logger.info("'ikon' kolonu yok, ekleniyor...")
                # SQLite veya MySQL'de sütun ekleme syntax'ı temelde aynıdır
                # ama MySQL veritabanı olduğunu belirttiğiniz için:
                add_col_sql = text("""
                    ALTER TABLE kategoriler 
                    ADD COLUMN ikon VARCHAR(50) DEFAULT 'FolderOpen';
                """)
                conn.execute(add_col_sql)
                conn.commit()
                logger.info("Migrasyon başarıyla tamamlandı: 'ikon' kolonu eklendi.")
    except Exception as e:
        logger.error(f"Hata oluştu: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate_kategori_ikon()
