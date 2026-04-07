"""
Unit testler: ZonUyumlulukServisi + ZonTipi uyumluluk matrisi.

Kapsam:
- Tüm depolama_tipi × zon_tipi kombinasyonları (pozitif + negatif)
- uyumlu_mu() domain metodu
- uyumlu_zonlari_getir() filtresi
- uyumsuzluk_mesaji() içeriği
- ZonTipi.izin_verilen_depolama_tipleri()
"""

import pytest
from unittest.mock import MagicMock

from app.core.entities.zon import Zon, ZonTipi
from app.core.services.zon_uyumluluk_servisi import ZonUyumlulukServisi

pytestmark = pytest.mark.unit


# ─── ZonTipi uyumluluk matrisi testleri ───────────────────────────────────

class TestZonTipiUyumlulukMatrisi:
    """
    Tüm zon_tipi × depolama_tipi kombinasyonları.
    Kaynak: ZonTipi._DEPOLAMA_TIPI_UYUMLULUK
    """

    @pytest.mark.parametrize("zon_tipi,depolama_tipi,beklenen", [
        # GENEL — sadece Kuru
        (ZonTipi.GENEL, "Kuru",     True),
        (ZonTipi.GENEL, "Soguk",    False),
        (ZonTipi.GENEL, "Tehlikeli", False),

        # SOGUK — Kuru ve Soguk
        (ZonTipi.SOGUK, "Kuru",     True),
        (ZonTipi.SOGUK, "Soguk",    True),
        (ZonTipi.SOGUK, "Tehlikeli", False),

        # TEHLIKELI — sadece Tehlikeli
        (ZonTipi.TEHLIKELI, "Tehlikeli", True),
        (ZonTipi.TEHLIKELI, "Kuru",    False),
        (ZonTipi.TEHLIKELI, "Soguk",   False),

        # MAL_KABUL — hepsi (geçici staging)
        (ZonTipi.MAL_KABUL, "Kuru",     True),
        (ZonTipi.MAL_KABUL, "Soguk",    True),
        (ZonTipi.MAL_KABUL, "Tehlikeli", True),

        # SEVKIYAT — hepsi (geçici dispatch)
        (ZonTipi.SEVKIYAT, "Kuru",      True),
        (ZonTipi.SEVKIYAT, "Soguk",     True),
        (ZonTipi.SEVKIYAT, "Tehlikeli", True),

        # KARANTINA — hepsi (izole)
        (ZonTipi.KARANTINA, "Kuru",      True),
        (ZonTipi.KARANTINA, "Soguk",     True),
        (ZonTipi.KARANTINA, "Tehlikeli", True),
    ])
    def test_uyumluluk_matrisi(self, zon_tipi, depolama_tipi, beklenen):
        assert ZonTipi.izin_verilen_depolama_tipleri(zon_tipi).__contains__(depolama_tipi) is beklenen

    def test_bilinmeyen_zon_tipi_bos_set(self):
        izinliler = ZonTipi.izin_verilen_depolama_tipleri("BilinmeyenZon")
        assert izinliler == set()


# ─── ZonUyumlulukServisi.uyumlu_mu() ──────────────────────────────────────

class TestUyumluMu:
    def _servis(self) -> ZonUyumlulukServisi:
        return ZonUyumlulukServisi(zon_repo=MagicMock())

    @pytest.mark.parametrize("depolama_tipi,zon_tipi,beklenen", [
        ("Kuru",     ZonTipi.GENEL,     True),
        ("Soguk",    ZonTipi.GENEL,     False),
        ("Tehlikeli", ZonTipi.GENEL,    False),
        ("Kuru",     ZonTipi.SOGUK,     True),
        ("Soguk",    ZonTipi.SOGUK,     True),
        ("Tehlikeli", ZonTipi.TEHLIKELI, True),
        ("Kuru",     ZonTipi.TEHLIKELI, False),
    ])
    def test_uyumlu_mu(self, depolama_tipi, zon_tipi, beklenen):
        servis = self._servis()
        assert servis.uyumlu_mu(depolama_tipi, zon_tipi) is beklenen


