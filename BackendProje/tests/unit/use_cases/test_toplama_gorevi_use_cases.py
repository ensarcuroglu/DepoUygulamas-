"""Unit testler: app.application.use_cases.toplama_gorevi_use_cases.

Davranış testleri — repository/servis bağımlılıkları MagicMock ile izole.
Hedef: pick task üretimi, pull-based görev alma, başlat/tamamla/iptal,
FEFO override, yetki ve geçersiz durum geçişi senaryoları.
"""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.application.dto.toplama_gorevi_dto import FefoOverrideRequestDTO
from app.application.use_cases.toplama_gorevi_use_cases import (
    FefoOverrideUseCase,
    GorevBaslatUseCase,
    GorevIptalUseCase,
    GorevTamamlaUseCase,
    PickTaskUretUseCase,
    SiradanGorevAlUseCase,
    ToplamaGoreviGetirUseCase,
    ToplamaGoreviListeleUseCase,
)
from app.core.entities.toplama_gorevi import ToplamaGorevi, ToplamaGoreviDurum
from app.core.exceptions import (
    GecersizDurumGecisiError,
    GecersizIslemError,
    KayitBulunamadiError,
    YetkisizIslemError,
)

pytestmark = pytest.mark.unit


def _gorev(
    *,
    id: int = 1,
    durum: str = ToplamaGoreviDurum.BEKLEMEDE,
    atanan_kullanici_id: int | None = None,
    palet_id: int = 100,
    lot_id: int = 55,
    urun_id: int = 501,
    sevkiyat_id: int = 77,
) -> ToplamaGorevi:
    return ToplamaGorevi(
        id=id,
        sevkiyat_id=sevkiyat_id,
        palet_id=palet_id,
        lot_id=lot_id,
        urun_id=urun_id,
        depo_id=7,
        atanan_kullanici_id=atanan_kullanici_id,
        durum=durum,
        sira_no=1,
        olusturma_tarihi=datetime(2026, 4, 10, 12, 0),
    )


class FakePalet:
    def __init__(self, id=100, palet_no="P-1", aktif=True, koli_adedi=120, lot_id=55, urun_id=501, raf=None):
        self.id = id
        self.palet_no = palet_no
        self.aktif = aktif
        self.koli_adedi = koli_adedi
        self.lot_id = lot_id
        self.urun_id = urun_id
        self.lot = SimpleNamespace(urun_id=urun_id)
        self.raf = raf


# ─────────────────────────────────────────────────────────────────
# LİSTELE / GETİR
# ─────────────────────────────────────────────────────────────────

class TestListeleGetir:
    def test_listele_filtreli_arama_delege_edilir(self):
        repo = MagicMock()
        repo.getir_hepsi.return_value = [_gorev(id=1), _gorev(id=2)]
        uc = ToplamaGoreviListeleUseCase(repo)

        sonuc = uc.execute(skip=10, limit=5, durum="Beklemede", sevkiyat_id=77, kullanici_id=5)

        assert len(sonuc) == 2
        repo.getir_hepsi.assert_called_once_with(
            skip=10, limit=5, durum="Beklemede",
            depo_id=None, kullanici_id=5, sevkiyat_id=77,
        )

    def test_getir_yoksa_hata(self):
        repo = MagicMock()
        repo.getir_id_ile.return_value = None
        uc = ToplamaGoreviGetirUseCase(repo)
        with pytest.raises(KayitBulunamadiError):
            uc.execute(gorev_id=1)

    def test_getir_happy_path(self):
        repo = MagicMock()
        repo.getir_id_ile.return_value = _gorev(id=9)
        uc = ToplamaGoreviGetirUseCase(repo)
        assert uc.execute(gorev_id=9).id == 9


# ─────────────────────────────────────────────────────────────────
# PICK TASK ÜRET
# ─────────────────────────────────────────────────────────────────

