"""
Faz 3 testleri — Durum senkronizasyonu.

Kapsam:
- SiparisDurumOrchestrator idempotent geçişleri.
- Sevkiyat oluştur → sipariş Hazirlaniyor.
- YuklemeOnayla → sipariş YolaCikti.
- Sevkiyat TeslimEdildi → sipariş TeslimEdildi.
- Sevkiyat silindi (başka plan yok) → sipariş Bekleme.
- SiparisGuncelle: Hazirlaniyor ve sonrası manuel durum değişimi reddedilir.
"""

from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from app.application.dto.sevkiyat_plani_dto import (
    SevkiyatPlaniOlusturRequestDTO,
    SevkiyatPlaniGuncelleRequestDTO,
)
from app.application.dto.siparis_dto import SiparisGuncelleRequestDTO
from app.core.entities.sevkiyat_plani import SevkiyatPlani, SevkiyatDurum
from app.core.entities.siparis import Siparis, SiparisDurum
from app.core.exceptions import GecersizIslemError
from app.core.services.siparis_durum_orchestrator import SiparisDurumOrchestrator

pytestmark = pytest.mark.unit


# ─── Yardımcılar ───


def _siparis(durum=SiparisDurum.BEKLEME, sid=1):
    return Siparis(
        id=sid,
        siparis_no=f"SIP-2026-{sid:04d}",
        musteri_adi="Test",
        teslimat_adresi="Adres",
        teslimat_tarihi=date(2026, 5, 1),
        durum=durum,
    )


def _siparis_with_kalemler(n=2, durum=SiparisDurum.HAZIRLANIYOR):
    s = MagicMock()
    s.id = 1
    s.siparis_no = "SIP-2026-0001"
    s.durum = durum
    kalemler = []
    for i in range(n):
        k = MagicMock()
        k.id = 100 + i
        k.urun_id = 10 + i
        k.miktar = 5 + i
        kalemler.append(k)
    s.kalemler = kalemler
    return s


def _sevkiyat(durum=SevkiyatDurum.PLANLANDI, plan_id=55, siparis_id=1):
    return SevkiyatPlani(
        id=plan_id,
        siparis_id=siparis_id,
        durum=durum,
        yukleme_tarihi=date(2026, 4, 20),
        olusturma_tarihi=datetime(2026, 4, 14),
        guncelleme_tarihi=datetime(2026, 4, 14),
    )


# ═══════════════════════════════════════════════════════
# 1. Orchestrator birim testleri
# ═══════════════════════════════════════════════════════