# ─── ZonUyumlulukServisi.uyumlu_zonlari_getir() ───────────────────────────

class TestUyumluZonlariGetir:
    def _zon(self, id: int, tip: str) -> Zon:
        return Zon(id=id, depo_id=1, isim=f"Zon {id}", tip=tip, kod=f"Z{id:03d}")

    def test_kuru_sadece_genel_ve_staging_zonlari_getirir(self):
        zon_repo = MagicMock()
        zon_repo.getir_hepsi.return_value = [
            self._zon(1, ZonTipi.GENEL),
            self._zon(2, ZonTipi.SOGUK),
            self._zon(3, ZonTipi.TEHLIKELI),
            self._zon(4, ZonTipi.MAL_KABUL),
        ]
        servis = ZonUyumlulukServisi(zon_repo=zon_repo)

        uyumlu = servis.uyumlu_zonlari_getir(depo_id=1, depolama_tipi="Kuru")
        uyumlu_idler = {z.id for z in uyumlu}

        # Kuru → Genel, Soguk (Kuru kabul eder), MalKabul, Sevkiyat, Karantina
        # Tehlikeli sadece Tehlikeli kabul eder → dışarıda
        assert 1 in uyumlu_idler   # Genel
        assert 2 in uyumlu_idler   # Soguk (Kuru da kabul eder)
        assert 3 not in uyumlu_idler  # Tehlikeli → dışarıda
        assert 4 in uyumlu_idler   # MalKabul

    def test_tehlikeli_sadece_tehlikeli_zonu_getirir(self):
        zon_repo = MagicMock()
        zon_repo.getir_hepsi.return_value = [
            self._zon(1, ZonTipi.GENEL),
            self._zon(2, ZonTipi.TEHLIKELI),
            self._zon(3, ZonTipi.KARANTINA),
        ]
        servis = ZonUyumlulukServisi(zon_repo=zon_repo)

        uyumlu = servis.uyumlu_zonlari_getir(depo_id=1, depolama_tipi="Tehlikeli")
        uyumlu_idler = {z.id for z in uyumlu}

        assert 1 not in uyumlu_idler  # Genel sadece Kuru
        assert 2 in uyumlu_idler      # Tehlikeli
        assert 3 in uyumlu_idler      # Karantina tümünü kabul eder

    def test_uyumlu_zon_yoksa_bos_liste(self):
        zon_repo = MagicMock()
        zon_repo.getir_hepsi.return_value = [
            self._zon(1, ZonTipi.GENEL),  # sadece Kuru
        ]
        servis = ZonUyumlulukServisi(zon_repo=zon_repo)

        uyumlu = servis.uyumlu_zonlari_getir(depo_id=1, depolama_tipi="Tehlikeli")
        assert uyumlu == []

    def test_depo_id_repo_ya_iletilir(self):
        zon_repo = MagicMock()
        zon_repo.getir_hepsi.return_value = []
        servis = ZonUyumlulukServisi(zon_repo=zon_repo)

        servis.uyumlu_zonlari_getir(depo_id=7, depolama_tipi="Kuru")

        cagri_kwargs = zon_repo.getir_hepsi.call_args.kwargs
        assert cagri_kwargs.get("depo_id") == 7


# ─── uyumsuzluk_mesaji() ─────────────────────────────────────────────────

class TestUyumsuzlukMesaji:
    def test_mesaj_depolama_tipi_ve_zon_tipini_icerir(self):
        servis = ZonUyumlulukServisi(zon_repo=MagicMock())
        mesaj = servis.uyumsuzluk_mesaji("Soguk", ZonTipi.TEHLIKELI)
        assert "Soguk" in mesaj
        assert ZonTipi.TEHLIKELI in mesaj

    def test_mesaj_izin_verilen_tipleri_listeler(self):
        servis = ZonUyumlulukServisi(zon_repo=MagicMock())
        mesaj = servis.uyumsuzluk_mesaji("Kuru", ZonTipi.TEHLIKELI)
        # Tehlikeli zonu yalnızca Tehlikeli tipi kabul eder
        assert "Tehlikeli" in mesaj
