"""
SQL guvenlik katmani.

LLM'in urettigi SQL'i calistirmadan once:
1. Markdown / "SQLQuery:" gibi gurultuyu temizle
2. Sadece tek statement oldugunu dogrula
3. SELECT disi bir komut varsa reddet
4. Yasakli keyword, sistem schema ve sistem fonksiyonlarini reddet
5. Whitelist'teki ai_*_view'lar disinda referans varsa reddet
6. Liste sorgularinda LIMIT politikasini uygula
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

# LLM ciktisinda sik gorulen gurultu prefix/suffix'leri
_NOISE_PREFIXES = (
    "sqlquery:",
    "sql query:",
    "sql:",
    "query:",
    "answer:",
    "cevap:",
)

_FORBIDDEN_KEYWORDS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "RENAME",
    "GRANT",
    "REVOKE",
    "REPLACE",
    "MERGE",
    "CALL",
    "EXEC",
    "EXECUTE",
    "LOAD",
    "HANDLER",
    "LOCK",
    "UNLOCK",
    "SET",
    "INTO",
    "OUTFILE",
    "DUMPFILE",
)

_FORBIDDEN_SCHEMAS = (
    "INFORMATION_SCHEMA",
    "PERFORMANCE_SCHEMA",
    "MYSQL",
    "SYS",
)

_FORBIDDEN_FUNCTIONS = (
    "SLEEP",
    "BENCHMARK",
    "UUID",
    "RAND",
    "DATABASE",
    "VERSION",
    "USER",
    "CURRENT_USER",
    "CONNECTION_ID",
    "LOAD_FILE",
)

_FORBIDDEN_BARE_TOKENS = (
    "@@",
    "CURRENT_USER",
    "USER",
)

_AGGREGATE_FUNCTIONS = (
    "COUNT",
    "SUM",
    "AVG",
    "MIN",
    "MAX",
)

SQL_DEFAULT_LIMIT = int(os.getenv("SQL_DEFAULT_LIMIT", "50"))
SQL_MAX_LIMIT = int(os.getenv("SQL_MAX_LIMIT", "200"))

# Identifier patterns support normal and backtick-quoted MySQL names.
_IDENT = r"(?:`[^`]+`|[a-zA-Z_][a-zA-Z0-9_]*)"
_TABLE_REF_RE = re.compile(
    rf"\b(?:FROM|JOIN)\s+((?:{_IDENT}\s*\.\s*)?{_IDENT})",
    flags=re.IGNORECASE,
)
_CTE_ALIAS_RE = re.compile(rf"(?:\bWITH|,)\s+({_IDENT})\s+AS\s*\(", flags=re.IGNORECASE)
_CTE_START_RE = re.compile(rf"\bWITH\s+{_IDENT}\s+AS\s*\(", flags=re.IGNORECASE)

# Whitelist - DB'de erisilmesine izin verilen view/tablo isimleri
ALLOWED_TABLES = {
    "ai_stok_durumu_view",
    "ai_palet_view",
    "ai_lot_view",
    "ai_irsaliye_view",
    "ai_mal_kabul_view",
    "ai_siparis_view",
    "ai_sevkiyat_view",
    "ai_stok_hareketi_view",
    "ai_depo_doluluk_view",
}


class SqlValidationError(Exception):
    """SQL guard reddi icin exception."""


@dataclass
class CleanResult:
    sql: str
    notes: list[str]


def _strip_code_fences(text: str) -> str:
    """```sql ... ``` veya ``` ... ``` bloklarinin icerigini al."""
    fence = re.search(r"```(?:sql)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    if fence:
        return fence.group(1)
    return text


def _strip_noise_prefix(text: str) -> str:
    """Satir basindaki 'SQLQuery:' gibi prefix'leri at."""
    cleaned = text.strip()
    lower = cleaned.lower()
    for prefix in _NOISE_PREFIXES:
        if lower.startswith(prefix):
            cleaned = cleaned[len(prefix) :].lstrip()
            lower = cleaned.lower()
    return cleaned


def _find_sql_start(masked_text: str) -> int:
    cte = _CTE_START_RE.search(masked_text)
    select = re.search(r"\bSELECT\b", masked_text, flags=re.IGNORECASE)
    candidates = [match.start() for match in (cte, select) if match is not None]
    return min(candidates) if candidates else -1


