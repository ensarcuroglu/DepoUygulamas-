"""Sutun esleme algoritmasi: deterministik + Turkce normalize."""

from __future__ import annotations

import pytest

from app.core.entities.wms_target_schemas import (
    SIPARIS_KALEMLERI,
    STOK_SAYIM_KALEMLERI,
    URUN,
    get_target_schema,
)
from app.core.services.sema_matcher import match_columns

pytestmark = pytest.mark.unit


def _by_source(mappings, source: str):
    return next(m for m in mappings if m.source_column == source)


def test_exact_match_siparis_kalemleri():
    cols = ["siparis_no", "urun_kodu", "miktar"]
    mappings = match_columns(source_columns=cols, schema=SIPARIS_KALEMLERI)

    assert _by_source(mappings, "siparis_no").target_field == "siparis_no"
    assert _by_source(mappings, "urun_kodu").target_field == "urun_kodu"
    assert _by_source(mappings, "miktar").target_field == "miktar"
    assert all(m.confidence >= 0.9 for m in mappings)


def test_alias_match_english_turkish_mix():
    cols = ["SKU", "Adet", "Unit Price", "Customer Name"]
    mappings = match_columns(source_columns=cols, schema=SIPARIS_KALEMLERI)

    assert _by_source(mappings, "SKU").target_field == "urun_kodu"
    assert _by_source(mappings, "Adet").target_field == "miktar"
    assert _by_source(mappings, "Unit Price").target_field == "birim_fiyat"
    assert _by_source(mappings, "Customer Name").target_field == "musteri"


def test_turkish_diacritics_normalized():
    """sutun adlarinda ı,ş,ğ,ü oldugunda da eslesir."""
    cols = ["Ürün Kodu", "Sipariş Numarası", "Müşteri"]
    mappings = match_columns(source_columns=cols, schema=SIPARIS_KALEMLERI)

    assert _by_source(mappings, "Ürün Kodu").target_field == "urun_kodu"
    assert _by_source(mappings, "Sipariş Numarası").target_field == "siparis_no"
    assert _by_source(mappings, "Müşteri").target_field == "musteri"


def test_unknown_columns_return_none_target():
    cols = ["random_x", "foobar"]
    mappings = match_columns(source_columns=cols, schema=URUN)
    for m in mappings:
        assert m.target_field is None
        assert m.confidence == 0.0


def test_required_fields_reported_missing():
    # urun.required = (urun_kodu, urun_adi). Sadece urun_kodu var.
    cols = ["urun_kodu", "barkod"]
    mappings = match_columns(source_columns=cols, schema=URUN)

    matched = {m.target_field for m in mappings if m.target_field}
    assert "urun_kodu" in matched
    assert "barkod" in matched
    # urun_adi eslemedi -> caller missing required listesinde gosterecek (router seviyesinde).
    assert "urun_adi" not in matched


def test_one_to_one_lock_prevents_double_assignment():
    """ayni hedef alanin iki kaynaga atanmamasi (1-1 kilit)."""
    cols = ["urun_kodu", "stok_kodu"]
    mappings = match_columns(source_columns=cols, schema=URUN)

    matched_targets = [m.target_field for m in mappings if m.target_field]
    # Ayni target_field iki kaynaga atanamaz.
    assert len(matched_targets) == len(set(matched_targets))


def test_candidates_top3_returned():
    cols = ["urun_kodu"]
    mappings = match_columns(source_columns=cols, schema=URUN)
    m = mappings[0]
    assert 1 <= len(m.candidates) <= 3
    assert m.candidates[0].score >= m.candidates[-1].score


def test_threshold_below_50_treated_as_no_match():
    # 'xyz' hicbir alana yakin degil -> None
    cols = ["xyz"]
    mappings = match_columns(source_columns=cols, schema=URUN)
    assert mappings[0].target_field is None


def test_get_target_schema_unknown_raises():
    with pytest.raises(ValueError):
        get_target_schema("bilinmeyen_sema")


def test_stok_sayim_schema_keys():
    cols = ["sayim_no", "sku", "fiili", "konum"]
    mappings = match_columns(source_columns=cols, schema=STOK_SAYIM_KALEMLERI)
    assert _by_source(mappings, "sayim_no").target_field == "sayim_no"
    assert _by_source(mappings, "sku").target_field == "urun_kodu"
    assert _by_source(mappings, "fiili").target_field == "sayim_miktari"
    assert _by_source(mappings, "konum").target_field == "lokasyon"
