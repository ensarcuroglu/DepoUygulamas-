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
from unittest.mock import MagicMock

from app.core.entities.palet import Palet
from app.core.entities.raf import Raf
from app.core.entities.urun import Urun
from app.core.entities.zon import Zon, ZonTipi
from app.core.services.yerlestirme_algoritmasi import (
    YerlestirmeAlgoritmasi,
    YerlestirmeAyarlari,
)

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
    ayarlar=None,
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
        ayarlar=ayarlar,
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
        # Rafta zaten 1 palet var (kapasite=1, dolu) — raf_id eşleşmesi şart
        mevcut = _palet()
        mevcut.raf_id = dolu_raf.id
        palet_repo.getir_hepsi.return_value = [mevcut]

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
        mevcut_palet.raf_id = raf_aynı_urun.id

        alg, raf_repo, zon_repo, palet_repo = _algoritma_kur()
        zon_repo.getir_hepsi.return_value = [_zon(tip=ZonTipi.GENEL)]
        raf_repo.getir_hepsi.return_value = [raf_aynı_urun, raf_bos]

        # Yeni algoritma raf_ids batch ile çağırır; tek listeyi döner.
        palet_repo.getir_hepsi.return_value = [mevcut_palet]

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
        yakin_palet.raf_id = raf_yakin.id

        uzak_palet = MagicMock()
        uzak_palet.lot = MagicMock()
        uzak_palet.lot.urun_id = 99
        uzak_palet.lot.son_kullanma_tarihi = date(2027, 1, 1)  # 7 ay fark
        uzak_palet.palet_kg = 100.0
        uzak_palet.raf_id = raf_uzak.id

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

        # Yeni imzaya uygun: _fifo_skoru artık (palet, mevcut_paletler) alır
        skor_yakin = alg._fifo_skoru(yeni_palet, [yakin_palet])
        skor_uzak = alg._fifo_skoru(yeni_palet, [uzak_palet])

        assert skor_yakin > skor_uzak


# ─── Skor Bileşen Sözlüğü (açıklanabilirlik) ──────────────────────────────

class TestSkorBilesenleri:
    def test_oneri_bilesenler_sozlugu_dolu_doner(self):
        """raf_oner sonucu bilesenler dict'i dolu olmalı (4 bileşen)."""
        raf = _raf(id=1, kapasite=10)

        alg, raf_repo, zon_repo, palet_repo = _algoritma_kur()
        zon_repo.getir_hepsi.return_value = [_zon(tip=ZonTipi.GENEL)]
        raf_repo.getir_hepsi.return_value = [raf]
        palet_repo.getir_hepsi.return_value = []

        oneri = alg.raf_oner(_palet(), _urun(), depo_id=1)

        assert oneri is not None
        assert set(oneri.bilesenler.keys()) == {
            "konsolidasyon", "doluluk", "fifo", "zon_oncelik",
        }
        for v in oneri.bilesenler.values():
            assert 0.0 <= v <= 100.0

    def test_alternatif_detaylari_skor_ve_gerekce_tasir(self):
        """Alternatifler için skor + gerekçe + bileşenler döner; sıralama korunur."""
        raflar = [_raf(id=i, kapasite=10) for i in range(1, 5)]

        alg, raf_repo, zon_repo, palet_repo = _algoritma_kur()
        zon_repo.getir_hepsi.return_value = [_zon(tip=ZonTipi.GENEL)]
        raf_repo.getir_hepsi.return_value = raflar
        palet_repo.getir_hepsi.return_value = []

        oneri = alg.raf_oner(_palet(), _urun(), depo_id=1)

        assert oneri is not None
        assert len(oneri.alternatif_detaylari) == len(oneri.alternatifler)
        for alt in oneri.alternatif_detaylari:
            assert 0.0 <= alt.skor <= 100.0
            assert isinstance(alt.gerekce, str)
            assert "konsolidasyon" in alt.bilesenler
        # Önerilen skoru, alternatiflerin tümünden büyük veya eşit olmalı
        for alt in oneri.alternatif_detaylari:
            assert oneri.skor >= alt.skor

    def test_skor_ve_bilesenler_toplami_skora_esit(self):
        """_skor_ve_bilesenler bileşen ağırlıklı toplamı = bileşik skor."""
        raf = _raf(id=1, kapasite=10)

        alg, raf_repo, zon_repo, palet_repo = _algoritma_kur()
        zon_repo.getir_hepsi.return_value = [_zon(tip=ZonTipi.GENEL)]
        raf_repo.getir_hepsi.return_value = [raf]
        palet_repo.getir_hepsi.return_value = []

        skor, bilesenler = alg._skor_ve_bilesenler(raf, _urun(), _palet())
        beklenen = (
            bilesenler["konsolidasyon"] * 0.40
            + bilesenler["doluluk"] * 0.30
            + bilesenler["fifo"] * 0.20
            + bilesenler["zon_oncelik"] * 0.10
        )
        assert abs(skor - beklenen) < 0.5  # round(1) toleransı

    def test_oneri_agirliklari_iceriyor(self):
        """Öneri DTO'sunda ağırlıklar şeffaf şekilde döner."""
        raf = _raf(id=1, kapasite=10)

        alg, raf_repo, zon_repo, palet_repo = _algoritma_kur()
        zon_repo.getir_hepsi.return_value = [_zon(tip=ZonTipi.GENEL)]
        raf_repo.getir_hepsi.return_value = [raf]
        palet_repo.getir_hepsi.return_value = []

        oneri = alg.raf_oner(_palet(), _urun(), depo_id=1)
        assert oneri is not None
        assert set(oneri.agirliklar.keys()) == {
            "konsolidasyon", "doluluk", "fifo", "zon_oncelik",
        }
        assert abs(sum(oneri.agirliklar.values()) - 1.0) < 1e-6