class TestSiparisDurumOrchestrator:

    def _make(self):
        siparis_repo = MagicMock()
        sevkiyat_repo = MagicMock()
        return (
            SiparisDurumOrchestrator(siparis_repo, sevkiyat_repo),
            siparis_repo,
            sevkiyat_repo,
        )

    def test_sevkiyat_planlandi_bekleme_ise_hazirlaniyora_cekilir(self):
        orch, siparis_repo, _ = self._make()
        siparis_repo.getir_id_ile.return_value = _siparis(SiparisDurum.BEKLEME)

        orch.sevkiyat_planlandi(1)

        kaydedilen = siparis_repo.guncelle.call_args.args[0]
        assert kaydedilen.durum == SiparisDurum.HAZIRLANIYOR

    def test_sevkiyat_planlandi_zaten_hazirlaniyorsa_noop(self):
        orch, siparis_repo, _ = self._make()
        siparis_repo.getir_id_ile.return_value = _siparis(SiparisDurum.HAZIRLANIYOR)

        orch.sevkiyat_planlandi(1)

        siparis_repo.guncelle.assert_not_called()

    def test_yukleme_onaylandi_hazirlaniyor_ise_yolacikti(self):
        orch, siparis_repo, _ = self._make()
        siparis_repo.getir_id_ile.return_value = _siparis(SiparisDurum.HAZIRLANIYOR)

        orch.yukleme_onaylandi(1)

        assert siparis_repo.guncelle.call_args.args[0].durum == SiparisDurum.YOLA_CIKTI

    def test_teslim_yolacikti_ise_teslim_edildi(self):
        orch, siparis_repo, _ = self._make()
        siparis_repo.getir_id_ile.return_value = _siparis(SiparisDurum.YOLA_CIKTI)

        orch.sevkiyat_teslim_edildi(1)

        assert siparis_repo.guncelle.call_args.args[0].durum == SiparisDurum.TESLIM_EDILDI

    def test_iptal_baska_plan_varsa_noop(self):
        orch, siparis_repo, sevkiyat_repo = self._make()
        sevkiyat_repo.getir_siparis_id_ile.return_value = _sevkiyat()

        orch.sevkiyat_plani_iptal(1)

        siparis_repo.guncelle.assert_not_called()

    def test_iptal_plan_kalmadi_ve_hazirlaniyor_ise_beklemeye_doner(self):
        orch, siparis_repo, sevkiyat_repo = self._make()
        sevkiyat_repo.getir_siparis_id_ile.return_value = None
        siparis_repo.getir_id_ile.return_value = _siparis(SiparisDurum.HAZIRLANIYOR)

        orch.sevkiyat_plani_iptal(1)

        assert siparis_repo.guncelle.call_args.args[0].durum == SiparisDurum.BEKLEME

    def test_iptal_yolacikti_siparis_geriye_alinmaz(self):
        orch, siparis_repo, sevkiyat_repo = self._make()
        sevkiyat_repo.getir_siparis_id_ile.return_value = None
        siparis_repo.getir_id_ile.return_value = _siparis(SiparisDurum.YOLA_CIKTI)

        orch.sevkiyat_plani_iptal(1)

        siparis_repo.guncelle.assert_not_called()


# ═══════════════════════════════════════════════════════
# 2. Sevkiyat use case'leri orchestrator'ı çağırır mı?
# ═══════════════════════════════════════════════════════


class TestSevkiyatOlusturOrchestrasyon:

    def test_sevkiyat_olusturulunca_orchestrator_cagrilir(self, sevkiyat_olustur_uc_mock):
        uc, mocks = sevkiyat_olustur_uc_mock
        dto = SevkiyatPlaniOlusturRequestDTO(siparis_id=1, yukleme_tarihi=date(2026, 4, 20))
        mocks["siparis_repo"].getir_id_ile.return_value = _siparis()
        mocks["sevkiyat_repo"].olustur.return_value = _sevkiyat()

        uc.execute(dto, kullanici_id=3)

        mocks["durum_orchestrator"].sevkiyat_planlandi.assert_called_once_with(1)


class TestYuklemeOnaylaOrchestrasyon:

    def test_yukleme_onayinda_orchestrator_cagrilir(self, yukleme_onayla_uc_mock):
        uc, mocks = yukleme_onayla_uc_mock
        mocks["sevkiyat_repo"].getir_id_ile_kilitli.return_value = _sevkiyat()
        mocks["sevkiyat_repo"].guncelle.return_value = _sevkiyat(SevkiyatDurum.YUKLENIYOR)
        mocks["siparis_repo"].getir_id_ile.return_value = _siparis_with_kalemler()

        uc.execute(plan_id=55, kullanici_id=7)

        mocks["durum_orchestrator"].yukleme_onaylandi.assert_called_once_with(1)
        mocks["db"].commit.assert_called_once()


