"""
Mal kabul kalemi istisna alanlari migration.

Adds nullable exception-tracking columns to `mal_kabul_kalemleri`:
  - istisna_tip
  - istisna_aciklama
  - gerceklesen_miktar

Usage:
    python migrate_mal_kabul_istisna_alanlari.py
"""

from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection
from app.core.config import get_settings


TABLE_NAME = "mal_kabul_kalemleri"
COLUMNS = {
    "istisna_tip": "ALTER TABLE `mal_kabul_kalemleri` ADD COLUMN `istisna_tip` VARCHAR(50) NULL",
    "istisna_aciklama": "ALTER TABLE `mal_kabul_kalemleri` ADD COLUMN `istisna_aciklama` TEXT NULL",
    "gerceklesen_miktar": "ALTER TABLE `mal_kabul_kalemleri` ADD COLUMN `gerceklesen_miktar` INT NULL",
}


def column_exists(conn: Connection, db_name: str, table_name: str, column_name: str) -> bool:
    result = conn.execute(
        text(
            """
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = :db_name
              AND TABLE_NAME = :table_name
              AND COLUMN_NAME = :column_name
            """
        ),
        {
            "db_name": db_name,
            "table_name": table_name,
            "column_name": column_name,
        },
    ).scalar()
    return bool(result)


def main() -> None:
    settings = get_settings()
    db_name = settings.db_name

    engine = create_engine(settings.sqlalchemy_database_url, pool_pre_ping=True)
    print(f"[INFO] Target database: {db_name}")
    print(f"[INFO] Updating table: {TABLE_NAME}")

    with engine.begin() as conn:
        for column_name, ddl in COLUMNS.items():
            if column_exists(conn, db_name, TABLE_NAME, column_name):
                print(f"[SKIP] {TABLE_NAME}.{column_name} already exists")
                continue

            conn.execute(text(ddl))
            print(f"[OK] Added column: {TABLE_NAME}.{column_name}")

    with engine.connect() as conn:
        missing = [
            column_name
            for column_name in COLUMNS
            if not column_exists(conn, db_name, TABLE_NAME, column_name)
        ]

    if missing:
        raise RuntimeError(f"Migration verification failed. Missing columns: {', '.join(missing)}")

    print("[DONE] Mal kabul istisna alanlari migration completed successfully.")


if __name__ == "__main__":
    main()
