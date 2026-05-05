"""
SQL güvenlik katmanı.

LLM'in ürettiği SQL'i çalıştırmadan önce:
1. Markdown / "SQLQuery:" gibi gürültüyü temizle
2. Sadece TEK statement olduğunu doğrula
3. SELECT dışı bir komut varsa reddet
4. Yasaklı anahtar kelimeleri (DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE...) reddet
5. Whitelist'teki view/tablolar dışında bir referans varsa reddet (best-effort)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# LLM çıktısında sık görülen gürültü prefix/suffix'leri
_NOISE_PREFIXES = (
    "sqlquery:",
    "sql query:",
    "sql:",
    "query:",
    "answer:",
    "cevap:",
)

# Yasaklı SQL anahtar kelimeleri (kelime sınırı ile aranır)
_FORBIDDEN_KEYWORDS = (
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "RENAME", "GRANT", "REVOKE", "REPLACE", "MERGE",
    "CALL", "EXEC", "EXECUTE", "LOAD", "HANDLER", "LOCK", "UNLOCK",
    "SET",
)

# Whitelist — DB'de erişilmesine izin verilen view/tablo isimleri
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
    """SQL guard reddi için exception."""


@dataclass
class CleanResult:
    sql: str
    notes: list[str]


def _strip_code_fences(text: str) -> str:
    """```sql ... ``` veya ``` ... ``` bloklarının içeriğini al."""
    fence = re.search(r"```(?:sql)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    if fence:
        return fence.group(1)
    return text


def _strip_noise_prefix(text: str) -> str:
    """Satır başındaki 'SQLQuery:' gibi prefix'leri at."""
    cleaned = text.strip()
    lower = cleaned.lower()
    for prefix in _NOISE_PREFIXES:
        if lower.startswith(prefix):
            cleaned = cleaned[len(prefix):].lstrip()
            lower = cleaned.lower()
    return cleaned


def _extract_select_block(text: str) -> str:
    """İlk SELECT'ten itibaren `;` veya metin sonuna kadar al."""
    upper = text.upper()
    idx = upper.find("SELECT")
    if idx == -1:
        return text.strip()
    rest = text[idx:]
    # İlk noktalı virgülde kes (TEK statement güvencesi için)
    semi = rest.find(";")
    if semi != -1:
        return rest[: semi + 1].strip()
    return rest.strip()


def clean_llm_sql(raw: str) -> CleanResult:
    """LLM çıktısını çalıştırılabilir SQL'e indirger."""
    notes: list[str] = []
    text = _strip_code_fences(raw)
    text = _strip_noise_prefix(text)
    text = _extract_select_block(text)
    if not text.endswith(";"):
        text = text.rstrip() + ";"
        notes.append("trailing-semicolon-added")
    return CleanResult(sql=text, notes=notes)


def validate_sql(sql: str) -> None:
    """Çalıştırma öncesi son güvenlik kontrolü. Reddedilirse exception fırlatır."""
    if not sql or not sql.strip():
        raise SqlValidationError("Boş SQL.")

    stripped = sql.strip().rstrip(";").strip()
    upper = stripped.upper()

    if not upper.startswith("SELECT") and not upper.startswith("WITH"):
        raise SqlValidationError("Sadece SELECT (veya WITH...SELECT) sorgularına izin var.")

    # Birden fazla statement engelle
    if stripped.count(";") > 0:
        raise SqlValidationError("Birden fazla SQL statement çalıştırılamaz.")

    # Yasaklı anahtar kelimeler — kelime sınırı ile
    for kw in _FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{kw}\b", upper):
            raise SqlValidationError(f"Yasaklı anahtar kelime: {kw}")

    # SQL yorum satırlarını engelle (--, /* */, #) — injection vektörü
    if "--" in stripped or "/*" in stripped or stripped.lstrip().startswith("#"):
        raise SqlValidationError("SQL yorum satırlarına izin verilmiyor.")

    # FROM / JOIN sonrası gelen identifier'ları whitelist'e karşı kontrol et
    refs = re.findall(r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)", upper)
    for ref in refs:
        if ref.lower() not in ALLOWED_TABLES:
            raise SqlValidationError(
                f"İzinsiz tablo/view referansı: {ref.lower()}. "
                f"Yalnızca şunlar kullanılabilir: {sorted(ALLOWED_TABLES)}"
            )


def clean_and_validate(raw: str) -> str:
    """Tek çağrıda temizleme + doğrulama. Geçerli SQL string döner."""
    cleaned = clean_llm_sql(raw)
    validate_sql(cleaned.sql)
    return cleaned.sql
