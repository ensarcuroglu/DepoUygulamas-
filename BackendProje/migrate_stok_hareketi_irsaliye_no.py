"""
Migration: stok_hareketleri tablosuna irsaliye_no sütunu ekle.

Çalıştırma:
    python migrate_stok_hareketi_irsaliye_no.py
"""

import os
import sys

from sqlalchemy import inspect, text

sys.path.insert(0, os.path.dirname(__file__))

from database import engine


TABLE_NAME = "stok_hareketleri"
COLUMN_NAME = "irsaliye_no"


def run():
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    if TABLE_NAME not in table_names:
        print(f"! {TABLE_NAME} tablosu bulunamadı. Migration atlandı.")
        return

    mevcut_sutunlar = {col["name"] for col in inspector.get_columns(TABLE_NAME)}
    if COLUMN_NAME in mevcut_sutunlar:
        print(f"- {TABLE_NAME}.{COLUMN_NAME} zaten mevcut, atlandı.")
        return

    if engine.dialect.name == "sqlite":
        # nosemgrep
        sql = text(
            f"ALTER TABLE {TABLE_NAME} ADD COLUMN {COLUMN_NAME} VARCHAR(100)"
        )
    else:
        # nosemgrep
        sql = text(
            f"ALTER TABLE {TABLE_NAME} ADD COLUMN {COLUMN_NAME} VARCHAR(100) NULL"
        )

    with engine.connect() as conn:
        conn.execute(sql)
        conn.commit()

    dogrulama_sutunlari = {
        col["name"] for col in inspect(engine).get_columns(TABLE_NAME)
    }
    if COLUMN_NAME not in dogrulama_sutunlari:
        raise RuntimeError(
            f"Migration doğrulaması başarısız: {TABLE_NAME}.{COLUMN_NAME} oluşturulamadı."
        )

    print(f"✓ {TABLE_NAME}.{COLUMN_NAME} sütunu başarıyla eklendi.")


if __name__ == "__main__":
    run()
