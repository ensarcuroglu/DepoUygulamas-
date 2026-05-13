"""Millisecond-scale route selection without an LLM call."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

from route_examples import ROUTE_DOCS, ROUTE_SQL
from vector_config import (
    ROUTER_COLLECTION_NAME,
    build_chroma,
    collection_count,
)

logger = logging.getLogger(__name__)

ROUTE_SOURCE_SEMANTIC = "semantic_router"

ROUTER_TOP_K = int(os.getenv("ROUTER_TOP_K", "6"))
ROUTER_CONFIDENCE_THRESHOLD = float(os.getenv("ROUTER_CONFIDENCE_THRESHOLD", "0.52"))
ROUTER_CONFIDENCE_MARGIN = float(os.getenv("ROUTER_CONFIDENCE_MARGIN", "0.04"))

DOC_KEYWORDS = {
    "agv",
    "api",
    "architecture",
    "clean architecture",
    "docai",
    "docker",
    "dokuman",
    "doküman",
    "dokumantasyon",
    "dokümantasyon",
    "entegrasyon",
    "fefo",
    "fifo",
    "kacis kapagi",
    "kaçış kapağı",
    "kilavuz",
    "kılavuz",
    "manual",
    "mantik",
    "mimari",
    "nasil",
    "nasıl",
    "nedir",
    "ne demek",
    "pwa",
    "rabbitmq",
    "surec",
    "süreç",
    "talimat",
    "yardim",
}


@dataclass(frozen=True)
class RouteDecision:
    route: str
    route_source: str
    confidence: float
    debug: dict[str, Any]


def distance_to_confidence(distance: float) -> float:
    if distance < 0:
        distance = 0
    return round(1 / (1 + distance), 4)


class SemanticRouter:
    def __init__(self, chroma: Any | None = None) -> None:
        self._chroma = chroma

    def route(self, question: str) -> RouteDecision:
        try:
            return self._route_with_chroma(question)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Semantic router vector fallback aktif: %s", exc)
            return self._route_with_keywords(question, str(exc))

    def _route_with_chroma(self, question: str) -> RouteDecision:
        chroma = self._chroma or build_chroma(collection_name=ROUTER_COLLECTION_NAME)
        count = collection_count(chroma)
        if count == 0:
            raise ValueError("router collection bos")

        docs_and_scores = chroma.similarity_search_with_score(question, k=ROUTER_TOP_K)
        if not docs_and_scores:
            raise ValueError("router sonucu yok")

        best_by_route: dict[str, float] = {}
        matches: list[dict[str, Any]] = []
        for doc, distance in docs_and_scores:
            route = doc.metadata.get("route")
            if route not in {ROUTE_SQL, ROUTE_DOCS}:
                continue
            distance = float(distance)
            best_by_route[route] = min(distance, best_by_route.get(route, distance))
            matches.append(
                {
                    "route": route,
                    "distance": round(distance, 4),
                    "text": doc.page_content[:120],
                }
            )

        if not best_by_route:
            raise ValueError("router metadata route icermiyor")

        ranked = sorted(
            best_by_route.items(),
            key=lambda item: distance_to_confidence(item[1]),
            reverse=True,
        )
        winner_route, winner_distance = ranked[0]
        winner_confidence = distance_to_confidence(winner_distance)
        second_confidence = (
            distance_to_confidence(ranked[1][1]) if len(ranked) > 1 else 0.0
        )
        margin = round(winner_confidence - second_confidence, 4)
        ambiguous = (
            winner_confidence < ROUTER_CONFIDENCE_THRESHOLD
            or (second_confidence and margin < ROUTER_CONFIDENCE_MARGIN)
        )

        route = ROUTE_SQL if ambiguous else winner_route
        return RouteDecision(
            route=route,
            route_source=ROUTE_SOURCE_SEMANTIC,
            confidence=winner_confidence,
            debug={
                "router_backend": "chroma",
                "collection": ROUTER_COLLECTION_NAME,
                "collection_count": count,
                "chosen_before_fallback": winner_route,
                "second_confidence": second_confidence,
                "margin": margin,
                "ambiguous_defaulted_to_sql": ambiguous,
                "matches": matches,
            },
        )

    def _route_with_keywords(self, question: str, reason: str) -> RouteDecision:
        lowered = question.lower()
        is_docs = any(keyword in lowered for keyword in DOC_KEYWORDS)
        return RouteDecision(
            route=ROUTE_DOCS if is_docs else ROUTE_SQL,
            route_source=ROUTE_SOURCE_SEMANTIC,
            confidence=0.55 if is_docs else 0.5,
            debug={
                "router_backend": "keyword_fallback",
                "fallback_reason": reason,
                "matched_docs_keyword": is_docs,
            },
        )


_router: SemanticRouter | None = None


def get_semantic_router() -> SemanticRouter:
    global _router
    if _router is None:
        _router = SemanticRouter()
    return _router