# ─── Karışık-SKU cezası ───────────────────────────────────────────────────

class TestKarisikSkuCezasi:
    def test_karisik_raf_bos_raftan_dusuk_skor_alir(self):
        """2+ farklı SKU içeren raf, boş rafa karşı kaybetmeli (konsolidasyon=0)."""
        raf_karisik = _raf(id=1, kapasite=10)
        raf_bos = _raf(id=2, kapasite=10)

        urun = _urun(id=42)

        p1 = MagicMock()
        p1.lot = MagicMock(urun_id=11, son_kullanma_tarihi=None)
        p1.palet_kg = 50.0
        p1.raf_id = raf_karisik.id
        p2 = MagicMock()
        p2.lot = MagicMock(urun_id=22, son_kullanma_tarihi=None)
        p2.palet_kg = 50.0
        p2.raf_id = raf_karisik.id

        alg, raf_repo, zon_repo, palet_repo = _algoritma_kur()
        zon_repo.getir_hepsi.return_value = [_zon(tip=ZonTipi.GENEL)]
        raf_repo.getir_hepsi.return_value = [raf_karisik, raf_bos]
        palet_repo.getir_hepsi.return_value = [p1, p2]

        oneri = alg.raf_oner(_palet(), urun, depo_id=1)
        assert oneri is not None
        # Karışık raf konsolidasyon=0; boş raf konsolidasyon=50 → boş raf kazanır.
        assert oneri.onerilen_raf.id == raf_bos.id

    def test_konsolidasyon_skoru_bantlari(self):
        """Boş=50, aynı SKU>50, farklı tek SKU=10, karışık=0."""
        alg, _, _, _ = _algoritma_kur()
        urun = _urun(id=7)

        # Boş
        assert alg._konsolidasyon_skoru(urun, []) == 50.0

        # Aynı SKU, 1 palet
        p_ayni = MagicMock()
        p_ayni.lot = MagicMock(urun_id=7)
        skor_ayni = alg._konsolidasyon_skoru(urun, [p_ayni])
        assert skor_ayni > 50.0

        # Farklı tek SKU
        p_farkli = MagicMock()
        p_farkli.lot = MagicMock(urun_id=99)
        assert alg._konsolidasyon_skoru(urun, [p_farkli]) == 10.0

        # Karışık (2+ farklı SKU)
        p_x = MagicMock()
        p_x.lot = MagicMock(urun_id=99)
        p_y = MagicMock()
        p_y.lot = MagicMock(urun_id=100)
        assert alg._konsolidasyon_skoru(urun, [p_x, p_y]) == 0.0


