"""
Unit testler: YerlestirmeAlgoritmasi domain servisi.

Kapsam:
- Uygun zon ve raf yoksa None döner
- Kapasitesi yeterli rafı seçer
- Konsolidasyon: aynı üründen palet olan raf yüksek skor alır
- Doluluk skoru: doluluk oranı yüksek raf tercih edilir
- Zon önceliği: MalKabul/Sevkiyat son tercih, Karantina hiç önerilmez
- FIFO: yakın SKT'li rafa öncelik
- En iyi skoru alanı onerilen_raf olarak seçer
- Top-3 alternatif döner
"""

import pytest
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

from app.core.entities.palet import Palet
from app.core.entities.raf import Raf
from app.core.entities.urun import Urun
from app.core.entities.zon import Zon, ZonTipi
from app.core.services.yerlestirme_algoritmasi import YerlestirmeAlgoritmasi

pytestmark = pytest.mark.unit


# ─── Yardımcılar ───────────────────────────────────────────────────────────

def _urun(id=1, depolama_tipi="Kuru") -> Urun:
    return Urun(id=id, isim="Test Ürün", depolama_tipi=depolama_tipi)


def _palet(id=1, lot_id=1, palet_kg=100.0) -> Palet:
    return Palet(
        id=id,
        lot_id=lot_id,
        raf_id=None,
        palet_no=f"PLT-{id:06d}",
        koli_adedi=5,
        palet_kg=palet_kg,
        tarih=datetime.now(timezone.utc),
        olusturma_tarihi=datetime.now(timezone.utc),
        aktif=True,
    )


def _raf(id=1, zon_id=1, kapasite=10, max_agirlik_kg=None) -> Raf:
    return Raf(id=id, zon_id=zon_id, kapasite=kapasite, max_agirlik_kg=max_agirlik_kg,
               kod=f"RAF-{id:03d}", aktif=True)


def _zon(id=1, tip=ZonTipi.GENEL) -> Zon:
    return Zon(id=id, depo_id=1, isim=f"Zon {id}", tip=tip, kod=f"Z{id:03d}")


def _algoritma_kur(
    raflar=None,
    zonlar=None,
    palet_repo_paletler=None,
    zon_repo_getir=None,
):
    raf_repo = MagicMock()
    zon_repo = MagicMock()
    palet_repo = MagicMock()

    raf_repo.getir_hepsi.return_value = raflar or []
    zon_repo.getir_hepsi.return_value = zonlar or []
    zon_repo.getir_id_ile.side_effect = zon_repo_getir or (lambda id: _zon(id))
    palet_repo.getir_hepsi.return_value = palet_repo_paletler or []

    from app.core.services.zon_uyumluluk_servisi import ZonUyumlulukServisi
    from app.core.services.kapasite_dogrulama_servisi import KapasiteDogrulamaServisi

    zon_uyumluluk = ZonUyumlulukServisi(zon_repo=zon_repo)
    kapasite = KapasiteDogrulamaServisi(palet_repo=palet_repo, raf_repo=raf_repo)

    alg = YerlestirmeAlgoritmasi(
        raf_repo=raf_repo,
        zon_repo=zon_repo,
        palet_repo=palet_repo,
        zon_uyumluluk=zon_uyumluluk,
        kapasite_dogrulama=kapasite,
    )
    return alg, raf_repo, zon_repo, palet_repo


# ─── Temel akış ─────────────────────────────────────────────────────────────