class TestPickTaskUret:
    def _mocks(self):
        return {
            "gorev_repo": MagicMock(),
            "rezervasyon_repo": MagicMock(),
            "sevkiyat_repo": MagicMock(),
            "palet_repo": MagicMock(),
            "log_repo": MagicMock(),
        }

    def test_sevkiyat_yoksa_hata(self):
        m = self._mocks()
        m["sevkiyat_repo"].getir_id_ile.return_value = None
        uc = PickTaskUretUseCase(**m)
        with pytest.raises(KayitBulunamadiError):
            uc.execute(sevkiyat_id=77, kullanici_id=5)

    def test_aktif_rezervasyon_yoksa_hata(self):
        m = self._mocks()
        m["sevkiyat_repo"].getir_id_ile.return_value = SimpleNamespace(siparis_id=11)
        m["rezervasyon_repo"].getir_aktif_by_siparis.return_value = []
        uc = PickTaskUretUseCase(**m)
        with pytest.raises(GecersizIslemError, match="rezervasyon"):
            uc.execute(sevkiyat_id=77, kullanici_id=5)

    def test_mevcut_gorev_varsa_skip_edilir(self):
        m = self._mocks()
        m["sevkiyat_repo"].getir_id_ile.return_value = SimpleNamespace(siparis_id=11)
        m["rezervasyon_repo"].getir_aktif_by_siparis.return_value = [
            SimpleNamespace(palet_id=100),
            SimpleNamespace(palet_id=101),
        ]
        # İlk palet için görev zaten var → skip; ikinci palet için üretilecek
        m["gorev_repo"].gorev_var_mi.side_effect = [True, False]
        palet = FakePalet(id=101, raf=SimpleNamespace(depo_id=7))
        m["palet_repo"].getir_id_ile.return_value = palet
        m["gorev_repo"].olustur.side_effect = lambda g: (setattr(g, "id", 9) or g)
        uc = PickTaskUretUseCase(**m)

        sonuc = uc.execute(sevkiyat_id=77, kullanici_id=5)

        assert len(sonuc) == 1
        assert sonuc[0].palet_id == 101
        assert m["gorev_repo"].olustur.call_count == 1

    def test_pasif_palet_skip_edilir(self):
        m = self._mocks()
        m["sevkiyat_repo"].getir_id_ile.return_value = SimpleNamespace(siparis_id=11)
        m["rezervasyon_repo"].getir_aktif_by_siparis.return_value = [
            SimpleNamespace(palet_id=100),
        ]
        m["gorev_repo"].gorev_var_mi.return_value = False
        m["palet_repo"].getir_id_ile.return_value = FakePalet(aktif=False)
        uc = PickTaskUretUseCase(**m)

        sonuc = uc.execute(sevkiyat_id=77, kullanici_id=5)
        assert sonuc == []
        m["gorev_repo"].olustur.assert_not_called()

    def test_happy_path_tum_paletler_icin_gorev_uretilir(self):
        m = self._mocks()
        m["sevkiyat_repo"].getir_id_ile.return_value = SimpleNamespace(siparis_id=11)
        m["rezervasyon_repo"].getir_aktif_by_siparis.return_value = [
            SimpleNamespace(palet_id=100),
            SimpleNamespace(palet_id=101),
        ]
        m["gorev_repo"].gorev_var_mi.return_value = False
        m["palet_repo"].getir_id_ile.side_effect = [
            FakePalet(id=100, raf=SimpleNamespace(depo_id=7)),
            FakePalet(id=101, raf=SimpleNamespace(depo_id=7)),
        ]
        counter = {"n": 0}

        def _olustur(g):
            counter["n"] += 1
            g.id = counter["n"]
            return g

        m["gorev_repo"].olustur.side_effect = _olustur
        uc = PickTaskUretUseCase(**m)

        sonuc = uc.execute(sevkiyat_id=77, kullanici_id=5)
        assert len(sonuc) == 2
        # sira_no 1,2 sırasıyla
        olusturulan_gorevler = [call.args[0] for call in m["gorev_repo"].olustur.call_args_list]
        assert olusturulan_gorevler[0].sira_no == 1
        assert olusturulan_gorevler[1].sira_no == 2
        m["log_repo"].olustur.assert_called_once()


# ─────────────────────────────────────────────────────────────────
# SIRADAN GÖREV AL
# ─────────────────────────────────────────────────────────────────

class TestSiradanGorevAl:
    def test_bekleyen_yoksa_none(self):
        repo = MagicMock()
        repo.getir_next_bekleyen.return_value = None
        uc = SiradanGorevAlUseCase(repo)
        assert uc.execute(kullanici_id=5) is None

    def test_ata_ve_guncelle(self):
        repo = MagicMock()
        gorev = _gorev(id=1, durum=ToplamaGoreviDurum.BEKLEMEDE)
        repo.getir_next_bekleyen.return_value = gorev
        repo.guncelle.return_value = gorev
        uc = SiradanGorevAlUseCase(repo)

        sonuc = uc.execute(kullanici_id=5, depo_id=7)

        assert sonuc.id == 1
        assert sonuc.durum == ToplamaGoreviDurum.ATANDI
        assert gorev.atanan_kullanici_id == 5
        repo.getir_next_bekleyen.assert_called_once_with(depo_id=7, with_lock=True)

    def test_guncelle_none_donerse_none(self):
        repo = MagicMock()
        repo.getir_next_bekleyen.return_value = _gorev()
        repo.guncelle.return_value = None
        uc = SiradanGorevAlUseCase(repo)
        assert uc.execute(kullanici_id=5) is None