# ─── Doluluk U-eğrisi ─────────────────────────────────────────────────────

class TestDolulukUegrisi:
    def test_dolma_orani_doyma_noktasinda_max(self):
        """Doluluk = doyma_orani noktasında skor 100."""
        alg, _, _, _ = _algoritma_kur()
        # Doyma 0.85 default, kapasite 100 ile test edelim:
        raf100 = _raf(kapasite=100)
        mevcut85 = [MagicMock(palet_kg=0.0, lot=None) for _ in range(85)]
        skor = alg._doluluk_skoru(raf100, mevcut85)
        assert 99.0 <= skor <= 100.0

    def test_asiri_dolu_raf_cezalandirilir(self):
        """%85 üstü doluluk skoru U-eğrisiyle düşer."""
        alg, _, _, _ = _algoritma_kur()
        raf = _raf(kapasite=100)
        mevcut95 = [MagicMock(palet_kg=0.0, lot=None) for _ in range(95)]
        mevcut70 = [MagicMock(palet_kg=0.0, lot=None) for _ in range(70)]
        skor95 = alg._doluluk_skoru(raf, mevcut95)
        skor70 = alg._doluluk_skoru(raf, mevcut70)
        # %95 dolu raf, %70 dolu raftan daha düşük skor almalı
        assert skor95 < skor70
        assert skor95 < 50.0

    def test_bos_raf_dusuk_doluluk_skoru(self):
        """Tamamen boş raf doluluk skoru sıfır olmalı (henüz konsolidasyon yok)."""
        alg, _, _, _ = _algoritma_kur()
        raf = _raf(kapasite=10)
        assert alg._doluluk_skoru(raf, []) == 0.0


# ─── Tie-break determinizmi ───────────────────────────────────────────────

class TestTieBreak:
    def test_esit_skor_raf_kod_ile_tie_break(self):
        """Eşit skorlu raflar arasında raf.kod alfabetik küçük olan kazanır."""
        raf_b = Raf(id=1, zon_id=1, kapasite=10, kod="RAF-B", aktif=True)
        raf_a = Raf(id=2, zon_id=1, kapasite=10, kod="RAF-A", aktif=True)

        alg, raf_repo, zon_repo, palet_repo = _algoritma_kur()
        zon_repo.getir_hepsi.return_value = [_zon(tip=ZonTipi.GENEL)]
        raf_repo.getir_hepsi.return_value = [raf_b, raf_a]
        palet_repo.getir_hepsi.return_value = []

        oneri = alg.raf_oner(_palet(), _urun(), depo_id=1)
        assert oneri is not None
        assert oneri.onerilen_raf.kod == "RAF-A"


# ─── Performans regresyonu (N+1 koruması) ─────────────────────────────────

