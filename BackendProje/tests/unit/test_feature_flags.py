"""Unit testleri — Feature flag konfigürasyonu.

Pilot depo ID kontrolü, TUMU sentinel, admin bypass.
"""

import os
import pytest
from app.core.config import FeatureFlags


class TestFeatureFlags:
    def test_bos_env_herkese_kapali(self):
        ff = FeatureFlags.from_env.__wrapped__() if hasattr(FeatureFlags.from_env, "__wrapped__") else FeatureFlags(pilot_depo_ids=[])
        ff = FeatureFlags(pilot_depo_ids=[])
        assert ff.uretim_paleti_aktif_mi(depo_id=1) is False
        assert ff.uretim_paleti_aktif_mi(depo_id=None) is False

    def test_pilot_depo_icinde(self):
        ff = FeatureFlags(pilot_depo_ids=[1, 2])
        assert ff.uretim_paleti_aktif_mi(depo_id=1) is True
        assert ff.uretim_paleti_aktif_mi(depo_id=2) is True

    def test_pilot_depo_disinda(self):
        ff = FeatureFlags(pilot_depo_ids=[1])
        assert ff.uretim_paleti_aktif_mi(depo_id=99) is False

    def test_tumu_sentinel_herkes_erisebilir(self):
        ff = FeatureFlags(pilot_depo_ids=[-1])
        assert ff.uretim_paleti_aktif_mi(depo_id=99) is True
        assert ff.uretim_paleti_aktif_mi(depo_id=1) is True

    def test_admin_bypass_depo_id_none(self):
        """Admin kullanıcı (depo_id=None) pilot listesi boş olsa bile erişebilmeli."""
        ff = FeatureFlags(pilot_depo_ids=[1])
        # depo_id=None → admin gibi davran (Kullanici entity'sindeki kontrolle uyumlu)
        assert ff.uretim_paleti_aktif_mi(depo_id=None) is True

    def test_from_env_csv_parse(self, monkeypatch):
        monkeypatch.setenv("FEATURE_URETIM_PALET_PILOT_DEPO_IDS", "3,7,12")
        ff = FeatureFlags.from_env()
        assert 3 in ff.pilot_depo_ids
        assert 7 in ff.pilot_depo_ids
        assert 12 in ff.pilot_depo_ids

    def test_from_env_tumu(self, monkeypatch):
        monkeypatch.setenv("FEATURE_URETIM_PALET_PILOT_DEPO_IDS", "TUMU")
        ff = FeatureFlags.from_env()
        assert -1 in ff.pilot_depo_ids
        assert ff.uretim_paleti_aktif_mi(depo_id=99) is True

    def test_from_env_bos(self, monkeypatch):
        monkeypatch.setenv("FEATURE_URETIM_PALET_PILOT_DEPO_IDS", "")
        ff = FeatureFlags.from_env()
        assert ff.pilot_depo_ids == []
        assert ff.uretim_paleti_aktif_mi(depo_id=1) is False

    def test_from_env_gecersiz_deger(self, monkeypatch):
        monkeypatch.setenv("FEATURE_URETIM_PALET_PILOT_DEPO_IDS", "abc,xyz")
        ff = FeatureFlags.from_env()
        # Hatalı parse → boş liste, hata fırlatmaz
        assert ff.pilot_depo_ids == []