# ─────────────────────────────────────────────────────────────────
# BAŞLAT
# ─────────────────────────────────────────────────────────────────

class TestBaslat:
    def test_gorev_yoksa_hata(self):
        repo = MagicMock()
        repo.getir_id_ile.return_value = None
        with pytest.raises(KayitBulunamadiError):
            GorevBaslatUseCase(repo).execute(1, kullanici_id=5)

    def test_yalnizca_atanan_operator(self):
        repo = MagicMock()
        repo.getir_id_ile.return_value = _gorev(
            durum=ToplamaGoreviDurum.ATANDI, atanan_kullanici_id=10,
        )
        with pytest.raises(YetkisizIslemError):
            GorevBaslatUseCase(repo).execute(1, kullanici_id=99)
        repo.guncelle.assert_not_called()

    def test_happy_path(self):
        repo = MagicMock()
        gorev = _gorev(durum=ToplamaGoreviDurum.ATANDI, atanan_kullanici_id=10)
        repo.getir_id_ile.return_value = gorev
        repo.guncelle.return_value = gorev

        sonuc = GorevBaslatUseCase(repo).execute(1, kullanici_id=10)
        assert sonuc.durum == ToplamaGoreviDurum.DEVAM_EDIYOR


# ─────────────────────────────────────────────────────────────────
# TAMAMLA
# ─────────────────────────────────────────────────────────────────

class TestTamamla:
    def _mocks(self):
        return {
            "gorev_repo": MagicMock(),
            "palet_repo": MagicMock(),
            "rezervasyon_repo": MagicMock(),
            "hareket_repo": MagicMock(),
            "log_repo": MagicMock(),
        }

    def test_gorev_yoksa_hata(self):
        m = self._mocks()
        m["gorev_repo"].getir_id_ile.return_value = None
        with pytest.raises(KayitBulunamadiError):
            GorevTamamlaUseCase(**m).execute(1, kullanici_id=5)

    def test_yalnizca_atanan_operator(self):
        m = self._mocks()
        m["gorev_repo"].getir_id_ile.return_value = _gorev(
            durum=ToplamaGoreviDurum.DEVAM_EDIYOR, atanan_kullanici_id=10,
        )
        with pytest.raises(YetkisizIslemError):
            GorevTamamlaUseCase(**m).execute(1, kullanici_id=99)

    def test_devam_etmeyen_gorev_tamamlanamaz(self):
        m = self._mocks()
        m["gorev_repo"].getir_id_ile.return_value = _gorev(
            durum=ToplamaGoreviDurum.ATANDI, atanan_kullanici_id=10,
        )
        with pytest.raises(GecersizIslemError, match="DevamEdiyor"):
            GorevTamamlaUseCase(**m).execute(1, kullanici_id=10)

    def test_pasif_palet_hatasi(self):
        m = self._mocks()
        m["gorev_repo"].getir_id_ile.return_value = _gorev(
            durum=ToplamaGoreviDurum.DEVAM_EDIYOR, atanan_kullanici_id=10,
        )
        m["palet_repo"].getir_id_ile.return_value = FakePalet(aktif=False)
        with pytest.raises(GecersizIslemError, match="palet"):
            GorevTamamlaUseCase(**m).execute(1, kullanici_id=10)

    def test_happy_path_stok_cikis_kayit_atar(self):
        m = self._mocks()
        gorev = _gorev(durum=ToplamaGoreviDurum.DEVAM_EDIYOR, atanan_kullanici_id=10)
        palet = FakePalet(id=100, koli_adedi=50, palet_no="P-100")
        rezervasyon = MagicMock(durum="Aktif")
        m["gorev_repo"].getir_id_ile.return_value = gorev
        m["palet_repo"].getir_id_ile.return_value = palet
        m["rezervasyon_repo"].getir_aktif_by_palet.return_value = rezervasyon

        sonuc = GorevTamamlaUseCase(**m).execute(1, kullanici_id=10)

        assert gorev.durum == ToplamaGoreviDurum.TAMAMLANDI
        assert palet.aktif is False
        rezervasyon.kesinlestir.assert_called_once()
        m["rezervasyon_repo"].guncelle.assert_called_once_with(rezervasyon, auto_commit=False)
        # Stok hareketi CIKIS çağrıldı ve miktar palet.koli_adedi
        hareket_call = m["hareket_repo"].olustur.call_args
        hareket_entity = hareket_call.args[0]
        assert hareket_entity.miktar == 50
        assert hareket_entity.palet_no == "P-100"
        assert sonuc.durum == ToplamaGoreviDurum.TAMAMLANDI

    def test_rezervasyon_yoksa_hareket_yine_de_yazilir(self):
        m = self._mocks()
        gorev = _gorev(durum=ToplamaGoreviDurum.DEVAM_EDIYOR, atanan_kullanici_id=10)
        palet = FakePalet(id=100, koli_adedi=40)
        m["gorev_repo"].getir_id_ile.return_value = gorev
        m["palet_repo"].getir_id_ile.return_value = palet
        m["rezervasyon_repo"].getir_aktif_by_palet.return_value = None

        GorevTamamlaUseCase(**m).execute(1, kullanici_id=10)

        m["rezervasyon_repo"].guncelle.assert_not_called()
        m["hareket_repo"].olustur.assert_called_once()


