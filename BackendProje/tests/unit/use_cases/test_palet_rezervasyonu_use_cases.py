"""Unit testler: app.application.use_cases.palet_rezervasyonu_use_cases.

Kapsam: rezervasyon başlatma (FEFO), iptal, kesinleştirme, değiştirme,
stok detayı ve idempotency / yetersiz stok / çakışma senaryoları.
"""

from __future__ import annotations

from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.application.use_cases.palet_rezervasyonu_use_cases import (
    PaletRezervasyonuListeleUseCase,
    RezervasyonBaslatUseCase,
    RezervasyonDegistirUseCase,
    RezervasyonIptalUseCase,
    RezervasyonKesinlestirUseCase,
    SiparisRezervasyonlariGetirUseCase,
    StokDetayUseCase,
)
from app.core.entities.palet_rezervasyonu import PaletRezervasyonu, RezervasyonDurum
from app.core.exceptions import (
    GecersizIslemError,
    KayitBulunamadiError,
    YetersizStokError,
)

pytestmark = pytest.mark.unit


def _rez(
    *,
    id: int = 1,
    palet_id: int = 100,
    siparis_id: int = 11,
    sevkiyat_kalemi_id: int | None = 21,
    durum: str = RezervasyonDurum.AKTIF,
) -> PaletRezervasyonu:
    return PaletRezervasyonu(
        id=id,
        palet_id=palet_id,
        siparis_id=siparis_id,
        sevkiyat_kalemi_id=sevkiyat_kalemi_id,
        durum=durum,
        rezerve_tarihi=datetime(2026, 4, 12),
    )


def _lot(skt=date(2026, 12, 31), uretim=date(2026, 1, 1)):
    return SimpleNamespace(son_kullanma_tarihi=skt, uretim_tarihi=uretim)


class FakePalet:
    def __init__(self, id=100, koli_adedi=50, lot=None, aktif=True):
        self.id = id
        self.koli_adedi = koli_adedi
        self.lot = lot if lot is not None else _lot()
        self.aktif = aktif


# ─────────────────────────────────────────────────────────────────
# LİSTELE / GETİR
# ─────────────────────────────────────────────────────────────────

class TestListele:
    def test_listele_filtreli_delege_edilir(self):
        repo = MagicMock()
        repo.getir_hepsi.return_value = [_rez(id=1), _rez(id=2)]
        uc = PaletRezervasyonuListeleUseCase(repo)
        sonuc = uc.execute(skip=0, limit=5, durum=RezervasyonDurum.AKTIF, siparis_id=11)
        assert len(sonuc) == 2
        repo.getir_hepsi.assert_called_once_with(skip=0, limit=5, durum=RezervasyonDurum.AKTIF, siparis_id=11)

    def test_siparis_rezervasyonlari(self):
        repo = MagicMock()
        repo.getir_siparis_rezervasyonlari.return_value = [_rez(id=1, siparis_id=11)]
        uc = SiparisRezervasyonlariGetirUseCase(repo)
        sonuc = uc.execute(siparis_id=11)
        assert sonuc[0].siparis_id == 11


# ─────────────────────────────────────────────────────────────────
# BAŞLAT
# ─────────────────────────────────────────────────────────────────