class TestSevkiyatGuncelleOrchestrasyon:

    def test_teslim_edildi_gecisinde_orchestrator_cagrilir(self, sevkiyat_guncelle_uc_mock):
        uc, mocks = sevkiyat_guncelle_uc_mock
        mocks["sevkiyat_repo"].getir_id_ile.return_value = _sevkiyat(SevkiyatDurum.YOLDA)
        mocks["sevkiyat_repo"].guncelle.return_value = _sevkiyat(SevkiyatDurum.TESLIM_EDILDI)
        dto = SevkiyatPlaniGuncelleRequestDTO(durum=SevkiyatDurum.TESLIM_EDILDI)

        uc.execute(plan_id=55, dto=dto, kullanici_id=3)

        mocks["durum_orchestrator"].sevkiyat_teslim_edildi.assert_called_once_with(1)

    def test_ara_durum_gecisinde_orchestrator_cagrilmaz(self, sevkiyat_guncelle_uc_mock):
        uc, mocks = sevkiyat_guncelle_uc_mock
        mocks["sevkiyat_repo"].getir_id_ile.return_value = _sevkiyat(SevkiyatDurum.YUKLENIYOR)
        mocks["sevkiyat_repo"].guncelle.return_value = _sevkiyat(SevkiyatDurum.YOLDA)
        dto = SevkiyatPlaniGuncelleRequestDTO(durum=SevkiyatDurum.YOLDA)

        uc.execute(plan_id=55, dto=dto, kullanici_id=3)

        mocks["durum_orchestrator"].sevkiyat_teslim_edildi.assert_not_called()


class TestSevkiyatSilOrchestrasyon:

    def test_silmede_orchestrator_iptal_cagrilir(self, sevkiyat_sil_uc_mock):
        uc, mocks = sevkiyat_sil_uc_mock
        mocks["sevkiyat_repo"].getir_id_ile.return_value = _sevkiyat()

        uc.execute(plan_id=55, kullanici_id=3)

        mocks["durum_orchestrator"].sevkiyat_plani_iptal.assert_called_once_with(1)


# ═══════════════════════════════════════════════════════
# 3. Sipariş manuel durum sıkılaştırması
# ═══════════════════════════════════════════════════════


class TestSiparisManuelDurumKisiti:

    @pytest.mark.parametrize("eski_durum,hedef", [
        (SiparisDurum.HAZIRLANIYOR, SiparisDurum.YOLA_CIKTI),
        (SiparisDurum.YOLA_CIKTI, SiparisDurum.TESLIM_EDILDI),
    ])
    def test_sistem_gudumlu_durumda_manuel_ilerletme_reddedilir(
        self, siparis_guncelle_uc_mock, eski_durum, hedef
    ):
        uc, mocks = siparis_guncelle_uc_mock
        mocks["siparis_repo"].getir_id_ile.return_value = _siparis(eski_durum)
        dto = SiparisGuncelleRequestDTO(durum=hedef)

        with pytest.raises(GecersizIslemError, match="sevkiyat lifecycle"):
            uc.execute(1, dto, kullanici_id=7)

        mocks["siparis_repo"].guncelle.assert_not_called()

    def test_hazirlaniyor_iken_iptal_serbest(self, siparis_guncelle_uc_mock):
        uc, mocks = siparis_guncelle_uc_mock
        mocks["siparis_repo"].getir_id_ile.return_value = _siparis(SiparisDurum.HAZIRLANIYOR)
        mocks["siparis_repo"].guncelle.return_value = _siparis(SiparisDurum.IPTAL)
        dto = SiparisGuncelleRequestDTO(durum=SiparisDurum.IPTAL)

        uc.execute(1, dto, kullanici_id=7)

        mocks["siparis_repo"].guncelle.assert_called_once()

    def test_bekleme_iken_hazirlaniyora_manuel_gecis_engellenmiyor(
        self, siparis_guncelle_uc_mock
    ):
        # Not: manuel Bekleme→Hazirlaniyor şu an engellenmiyor (sevkiyat yokken
        # aşama ilerletilemez ama orchestrator bunu ayrıca idempotent tutuyor).
        uc, mocks = siparis_guncelle_uc_mock
        mocks["siparis_repo"].getir_id_ile.return_value = _siparis(SiparisDurum.BEKLEME)
        mocks["siparis_repo"].guncelle.return_value = _siparis(SiparisDurum.HAZIRLANIYOR)
        dto = SiparisGuncelleRequestDTO(durum=SiparisDurum.HAZIRLANIYOR)

        uc.execute(1, dto, kullanici_id=7)

        mocks["siparis_repo"].guncelle.assert_called_once()