def _extract_select_block(text: str) -> str:
    """Ilk WITH/SELECT'ten itibaren metin sonuna kadar al."""
    masked = _mask_string_literals(text)
    idx = _find_sql_start(masked)
    if idx == -1:
        return text.strip()
    return text[idx:].strip()


def clean_llm_sql(raw: str) -> CleanResult:
    """LLM ciktisini calistirilabilir SQL'e indirger."""
    notes: list[str] = []
    text = _strip_code_fences(raw)
    text = _strip_noise_prefix(text)
    text = _extract_select_block(text)
    if not text.endswith(";"):
        text = text.rstrip() + ";"
        notes.append("trailing-semicolon-added")
    return CleanResult(sql=text, notes=notes)


def validate_sql(sql: str) -> None:
    """Calistirma oncesi son guvenlik kontrolu. Reddedilirse exception firlatir."""
    if not sql or not sql.strip():
        raise SqlValidationError("Bos SQL.")

    raw_sql = sql.strip()
    masked_raw = _mask_string_literals(raw_sql)
    masked_without_final_semicolon = masked_raw[:-1] if raw_sql.endswith(";") else masked_raw
    if ";" in masked_without_final_semicolon:
        raise SqlValidationError("Birden fazla SQL statement calistirilamaz.")

    stripped = raw_sql.rstrip(";").strip()
    masked = _mask_string_literals(stripped)
    upper = masked.upper()

    if not upper.startswith("SELECT") and not upper.startswith("WITH"):
        raise SqlValidationError("Sadece SELECT (veya WITH...SELECT) sorgularina izin var.")

    for kw in _FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{kw}\b", upper):
            raise SqlValidationError(f"Yasakli anahtar kelime: {kw}")

    for schema in _FORBIDDEN_SCHEMAS:
        if re.search(rf"\b{schema}\b", upper):
            raise SqlValidationError(f"Yasakli sistem semasi: {schema}")

    for func in _FORBIDDEN_FUNCTIONS:
        if re.search(rf"\b{func}\s*\(", upper):
            raise SqlValidationError(f"Yasakli SQL fonksiyonu: {func}")

    for token in _FORBIDDEN_BARE_TOKENS:
        if token == "@@":
            if token in upper:
                raise SqlValidationError("Yasakli sistem degiskeni: @@")
            continue
        if re.search(rf"\b{token}\b", upper):
            raise SqlValidationError(f"Yasakli sistem ifadesi: {token}")

    if "--" in masked or "/*" in masked or masked.lstrip().startswith("#"):
        raise SqlValidationError("SQL yorum satirlarina izin verilmiyor.")

    cte_aliases = _extract_cte_aliases(masked)
    refs = _extract_table_refs(masked)
    allowed_view_seen = False

    for ref in refs:
        normalized = _normalize_identifier(ref)
        table_name = normalized.split(".")[-1]
        if table_name in ALLOWED_TABLES:
            allowed_view_seen = True
            continue
        if table_name in cte_aliases or normalized in cte_aliases:
            continue
        raise SqlValidationError(
            f"Izinsiz tablo/view referansi: {normalized}. "
            f"Yalnizca sunlar kullanilabilir: {sorted(ALLOWED_TABLES)}"
        )

    if not allowed_view_seen:
        raise SqlValidationError("Sorgu en az bir izinli ai_*_view referansi icermelidir.")


def _mask_string_literals(sql: str) -> str:
    """String literal icerigini maskeleyerek keyword kontrollerini guvenli yap."""
    result: list[str] = []
    quote: str | None = None
    i = 0
    while i < len(sql):
        char = sql[i]
        if quote is None:
            if char in {"'", '"'}:
                quote = char
            result.append(char)
            i += 1
            continue

        if char == "\\" and i + 1 < len(sql):
            result.extend([" ", " "])
            i += 2
            continue
        if char == quote:
            if i + 1 < len(sql) and sql[i + 1] == quote:
                result.extend([" ", " "])
                i += 2
                continue
            quote = None
            result.append(char)
            i += 1
            continue

        result.append(" ")
        i += 1
    return "".join(result)


def _is_keyword_at(sql: str, index: int, keyword: str) -> bool:
    end = index + len(keyword)
    if sql[index:end].upper() != keyword:
        return False
    before = sql[index - 1] if index > 0 else " "
    after = sql[end] if end < len(sql) else " "
    return not (before.isalnum() or before == "_") and not (after.isalnum() or after == "_")