# ─────────────────────────────────────────────────────────────────
# İPTAL
# ─────────────────────────────────────────────────────────────────

class TestIptal:
    def _mocks(self):
        return {
            "gorev_repo": MagicMock(),
            "rezervasyon_repo": MagicMock(),
            "log_repo": MagicMock(),
        }

    def test_gorev_yoksa_hata(self):
        m = self._mocks()
        m["gorev_repo"].getir_id_ile.return_value = None
        with pytest.raises(KayitBulunamadiError):
            GorevIptalUseCase(**m).execute(1, kullanici_id=5, neden="n")

    def test_tamamlanmis_gorev_iptal_edilemez(self):
        m = self._mocks()
        m["gorev_repo"].getir_id_ile.return_value = _gorev(durum=ToplamaGoreviDurum.TAMAMLANDI)
        with pytest.raises(GecersizDurumGecisiError):
            GorevIptalUseCase(**m).execute(1, kullanici_id=5, neden="n")

    def test_iptal_rezervasyonu_da_iptal_eder(self):
        m = self._mocks()
        gorev = _gorev(durum=ToplamaGoreviDurum.ATANDI)
        rezervasyon = MagicMock()
        m["gorev_repo"].getir_id_ile.return_value = gorev
        m["rezervasyon_repo"].getir_aktif_by_palet.return_value = rezervasyon

        sonuc = GorevIptalUseCase(**m).execute(1, kullanici_id=5, neden="musteri talebi")

        assert sonuc.durum == ToplamaGoreviDurum.IPTAL_EDILDI
        rezervasyon.iptal_et.assert_called_once()
        m["rezervasyon_repo"].guncelle.assert_called_once_with(rezervasyon)

    def test_iptal_rezervasyon_yoksa_atlanir(self):
        m = self._mocks()
        gorev = _gorev(durum=ToplamaGoreviDurum.BEKLEMEDE)
        m["gorev_repo"].getir_id_ile.return_value = gorev
        m["rezervasyon_repo"].getir_aktif_by_palet.return_value = None

        GorevIptalUseCase(**m).execute(1, kullanici_id=5, neden=None)
        m["rezervasyon_repo"].guncelle.assert_not_called()


# ─────────────────────────────────────────────────────────────────
# FEFO OVERRIDE
# ─────────────────────────────────────────────────────────────────