class TestPerformansRegresyonu:
    def test_palet_repo_tek_batch_cagrisi(self):
        """Aday raf sayısından bağımsız, palet_repo.getir_hepsi tek seferde
        raf_ids parametresiyle çağrılmalı (N+1 regresyonu testi)."""
        raflar = [_raf(id=i, kapasite=10, zon_id=1) for i in range(1, 21)]

        alg, raf_repo, zon_repo, palet_repo = _algoritma_kur()
        zon_repo.getir_hepsi.return_value = [_zon(id=1, tip=ZonTipi.GENEL)]
        raf_repo.getir_hepsi.return_value = raflar
        palet_repo.getir_hepsi.return_value = []

        oneri = alg.raf_oner(_palet(), _urun(), depo_id=1)
        assert oneri is not None

        # Algoritma tüm aday raflar için palet_repo'yu tek batch ile çağırmalı.
        raf_ids_calls = [
            call for call in palet_repo.getir_hepsi.call_args_list
            if call.kwargs.get("raf_ids") is not None
        ]
        assert len(raf_ids_calls) == 1
        # Tek raf_id ile yapılan çağrı olmamalı (per-raf N+1 regresyonu).
        per_raf_calls = [
            call for call in palet_repo.getir_hepsi.call_args_list
            if call.kwargs.get("raf_id") is not None
        ]
        assert per_raf_calls == []

    def test_zon_repo_id_per_raf_cagrisi_yok(self):
        """_zon_onceligi_skoru için DB'ye gidilmemeli — zon haritası ön-yüklü."""
        raflar = [_raf(id=i, kapasite=10, zon_id=1) for i in range(1, 11)]

        alg, raf_repo, zon_repo, palet_repo = _algoritma_kur()
        zon_repo.getir_hepsi.return_value = [_zon(id=1, tip=ZonTipi.GENEL)]
        raf_repo.getir_hepsi.return_value = raflar
        palet_repo.getir_hepsi.return_value = []

        alg.raf_oner(_palet(), _urun(), depo_id=1)

        # Zon haritası uyumlu_zonlari_getir'den geldiği için getir_id_ile
        # her raf başına çağrılmamalı.
        assert zon_repo.getir_id_ile.call_count == 0


# ─── Kalıcı depolama filtresi ─────────────────────────────────────────────

class TestKaliciDepolamaFiltresi:
    def test_mal_kabul_zonu_oneriye_dahil_edilmez(self):
        """MalKabul zonu kalıcı depolama hedefi değil; algoritma önermez."""
        raf_genel = _raf(id=1, zon_id=1, kapasite=10)
        raf_staging = _raf(id=2, zon_id=2, kapasite=10)

        zon_genel = _zon(id=1, tip=ZonTipi.GENEL)
        zon_staging = _zon(id=2, tip=ZonTipi.MAL_KABUL)

        alg, raf_repo, zon_repo, palet_repo = _algoritma_kur()
        zon_repo.getir_hepsi.return_value = [zon_genel, zon_staging]

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
        # Sadece Genel zon değerlendirildi → MalKabul rafı ne öneride ne alternatifte
        assert oneri.onerilen_raf.id == raf_genel.id
        assert raf_staging.id not in {a.id for a in oneri.alternatifler}


# ─── Yapılandırılabilir ağırlıklar ────────────────────────────────────────

class TestAyarlar:
    def test_ozel_agirliklar_skoru_etkiler(self):
        """YerlestirmeAyarlari ile ağırlıklar değiştirildiğinde skor değişmeli."""
        raf = _raf(id=1, kapasite=10)

        alg_default, raf_repo, zon_repo, palet_repo = _algoritma_kur()
        zon_repo.getir_hepsi.return_value = [_zon(tip=ZonTipi.GENEL)]
        raf_repo.getir_hepsi.return_value = [raf]
        palet_repo.getir_hepsi.return_value = []
        oneri_default = alg_default.raf_oner(_palet(), _urun(), depo_id=1)

        ayarlar = YerlestirmeAyarlari(
            konsolidasyon_agirlik=1.0,
            doluluk_agirlik=0.0,
            fifo_agirlik=0.0,
            zon_oncelik_agirlik=0.0,
        )
        alg_ozel, raf_repo2, zon_repo2, palet_repo2 = _algoritma_kur(ayarlar=ayarlar)
        zon_repo2.getir_hepsi.return_value = [_zon(tip=ZonTipi.GENEL)]
        raf_repo2.getir_hepsi.return_value = [raf]
        palet_repo2.getir_hepsi.return_value = []
        oneri_ozel = alg_ozel.raf_oner(_palet(), _urun(), depo_id=1)

        assert oneri_default is not None and oneri_ozel is not None
        # Tek bileşene odaklanmış skor, default ile farklı olmalı (boş raf konsolidasyon=50)
        assert oneri_ozel.skor != oneri_default.skor
        assert oneri_ozel.agirliklar["konsolidasyon"] == 1.0
