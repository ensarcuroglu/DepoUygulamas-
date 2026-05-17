"""
Cevap üretim katmanı.

Strateji (template-first; LLM by-pass):
- EMPTY  -> sabit Türkçe cümle.
- SCALAR -> deterministik şablon (kolon adı + değer).
- LIST   -> deterministik liste şablonu (list_renderer.py).
            LLM yalnızca şablon hiç eşleşmediği veya kullanıcı verbose
            modda istediği durumda devreye girer. Bu durumda da çıktı
            validation döngüsünden geçer; sayı/isim eşleşmesi yoksa
            template fallback'e döner.

Bu yaklaşım qwen2.5-coder:7b'nin Türkçe morfoloji bozukluklarına maruz kalma alanını
büyük ölçüde kapatır.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from langfuse_tracing import langchain_config, safe_metadata
from list_renderer import render_list
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
    row = structured.rows[0]
    parts = [f"{_humanize(col)}: {_pretty_value(val)}" for col, val in row.items()]
    return "1 sonuç bulundu — " + ", ".join(parts) + "."


# ----------------------------------------------------------------------------
# Scalar şablonu
# ----------------------------------------------------------------------------

_SCALAR_LABEL_RULES: list[tuple[str, str]] = [
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

    if isinstance(value, Decimal):
        value = int(value) if value == value.to_integral_value() else float(value)

    pretty_value = _pretty_value(value)
    is_count_label = "sayı" in label or label in {"ürün", "kayıt"}

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value == 0 and is_count_label:
            return f"Hiç {label} bulunamadı."
        if is_count_label:
            return f"Toplam {pretty_value} {label} bulunuyor."
        return f"{label.capitalize()}: {pretty_value}."

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
# LLM tabanlı list cevap (yalnızca verbose modda devreye girer)
# ----------------------------------------------------------------------------

class ListAnswerLLM:
    """qwen2.5-coder:7b için sıkı sampling parametreleriyle disipline edilmiş üretici."""

    def __init__(
        self,
        model: str,
        base_url: str,
        timeout: float,
        num_ctx: int,
        num_predict: int = 40,
        repeat_penalty: float = 1.2,
        top_k: int = 1,
    ) -> None:
        self.model = model
        self.llm = ChatOllama(
            model=model,
            base_url=base_url,
            temperature=0,
            top_k=top_k,
            top_p=1.0,
            repeat_penalty=repeat_penalty,
            num_ctx=num_ctx,
            num_predict=num_predict,
            timeout=timeout,
            # Sıkı stop: ilk paragraf bittiği anda kes
            stop=[
                "\n",
                "\nSoru:",
                "\nKullanıcı:",
                "Soru:",
                "•",
                "1)",
                "2)",
                "- ",
            ],
        )
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", ANSWER_SYSTEM_PROMPT),
                ("human", ANSWER_USER_PROMPT),
            ]
        ).partial(examples=render_answer_few_shot_block())
        self.chain = self.prompt | self.llm | StrOutputParser()

    def invoke(self, soru: str, sonuc_metni: str) -> str:
        raw = self.chain.invoke(
            {"soru": soru, "sonuc": sonuc_metni},
            config=langchain_config(
                run_name="wms-ai.answer.verbose",
                tags=["sql", "answer"],
                metadata=safe_metadata(operation="verbose_answer", model=self.model),
            ),
        )
        return _post_process(raw)


# ----------------------------------------------------------------------------
# Post-processing
# ----------------------------------------------------------------------------

_REPLACEMENTS = [
    (re.compile(r"\bvar değildir\b", re.IGNORECASE), "yok"),
    (re.compile(r"\bvar değil\b", re.IGNORECASE), "yok"),
    (re.compile(r"\byok değildir\b", re.IGNORECASE), "var"),
    (re.compile(r"\bbulunmaz\b", re.IGNORECASE), "bulunmuyor"),
]


def _post_process(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^(Cevap|Yanıt)\s*:\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^[\-\*\d\.\)]+\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    for pattern, repl in _REPLACEMENTS:
        cleaned = pattern.sub(repl, cleaned)
    if cleaned and cleaned[-1] not in ".!?":
        cleaned += "."
    return cleaned


# ----------------------------------------------------------------------------
# Validation: LLM cevabı SQL sonucundaki sayı/isimleri içeriyor mu?
# ----------------------------------------------------------------------------

# En az kaç anchor (sayı veya öne çıkan isim) tutulmalı
_MIN_ANCHOR_HITS = 1
_MIN_ANSWER_CHARS = 8
_MAX_ANSWER_CHARS = 400


def _extract_anchors(structured: StructuredResult) -> set[str]:
    """SQL sonucundan, cevapta görmeyi beklediğimiz 'anchor' token'lar."""
    anchors: set[str] = set()

    # Scalar değerler
    if structured.scalar_value is not None:
        anchors.add(str(structured.scalar_value))

    # İlk birkaç satırın sayı/metin değerleri
    for row in structured.rows[:5]:
        for v in row.values():
            if v is None:
                continue
            text = str(v).strip()
            if not text or text == "—":
                continue
            # Sayılar: rakam dizilerini al
            if re.fullmatch(r"-?\d+(\.\d+)?", text):
                anchors.add(text.split(".")[0])  # "0.00" -> "0"
                continue
            # İsimler: 3+ karakter olan tokenları ekle
            if len(text) >= 3:
                anchors.add(text)

    return {a for a in anchors if a}


