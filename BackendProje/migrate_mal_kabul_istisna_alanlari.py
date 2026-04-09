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

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection


TABLE_NAME = "mal_kabul_kalemleri"
COLUMNS = {
    "istisna_tip": "ALTER TABLE `mal_kabul_kalemleri` ADD COLUMN `istisna_tip` VARCHAR(50) NULL",
    "istisna_aciklama": "ALTER TABLE `mal_kabul_kalemleri` ADD COLUMN `istisna_aciklama` TEXT NULL",
    "gerceklesen_miktar": "ALTER TABLE `mal_kabul_kalemleri` ADD COLUMN `gerceklesen_miktar` INT NULL",
}


def load_environment() -> None:
    base_dir = Path(__file__).resolve().parent
    env_path = base_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()


def build_db_url() -> str:
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    name = os.getenv("DB_NAME")

    missing = [
        key
        for key, value in {
            "DB_USER": user,
            "DB_HOST": host,
            "DB_PORT": port,
            "DB_NAME": name,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")

    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"


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
    load_environment()
    db_name = os.getenv("DB_NAME")
    if not db_name:
        raise RuntimeError("DB_NAME is not defined")

    engine = create_engine(build_db_url(), pool_pre_ping=True)
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