class TestRezervasyonBaslat:
    def _mocks(self):
        return {
            "rezervasyon_repo": MagicMock(),
            "palet_repo": MagicMock(),
            "siparis_repo": MagicMock(),
            "log_repo": MagicMock(),
        }

    def test_siparis_yoksa_hata(self):
        m = self._mocks()
        m["siparis_repo"].getir_id_ile.return_value = None
        uc = RezervasyonBaslatUseCase(**m)
        with pytest.raises(KayitBulunamadiError):
            uc.execute(siparis_id=11, kullanici_id=5)

    def test_mevcut_aktif_rezervasyon_skip_edilir(self):
        m = self._mocks()
        kalem = SimpleNamespace(id=21, urun_id=501)
        m["siparis_repo"].getir_id_ile.return_value = SimpleNamespace(kalemler=[kalem])
        m["rezervasyon_repo"].getir_by_sevkiyat_kalemi.return_value = _rez(
            id=99, sevkiyat_kalemi_id=21, durum=RezervasyonDurum.AKTIF,
        )
        uc = RezervasyonBaslatUseCase(**m)

        sonuc = uc.execute(siparis_id=11, kullanici_id=5)
        assert sonuc == []
        m["palet_repo"].getir_fifo_sirayla_kilitli.assert_not_called()
        m["rezervasyon_repo"].olustur.assert_not_called()

    def test_yetersiz_stok_fefo_aday_yoksa(self):
        m = self._mocks()
        kalem = SimpleNamespace(id=21, urun_id=501)
        m["siparis_repo"].getir_id_ile.return_value = SimpleNamespace(kalemler=[kalem])
        m["rezervasyon_repo"].getir_by_sevkiyat_kalemi.return_value = None
        m["palet_repo"].getir_fifo_sirayla_kilitli.return_value = []
        m["rezervasyon_repo"].rezerve_palet_idleri.return_value = []
        uc = RezervasyonBaslatUseCase(**m)

        with pytest.raises(YetersizStokError):
            uc.execute(siparis_id=11, kullanici_id=5)

    def test_rezerveli_paletler_fefo_disinda_kalir(self):
        m = self._mocks()
        kalem = SimpleNamespace(id=21, urun_id=501)
        m["siparis_repo"].getir_id_ile.return_value = SimpleNamespace(kalemler=[kalem])
        m["rezervasyon_repo"].getir_by_sevkiyat_kalemi.return_value = None
        p1 = FakePalet(id=100, lot=_lot(skt=date(2026, 6, 1)))
        p2 = FakePalet(id=101, lot=_lot(skt=date(2026, 5, 1)))  # daha erken SKT
        m["palet_repo"].getir_fifo_sirayla_kilitli.return_value = [p1, p2]
        m["rezervasyon_repo"].rezerve_palet_idleri.return_value = [101]  # p2 rezerveli
        m["rezervasyon_repo"].olustur.side_effect = lambda r, auto_commit=True: (setattr(r, "id", 77) or r)
        uc = RezervasyonBaslatUseCase(**m)

        sonuc = uc.execute(siparis_id=11, kullanici_id=5)

        # Sadece p1 kullanılabilir
        assert len(sonuc) == 1
        assert sonuc[0].palet_id == 100

    def test_fefo_sirali_en_yakin_skt_secilir(self):
        m = self._mocks()
        kalem = SimpleNamespace(id=21, urun_id=501)
        m["siparis_repo"].getir_id_ile.return_value = SimpleNamespace(kalemler=[kalem])
        m["rezervasyon_repo"].getir_by_sevkiyat_kalemi.return_value = None
        # Repo FIFO ile dönsün; use-case FEFO ile sıralayacak
        p_gec = FakePalet(id=100, lot=_lot(skt=date(2027, 1, 1)))
        p_yak = FakePalet(id=101, lot=_lot(skt=date(2026, 5, 1)))
        m["palet_repo"].getir_fifo_sirayla_kilitli.return_value = [p_gec, p_yak]
        m["rezervasyon_repo"].rezerve_palet_idleri.return_value = []
        m["rezervasyon_repo"].olustur.side_effect = lambda r, auto_commit=True: (setattr(r, "id", 1) or r)
        uc = RezervasyonBaslatUseCase(**m)

        sonuc = uc.execute(siparis_id=11, kullanici_id=5)
        assert len(sonuc) == 1
        assert sonuc[0].palet_id == 101  # en yakın SKT olan


# ─────────────────────────────────────────────────────────────────
# İPTAL
# ─────────────────────────────────────────────────────────────────

class TestRezervasyonIptal:
    def test_aktif_yoksa_log_atmaz_sifir_doner(self):
        repo = MagicMock(); log = MagicMock()
        repo.getir_aktif_by_siparis.return_value = []
        uc = RezervasyonIptalUseCase(repo, log)
        assert uc.execute(siparis_id=11, kullanici_id=5) == 0
        log.olustur.assert_not_called()

    def test_iptal_ederse_her_rezervasyonu_guncelle_cagirir(self):
        repo = MagicMock(); log = MagicMock()
        r1 = _rez(id=1); r2 = _rez(id=2, palet_id=101)
        repo.getir_aktif_by_siparis.return_value = [r1, r2]
        uc = RezervasyonIptalUseCase(repo, log)

        sayi = uc.execute(siparis_id=11, kullanici_id=5, neden="musteri iptali")

        assert sayi == 2
        assert r1.durum == RezervasyonDurum.IPTAL_EDILDI
        assert r2.durum == RezervasyonDurum.IPTAL_EDILDI
        assert repo.guncelle.call_count == 2
        log.olustur.assert_called_once()


# ─────────────────────────────────────────────────────────────────
# KESİNLEŞTİR
# ─────────────────────────────────────────────────────────────────

class TestRezervasyonKesinlestir:
    def test_kesinlestirir_ve_log_atar(self):
        repo = MagicMock(); log = MagicMock()
        r1 = _rez(id=1); r2 = _rez(id=2)
        repo.getir_aktif_by_siparis.return_value = [r1, r2]
        uc = RezervasyonKesinlestirUseCase(repo, log)

        sayi = uc.execute(siparis_id=11, kullanici_id=5)

        assert sayi == 2
        assert r1.durum == RezervasyonDurum.KESINLESTI
        assert r2.durum == RezervasyonDurum.KESINLESTI
        log.olustur.assert_called_once()

    def test_bos_liste_log_atmaz(self):
        repo = MagicMock(); log = MagicMock()
        repo.getir_aktif_by_siparis.return_value = []
        assert RezervasyonKesinlestirUseCase(repo, log).execute(11, 5) == 0
        log.olustur.assert_not_called()