def _is_valid_llm_answer(answer: str, structured: StructuredResult) -> bool:
    """LLM cevabı sıhhat kontrolünden geçiyor mu?"""
    if not answer:
        return False
    n = len(answer)
    if n < _MIN_ANSWER_CHARS or n > _MAX_ANSWER_CHARS:
        return False

    anchors = _extract_anchors(structured)
    if not anchors:
        # Eğer anchor çıkaramadıysak (boş sonuç vs.) length kontrolü yeterli
        return True

    lower = answer.lower()
    hits = sum(1 for a in anchors if a.lower() in lower)
    return hits >= _MIN_ANCHOR_HITS


# ----------------------------------------------------------------------------
# Dispatcher
# ----------------------------------------------------------------------------

class Answerer:
    """
    Template-first cevap üretici.

    Args:
        list_llm: LIST sorularda 'verbose' istendiğinde devreye giren LLM.
                  Default akışta hiç çağrılmaz.
    """

    def __init__(self, list_llm: ListAnswerLLM | None = None) -> None:
        self._list_llm = list_llm

    def answer(
        self,
        soru: str,
        structured: StructuredResult,
        verbose: bool = False,
    ) -> str:
        if structured.intent == ResultIntent.EMPTY:
            return EMPTY_RESPONSE

        if structured.intent == ResultIntent.SCALAR:
            return _format_scalar(structured, soru)

        # Tek-satır LIST
        if structured.row_count == 1:
            return _format_single_row(structured)

        # Çok satırlı LIST — default: deterministik template renderer
        template_answer = render_list(structured)

        if not verbose or self._list_llm is None:
            return template_answer

        # verbose=True -> LLM'i denemeye değer; ama validation gate'i var
        sonuc_metni = render_rows_for_prompt(
            structured.rows, limit=DEFAULT_LIST_PREVIEW_ROWS
        )
        try:
            llm_answer = self._list_llm.invoke(soru, sonuc_metni)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Answer LLM failed, falling back to template: %s", exc)
            return template_answer

        if _is_valid_llm_answer(llm_answer, structured):
            return llm_answer

        logger.info(
            "LLM cevabı validation'dan geçemedi, template fallback uygulanıyor. "
            "LLM çıktı: %r",
            llm_answer,
        )
        return template_answer
