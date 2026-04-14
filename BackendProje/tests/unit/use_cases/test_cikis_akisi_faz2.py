"""
Faz 2 testleri — Çıkış akışı süreç ayrıştırma.

Kapsam:
- YuklemeOnaylaUseCase başarılı akış (kalem üretimi + stok çıkışı + durum değişimi)
- Planlandi dışındaki planda onay reddedilir (mükerrer onay dahil)
- SevkiyatPlaniGuncelle: Planlandi→Yukleniyor geçişi engellenir
- IrsaliyeOlustur: stok çıkışı yapılmaz (evrak-only)
- IrsaliyeOlustur: aynı sevkiyata mükerrer irsaliye reddedilir
"""

from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from app.application.dto.irsaliye_dto import IrsaliyeOlusturRequestDTO
from app.application.dto.sevkiyat_plani_dto import SevkiyatPlaniGuncelleRequestDTO
from app.core.entities.sevkiyat_plani import SevkiyatPlani, SevkiyatDurum
from app.core.exceptions import GecersizIslemError

pytestmark = pytest.mark.unit


# ─── Yardımcılar ───


def _siparis_with_kalemler(n=2):
    siparis = MagicMock()
    siparis.id = 1
    siparis.siparis_no = "SIP-2026-0001"
    kalemler = []
    for i in range(n):
        k = MagicMock()
        k.id = 100 + i
        k.urun_id = 10 + i
        k.miktar = 5 + i
        kalemler.append(k)
    siparis.kalemler = kalemler
    return siparis


def _sevkiyat(durum=SevkiyatDurum.PLANLANDI):
    return SevkiyatPlani(
        id=55,
        siparis_id=1,
        durum=durum,
        yukleme_tarihi=date(2026, 4, 20),
        olusturma_tarihi=datetime(2026, 4, 14),
        guncelleme_tarihi=datetime(2026, 4, 14),
    )


def _irsaliye_entity(sevkiyat_id=55):
    entity = MagicMock()
    entity.id = 200
    entity.siparis_id = 1
    entity.sevkiyat_id = sevkiyat_id
    entity.irsaliye_no = "IRS-2026-0010"
    entity.irsaliye_tarihi = date(2026, 4, 14)
    entity.belge_turu = "SevkIrsaliyesi"
    entity.tir_plaka = None
    entity.sofor_adi = None
    entity.durum = "Taslak"
    entity.olusturma_tarihi = datetime(2026, 4, 14)
    entity.guncelleme_tarihi = datetime(2026, 4, 14)
    return entity


# ═══════════════════════════════════════════════════════
# 1. YuklemeOnaylaUseCase başarılı akış
# ═══════════════════════════════════════════════════════


