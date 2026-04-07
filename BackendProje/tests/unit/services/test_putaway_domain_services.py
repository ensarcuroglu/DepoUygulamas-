"""Unit testler: putaway domain servisleri."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.core.entities.palet import Palet
from app.core.entities.raf import Raf
from app.core.entities.zon import Zon, ZonTipi
from app.core.services.kapasite_dogrulama_servisi import KapasiteDogrulamaServisi
from app.core.services.zon_uyumluluk_servisi import ZonUyumlulukServisi

pytestmark = pytest.mark.unit


def _paletler_olustur(adet: int, agirlik: float) -> list[Palet]:
    simdi = datetime.now(timezone.utc)
    return [
        Palet(
            id=i + 1,
            lot_id=1,
            raf_id=1,
            palet_no=f"PLT-{i + 1:06d}",
            koli_adedi=1,
            palet_kg=agirlik,
            tarih=simdi,
            olusturma_tarihi=simdi,
            aktif=True,
        )
        for i in range(adet)
    ]


class TestKapasiteDogrulamaServisi:
    def test_dogrula_tum_sayfalari_hesaba_katar(self):
        palet_repo = MagicMock()
        raf_repo = MagicMock()
        service = KapasiteDogrulamaServisi(palet_repo=palet_repo, raf_repo=raf_repo)

        def fake_getir_hepsi(skip=0, limit=50, raf_id=None, sadece_aktif=True, **kwargs):
            if skip == 0:
                return _paletler_olustur(limit, 1.0)
            if skip == limit:
                return _paletler_olustur(limit, 1.0)
            if skip == limit * 2:
                return _paletler_olustur(200, 1.0)
            return []

        palet_repo.getir_hepsi.side_effect = fake_getir_hepsi

        raf = Raf(id=1, kapasite=1100, max_agirlik_kg=2000.0)
        sonuc = service.dogrula(raf, yeni_palet_kg=0.0)

        assert sonuc.yeterli is False
        assert palet_repo.getir_hepsi.call_count == 3

    def test_mevcut_sayi_ve_doluluk_orani_tum_sayfalari_hesaplar(self):
        palet_repo = MagicMock()
        raf_repo = MagicMock()
        service = KapasiteDogrulamaServisi(palet_repo=palet_repo, raf_repo=raf_repo)

        def fake_getir_hepsi(skip=0, limit=50, raf_id=None, sadece_aktif=True, **kwargs):
            if skip == 0:
                return _paletler_olustur(limit, 1.0)
            if skip == limit:
                return _paletler_olustur(limit, 1.0)
            if skip == limit * 2:
                return _paletler_olustur(200, 1.0)
            return []

        palet_repo.getir_hepsi.side_effect = fake_getir_hepsi

        raf = Raf(id=1, kapasite=2000)
        assert service.mevcut_palet_sayisi(1) == 1200
        assert service.doluluk_orani(raf) == pytest.approx(0.6)


class TestZonUyumlulukServisi:
    def test_uyumlu_zonlari_getir_tum_sayfalari_tarar(self):
        zon_repo = MagicMock()
        service = ZonUyumlulukServisi(zon_repo=zon_repo)

        def fake_getir_hepsi(skip=0, limit=100, depo_id=None, sadece_aktif=True, **kwargs):
            if skip == 0:
                return [
                    Zon(
                        id=i + 1,
                        depo_id=1,
                        isim=f"Genel Zon {i + 1}",
                        tip=ZonTipi.GENEL,
                        kod=f"GNL-{i + 1:03d}",
                    )
                    for i in range(limit)
                ]
            if skip == limit:
                return [
                    Zon(
                        id=999,
                        depo_id=1,
                        isim="Tehlikeli Zon",
                        tip=ZonTipi.TEHLIKELI,
                        kod="THL-001",
                    )
                ]
            return []

        zon_repo.getir_hepsi.side_effect = fake_getir_hepsi

        uyumlu = service.uyumlu_zonlari_getir(depo_id=1, depolama_tipi="Tehlikeli")

        assert [z.id for z in uyumlu] == [999]
        assert zon_repo.getir_hepsi.call_count == 2