class TestTemelAkis:
    def test_uygun_zon_yoksa_none(self):
        """Depolama tipiyle uyumlu hiç zon yoksa None döner."""
        alg, _, zon_repo, _ = _algoritma_kur(zonlar=[])
        zon_repo.getir_hepsi.return_value = []

        oneri = alg.raf_oner(_palet(), _urun(depolama_tipi="Tehlikeli"), depo_id=1)

        assert oneri is None

    def test_uygun_raf_yoksa_none(self):
        """Uygun zon var ama hiç raf atanmamışsa None döner."""
        alg, raf_repo, zon_repo, _ = _algoritma_kur(
            zonlar=[_zon(tip=ZonTipi.GENEL)],
        )
        zon_repo.getir_hepsi.return_value = [_zon(tip=ZonTipi.GENEL)]
        raf_repo.getir_hepsi.return_value = []

        oneri = alg.raf_oner(_palet(), _urun(), depo_id=1)
        assert oneri is None

    def test_kapasite_dolu_raflar_elenir_none(self):
        """Tüm raflar doluysa None döner."""
        dolu_raf = _raf(kapasite=1)

        alg, raf_repo, zon_repo, palet_repo = _algoritma_kur(
            zonlar=[_zon(tip=ZonTipi.GENEL)],
            raflar=[dolu_raf],
        )
        zon_repo.getir_hepsi.return_value = [_zon(tip=ZonTipi.GENEL)]
        raf_repo.getir_hepsi.return_value = [dolu_raf]
        # Rafta zaten 1 palet var (kapasite=1, dolu)
        palet_repo.getir_hepsi.return_value = [_palet()]

        oneri = alg.raf_oner(_palet(), _urun(), depo_id=1)
        assert oneri is None

    def test_tek_uygun_raf_oneri_verir(self):
        """Tek uygun raf varsa onu önerir, alternatif listesi boş olabilir."""
        raf = _raf(id=1, kapasite=10)

        alg, raf_repo, zon_repo, palet_repo = _algoritma_kur()
        zon_repo.getir_hepsi.return_value = [_zon(tip=ZonTipi.GENEL)]
        raf_repo.getir_hepsi.return_value = [raf]
        palet_repo.getir_hepsi.return_value = []

        oneri = alg.raf_oner(_palet(), _urun(), depo_id=1)

        assert oneri is not None
        assert oneri.onerilen_raf.id == raf.id

    def test_skor_0_ile_100_arasinda(self):
        raf = _raf(id=1, kapasite=10)

        alg, raf_repo, zon_repo, palet_repo = _algoritma_kur()
        zon_repo.getir_hepsi.return_value = [_zon(tip=ZonTipi.GENEL)]
        raf_repo.getir_hepsi.return_value = [raf]
        palet_repo.getir_hepsi.return_value = []

        oneri = alg.raf_oner(_palet(), _urun(), depo_id=1)
        assert 0.0 <= oneri.skor <= 100.0

    def test_alternatifler_max_3(self):
        """4 aday raf varsa en iyi 1 öneri + max 3 alternatif döner."""
        raflar = [_raf(id=i, kapasite=10) for i in range(1, 5)]

        alg, raf_repo, zon_repo, palet_repo = _algoritma_kur()
        zon_repo.getir_hepsi.return_value = [_zon(tip=ZonTipi.GENEL)]
        raf_repo.getir_hepsi.return_value = raflar
        palet_repo.getir_hepsi.return_value = []

        oneri = alg.raf_oner(_palet(), _urun(), depo_id=1)

        assert oneri is not None
        assert len(oneri.alternatifler) <= 3
        # Önerilen raf alternatifler listesinde olmamalı
        assert oneri.onerilen_raf.id not in {r.id for r in oneri.alternatifler}


# ─── Konsolidasyon skoru ──────────────────────────────────────────────────

class TestKonsolidasyonSkoru:
    def test_ayni_urunlu_raf_yuksek_skor_alir(self):
        """Aynı üründen palet olan raf, boş rafa karşı tercih edilmeli."""
        raf_aynı_urun = _raf(id=1, kapasite=10)   # üründen palet var
        raf_bos = _raf(id=2, kapasite=10)           # boş

        urun = _urun(id=42)

        # lot.urun_id = 42 olan mock palet
        mevcut_palet = MagicMock()
        mevcut_palet.lot = MagicMock()
        mevcut_palet.lot.urun_id = 42
        mevcut_palet.lot.son_kullanma_tarihi = None
        mevcut_palet.palet_kg = 100.0

        alg, raf_repo, zon_repo, palet_repo = _algoritma_kur()
        zon_repo.getir_hepsi.return_value = [_zon(tip=ZonTipi.GENEL)]
        raf_repo.getir_hepsi.return_value = [raf_aynı_urun, raf_bos]

        def palet_getir_hepsi(**kwargs):
            if kwargs.get("raf_id") == raf_aynı_urun.id:
                return [mevcut_palet]  # mevcut_palet.lot.urun_id == 42
            return []

        palet_repo.getir_hepsi.side_effect = palet_getir_hepsi

        oneri = alg.raf_oner(_palet(), urun, depo_id=1)

        assert oneri is not None
        assert oneri.onerilen_raf.id == raf_aynı_urun.id


# ─── Zon önceliği skoru ───────────────────────────────────────────────────