class TestYuklemeOnaylaBasariliAkis:

    def test_sevkiyat_kalemleri_siparis_kalemlerinden_kopyalanir(self, yukleme_onayla_uc_mock):
        uc, mocks = yukleme_onayla_uc_mock
        plan = _sevkiyat()
        siparis = _siparis_with_kalemler(n=2)

        mocks["sevkiyat_repo"].getir_id_ile_kilitli.return_value = plan
        mocks["sevkiyat_repo"].guncelle.return_value = _sevkiyat(SevkiyatDurum.YUKLENIYOR)
        mocks["siparis_repo"].getir_id_ile.return_value = siparis

        uc.execute(plan_id=55, kullanici_id=7)

        kaydedilen_plan = mocks["sevkiyat_repo"].guncelle.call_args.args[0]
        assert len(kaydedilen_plan.kalemler) == 2
        assert kaydedilen_plan.kalemler[0].siparis_kalemi_id == 100
        assert kaydedilen_plan.kalemler[0].urun_id == 10
        assert kaydedilen_plan.kalemler[0].miktar == 5
        assert kaydedilen_plan.kalemler[1].miktar == 6

    def test_durum_yukleniyor_yapilir(self, yukleme_onayla_uc_mock):
        uc, mocks = yukleme_onayla_uc_mock
        plan = _sevkiyat()
        mocks["sevkiyat_repo"].getir_id_ile_kilitli.return_value = plan
        mocks["sevkiyat_repo"].guncelle.return_value = _sevkiyat(SevkiyatDurum.YUKLENIYOR)
        mocks["siparis_repo"].getir_id_ile.return_value = _siparis_with_kalemler()

        uc.execute(plan_id=55, kullanici_id=7)

        kaydedilen_plan = mocks["sevkiyat_repo"].guncelle.call_args.args[0]
        assert kaydedilen_plan.durum == SevkiyatDurum.YUKLENIYOR

    def test_stok_cikisi_tetiklenir(self, yukleme_onayla_uc_mock):
        uc, mocks = yukleme_onayla_uc_mock
        mocks["sevkiyat_repo"].getir_id_ile_kilitli.return_value = _sevkiyat()
        mocks["sevkiyat_repo"].guncelle.return_value = _sevkiyat(SevkiyatDurum.YUKLENIYOR)
        mocks["siparis_repo"].getir_id_ile.return_value = _siparis_with_kalemler()

        uc.execute(plan_id=55, kullanici_id=7)

        mocks["stok_cikis_service"].siparis_bazli_stok_cikisi.assert_called_once()


# ═══════════════════════════════════════════════════════
# 2. Mükerrer onay + yanlış durumda onay reddi
# ═══════════════════════════════════════════════════════


class TestYuklemeOnayDurumKisitlamasi:

    @pytest.mark.parametrize("durum", [
        SevkiyatDurum.YUKLENIYOR,
        SevkiyatDurum.YOLDA,
        SevkiyatDurum.TESLIM_EDILDI,
    ])
    def test_planlandi_disi_durumda_reddedilir(self, yukleme_onayla_uc_mock, durum):
        uc, mocks = yukleme_onayla_uc_mock
        mocks["sevkiyat_repo"].getir_id_ile_kilitli.return_value = _sevkiyat(durum)

        with pytest.raises(GecersizIslemError, match="Planlandi"):
            uc.execute(plan_id=55, kullanici_id=7)

        mocks["stok_cikis_service"].siparis_bazli_stok_cikisi.assert_not_called()

    def test_kalemsiz_siparis_reddedilir(self, yukleme_onayla_uc_mock):
        uc, mocks = yukleme_onayla_uc_mock
        siparis = MagicMock()
        siparis.kalemler = []
        mocks["sevkiyat_repo"].getir_id_ile_kilitli.return_value = _sevkiyat()
        mocks["siparis_repo"].getir_id_ile.return_value = siparis

        with pytest.raises(GecersizIslemError, match="kalem bulunmadığından"):
            uc.execute(plan_id=55, kullanici_id=7)

    def test_onceki_stok_cikisi_varsa_reddedilir(self, yukleme_onayla_uc_mock):
        uc, mocks = yukleme_onayla_uc_mock
        mocks["sevkiyat_repo"].getir_id_ile_kilitli.return_value = _sevkiyat()
        mocks["siparis_repo"].getir_id_ile.return_value = _siparis_with_kalemler()
        mocks["hareket_repo"].siparis_icin_cikis_var_mi.return_value = True

        with pytest.raises(GecersizIslemError, match="stok"):
            uc.execute(plan_id=55, kullanici_id=7)

        mocks["sevkiyat_repo"].guncelle.assert_not_called()
        mocks["stok_cikis_service"].siparis_bazli_stok_cikisi.assert_not_called()


# ═══════════════════════════════════════════════════════
# 3. SevkiyatPlaniGuncelle: Planlandi→Yukleniyor engeli
# ═══════════════════════════════════════════════════════


