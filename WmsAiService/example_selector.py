"""
Dinamik Few-Shot Örnek Seçici.

ChromaDB'de saklanan soru/SQL çiftlerinden (ornekler.json kaynağı),
kullanıcı sorusuna semantik olarak en yakın k=3 örneği seçer.

Embedding modeli: sentence-transformers/all-MiniLM-L6-v2
Vektör deposu:   wms_chroma_db/ (persistent ChromaDB)

ChromaDB yapısı:
  - document (page_content): Soru metni (Türkçe)
  - metadata: {"query": "SELECT ..."}

SemanticSimilarityExampleSelector metadata'da 'input' key'i aramakta
ve document'ı (page_content) döndürmemektedir. Bu nedenle kendi
wrapper sınıfımızı kullanıyoruz: _ChromaExampleSelector.

Fallback: ChromaDB yüklenemez veya selector hata verirse
          prompts.py'deki statik FEW_SHOT_EXAMPLES'dan ilk 3 örnek döner.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from vector_config import CHROMA_PERSIST_DIR, EMBEDDING_MODEL, get_embeddings

logger = logging.getLogger(__name__)

# Varsayılan parametreler
_DEFAULT_K = int(os.getenv("FEW_SHOT_K", "3"))
_CHROMA_DIR = os.getenv(
    "CHROMA_PERSIST_DIR",
    CHROMA_PERSIST_DIR,
)
_EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    EMBEDDING_MODEL,
)

# Prompt'a enjekte edilecek key isimleri
_INPUT_KEY = "input"
_QUERY_KEY = "query"


# ----------------------------------------------------------------------------
# ChromaDB-backed example selector (kendi wrapper'ımız)
# ----------------------------------------------------------------------------

class _ChromaExampleSelector:
    """
    Chroma.similarity_search() ile en benzer k örneği döndüren wrapper.

    LangChain'in SemanticSimilarityExampleSelector'ı, ChromaDB'deki
    document (page_content) bilgisini metadata'ya dahil etmediği için
    sorular kayboluyordu. Bu wrapper:
    1. Chroma.similarity_search(soru, k) çağırır
    2. Her Document'tan page_content (soru) + metadata["query"] (SQL) alır
    3. {"input": soru, "query": SQL} formatında dict listesi döner
    """

    def __init__(self, chroma: Any, k: int = _DEFAULT_K) -> None:
        self._chroma = chroma
        self.k = k

    def select_examples(self, input_variables: dict[str, str]) -> list[dict[str, str]]:
        query = input_variables.get(_INPUT_KEY, "")
        docs = self._chroma.similarity_search(query, k=self.k)

        examples: list[dict[str, str]] = []
        for doc in docs:
            examples.append({
                _INPUT_KEY: doc.page_content,
                _QUERY_KEY: doc.metadata.get(_QUERY_KEY, ""),
            })
        return examples


# ----------------------------------------------------------------------------
# Builder
# ----------------------------------------------------------------------------

def _build_selector(k: int = _DEFAULT_K) -> _ChromaExampleSelector:
    """ChromaDB-backed example selector oluşturur."""
    from langchain_chroma import Chroma

    logger.info(
        "ChromaDB selector yükleniyor — persist_dir=%s, model=%s, k=%d",
        _CHROMA_DIR,
        _EMBEDDING_MODEL,
        k,
    )

    chroma = Chroma(
        persist_directory=_CHROMA_DIR,
        embedding_function=get_embeddings(),
    )

    # Collection'daki kayıt sayısını logla
    collection_count = chroma._collection.count()
    logger.info("ChromaDB collection yüklendi — %d kayıt mevcut.", collection_count)

    if collection_count == 0:
        raise ValueError("ChromaDB collection boş, fallback'e geçiliyor.")

    return _ChromaExampleSelector(chroma=chroma, k=k)


# ----------------------------------------------------------------------------
# Fallback: statik örneklerden seç
# ----------------------------------------------------------------------------

class _StaticFallbackSelector:
    """ChromaDB erişilemezse statik örneklerden ilk k tanesini döner."""

    def __init__(self, k: int = _DEFAULT_K) -> None:
        self.k = k
        self._examples: list[dict[str, str]] = []

    def _load(self) -> None:
        if self._examples:
            return
        from prompts import FEW_SHOT_EXAMPLES

        # prompts.py formatı: {"soru": ..., "sql": ...}
        # prompt enjeksiyon formatına map: {"input": ..., "query": ...}
        self._examples = [
            {_INPUT_KEY: ex["soru"], _QUERY_KEY: ex["sql"]}
            for ex in FEW_SHOT_EXAMPLES
        ]

    def select_examples(self, input_variables: dict[str, str]) -> list[dict[str, str]]:
        self._load()
        return self._examples[: self.k]


# ----------------------------------------------------------------------------
# Singleton
# ----------------------------------------------------------------------------

_selector: _ChromaExampleSelector | _StaticFallbackSelector | None = None
_is_fallback: bool = False


def get_example_selector() -> _ChromaExampleSelector | _StaticFallbackSelector:
    """Modül seviyesinde singleton selector döner. Thread-safe değil ama startup'ta çağrılır."""
    global _selector, _is_fallback

    if _selector is not None:
        return _selector

    try:
        _selector = _build_selector()
        _is_fallback = False
        logger.info("Dinamik Few-Shot selector (ChromaDB) başarıyla yüklendi.")
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "ChromaDB selector yüklenemedi, statik fallback aktif: %s", exc
        )
        _selector = _StaticFallbackSelector()
        _is_fallback = True

    return _selector


def is_fallback_active() -> bool:
    """Test/debug için: fallback mi kullanılıyor?"""
    return _is_fallback


# ----------------------------------------------------------------------------
# Yardımcı: seçilen örnekleri formatla
# ----------------------------------------------------------------------------

def format_selected_examples(examples: list[dict[str, str]]) -> str:
    """Seçilen örnekleri prompt'a enjekte edilecek string formatına çevirir."""
    parts: list[str] = []
    for ex in examples:
        soru = ex.get(_INPUT_KEY, ex.get("soru", ""))
        sql = ex.get(_QUERY_KEY, ex.get("sql", ""))
        parts.append(f"Soru: {soru}\nSQL: {sql}")
    return "\n\n".join(parts)


def select_and_format(soru: str, k: int | None = None) -> str:
    """
    Kullanıcı sorusu için en uygun örnekleri seçip formatlanmış string döner.

    Bu fonksiyon, chains.py'nin _generate_sql() metodundan çağrılır.
    Selector hata verirse boş string döner (graceful degradation).
    """
    selector = get_example_selector()

    try:
        selected = selector.select_examples({_INPUT_KEY: soru})
        if k is not None:
            selected = selected[:k]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Örnek seçimi başarısız, boş örneklerle devam: %s", exc)
        return ""

    formatted = format_selected_examples(selected)

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "Seçilen %d örnek (soru: %s):\n%s",
            len(selected),
            soru[:60],
            formatted,
        )

    return formatted
