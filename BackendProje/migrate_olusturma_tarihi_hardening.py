"""
olusturma_tarihi hardening migration

Purpose:
1) Backfill NULL values in `olusturma_tarihi` with UTC_TIMESTAMP.
2) Harden every `olusturma_tarihi` column as
   `DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP`.

Usage:
    python migrate_olusturma_tarihi_hardening.py
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection


COLUMN_NAME = "olusturma_tarihi"


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
        k
        for k, v in {
            "DB_USER": user,
            "DB_HOST": host,
            "DB_PORT": port,
            "DB_NAME": name,
        }.items()
        if not v
    ]
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")

    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"


def fetch_target_tables(conn: Connection, db_name: str) -> list[str]:
    q = text(
        """
        SELECT TABLE_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = :db_name
          AND COLUMN_NAME = :column_name
        ORDER BY TABLE_NAME
        """
    )
    rows = conn.execute(q, {"db_name": db_name, "column_name": COLUMN_NAME}).fetchall()
    return [r[0] for r in rows]


def count_nulls(conn: Connection, table_name: str) -> int:
    return int(
        conn.execute(
            # nosemgrep
            text(f"SELECT COUNT(*) FROM `{table_name}` WHERE `{COLUMN_NAME}` IS NULL")
        ).scalar()
    )


def backfill_nulls(conn: Connection, table_name: str) -> int:
    result = conn.execute(
        text(
            f"UPDATE `{table_name}` "
            f"SET `{COLUMN_NAME}` = UTC_TIMESTAMP() "
            f"WHERE `{COLUMN_NAME}` IS NULL"
        )
    )
    return int(result.rowcount or 0)


def harden_column(conn: Connection, table_name: str) -> None:
    conn.execute(
        text(
            f"ALTER TABLE `{table_name}` "
            f"MODIFY COLUMN `{COLUMN_NAME}` DATETIME NOT NULL "
            f"DEFAULT CURRENT_TIMESTAMP"
        )
    )


def fetch_column_state(conn: Connection, db_name: str, table_name: str) -> tuple[str, str | None, str]:
    row = conn.execute(
        text(
            """
            SELECT IS_NULLABLE, COLUMN_DEFAULT, DATA_TYPE
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = :db_name
              AND TABLE_NAME = :table_name
              AND COLUMN_NAME = :column_name
            """
        ),
        {"db_name": db_name, "table_name": table_name, "column_name": COLUMN_NAME},
    ).fetchone()
    if not row:
        raise RuntimeError(f"{table_name}.{COLUMN_NAME} not found")
    return str(row[0]), row[1], str(row[2])


def main() -> None:
    load_environment()
    db_name = os.getenv("DB_NAME")
    if not db_name:
        raise RuntimeError("DB_NAME is not defined")

    engine = create_engine(build_db_url(), pool_pre_ping=True)
    print(f"[INFO] Target database: {db_name}")

    with engine.begin() as conn:
        tables = fetch_target_tables(conn, db_name)
        if not tables:
            raise RuntimeError(f"No table contains `{COLUMN_NAME}`")
        print(f"[INFO] Found {len(tables)} tables: {', '.join(tables)}")

    print("\n[STEP 1] NULL backfill starting...")
    with engine.begin() as conn:
        for table in tables:
            null_before = count_nulls(conn, table)
            updated = backfill_nulls(conn, table) if null_before > 0 else 0
            null_after = count_nulls(conn, table)
            print(
                f"[BACKFILL] {table}: "
                f"null_before={null_before}, updated={updated}, null_after={null_after}"
            )

    print("\n[STEP 2] Schema hardening starting...")
    with engine.begin() as conn:
        for table in tables:
            harden_column(conn, table)
            is_nullable, default_value, data_type = fetch_column_state(conn, db_name, table)
            print(
                f"[HARDEN] {table}: data_type={data_type}, "
                f"is_nullable={is_nullable}, default={default_value}"
            )

    print("\n[STEP 3] Final verification...")
    with engine.connect() as conn:
        has_null_any = False
        for table in tables:
            null_count = count_nulls(conn, table)
            print(f"[VERIFY] {table}: null_count={null_count}")
            if null_count > 0:
                has_null_any = True

    if has_null_any:
        raise RuntimeError("Verification failed: some tables still have NULL olusturma_tarihi")

    print("\nMigration completed: all `olusturma_tarihi` values backfilled and hardened.")


if __name__ == "__main__":
    main()