class TestZonOnceligiSkoru:
    def test_karantina_zonu_onerilmez(self):
        """Algoritma Karantina zonunu filtrelemeli — öneriye dahil etmemeli."""
        raf_karantina = _raf(id=1, zon_id=10, kapasite=10)
        raf_genel = _raf(id=2, zon_id=20, kapasite=10)

        zon_karantina = _zon(id=10, tip=ZonTipi.KARANTINA)
        zon_genel = _zon(id=20, tip=ZonTipi.GENEL)

        alg, raf_repo, zon_repo, palet_repo = _algoritma_kur()
        zon_repo.getir_hepsi.return_value = [zon_karantina, zon_genel]
        zon_repo.getir_id_ile.side_effect = lambda id: zon_karantina if id == 10 else zon_genel

        def raf_getir_hepsi(**kwargs):
            if kwargs.get("zon_id") == 10:
                return [raf_karantina]
            if kwargs.get("zon_id") == 20:
                return [raf_genel]
            return [raf_karantina, raf_genel]

        raf_repo.getir_hepsi.side_effect = raf_getir_hepsi
        palet_repo.getir_hepsi.return_value = []

        oneri = alg.raf_oner(_palet(), _urun(), depo_id=1)

        # Karantina filtrelendi, sadece Genel kalır
        assert oneri is not None
        assert oneri.onerilen_raf.id == raf_genel.id

    def test_genel_zon_malkabul_zonuna_tercih_edilir(self):
        """Genel zon (skor 100) MalKabul (skor düşük) önünde gelir."""
        raf_genel = _raf(id=1, zon_id=1, kapasite=10)
        raf_staging = _raf(id=2, zon_id=2, kapasite=10)

        zon_genel = _zon(id=1, tip=ZonTipi.GENEL)
        zon_staging = _zon(id=2, tip=ZonTipi.MAL_KABUL)

        alg, raf_repo, zon_repo, palet_repo = _algoritma_kur()
        zon_repo.getir_hepsi.return_value = [zon_genel, zon_staging]
        zon_repo.getir_id_ile.side_effect = lambda id: zon_genel if id == 1 else zon_staging

        def raf_getir_hepsi(**kwargs):
            zon_id = kwargs.get("zon_id")
            if zon_id == 1:
                return [raf_genel]
            if zon_id == 2:
                return [raf_staging]
            return []

        raf_repo.getir_hepsi.side_effect = raf_getir_hepsi
        palet_repo.getir_hepsi.return_value = []

        oneri = alg.raf_oner(_palet(), _urun(depolama_tipi="Kuru"), depo_id=1)

        assert oneri is not None
        assert oneri.onerilen_raf.id == raf_genel.id


# ─── FIFO skoru ───────────────────────────────────────────────────────────

class TestFIFOSkoru:
    def test_yakin_skt_raf_yuksek_skor(self):
        """Palet SKT'sine yakın tarihli raf daha yüksek skor almalı."""
        raf_yakin = _raf(id=1, kapasite=10)
        raf_uzak = _raf(id=2, kapasite=10)

        palet_skt = date(2026, 6, 1)
        yakin_palet = MagicMock()
        yakin_palet.lot = MagicMock()
        yakin_palet.lot.urun_id = 99
        yakin_palet.lot.son_kullanma_tarihi = date(2026, 6, 5)  # 4 gün fark
        yakin_palet.palet_kg = 100.0

        uzak_palet = MagicMock()
        uzak_palet.lot = MagicMock()
        uzak_palet.lot.urun_id = 99
        uzak_palet.lot.son_kullanma_tarihi = date(2027, 1, 1)  # 7 ay fark
        uzak_palet.palet_kg = 100.0

        yeni_palet = MagicMock(spec=Palet)
        yeni_palet.id = 99
        yeni_palet.lot_id = 1
        yeni_palet.raf_id = None
        yeni_palet.palet_no = "PLT-NEW"
        yeni_palet.koli_adedi = 5
        yeni_palet.palet_kg = 100.0
        yeni_palet.aktif = True
        yeni_palet.lot = MagicMock()
        yeni_palet.lot.son_kullanma_tarihi = palet_skt

        alg, raf_repo, zon_repo, palet_repo = _algoritma_kur()
        zon_repo.getir_hepsi.return_value = [_zon(tip=ZonTipi.GENEL)]
        raf_repo.getir_hepsi.return_value = [raf_yakin, raf_uzak]

        def palet_getir(**kwargs):
            if kwargs.get("raf_id") == raf_yakin.id:
                return [yakin_palet]
            if kwargs.get("raf_id") == raf_uzak.id:
                return [uzak_palet]
            return []

        palet_repo.getir_hepsi.side_effect = palet_getir

        # Skoru doğrudan al
        skor_yakin = alg._fifo_skoru(raf_yakin, yeni_palet)
        skor_uzak = alg._fifo_skoru(raf_uzak, yeni_palet)

        assert skor_yakin > skor_uzak
