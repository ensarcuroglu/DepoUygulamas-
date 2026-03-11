"""
Migration: Kullanici tablosuna refresh token sütunları ekle
Çalıştırma: python migrate_refresh_token.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import engine
from sqlalchemy import text, inspect

def run():
    inspector = inspect(engine)
    cols = [c['name'] for c in inspector.get_columns('kullanicilar')]
    print(f"Mevcut sütunlar: {cols}")

    with engine.connect() as conn:
        if 'refresh_token_hash' not in cols:
            conn.execute(text(
                'ALTER TABLE kullanicilar ADD COLUMN refresh_token_hash VARCHAR(255) NULL'
            ))
            print("✓ refresh_token_hash sütunu eklendi.")
        else:
            print("- refresh_token_hash zaten mevcut, atlandı.")

        if 'refresh_token_son_kullanim' not in cols:
            conn.execute(text(
                'ALTER TABLE kullanicilar ADD COLUMN refresh_token_son_kullanim DATETIME NULL'
            ))
            print("✓ refresh_token_son_kullanim sütunu eklendi.")
        else:
            print("- refresh_token_son_kullanim zaten mevcut, atlandı.")

        conn.commit()

    print("\nMigration tamamlandı!")

if __name__ == "__main__":
    run()
