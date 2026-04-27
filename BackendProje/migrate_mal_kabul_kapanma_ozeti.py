"""
Mal kabul irsaliyeleri kapanma_ozeti kolonu migration.

Adds nullable JSON column `kapanma_ozeti` to `mal_kabul_irsaliyeleri`.

Usage:
    python migrate_mal_kabul_kapanma_ozeti.py
"""

from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection
from app.core.config import get_settings


TABLE_NAME = "mal_kabul_irsaliyeleri"
COLUMN_NAME = "kapanma_ozeti"
COLUMN_DDL = (
    "ALTER TABLE `mal_kabul_irsaliyeleri` "
    "ADD COLUMN `kapanma_ozeti` JSON NULL"
)


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
