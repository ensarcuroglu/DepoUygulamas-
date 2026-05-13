"""RAG retrieval kalite testi.

Bu suite LLM cagirmaz; sadece Chroma retrieval'i ve strict-gate'i degerlendirir:

  - **recall@1** ve **recall@4**: pozitif sorular icin beklenen kaynak ilk
    1 / 4 sonucta yer aliyor mu?
  - **negatif reddetme**: alakasiz sorular icin en iyi chunk distance'i
    `RAG_STRICT_DISTANCE` esiginin uzerinde olmali (LLM cagrilmadan
    "Bu konuda bilgi bulamadim" donmesi gerekir).
  - **distance dagilimi**: pozitif vs negatif sorularda `best_distance`
    min/median/max degerleri rapor edilir.

Test calistirma:

    cd WmsAiService
    pytest tests/test_rag_retrieval_quality.py -v -s

Esik:
  - recall@4 >= RECALL_AT_4_TARGET (0.85)
  - negatif reddetme orani == 1.0

Esige takilirsan **once dokumana** mudahale et (eksik alias, paraphrase,
ornek soru), embedding modeli/prompt'a dokunma. Bu suite ingest sonrasi
calistirilmali: `python ingest_docs.py --docs`.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

from docs_rag import RAG_STRICT_DISTANCE, RAG_TOP_K  # noqa: E402
from vector_config import DOCS_COLLECTION_NAME, build_chroma, collection_count  # noqa: E402

GOLDSET_PATH = Path(__file__).resolve().parent / "data" / "rag_goldset.yaml"
RECALL_AT_4_TARGET = 0.85
RECALL_AT_1_TARGET = 0.55  # daha gevsek, sadece bilgi amacli; gate degil


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def goldset() -> list[dict[str, Any]]:
    if not GOLDSET_PATH.exists():
        pytest.skip(f"Gold-set bulunamadi: {GOLDSET_PATH}")
    with GOLDSET_PATH.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    assert isinstance(data, list) and data, "Gold-set bos veya gecersiz"
    for item in data:
        assert "question" in item and "kind" in item, f"Gecersiz madde: {item}"
        if item["kind"] in {"literal", "paraphrase"}:
            assert "expected_source_path" in item, f"Pozitif madde icin kaynak yok: {item}"
        elif item["kind"] == "negative":
            assert item.get("expected_no_info") is True, f"Negatif madde no_info=true olmali: {item}"
        else:
            raise AssertionError(f"Bilinmeyen kind: {item['kind']}")
    return data


@pytest.fixture(scope="module")
def chroma():
    try:
        store = build_chroma(collection_name=DOCS_COLLECTION_NAME)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"Chroma erisilemiyor: {exc}")
    count = collection_count(store)
    if count == 0:
        pytest.skip(
            "Docs koleksiyonu bos. Once `python ingest_docs.py --docs` calistirin."
        )
    return store


# ---------------------------------------------------------------------------
# Yardimcilar
# ---------------------------------------------------------------------------

def _retrieve(chroma, question: str, k: int = RAG_TOP_K):
    return chroma.similarity_search_with_score(question, k=k)


def _source_paths(results) -> list[str]:
    return [doc.metadata.get("source_path", "") for doc, _ in results]


def _best_distance(results) -> float:
    if not results:
        return float("inf")
    return min(float(distance) for _, distance in results)


# ---------------------------------------------------------------------------
# Testler
# ---------------------------------------------------------------------------

def test_recall_at_k(goldset, chroma, capsys):
    """Pozitif sorularda beklenen kaynak top-K icinde olmali."""
    positives = [item for item in goldset if item["kind"] in {"literal", "paraphrase"}]
    assert positives, "Gold-set'te pozitif soru yok"

    hits_at_1 = 0
    hits_at_4 = 0
    misses: list[dict[str, Any]] = []
    distances: list[float] = []

    by_kind: dict[str, list[bool]] = defaultdict(list)
    by_doc: dict[str, list[bool]] = defaultdict(list)

    for item in positives:
        results = _retrieve(chroma, item["question"], k=RAG_TOP_K)
        paths = _source_paths(results)
        expected = item["expected_source_path"]
        hit4 = expected in paths
        hit1 = bool(paths) and paths[0] == expected

        hits_at_4 += int(hit4)
        hits_at_1 += int(hit1)
        distances.append(_best_distance(results))
        by_kind[item["kind"]].append(hit4)
        by_doc[expected].append(hit4)

        if not hit4:
            misses.append({
                "question": item["question"],
                "expected": expected,
                "got": paths,
                "best_distance": round(_best_distance(results), 4),
            })

    total = len(positives)
    recall_at_4 = hits_at_4 / total
    recall_at_1 = hits_at_1 / total

    with capsys.disabled():
        print("\n=== Retrieval Quality Report ===")
        print(f"Total positive questions: {total}")
        print(f"recall@1 = {recall_at_1:.2%}  (target >= {RECALL_AT_1_TARGET:.0%})")
        print(f"recall@4 = {recall_at_4:.2%}  (target >= {RECALL_AT_4_TARGET:.0%})")
        if distances:
            print(
                f"best_distance (positives): "
                f"min={min(distances):.3f}  "
                f"median={statistics.median(distances):.3f}  "
                f"max={max(distances):.3f}"
            )
        print("\nBy kind:")
        for kind, hits in sorted(by_kind.items()):
            rate = sum(hits) / len(hits) if hits else 0
            print(f"  {kind}: {sum(hits)}/{len(hits)} = {rate:.0%}")
        print("\nBy doc:")
        for doc, hits in sorted(by_doc.items()):
            rate = sum(hits) / len(hits) if hits else 0
            print(f"  {doc}: {sum(hits)}/{len(hits)} = {rate:.0%}")
        if misses:
            print("\nMisses (recall@4):")
            for miss in misses:
                print(f"  Q: {miss['question']}")
                print(f"    expected: {miss['expected']}")
                print(f"    got:      {miss['got']}")
                print(f"    best_distance: {miss['best_distance']}")
        print("================================\n")

    assert recall_at_4 >= RECALL_AT_4_TARGET, (
        f"recall@4 = {recall_at_4:.2%} hedef {RECALL_AT_4_TARGET:.0%} altinda. "
        f"Eksik chunk ya da yetersiz aliases. Detay icin -s ile calistir."
    )


def test_negative_rejection(goldset, chroma, capsys):
    """Negatif sorularda en iyi chunk strict-gate uzerinde olmali."""
    negatives = [item for item in goldset if item["kind"] == "negative"]
    assert negatives, "Gold-set'te negatif soru yok"

    rejected = 0
    leaks: list[dict[str, Any]] = []
    distances: list[float] = []

    for item in negatives:
        results = _retrieve(chroma, item["question"], k=RAG_TOP_K)
        best = _best_distance(results)
        distances.append(best)
        if best > RAG_STRICT_DISTANCE or not results:
            rejected += 1
        else:
            leaks.append({
                "question": item["question"],
                "best_distance": round(best, 4),
                "strict_threshold": RAG_STRICT_DISTANCE,
                "top_sources": _source_paths(results),
            })

    total = len(negatives)
    rejection_rate = rejected / total

    with capsys.disabled():
        print("\n=== Negative Rejection Report ===")
        print(f"Total negative questions: {total}")
        print(f"rejection_rate = {rejection_rate:.2%}  (target = 100%)")
        print(f"strict_distance = {RAG_STRICT_DISTANCE}")
        if distances:
            print(
                f"best_distance (negatives): "
                f"min={min(distances):.3f}  "
                f"median={statistics.median(distances):.3f}  "
                f"max={max(distances):.3f}"
            )
        if leaks:
            print("\nLeaks (negative passed strict-gate):")
            for leak in leaks:
                print(f"  Q: {leak['question']}")
                print(f"    best_distance: {leak['best_distance']}  (strict {leak['strict_threshold']})")
                print(f"    top sources:   {leak['top_sources']}")
        print("=================================\n")

    assert rejection_rate == 1.0, (
        f"Negatif reddetme orani = {rejection_rate:.2%}, %100 olmali. "
        f"Strict threshold ({RAG_STRICT_DISTANCE}) altinda kalan negatif sorular var; "
        f"esigi sikilastir veya alakasiz chunk'i tespit edip dokumandan cikar."
    )
