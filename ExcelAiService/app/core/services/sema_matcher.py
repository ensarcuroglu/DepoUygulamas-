"""Excel sutunlarini WMS hedef sema alanlariyla eslesetiren saf domain servisi.

LLM kullanmaz: normalize edilmis token bazli Jaccard + substring skoru
ile deterministik bir esleme uretir. Bu sayede testler stabil olur ve
ayni dosya icin ayni cevap garanti edilir (idempotency'yi destekler).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from app.core.entities.responses import ColumnMapping, FieldMatchCandidate
from app.core.entities.wms_target_schemas import TargetField, TargetSchema

_MATCH_THRESHOLD = 0.50
_MAX_CANDIDATES = 3


@dataclass(frozen=True)
class _Term:
    raw: str
    normalized: str
    tokens: frozenset[str]


def _normalize(value: str) -> str:
    """Lowercase + Turkce karakter sadelestirme + non-alphanumeric -> bosluk."""
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_only = "".join(c for c in decomposed if not unicodedata.combining(c))
    # Turkce'ye ozgu yumusatma (NFKD bazi karakterleri korur).
    ascii_only = (
        ascii_only.replace("ı", "i")
        .replace("I", "i")
        .replace("İ", "i")
        .replace("ğ", "g")
        .replace("Ğ", "g")
        .replace("ü", "u")
        .replace("Ü", "u")
        .replace("ş", "s")
        .replace("Ş", "s")
        .replace("ö", "o")
        .replace("Ö", "o")
        .replace("ç", "c")
        .replace("Ç", "c")
    )
    cleaned = re.sub(r"[^a-z0-9]+", " ", ascii_only.lower()).strip()
    return cleaned


def _build_term(value: str) -> _Term:
    normalized = _normalize(value)
    tokens = frozenset(t for t in normalized.split() if t)
    return _Term(raw=value, normalized=normalized, tokens=tokens)


def _score(source: _Term, target_term: _Term) -> float:
    if not source.normalized or not target_term.normalized:
        return 0.0
    if source.normalized == target_term.normalized:
        return 1.0
    if source.normalized in target_term.normalized or target_term.normalized in source.normalized:
        # Substring match: uzunluk oranina gore yaklasik skor.
        longer = max(len(source.normalized), len(target_term.normalized))
        shorter = min(len(source.normalized), len(target_term.normalized))
        return 0.6 + 0.3 * (shorter / longer)
    if source.tokens and target_term.tokens:
        intersection = source.tokens & target_term.tokens
        union = source.tokens | target_term.tokens
        if intersection:
            return 0.5 * (len(intersection) / len(union))
    return 0.0


def _best_field_score(source: _Term, field: TargetField) -> float:
    candidates = [_build_term(term) for term in field.all_terms]
    return max(_score(source, t) for t in candidates) if candidates else 0.0


def match_columns(
    *,
    source_columns: list[str],
    schema: TargetSchema,
) -> list[ColumnMapping]:
    """Her kaynak sutun icin top-N hedef alan onerisi uretir."""
    mappings: list[ColumnMapping] = []
    used_targets: dict[str, str] = {}  # target_field -> source_column (1-1 kilit)

    # Onceligi yuksek skorlulara vermek icin (source, target, score) listesini once doldur.
    ranked: list[tuple[str, str, float]] = []
    source_terms = {col: _build_term(col) for col in source_columns}
    for col, term in source_terms.items():
        for field in schema.fields:
            score = _best_field_score(term, field)
            if score > 0:
                ranked.append((col, field.name, score))
    ranked.sort(key=lambda x: x[2], reverse=True)

    # 1-1 esleme: en yuksek skor uretilen ciftleri once kilitle.
    pinned: dict[str, tuple[str, float]] = {}  # source_column -> (target, score)
    for src, tgt, score in ranked:
        if score < _MATCH_THRESHOLD:
            continue
        if src in pinned or tgt in used_targets:
            continue
        pinned[src] = (tgt, score)
        used_targets[tgt] = src

    # Tum kaynak sutunlar icin response uret.
    for col in source_columns:
        term = source_terms[col]
        all_candidates: list[FieldMatchCandidate] = []
        for fld in schema.fields:
            sc = _best_field_score(term, fld)
            if sc > 0:
                all_candidates.append(FieldMatchCandidate(target_field=fld.name, score=round(sc, 3)))
        all_candidates.sort(key=lambda c: c.score, reverse=True)
        top = all_candidates[:_MAX_CANDIDATES]

        if col in pinned:
            tgt, score = pinned[col]
            mappings.append(
                ColumnMapping(
                    source_column=col,
                    target_field=tgt,
                    confidence=round(score, 3),
                    candidates=top,
                )
            )
        else:
            mappings.append(
                ColumnMapping(
                    source_column=col,
                    target_field=None,
                    confidence=0.0,
                    candidates=top,
                )
            )

    return mappings
