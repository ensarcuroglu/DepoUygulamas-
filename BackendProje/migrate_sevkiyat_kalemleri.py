"""
Migration: sevkiyat_kalemleri tablosunu ve benzersiz plan/kalem kuralını ekle.

Çalıştırma:
    python migrate_sevkiyat_kalemleri.py
"""

import os
import sys

from sqlalchemy import inspect, text

sys.path.insert(0, os.path.dirname(__file__))

from database import engine


TABLE_NAME = "sevkiyat_kalemleri"
UNIQUE_NAME = "uq_sevkiyat_kalemi_plan_siparis_kalem"


def _create_table_sql() -> str:
    if engine.dialect.name == "sqlite":
        return f"""
        CREATE TABLE {TABLE_NAME} (
            id INTEGER NOT NULL PRIMARY KEY,
            sevkiyat_id INTEGER NOT NULL,
            siparis_kalemi_id INTEGER NOT NULL,
            urun_id INTEGER NOT NULL,
            miktar INTEGER NOT NULL,
            CONSTRAINT {UNIQUE_NAME} UNIQUE (sevkiyat_id, siparis_kalemi_id),
            FOREIGN KEY(sevkiyat_id) REFERENCES sevkiyat_planlari (id),
            FOREIGN KEY(siparis_kalemi_id) REFERENCES siparis_kalemleri (id),
            FOREIGN KEY(urun_id) REFERENCES urunler (id)
        )
        """

    return f"""
    CREATE TABLE {TABLE_NAME} (
        id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        sevkiyat_id INT NOT NULL,
        siparis_kalemi_id INT NOT NULL,
        urun_id INT NOT NULL,
        miktar INT NOT NULL,
        CONSTRAINT fk_sevkiyat_kalemleri_plan
            FOREIGN KEY (sevkiyat_id) REFERENCES sevkiyat_planlari(id),
        CONSTRAINT fk_sevkiyat_kalemleri_siparis_kalemi
            FOREIGN KEY (siparis_kalemi_id) REFERENCES siparis_kalemleri(id),
        CONSTRAINT fk_sevkiyat_kalemleri_urun
            FOREIGN KEY (urun_id) REFERENCES urunler(id),
        CONSTRAINT {UNIQUE_NAME}
            UNIQUE (sevkiyat_id, siparis_kalemi_id)
    )
    """


def run():
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    with engine.connect() as conn:
        if TABLE_NAME not in table_names:
            conn.execute(text(_create_table_sql()))
            conn.commit()
            print(f"✓ {TABLE_NAME} tablosu oluşturuldu.")
        else:
            print(f"- {TABLE_NAME} tablosu zaten mevcut.")

        inspector = inspect(engine)
        unique_constraints = {
            constraint["name"]
            for constraint in inspector.get_unique_constraints(TABLE_NAME)
            if constraint.get("name")
        }
        indexes = {
            index["name"]
            for index in inspector.get_indexes(TABLE_NAME)
            if index.get("unique")
        }

        if UNIQUE_NAME not in unique_constraints and UNIQUE_NAME not in indexes:
            conn.execute(
                text(
                    f"CREATE UNIQUE INDEX {UNIQUE_NAME} "
                    f"ON {TABLE_NAME} (sevkiyat_id, siparis_kalemi_id)"
                )
            )
            conn.commit()
            print(f"✓ {UNIQUE_NAME} benzersiz indeksi oluşturuldu.")
        else:
            print(f"- {UNIQUE_NAME} zaten mevcut.")

    final_tables = set(inspect(engine).get_table_names())
    if TABLE_NAME not in final_tables:
        raise RuntimeError(f"Migration doğrulaması başarısız: {TABLE_NAME} oluşturulamadı.")

    final_unique_constraints = {
        constraint["name"]
        for constraint in inspect(engine).get_unique_constraints(TABLE_NAME)
        if constraint.get("name")
    }
    final_indexes = {
        index["name"]
        for index in inspect(engine).get_indexes(TABLE_NAME)
        if index.get("unique")
    }
    if UNIQUE_NAME not in final_unique_constraints and UNIQUE_NAME not in final_indexes:
        raise RuntimeError(
            f"Migration doğrulaması başarısız: {UNIQUE_NAME} oluşturulamadı."
        )


if __name__ == "__main__":
    run()
