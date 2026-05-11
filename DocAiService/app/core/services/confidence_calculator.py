"""Confidence scoring and missing-field normalization for extracted invoices."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable

REQUIRED_HEADER_FIELDS = ("tedarikci", "irsaliye_no", "tarih")
REQUIRED_ITEM_FIELDS = ("urun_kodu", "ad", "miktar", "birim")
OPTIONAL_ITEM_FIELDS = ("lot_no", "palet_no", "uretim_tarihi", "son_kullanma_tarihi")


def _clamp_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(confidence, 1.0))


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _field_payload(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict) and ("value" in raw or "confidence" in raw):
        return {
            "value": raw.get("value"),
            "confidence": _clamp_confidence(raw.get("confidence")),
        }
    return {"value": raw, "confidence": 0.0 if not _has_value(raw) else 1.0}


def _normalize_required_field(raw: Any, path: str) -> tuple[dict[str, Any], list[str]]:
    field = _field_payload(raw)
    errors: list[str] = []
    if not _has_value(field.get("value")):
        field["value"] = None
        field["confidence"] = 0.0
        errors.append(path)
    return field, errors


def _normalize_optional_field(raw: Any) -> dict[str, Any] | None:
    if raw is None:
        return None
    field = _field_payload(raw)
    if not _has_value(field.get("value")):
        return None
    return field


def _normalize_total(raw: Any) -> dict[str, Any] | None:
    field = _normalize_optional_field(raw)
    if field is None:
        return None
    try:
        Decimal(str(field.get("value")))
    except (InvalidOperation, TypeError, ValueError):
        field["confidence"] = 0.0
    return field


def _average(values: Iterable[float]) -> float:
    scores = list(values)
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 4)


class ConfidenceCalculator:
    """Normalizes LLM output into a schema-safe draft with confidence metadata."""

    def normalize_irsaliye(self, payload: dict[str, Any]) -> dict[str, Any]:
        source = deepcopy(payload or {})
        source.pop("confidence_score", None)

        normalized: dict[str, Any] = {
            "belge_tipi": "IRSALIYE",
            "kalemler": [],
            "missing_fields": [],
            "validation_errors": [],
        }
        if source.get("belge_tipi") == "IRSALIYE":
            normalized["belge_tipi"] = "IRSALIYE"

        confidence_values: list[float] = []
        for field_name in REQUIRED_HEADER_FIELDS:
            field, missing = _normalize_required_field(source.get(field_name), field_name)
            normalized[field_name] = field
            confidence_values.append(field["confidence"])
            normalized["missing_fields"].extend(missing)

        raw_items = source.get("kalemler")
        if not isinstance(raw_items, list) or not raw_items:
            normalized["missing_fields"].append("kalemler")
            confidence_values.extend([0.0] * len(REQUIRED_ITEM_FIELDS))
        else:
            for index, raw_item in enumerate(raw_items):
                item_source = raw_item if isinstance(raw_item, dict) else {}
                item: dict[str, Any] = {}
                for field_name in REQUIRED_ITEM_FIELDS:
                    path = f"kalemler[{index}].{field_name}"
                    field, missing = _normalize_required_field(item_source.get(field_name), path)
                    item[field_name] = field
                    confidence_values.append(field["confidence"])
                    normalized["missing_fields"].extend(missing)

                for field_name in OPTIONAL_ITEM_FIELDS:
                    field = _normalize_optional_field(item_source.get(field_name))
                    if field is not None:
                        item[field_name] = field

                normalized["kalemler"].append(item)

        toplam = _normalize_total(source.get("toplam"))
        if toplam is not None:
            normalized["toplam"] = toplam
            confidence_values.append(toplam["confidence"])

        normalized["validation_errors"] = [
            f"{field_path} alani eksik veya bos"
            for field_path in normalized["missing_fields"]
        ]
        normalized["confidence_score"] = _average(confidence_values)
        return normalized


def normalize_irsaliye_confidence(payload: dict[str, Any]) -> dict[str, Any]:
    return ConfidenceCalculator().normalize_irsaliye(payload)
