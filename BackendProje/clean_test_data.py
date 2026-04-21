"""
Clean transactional test/development data while preserving master data.

Default mode is a dry run. To execute:

    python clean_test_data.py --execute --confirm-db-name depo_yonetim

For the dedicated pytest database:

    python clean_test_data.py --env-file .env.test
    python clean_test_data.py --env-file .env.test --execute --confirm-db-name depo_db_test

Safer, transactional cleanup uses DELETE by default. TRUNCATE is available when
you explicitly want faster cleanup and auto-increment reset:

    python clean_test_data.py --execute --confirm-db-name depo_yonetim --method truncate
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv
from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection


BASE_DIR = Path(__file__).resolve().parent


def _resolve_env_file_from_argv(argv: list[str]) -> Path:
    env_file = ".env"
    for index, arg in enumerate(argv):
        if arg == "--env-file" and index + 1 < len(argv):
            env_file = argv[index + 1]
            break
        if arg.startswith("--env-file="):
            env_file = arg.split("=", 1)[1]
            break

    env_path = Path(env_file)
    if not env_path.is_absolute():
        env_path = BASE_DIR / env_path
    if not env_path.exists():
        raise FileNotFoundError(f"Env file not found: {env_path}")
    return env_path


LOADED_ENV_FILE = _resolve_env_file_from_argv(sys.argv[1:])
load_dotenv(LOADED_ENV_FILE, override=True)
sys.path.insert(0, str(BASE_DIR))

import models  # noqa: E402,F401  # Load all SQLAlchemy models into Base.metadata.
from database import Base, engine  # noqa: E402


MASTER_TABLES: tuple[str, ...] = (
    "kullanicilar",
    "markalar",
    "kategoriler",
    "depolar",
    "zonlar",
    "raflar",
    "tedarikciler",
    "urunler",
    "rapor_sablonlari",
)

# These are configuration-like records, not operational movement data.
# They are preserved by default and can be cleaned with --include-report-schedules.
OPTIONAL_TRANSACTIONAL_TABLES: tuple[str, ...] = (
    "rapor_schedules",
)

# Ordered from children to parents. FK checks are still disabled during cleanup,
# but keeping the natural dependency order makes dry-run output easier to audit.
TRANSACTIONAL_TABLES: tuple[str, ...] = (
    "idempotency_kayitlari",
    "palet_rezervasyonlari",
    "toplama_gorevleri",
    "yerlestirme_gorevleri",
    "palet_durum_log",
    "stok_hareketleri",
    "stok_sayim_kalemleri",
    "stok_sayimlar",
    "rapor_loglari",
    "destek_talepleri",
    "sistem_loglari",
    "irsaliyeler",
    "sevkiyat_kalemleri",
    "sevkiyat_planlari",
    "siparis_kalemleri",
    "siparisler",
    "mal_kabul_kalemleri",
    "mal_kabul_irsaliyeleri",
    "paletler",
    "lotlar",
    "uretim_seri_sayac",
)

ALLOWED_DB_NAMES: tuple[str, ...] = (
    "depo_yonetim",
    "depo_db",
    "depo_db_test",
    "depo_yonetim_test",
)

DANGEROUS_DB_NAME_PARTS: tuple[str, ...] = (
    "prod",
    "production",
    "canli",
    "live",
)


@dataclass(frozen=True)
class TableCount:
    table: str
    count: int


def _quote_identifier(name: str) -> str:
    if "`" in name:
        raise ValueError(f"Invalid table name: {name!r}")
    return f"`{name}`"


def _get_current_database(conn: Connection) -> str:
    db_name = conn.execute(text("SELECT DATABASE()")).scalar()
    if not db_name:
        raise RuntimeError("No database selected.")
    return str(db_name)


def _count_table(conn: Connection, table: str) -> int:
    return int(conn.execute(text(f"SELECT COUNT(*) FROM {_quote_identifier(table)}")).scalar() or 0)


def _count_tables(conn: Connection, tables: Iterable[str]) -> list[TableCount]:
    return [TableCount(table=table, count=_count_table(conn, table)) for table in tables]


def _print_counts(title: str, counts: Iterable[TableCount]) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    for item in counts:
        print(f"{item.table:<30} {item.count:>8}")


def _format_env_file_for_command() -> str:
    try:
        env_file = str(LOADED_ENV_FILE.relative_to(BASE_DIR))
    except ValueError:
        env_file = str(LOADED_ENV_FILE)
    if " " in env_file:
        return f'"{env_file}"'
    return env_file


def _build_clean_table_list(include_report_schedules: bool) -> tuple[str, ...]:
    tables = list(TRANSACTIONAL_TABLES)
    if include_report_schedules:
        tables.extend(OPTIONAL_TRANSACTIONAL_TABLES)
    return tuple(tables)


def _validate_database_name(db_name: str, confirm_db_name: str | None, execute: bool) -> None:
    lowered = db_name.lower()
    if any(part in lowered for part in DANGEROUS_DB_NAME_PARTS):
        raise RuntimeError(
            f"Refusing to clean database with dangerous-looking name: {db_name!r}"
        )

    allowed = {name.lower() for name in ALLOWED_DB_NAMES}
    env_allowed = os.getenv("CLEAN_TEST_DATA_ALLOWED_DBS", "")
    allowed.update(name.strip().lower() for name in env_allowed.split(",") if name.strip())
    if lowered not in allowed:
        raise RuntimeError(
            f"Database {db_name!r} is not in the allowed cleanup list. "
            "Set CLEAN_TEST_DATA_ALLOWED_DBS or update ALLOWED_DB_NAMES intentionally."
        )

    if execute and confirm_db_name != db_name:
        raise RuntimeError(
            "Execution requires an exact database confirmation. "
            f"Use: --confirm-db-name {db_name}"
        )


def _validate_schema(conn: Connection, clean_tables: tuple[str, ...]) -> None:
    inspector = inspect(conn)
    actual_tables = set(inspector.get_table_names())
    required_tables = set(MASTER_TABLES) | set(clean_tables)
    missing = sorted(required_tables - actual_tables)
    if missing:
        raise RuntimeError(
            "Database schema is not ready. Missing required tables:\n  "
            + "\n  ".join(missing)
        )

    model_tables = set(Base.metadata.tables.keys())
    unknown_clean = sorted(set(clean_tables) - model_tables)
    if unknown_clean:
        raise RuntimeError(
            "Cleanup list contains tables that are not mapped in models.py:\n  "
            + "\n  ".join(unknown_clean)
        )


def _validate_no_preserved_table_references_clean_tables(
    conn: Connection,
    clean_tables: tuple[str, ...],
) -> None:
    inspector = inspect(conn)
    clean_set = set(clean_tables)
    actual_tables = set(inspector.get_table_names())
    preserved_tables = sorted(actual_tables - clean_set)
    violations: list[str] = []

    for table in preserved_tables:
        for fk in inspector.get_foreign_keys(table):
            referred_table = fk.get("referred_table")
            if referred_table in clean_set:
                columns = ", ".join(fk.get("constrained_columns") or [])
                ref_columns = ", ".join(fk.get("referred_columns") or [])
                violations.append(
                    f"{table}({columns}) -> {referred_table}({ref_columns})"
                )

    if violations:
        raise RuntimeError(
            "A preserved table references a table selected for cleanup. "
            "Review the table list before continuing:\n  "
            + "\n  ".join(violations)
        )


def _validate_master_counts_unchanged(
    before: list[TableCount],
    after: list[TableCount],
) -> None:
    before_map = {item.table: item.count for item in before}
    after_map = {item.table: item.count for item in after}
    changed = [
        f"{table}: {before_map[table]} -> {after_map.get(table)}"
        for table in before_map
        if before_map[table] != after_map.get(table)
    ]
    if changed:
        raise RuntimeError(
            "Master table row counts changed unexpectedly:\n  "
            + "\n  ".join(changed)
        )


def _validate_clean_tables_empty(after: list[TableCount]) -> None:
    not_empty = [f"{item.table}: {item.count}" for item in after if item.count != 0]
    if not_empty:
        raise RuntimeError(
            "Some transactional tables are not empty after cleanup:\n  "
            + "\n  ".join(not_empty)
        )


def _delete_tables(conn: Connection, tables: tuple[str, ...]) -> None:
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    try:
        for table in tables:
            conn.execute(text(f"DELETE FROM {_quote_identifier(table)}"))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        conn.commit()


def _truncate_tables(conn: Connection, tables: tuple[str, ...]) -> None:
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    try:
        for table in tables:
            conn.execute(text(f"TRUNCATE TABLE {_quote_identifier(table)}"))
        conn.commit()
    except Exception:
        # MySQL TRUNCATE performs implicit commits. This rollback only protects
        # pending statements around the failing operation.
        conn.rollback()
        raise
    finally:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        conn.commit()


def run(
    *,
    execute: bool = False,
    confirm_db_name: str | None = None,
    method: str = "delete",
    include_report_schedules: bool = False,
) -> None:
    clean_tables = _build_clean_table_list(include_report_schedules)

    with engine.connect() as conn:
        db_name = _get_current_database(conn)
        _validate_database_name(db_name, confirm_db_name, execute)
        _validate_schema(conn, clean_tables)
        _validate_no_preserved_table_references_clean_tables(conn, clean_tables)

        master_before = _count_tables(conn, MASTER_TABLES)
        clean_before = _count_tables(conn, clean_tables)

        print("Clean transactional data")
        print("=" * 24)
        print(f"Database : {db_name}")
        print(f"Env file : {LOADED_ENV_FILE.name}")
        print(f"Mode     : {'EXECUTE' if execute else 'DRY-RUN'}")
        print(f"Method   : {method}")
        print(f"Schedule : {'clean rapor_schedules' if include_report_schedules else 'preserve rapor_schedules'}")

        _print_counts("Master tables preserved", master_before)
        _print_counts("Transactional tables to clean", clean_before)

        total_rows = sum(item.count for item in clean_before)
        if not execute:
            print(f"\nDRY-RUN complete. Rows that would be removed: {total_rows}")
            print(
                f"To execute: python clean_test_data.py --env-file {_format_env_file_for_command()} --execute "
                f"--confirm-db-name {db_name}"
            )
            return

        if method == "delete":
            _delete_tables(conn, clean_tables)
        elif method == "truncate":
            _truncate_tables(conn, clean_tables)
        else:
            raise ValueError(f"Unsupported cleanup method: {method!r}")

        master_after = _count_tables(conn, MASTER_TABLES)
        clean_after = _count_tables(conn, clean_tables)
        _validate_master_counts_unchanged(master_before, master_after)
        _validate_clean_tables_empty(clean_after)

        _print_counts("Transactional tables after cleanup", clean_after)
        print(f"\nCleanup complete. Removed rows: {total_rows}")
        print("Master table row counts are unchanged.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Delete transactional warehouse/application data while preserving "
            "master data such as users, products, warehouses and report templates."
        )
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Environment file to load before connecting. Example: .env.test",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually clean the database. Without this flag the script only prints a dry-run.",
    )
    parser.add_argument(
        "--confirm-db-name",
        default=None,
        help="Required with --execute. Must exactly match SELECT DATABASE().",
    )
    parser.add_argument(
        "--method",
        choices=("delete", "truncate"),
        default="delete",
        help="delete is transactional; truncate is faster and resets auto-increment in MySQL.",
    )
    parser.add_argument(
        "--include-report-schedules",
        action="store_true",
        help="Also clean rapor_schedules. By default schedules are preserved as configuration.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(
        execute=args.execute,
        confirm_db_name=args.confirm_db_name,
        method=args.method,
        include_report_schedules=args.include_report_schedules,
    )
