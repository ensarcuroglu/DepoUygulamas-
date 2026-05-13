"""Shared vector-store configuration for WmsAiService."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

CHROMA_PERSIST_DIR = os.getenv(
    "CHROMA_PERSIST_DIR",
    str(Path(__file__).parent / "wms_chroma_db"),
)
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)

ROUTER_COLLECTION_NAME = os.getenv(
    "ROUTER_COLLECTION_NAME",
    "wms_ai_router_intents",
)
DOCS_COLLECTION_NAME = os.getenv(
    "DOCS_COLLECTION_NAME",
    "wms_ai_docs_chunks",
)


@lru_cache(maxsize=1)
def get_embeddings() -> Any:
    from langchain_community.embeddings import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def build_chroma(*, collection_name: str | None = None) -> Any:
    from langchain_chroma import Chroma

    kwargs: dict[str, Any] = {
        "persist_directory": CHROMA_PERSIST_DIR,
        "embedding_function": get_embeddings(),
    }
    if collection_name:
        kwargs["collection_name"] = collection_name
    return Chroma(**kwargs)


def collection_count(chroma: Any) -> int:
    collection = getattr(chroma, "_collection", None)
    if collection is None:
        return 0
    return int(collection.count())