def _find_top_level_keyword(sql: str, keyword: str, start: int = 0) -> int:
    depth = 0
    i = start
    while i < len(sql):
        char = sql[i]
        if char == "(":
            depth += 1
        elif char == ")" and depth > 0:
            depth -= 1
        elif depth == 0 and _is_keyword_at(sql, i, keyword):
            return i
        i += 1
    return -1


def _normalize_identifier(identifier: str) -> str:
    parts = [
        part.strip().strip("`").lower()
        for part in identifier.split(".")
        if part.strip()
    ]
    return ".".join(parts)


def _extract_cte_aliases(masked_sql: str) -> set[str]:
    return {_normalize_identifier(match.group(1)) for match in _CTE_ALIAS_RE.finditer(masked_sql)}


def _extract_table_refs(masked_sql: str) -> list[str]:
    return [match.group(1) for match in _TABLE_REF_RE.finditer(masked_sql)]


def _split_top_level_csv(text: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    start = 0
    for index, char in enumerate(text):
        if char == "(":
            depth += 1
        elif char == ")" and depth > 0:
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(text[start:index].strip())
            start = index + 1
    tail = text[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def _outer_select_clause(masked_sql: str) -> str | None:
    select_idx = _find_top_level_keyword(masked_sql, "SELECT")
    if select_idx == -1:
        return None
    from_idx = _find_top_level_keyword(masked_sql, "FROM", select_idx + len("SELECT"))
    if from_idx == -1:
        return None
    return masked_sql[select_idx + len("SELECT") : from_idx].strip()


def _is_aggregate_expression(expr: str) -> bool:
    expr = re.sub(r"\s+AS\s+`?[\w_]+`?\s*$", "", expr.strip(), flags=re.IGNORECASE)
    expr = re.sub(r"\s+`?[\w_]+`?\s*$", "", expr.strip())
    aggregate_names = "|".join(_AGGREGATE_FUNCTIONS)
    return bool(
        re.match(rf"^(?:{aggregate_names})\s*\(", expr, flags=re.IGNORECASE)
        or re.match(rf"^COALESCE\s*\(\s*(?:{aggregate_names})\s*\(", expr, flags=re.IGNORECASE)
    )


def _is_aggregate_only(masked_sql: str) -> bool:
    if _find_top_level_keyword(masked_sql, "GROUP") != -1:
        return False
    select_clause = _outer_select_clause(masked_sql)
    if not select_clause:
        return False
    expressions = _split_top_level_csv(select_clause)
    return bool(expressions) and all(_is_aggregate_expression(expr) for expr in expressions)


def _parse_limit_value(limit_text: str) -> tuple[int, tuple[int, int]]:
    comma_form = re.match(r"\s*(\d+)\s*,\s*(\d+)", limit_text)
    if comma_form:
        return int(comma_form.group(2)), comma_form.span(2)

    simple_form = re.match(r"\s*(\d+)", limit_text)
    if simple_form:
        return int(simple_form.group(1)), simple_form.span(1)

    raise SqlValidationError("LIMIT degeri sayisal olmalidir.")


def enforce_limit(sql: str) -> str:
    """Liste sorgularinda limit ekle veya ust siniri uygula."""
    stripped = sql.strip()
    core = stripped[:-1].rstrip() if stripped.endswith(";") else stripped
    masked = _mask_string_literals(core)
    limit_idx = _find_top_level_keyword(masked, "LIMIT")

    if limit_idx != -1:
        limit_start = limit_idx + len("LIMIT")
        current_limit, relative_span = _parse_limit_value(core[limit_start:])
        if current_limit <= SQL_MAX_LIMIT:
            return core + ";"
        absolute_start = limit_start + relative_span[0]
        absolute_end = limit_start + relative_span[1]
        core = core[:absolute_start] + str(SQL_MAX_LIMIT) + core[absolute_end:]
        return core + ";"

    if _is_aggregate_only(masked):
        return core + ";"

    return f"{core} LIMIT {SQL_DEFAULT_LIMIT};"


def clean_and_validate(raw: str) -> str:
    """Tek cagrida temizleme + dogrulama. Gecerli SQL string doner."""
    cleaned = clean_llm_sql(raw)
    validate_sql(cleaned.sql)
    limited_sql = enforce_limit(cleaned.sql)
    validate_sql(limited_sql)
    return limited_sql
