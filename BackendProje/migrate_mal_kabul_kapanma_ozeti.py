"""
Mal kabul irsaliyeleri kapanma_ozeti kolonu migration.

Adds nullable JSON column `kapanma_ozeti` to `mal_kabul_irsaliyeleri`.

Usage:
    python migrate_mal_kabul_kapanma_ozeti.py
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection


TABLE_NAME = "mal_kabul_irsaliyeleri"
COLUMN_NAME = "kapanma_ozeti"
COLUMN_DDL = (
    "ALTER TABLE `mal_kabul_irsaliyeleri` "
    "ADD COLUMN `kapanma_ozeti` JSON NULL"
)


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
        if column_exists(conn, db_name, TABLE_NAME, COLUMN_NAME):
            print(f"[SKIP] {TABLE_NAME}.{COLUMN_NAME} already exists")
        else:
            conn.execute(text(COLUMN_DDL))
            print(f"[OK] Added column: {TABLE_NAME}.{COLUMN_NAME}")

    with engine.connect() as conn:
        if not column_exists(conn, db_name, TABLE_NAME, COLUMN_NAME):
            raise RuntimeError(
                f"Migration verification failed. Missing column: {TABLE_NAME}.{COLUMN_NAME}"
            )

    print("[DONE] Mal kabul kapanma_ozeti migration completed successfully.")


if __name__ == "__main__":
    main()