class TestFefoOverride:
    def _mocks(self):
        return {
            "gorev_repo": MagicMock(),
            "rezervasyon_repo": MagicMock(),
            "palet_repo": MagicMock(),
            "log_repo": MagicMock(),
        }

    def _dto(self, palet_id=200, neden="Acil sevkiyat gerektiriyor."):
        return FefoOverrideRequestDTO(yeni_palet_id=palet_id, override_neden=neden)

    def test_sadece_admin_cagirabilir(self):
        uc = FefoOverrideUseCase(**self._mocks())
        with pytest.raises(YetkisizIslemError):
            uc.execute(1, self._dto(), kullanici_id=5, kullanici_rol="depocu")

    def test_gorev_yoksa_hata(self):
        m = self._mocks()
        m["gorev_repo"].getir_id_ile.return_value = None
        with pytest.raises(KayitBulunamadiError):
            FefoOverrideUseCase(**m).execute(1, self._dto(), kullanici_id=5, kullanici_rol="admin")

    def test_tamamlanmis_gorev_icin_override_reddedilir(self):
        m = self._mocks()
        m["gorev_repo"].getir_id_ile.return_value = _gorev(durum=ToplamaGoreviDurum.TAMAMLANDI)
        with pytest.raises(GecersizIslemError):
            FefoOverrideUseCase(**m).execute(1, self._dto(), kullanici_id=5, kullanici_rol="admin")

    def test_yeni_palet_pasifse_hata(self):
        m = self._mocks()
        m["gorev_repo"].getir_id_ile.return_value = _gorev(durum=ToplamaGoreviDurum.BEKLEMEDE)
        m["palet_repo"].getir_id_ile.return_value = FakePalet(aktif=False)
        with pytest.raises(KayitBulunamadiError):
            FefoOverrideUseCase(**m).execute(1, self._dto(), kullanici_id=5, kullanici_rol="admin")

    def test_ayni_paletse_reddedilir(self):
        m = self._mocks()
        gorev = _gorev(durum=ToplamaGoreviDurum.BEKLEMEDE, palet_id=200)
        m["gorev_repo"].getir_id_ile.return_value = gorev
        m["palet_repo"].getir_id_ile.return_value = FakePalet(id=200)
        with pytest.raises(GecersizIslemError, match="farkl"):
            FefoOverrideUseCase(**m).execute(
                1, self._dto(palet_id=200), kullanici_id=5, kullanici_rol="admin",
            )

    def test_farkli_urun_paletine_override_reddedilir(self):
        m = self._mocks()
        gorev = _gorev(durum=ToplamaGoreviDurum.BEKLEMEDE, palet_id=100, urun_id=501)
        m["gorev_repo"].getir_id_ile.return_value = gorev
        # Yeni palet farklı ürün — lot.urun_id=999
        m["palet_repo"].getir_id_ile.return_value = FakePalet(id=200, urun_id=999)
        with pytest.raises(GecersizIslemError, match="aynı ürüne"):
            FefoOverrideUseCase(**m).execute(1, self._dto(), kullanici_id=5, kullanici_rol="admin")

    def test_yeni_palet_rezerveliyse_reddedilir(self):
        m = self._mocks()
        gorev = _gorev(durum=ToplamaGoreviDurum.BEKLEMEDE, palet_id=100, urun_id=501)
        m["gorev_repo"].getir_id_ile.return_value = gorev
        m["palet_repo"].getir_id_ile.return_value = FakePalet(id=200, urun_id=501)
        m["rezervasyon_repo"].getir_aktif_by_palet.side_effect = [
            MagicMock(),  # yeni palet için çakışma
            None,          # eski palet (çağrılmayacak)
        ]
        with pytest.raises(GecersizIslemError, match="zaten"):
            FefoOverrideUseCase(**m).execute(1, self._dto(), kullanici_id=5, kullanici_rol="admin")

    def test_happy_path_eski_rezervasyon_iptal_yeni_olusur(self):
        m = self._mocks()
        gorev = _gorev(durum=ToplamaGoreviDurum.ATANDI, palet_id=100, urun_id=501, lot_id=55)
        m["gorev_repo"].getir_id_ile.return_value = gorev
        m["palet_repo"].getir_id_ile.return_value = FakePalet(id=200, urun_id=501, lot_id=77)
        eski_rezervasyon = MagicMock(siparis_id=11, sevkiyat_kalemi_id=22)
        # İlk çağrı yeni_palet için çakışma kontrolü (None = temiz), ikinci eski_palet için iptal arama
        m["rezervasyon_repo"].getir_aktif_by_palet.side_effect = [None, eski_rezervasyon]

        sonuc = FefoOverrideUseCase(**m).execute(
            1, self._dto(), kullanici_id=5, kullanici_rol="admin",
        )

        # Eski rezervasyon iptal edilip yeni rezervasyon oluşturuldu
        eski_rezervasyon.iptal_et.assert_called_once()
        m["rezervasyon_repo"].guncelle.assert_called_once_with(eski_rezervasyon)
        m["rezervasyon_repo"].olustur.assert_called_once()

        # Görev palet/lot güncellendi
        assert gorev.palet_id == 200
        assert gorev.lot_id == 77
        assert gorev.urun_id == 501
        assert gorev.fefo_override is True
        assert gorev.override_kullanici_id == 5
        assert sonuc.fefo_override is True