# ─────────────────────────────────────────────────────────────────
# DEĞİŞTİR
# ─────────────────────────────────────────────────────────────────

class TestRezervasyonDegistir:
    def _mocks(self):
        return {
            "rezervasyon_repo": MagicMock(),
            "palet_repo": MagicMock(),
            "log_repo": MagicMock(),
        }

    def test_rezervasyon_yoksa_hata(self):
        m = self._mocks()
        m["rezervasyon_repo"].getir_id_ile.return_value = None
        uc = RezervasyonDegistirUseCase(**m)
        with pytest.raises(KayitBulunamadiError):
            uc.execute(rezervasyon_id=1, yeni_palet_id=200, kullanici_id=5)

    def test_aktif_olmayan_degistirilemez(self):
        m = self._mocks()
        m["rezervasyon_repo"].getir_id_ile.return_value = _rez(durum=RezervasyonDurum.KESINLESTI)
        with pytest.raises(GecersizIslemError):
            RezervasyonDegistirUseCase(**m).execute(1, 200, kullanici_id=5)

    def test_yeni_palet_pasifse_hata(self):
        m = self._mocks()
        m["rezervasyon_repo"].getir_id_ile.return_value = _rez()
        m["palet_repo"].getir_id_ile.return_value = FakePalet(id=200, aktif=False)
        with pytest.raises(KayitBulunamadiError):
            RezervasyonDegistirUseCase(**m).execute(1, 200, kullanici_id=5)

    def test_cakisan_rezervasyon_reddedilir(self):
        m = self._mocks()
        m["rezervasyon_repo"].getir_id_ile.return_value = _rez()
        m["palet_repo"].getir_id_ile.return_value = FakePalet(id=200)
        m["rezervasyon_repo"].getir_aktif_by_palet.return_value = _rez(id=55)
        with pytest.raises(GecersizIslemError, match="zaten"):
            RezervasyonDegistirUseCase(**m).execute(1, 200, kullanici_id=5)

    def test_happy_path_eski_iptal_yeni_aktif(self):
        m = self._mocks()
        eski = _rez(id=1, palet_id=100, siparis_id=11, sevkiyat_kalemi_id=21)
        m["rezervasyon_repo"].getir_id_ile.return_value = eski
        m["palet_repo"].getir_id_ile.return_value = FakePalet(id=200)
        m["rezervasyon_repo"].getir_aktif_by_palet.return_value = None
        m["rezervasyon_repo"].olustur.side_effect = lambda r: (setattr(r, "id", 99) or r)

        sonuc = RezervasyonDegistirUseCase(**m).execute(1, 200, kullanici_id=5, neden="hasar")

        assert eski.durum == RezervasyonDurum.IPTAL_EDILDI
        assert eski.iptal_nedeni == "hasar"
        assert sonuc.id == 99
        assert sonuc.palet_id == 200
        assert sonuc.sevkiyat_kalemi_id == 21


# ─────────────────────────────────────────────────────────────────
# STOK DETAY
# ─────────────────────────────────────────────────────────────────

class TestStokDetay:
    def test_rezerveli_ve_uygun_ayirir(self):
        palet_repo = MagicMock()
        rezervasyon_repo = MagicMock()
        palet_repo.getir_fifo_sirayla.return_value = [
            FakePalet(id=1, koli_adedi=10),
            FakePalet(id=2, koli_adedi=20),
            FakePalet(id=3, koli_adedi=30),
        ]
        rezervasyon_repo.rezerve_palet_idleri.return_value = [2]  # sadece 2. palet rezerve

        sonuc = StokDetayUseCase(palet_repo, rezervasyon_repo).execute(urun_id=501)

        assert sonuc.urun_id == 501
        assert sonuc.toplam_stok == 60
        assert sonuc.rezerve_stok == 20
        assert sonuc.uygun_stok == 40

    def test_bos_stok_negatif_olmaz(self):
        palet_repo = MagicMock()
        rezervasyon_repo = MagicMock()
        palet_repo.getir_fifo_sirayla.return_value = []
        rezervasyon_repo.rezerve_palet_idleri.return_value = []

        sonuc = StokDetayUseCase(palet_repo, rezervasyon_repo).execute(urun_id=501)
        assert sonuc.toplam_stok == 0
        assert sonuc.rezerve_stok == 0
        assert sonuc.uygun_stok == 0
