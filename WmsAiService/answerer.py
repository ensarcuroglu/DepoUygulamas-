"""
Cevap üretim katmanı.

Strateji:
- EMPTY  -> sabit Türkçe cümle (LLM yok)
- SCALAR -> deterministik şablon. Tek hücre sonuç (COUNT, SUM, AVG vb.)
            phi3'e bırakılmaz; akıcı bir Türkçe cümleye dönüştürülür.
- LIST   -> few-shot ile beslenen LLM. temperature=0, num_predict=80,
            stop sequence ile uzayıp bozulmasını engelleriz.

Bu katman pipeline'a `answer(soru, sql, structured)` arayüzü sunar.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from prompts import (
    ANSWER_SYSTEM_PROMPT,
    ANSWER_USER_PROMPT,
    render_answer_few_shot_block,
)
from result_formatter import (
    DEFAULT_LIST_PREVIEW_ROWS,
    ResultIntent,
    StructuredResult,
    render_rows_for_prompt,
)

logger = logging.getLogger(__name__)

EMPTY_RESPONSE = "Bu kriterlere uygun kayıt bulunamadı."

# Tek-satır LIST sonuçlarını LLM'e göndermeden şablonla cevaplamak için
# kolon adı -> Türkçe insan etiketi haritası
_HUMAN_LABELS: dict[str, str] = {
    "urun_adi": "Ürün",
    "urun_id": "Ürün ID",
    "barkod": "Barkod",
    "kategori_adi": "Kategori",
    "marka_adi": "Marka",
    "guncel_stok_miktari": "Stok",
    "kritik_stok_siniri": "Kritik stok sınırı",
    "birim": "Birim",
    "stok_durumu": "Stok durumu",
    "urun_sayisi": "Ürün sayısı",
    "toplam_miktar": "Toplam",
    "adet": "Adet",
}


def _humanize(col: str) -> str:
    return _HUMAN_LABELS.get(col, col.replace("_", " ").capitalize())


def _format_single_row(structured: StructuredResult) -> str:
    """Tek satır + birden çok kolon — LLM'e gitmeden Türkçe cümle üret.

    Örnek:
      rows=[{"urun_adi":"DEV Bulgur 1kg","guncel_stok_miktari":"0"}]
      -> "1 sonuç bulundu: Ürün: DEV Bulgur 1kg, Stok: 0."
    """
    row = structured.rows[0]
    parts = [f"{_humanize(col)}: {_pretty_value(val)}" for col, val in row.items()]
    return "1 sonuç bulundu — " + ", ".join(parts) + "."


# ----------------------------------------------------------------------------
# Scalar şablonu — kolon adına göre Türkçe cümle üretir
# ----------------------------------------------------------------------------

# Kolon adlarındaki ipuçlarını (substring match) Türkçe ifadelere eşler.
_SCALAR_LABEL_RULES: list[tuple[str, str]] = [
    # Daha spesifik (uzun) eşleşmeler önce gelmeli.
    # LLM kolon takma adında "stoq", "stoğ", "miktar", "miktari" varyantları
    # üretebilir; bu yüzden gevşek substring eşleştirmesi yapıyoruz.
    ("guncel_stok_miktari", "stok"),
    ("kritik_stok_siniri", "kritik stok eşiği"),
    ("urun_sayisi", "ürün"),
    ("kayit_sayisi", "kayıt"),
    ("palet_sayisi", "palet"),
    ("toplam_miktar", "toplam stok"),
    ("toplam_stok", "toplam stok"),
    ("toplam_stoq", "toplam stok"),
    ("toplam_stog", "toplam stok"),
    ("toplam", "toplam"),
    ("ortalama", "ortalama"),
    ("adet", "kayıt"),
    ("count", "kayıt"),
    ("sum", "toplam"),
    ("avg", "ortalama"),
    ("miktar", "miktar"),
    ("stok", "stok"),
]


def _label_for_scalar(column: str) -> str:
    lc = column.lower()
    for needle, label in _SCALAR_LABEL_RULES:
        if needle in lc:
            return label
    return column.replace("_", " ")


def _format_scalar(structured: StructuredResult, soru: str) -> str:
    from decimal import Decimal

    value = structured.scalar_value
    column = structured.scalar_column or ""
    label = _label_for_scalar(column)

    # Decimal -> int/float normalize
    if isinstance(value, Decimal):
        value = int(value) if value == value.to_integral_value() else float(value)

    pretty_value = _pretty_value(value)
    is_count_label = "sayı" in label or label in {
        "ürün",
        "kayıt",
    }

    # Sayım/sayı sonuçları için "Toplam X Y bulunuyor."
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value == 0 and is_count_label:
            return f"Hiç {label} bulunamadı."
        if is_count_label:
            return f"Toplam {pretty_value} {label} bulunuyor."
        return f"{label.capitalize()}: {pretty_value}."

    # Metinsel scalar — örneğin tek bir marka/kategori adı
    if value is None:
        return EMPTY_RESPONSE
    return f"Sonuç: {pretty_value}."


def _pretty_value(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        if value == int(value):
            return str(int(value))
        return f"{value:.2f}"
    return str(value)


# ----------------------------------------------------------------------------
# LLM tabanlı list cevap
# ----------------------------------------------------------------------------

class ListAnswerLLM:
    """Few-shot ile disipline edilmiş, deterministik (temp=0) cevap üretici."""

    def __init__(
        self,
        model: str,
        base_url: str,
        timeout: float,
        num_ctx: int,
        num_predict: int = 96,
    ) -> None:
        self.llm = ChatOllama(
            model=model,
            base_url=base_url,
            temperature=0,
            num_ctx=num_ctx,
            num_predict=num_predict,
            timeout=timeout,
            # Modelin uzayıp ikinci paragrafa veya saçma metne kayma riskine karşı
            stop=["\nSoru:", "\nKullanıcı:", "\n\n\n"],
        )
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", ANSWER_SYSTEM_PROMPT),
                ("human", ANSWER_USER_PROMPT),
            ]
        ).partial(examples=render_answer_few_shot_block())
        self.chain = self.prompt | self.llm | StrOutputParser()

    def invoke(self, soru: str, sonuc_metni: str) -> str:
        raw = self.chain.invoke({"soru": soru, "sonuc": sonuc_metni})
        return _post_process(raw)


# ----------------------------------------------------------------------------
# Post-processing — yaygın phi3 bozukluklarını törpüler
# ----------------------------------------------------------------------------

_REPLACEMENTS = [
    (re.compile(r"\bvar değildir\b", re.IGNORECASE), "yok"),
    (re.compile(r"\bvar değil\b", re.IGNORECASE), "yok"),
    (re.compile(r"\byok değildir\b", re.IGNORECASE), "var"),
    (re.compile(r"\bbulunmaz\b", re.IGNORECASE), "bulunmuyor"),
]


def _post_process(text: str) -> str:
    cleaned = text.strip()
    # Bazı modeller "Cevap:" prefix'ini tekrar yazar
    cleaned = re.sub(r"^(Cevap|Yanıt)\s*:\s*", "", cleaned, flags=re.IGNORECASE)
    # Markdown bullet'larını sıyır
    cleaned = re.sub(r"^[\-\*\d\.\)]+\s*", "", cleaned, flags=re.MULTILINE)
    # Çoklu boşluk/satır
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    for pattern, repl in _REPLACEMENTS:
        cleaned = pattern.sub(repl, cleaned)
    # Sonuna nokta ekle
    if cleaned and cleaned[-1] not in ".!?":
        cleaned += "."
    return cleaned


# ----------------------------------------------------------------------------
# Dispatcher
# ----------------------------------------------------------------------------

class Answerer:
    def __init__(self, list_llm: ListAnswerLLM) -> None:
        self._list_llm = list_llm

    def answer(self, soru: str, structured: StructuredResult) -> str:
        if structured.intent == ResultIntent.EMPTY:
            return EMPTY_RESPONSE

        if structured.intent == ResultIntent.SCALAR:
            return _format_scalar(structured, soru)

        # Tek-satır LIST: LLM'e gitmeden deterministik şablon (phi3 bypass)
        if structured.row_count == 1:
            return _format_single_row(structured)

        # Çok satırlı LIST
        sonuc_metni = render_rows_for_prompt(
            structured.rows, limit=DEFAULT_LIST_PREVIEW_ROWS
        )
        try:
            return self._list_llm.invoke(soru, sonuc_metni)
        except Exception as exc:  # noqa: BLE001
            # LLM çökerse minimum güvenli fallback — kullanıcı boş kalmasın
            logger.warning("Answer LLM failed, falling back to summary: %s", exc)
            return _fallback_list_summary(structured)


def _fallback_list_summary(structured: StructuredResult) -> str:
    n = structured.row_count
    cols = ", ".join(structured.columns)
    return f"Sorgu {n} satır döndürdü ({cols}). Detay için sonucu inceleyin."
