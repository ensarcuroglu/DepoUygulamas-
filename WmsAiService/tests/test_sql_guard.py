from __future__ import annotations

import pytest

from sql_guard import SQL_DEFAULT_LIMIT, SQL_MAX_LIMIT, SqlValidationError, clean_and_validate


def test_allowed_view_select_adds_default_limit() -> None:
    sql = "SELECT urun_adi FROM ai_stok_durumu_view;"

    assert clean_and_validate(sql) == (
        f"SELECT urun_adi FROM ai_stok_durumu_view LIMIT {SQL_DEFAULT_LIMIT};"
    )


def test_allowed_existing_limit_is_preserved() -> None:
    sql = "SELECT palet_no FROM ai_palet_view WHERE aktif = 1 LIMIT 10;"

    assert clean_and_validate(sql) == sql


def test_large_limit_is_clamped() -> None:
    sql = "SELECT palet_no FROM ai_palet_view WHERE aktif = 1 LIMIT 500;"

    assert clean_and_validate(sql) == (
        f"SELECT palet_no FROM ai_palet_view WHERE aktif = 1 LIMIT {SQL_MAX_LIMIT};"
    )


def test_mysql_offset_limit_row_count_is_clamped() -> None:
    sql = "SELECT palet_no FROM ai_palet_view LIMIT 10, 500;"

    assert clean_and_validate(sql) == f"SELECT palet_no FROM ai_palet_view LIMIT 10, {SQL_MAX_LIMIT};"


def test_aggregate_only_count_does_not_add_limit() -> None:
    sql = "SELECT COUNT(*) AS palet_sayisi FROM ai_palet_view WHERE aktif = 1;"

    assert clean_and_validate(sql) == sql


def test_aggregate_only_multiple_aggregates_does_not_add_limit() -> None:
    sql = "SELECT COUNT(*) AS adet, SUM(koli_adedi) AS toplam FROM ai_palet_view;"

    assert clean_and_validate(sql) == sql


def test_grouped_aggregate_is_treated_as_list_and_limited() -> None:
    sql = "SELECT depo_adi, COUNT(*) AS adet FROM ai_palet_view GROUP BY depo_adi;"

    assert clean_and_validate(sql) == (
        f"SELECT depo_adi, COUNT(*) AS adet FROM ai_palet_view GROUP BY depo_adi LIMIT {SQL_DEFAULT_LIMIT};"
    )


def test_cte_with_allowed_view_and_local_alias_is_allowed() -> None:
    sql = (
        "WITH aktif AS (SELECT palet_id FROM ai_palet_view WHERE aktif = 1) "
        "SELECT palet_id FROM aktif;"
    )

    assert clean_and_validate(sql) == (
        "WITH aktif AS (SELECT palet_id FROM ai_palet_view WHERE aktif = 1) "
        f"SELECT palet_id FROM aktif LIMIT {SQL_DEFAULT_LIMIT};"
    )


def test_schema_qualified_backtick_allowed_view_is_allowed() -> None:
    sql = "SELECT palet_no FROM `depo_yonetim`.`ai_palet_view` LIMIT 5;"

    assert clean_and_validate(sql) == sql


def test_forbidden_words_inside_string_literals_are_ignored() -> None:
    sql = "SELECT urun_adi FROM ai_stok_durumu_view WHERE urun_adi LIKE '%DROP SLEEP(10)%';"

    assert clean_and_validate(sql) == (
        "SELECT urun_adi FROM ai_stok_durumu_view "
        f"WHERE urun_adi LIKE '%DROP SLEEP(10)%' LIMIT {SQL_DEFAULT_LIMIT};"
    )


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM ai_palet_view;",
        "SELECT * FROM kullanicilar;",
        "SELECT 1;",
        "SELECT 1 WHERE 1=0;",
        "SELECT @@version;",
        "SELECT VERSION() FROM ai_palet_view;",
        "SELECT USER FROM ai_palet_view;",
        "SELECT CURRENT_USER FROM ai_palet_view;",
        "SELECT SLEEP(10) FROM ai_palet_view;",
        "SELECT BENCHMARK(100, MD5('x')) FROM ai_palet_view;",
        "SELECT LOAD_FILE('/etc/passwd') FROM ai_palet_view;",
        "SELECT * INTO OUTFILE '/tmp/export.txt' FROM ai_palet_view;",
        "SELECT * FROM information_schema.tables;",
        "SELECT * FROM mysql.user;",
        "SELECT * FROM ai_palet_view; DROP TABLE ai_palet_view;",
        "SELECT * FROM ai_palet_view -- comment",
        "SELECT * FROM ai_palet_view /* comment */",
        "WITH x AS (SELECT * FROM kullanicilar) SELECT * FROM x;",
    ],
)
def test_rejects_unsafe_sql(sql: str) -> None:
    with pytest.raises(SqlValidationError):
        clean_and_validate(sql)