class TestSevkiyatGuncellePlanlandiYukleniyorEngeli:

    def test_planlandi_yukleniyor_gecisi_engellenir(self, sevkiyat_guncelle_uc_mock):
        uc, mocks = sevkiyat_guncelle_uc_mock
        mocks["sevkiyat_repo"].getir_id_ile.return_value = _sevkiyat()
        dto = SevkiyatPlaniGuncelleRequestDTO(durum=SevkiyatDurum.YUKLENIYOR)

        with pytest.raises(GecersizIslemError, match="yukleme-onayla"):
            uc.execute(plan_id=55, dto=dto, kullanici_id=3)

        mocks["sevkiyat_repo"].guncelle.assert_not_called()

    def test_yukleniyor_yolda_gecisi_serbest(self, sevkiyat_guncelle_uc_mock):
        uc, mocks = sevkiyat_guncelle_uc_mock
        mocks["sevkiyat_repo"].getir_id_ile.return_value = _sevkiyat(SevkiyatDurum.YUKLENIYOR)
        mocks["sevkiyat_repo"].guncelle.return_value = _sevkiyat(SevkiyatDurum.YOLDA)
        dto = SevkiyatPlaniGuncelleRequestDTO(durum=SevkiyatDurum.YOLDA)

        result = uc.execute(plan_id=55, dto=dto, kullanici_id=3)
        assert result.durum == SevkiyatDurum.YOLDA


# ═══════════════════════════════════════════════════════
# 4. IrsaliyeOlustur: stok çıkışı yok + mükerrer irsaliye reddi
# ═══════════════════════════════════════════════════════


class TestIrsaliyeEvrakOnly:

    def test_sevkiyat_id_zorunludur(self, irsaliye_olustur_uc_mock):
        use_case, mocks = irsaliye_olustur_uc_mock
        dto = IrsaliyeOlusturRequestDTO(siparis_id=1, irsaliye_tarihi=date(2026, 4, 14))

        with pytest.raises(GecersizIslemError, match="sevkiyat plan"):
            use_case.execute(dto, kullanici_id=7)

        mocks["irsaliye_repo"].olustur.assert_not_called()

    def test_ayni_sevkiyata_mukerrer_irsaliye_reddedilir(self, irsaliye_olustur_uc_mock):
        use_case, mocks = irsaliye_olustur_uc_mock
        dto = IrsaliyeOlusturRequestDTO(
            siparis_id=1, sevkiyat_id=55, irsaliye_tarihi=date(2026, 4, 14)
        )

        mocks["siparis_repo"].getir_id_ile.return_value = _siparis_with_kalemler()
        mocks["sevkiyat_repo"].getir_id_ile.return_value = _sevkiyat()
        mocks["irsaliye_repo"].sevkiyat_icin_irsaliye_var_mi.return_value = True

        with pytest.raises(GecersizIslemError, match="zaten bir irsaliye bağlı"):
            use_case.execute(dto, kullanici_id=7)

    def test_gecerli_sevkiyatla_irsaliye_olusturulur(self, irsaliye_olustur_uc_mock):
        use_case, mocks = irsaliye_olustur_uc_mock
        dto = IrsaliyeOlusturRequestDTO(
            siparis_id=1, sevkiyat_id=55, irsaliye_tarihi=date(2026, 4, 14)
        )

        mocks["siparis_repo"].getir_id_ile.return_value = _siparis_with_kalemler()
        mocks["sevkiyat_repo"].getir_id_ile.return_value = _sevkiyat()
        mocks["irsaliye_repo"].sevkiyat_icin_irsaliye_var_mi.return_value = False
        mocks["irsaliye_repo"].sonraki_irsaliye_no.return_value = "IRS-2026-0001"
        mocks["irsaliye_repo"].olustur.return_value = _irsaliye_entity(sevkiyat_id=55)

        result = use_case.execute(dto, kullanici_id=7)

        assert result.id == 200
        assert result.sevkiyat_id == 55
