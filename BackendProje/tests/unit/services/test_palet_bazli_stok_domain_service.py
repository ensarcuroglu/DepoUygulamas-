"""
Unit testler: PaletBazliStokDomainService is kurallari (mock repo ile).
"""

import pytest
from unittest.mock import call
from datetime import date

from app.core.services.palet_bazli_stok_domain_service import PaletBazliStokDomainService
from app.core.entities.kullanici import Kullanici, KullaniciRol
from app.core.entities.palet import Palet
from app.core.entities.lot import Lot
from app.core.entities.raf import Raf
from app.core.entities.stok_hareketi import StokHareketi, HareketTipi
from app.application.dto.palet_bilgi_dto import PaletBilgiDTO
from app.core.exceptions import (
    KayitBulunamadiError,
    GecersizIslemError,
    CakismaHatasi,
    DepoErisimHatasi,
)

pytestmark = pytest.mark.unit


# ── Test veri oluşturucuları ──

def _make_palet_bilgi_dto(**overrides) -> PaletBilgiDTO:
    defaults = dict(
        palet_no="PLT-2026-00001",
        urun_id=1,
        urun_adi="Test Urun",
        urun_barkod="1234567890123",
        lot_no="LOT-2026-0001",
        lot_id=None,
        miktar=100,
        raf_id=5,
        raf_bilgi="Depo-A / R-01-A",
        depo_id=1,
        depo_adi="Depo-A",
        durum="aktif",
        kaynak="irsaliye",
        son_kullanma_tarihi=date(2027, 6, 15),
        giris_yapildi_mi=False,
    )
    defaults.update(overrides)
    return PaletBilgiDTO(**defaults)


def _make_kullanici(**overrides) -> Kullanici:
    defaults = dict(id=1, kullanici_adi="depocu1", rol=KullaniciRol.DEPOCU, depo_id=1)
    defaults.update(overrides)
    return Kullanici(**defaults)


def _make_palet(**overrides) -> Palet:
    defaults = dict(id=10, lot_id=1, raf_id=5, palet_no="PLT-2026-00001", koli_adedi=100, aktif=True)
    defaults.update(overrides)
    return Palet(**defaults)


# ══════════════════════════════════════════
# PALET GIRIS TESTLERI
# ══════════════════════════════════════════

class TestPaletGiris:

    def _setup_giris(self, m, dto=None, lot=None):
        """Ortak giris mock setup'i."""
        dto = dto or _make_palet_bilgi_dto()
        m["veri_kaynagi"].palet_bilgisi_getir.return_value = dto
        m["palet_repo"].getir_palet_no_ile.return_value = None
        m["lot_repo"].getir_lot_no_ile.return_value = lot
        m["lot_repo"].olustur.return_value = Lot(id=1, urun_id=1, lot_no=dto.lot_no)
        m["palet_repo"].olustur.return_value = Palet(id=10, lot_id=1, palet_no=dto.palet_no, koli_adedi=dto.miktar)
        m["hareket_repo"].olustur.return_value = StokHareketi(id=1, hareket_tipi=HareketTipi.GIRIS, miktar=dto.miktar)

    def test_basarili_giris(self, palet_stok_service_mock):
        service, m = palet_stok_service_mock
        self._setup_giris(m)

        result = service.palet_giris("PLT-2026-00001", _make_kullanici())

        assert result.hareket_tipi == HareketTipi.GIRIS
        m["veri_kaynagi"].palet_giris_onayla.assert_called_once_with("PLT-2026-00001")
        m["log_repo"].olustur.assert_called_once()

    def test_kaynak_onayi_opsiyonel_kapatilabilir(self, palet_stok_service_mock):
        service, m = palet_stok_service_mock
        self._setup_giris(m)

        result = service.palet_giris(
            "PLT-2026-00001",
            _make_kullanici(),
            kaynagi_onayla=False,
        )

        assert result.hareket_tipi == HareketTipi.GIRIS
        m["veri_kaynagi"].palet_giris_onayla.assert_not_called()

    def test_zaten_giris_yapilmis(self, palet_stok_service_mock):
        service, m = palet_stok_service_mock
        dto = _make_palet_bilgi_dto(giris_yapildi_mi=True)
        m["veri_kaynagi"].palet_bilgisi_getir.return_value = dto

        with pytest.raises(GecersizIslemError, match="zaten sisteme kaydedilmis"):
            service.palet_giris("PLT-2026-00001", _make_kullanici())

    def test_db_de_mevcut_palet_cakisma(self, palet_stok_service_mock):
        service, m = palet_stok_service_mock
        dto = _make_palet_bilgi_dto()
        m["veri_kaynagi"].palet_bilgisi_getir.return_value = dto
        m["palet_repo"].getir_palet_no_ile.return_value = _make_palet()

        with pytest.raises(CakismaHatasi):
            service.palet_giris("PLT-2026-00001", _make_kullanici())

    def test_depo_yetki_hatasi(self, palet_stok_service_mock):
        service, m = palet_stok_service_mock
        dto = _make_palet_bilgi_dto(depo_id=2, depo_adi="Depo-B")
        m["veri_kaynagi"].palet_bilgisi_getir.return_value = dto
        m["palet_repo"].getir_palet_no_ile.return_value = None

        with pytest.raises(DepoErisimHatasi):
            service.palet_giris("PLT-2026-00001", _make_kullanici(depo_id=1))

    def test_hicbir_depoda_yetkisi_olmayan_kullanici_depo_erisim_hatasi_alir(self, palet_stok_service_mock):
        service, m = palet_stok_service_mock
        dto = _make_palet_bilgi_dto(depo_id=1, depo_adi="Depo-A")
        m["veri_kaynagi"].palet_bilgisi_getir.return_value = dto
        m["palet_repo"].getir_palet_no_ile.return_value = None

        with pytest.raises(DepoErisimHatasi):
            service.palet_giris(
                "PLT-2026-00001",
                _make_kullanici(depo_id=None, depo_erisimi_yok=True),
            )

    def test_mevcut_lot_bulunur(self, palet_stok_service_mock):
        service, m = palet_stok_service_mock
        mevcut_lot = Lot(id=5, urun_id=1, lot_no="LOT-2026-0001")
        self._setup_giris(m, lot=mevcut_lot)

        service.palet_giris("PLT-2026-00001", _make_kullanici())

        m["lot_repo"].olustur.assert_not_called()

    def test_lot_no_bos_yeni_lot_olusturulur(self, palet_stok_service_mock):
        service, m = palet_stok_service_mock
        self._setup_giris(m, dto=_make_palet_bilgi_dto(lot_no=None))

        service.palet_giris("PLT-2026-00001", _make_kullanici())

        m["lot_repo"].olustur.assert_called_once()

    def test_depo_id_none_yetki_kontrolu_atlanir(self, palet_stok_service_mock):
        """depo_id=0 olan DTO'da yetki kontrolu yapilmaz."""
        service, m = palet_stok_service_mock
        self._setup_giris(m, dto=_make_palet_bilgi_dto(depo_id=0))

        service.palet_giris("PLT-2026-00001", _make_kullanici(depo_id=99))


class TestTopluPaletGiris:

    def test_toplu_giriste_kaynak_onayi_commit_sonrasina_birakilir(self, palet_stok_service_mock):
        service, m = palet_stok_service_mock
        paletler = ["PLT-2026-00001", "PLT-2026-00002"]

        def _dto_getir(palet_no):
            return _make_palet_bilgi_dto(
                palet_no=palet_no,
                lot_no=f"LOT-{palet_no}",
                depo_id=1,
                depo_adi="Depo-A",
            )

        m["veri_kaynagi"].palet_bilgisi_getir.side_effect = _dto_getir
        m["palet_repo"].getir_palet_no_ile.return_value = None
        m["lot_repo"].getir_lot_no_ile.return_value = None
        m["lot_repo"].olustur.return_value = Lot(id=1, urun_id=1, lot_no="LOT")
        m["palet_repo"].olustur.side_effect = lambda p, auto_commit=False: Palet(
            id=10 if p.palet_no.endswith("1") else 11,
            lot_id=p.lot_id,
            raf_id=p.raf_id,
            palet_no=p.palet_no,
            koli_adedi=p.koli_adedi,
            aktif=True,
        )
        m["hareket_repo"].olustur.side_effect = lambda h, auto_commit=False: StokHareketi(
            id=1 if h.palet_id == 10 else 2,
            hareket_tipi=h.hareket_tipi,
            miktar=h.miktar,
        )

        sonuclar = service.toplu_palet_giris(paletler, _make_kullanici())

        assert len(sonuclar) == 2
        assert all(s.basarili for s in sonuclar)
        m["veri_kaynagi"].palet_giris_onayla.assert_not_called()

        service.toplu_palet_giris_kaynagini_onayla(paletler)
        m["veri_kaynagi"].palet_giris_onayla.assert_has_calls(
            [call("PLT-2026-00001"), call("PLT-2026-00002")]
        )


# ══════════════════════════════════════════
# PALET CIKIS TESTLERI
# ══════════════════════════════════════════

class TestPaletCikis:

    def _setup_cikis(self, m, palet=None, raf=None, lot=None):
        palet = palet or _make_palet()
        m["palet_repo"].getir_palet_no_ile.return_value = palet
        m["raf_repo"].getir_id_ile.return_value = raf or Raf(id=5, depo_id=1, kod="R-01-A")
        m["lot_repo"].getir_id_ile.return_value = lot or Lot(id=1, urun_id=1, lot_no="LOT-2026-0001")
        m["hareket_repo"].olustur.return_value = StokHareketi(
            id=1, hareket_tipi=HareketTipi.CIKIS, miktar=palet.koli_adedi,
        )
        return palet

    def test_tam_cikis(self, palet_stok_service_mock):
        service, m = palet_stok_service_mock
        self._setup_cikis(m)

        result = service.palet_cikis("PLT-2026-00001", _make_kullanici())

        assert result.hareket_tipi == HareketTipi.CIKIS
        m["palet_repo"].guncelle.assert_called_once()
        m["log_repo"].olustur.assert_called_once()

    def test_kismi_cikis(self, palet_stok_service_mock):
        service, m = palet_stok_service_mock
        palet = self._setup_cikis(m)
        m["hareket_repo"].olustur.return_value = StokHareketi(
            id=1, hareket_tipi=HareketTipi.CIKIS, miktar=30,
        )

        result = service.palet_cikis("PLT-2026-00001", _make_kullanici(), miktar=30)

        assert result.miktar == 30
        assert palet.koli_adedi == 70  # 100 - 30
        assert palet.aktif is True

    def test_palet_bulunamadi(self, palet_stok_service_mock):
        service, m = palet_stok_service_mock
        m["palet_repo"].getir_palet_no_ile.return_value = None

        with pytest.raises(KayitBulunamadiError):
            service.palet_cikis("PLT-YOOOOK", _make_kullanici())

    def test_pasif_palet(self, palet_stok_service_mock):
        service, m = palet_stok_service_mock
        m["palet_repo"].getir_palet_no_ile.return_value = _make_palet(aktif=False, koli_adedi=0)

        with pytest.raises(GecersizIslemError, match="stok bulunmuyor"):
            service.palet_cikis("PLT-2026-00001", _make_kullanici())

    def test_bos_palet(self, palet_stok_service_mock):
        service, m = palet_stok_service_mock
        m["palet_repo"].getir_palet_no_ile.return_value = _make_palet(koli_adedi=0)

        with pytest.raises(GecersizIslemError, match="stok bulunmuyor"):
            service.palet_cikis("PLT-2026-00001", _make_kullanici())

    def test_miktar_asimi(self, palet_stok_service_mock):
        service, m = palet_stok_service_mock
        self._setup_cikis(m, palet=_make_palet(koli_adedi=50))

        with pytest.raises(GecersizIslemError, match="fazla"):
            service.palet_cikis("PLT-2026-00001", _make_kullanici(), miktar=100)

    def test_depo_yetki_hatasi(self, palet_stok_service_mock):
        service, m = palet_stok_service_mock
        m["palet_repo"].getir_palet_no_ile.return_value = _make_palet()
        m["raf_repo"].getir_id_ile.return_value = Raf(id=5, depo_id=1, kod="R-01-A")

        with pytest.raises(DepoErisimHatasi):
            service.palet_cikis("PLT-2026-00001", _make_kullanici(depo_id=99))

    def test_raf_id_none_yetki_kontrolu_atlanir(self, palet_stok_service_mock):
        service, m = palet_stok_service_mock
        palet = _make_palet(raf_id=None)
        m["palet_repo"].getir_palet_no_ile.return_value = palet
        m["lot_repo"].getir_id_ile.return_value = Lot(id=1, urun_id=1)
        m["hareket_repo"].olustur.return_value = StokHareketi(
            id=1, hareket_tipi=HareketTipi.CIKIS, miktar=100,
        )

        service.palet_cikis("PLT-2026-00001", _make_kullanici(depo_id=99))


# ══════════════════════════════════════════
# DEPO ERISIM DOGRULAMA TESTLERI
# ══════════════════════════════════════════

class TestDepoErisimDogrula:

    def test_admin_her_depoya_erisir(self):
        kullanici = _make_kullanici(rol=KullaniciRol.ADMIN, depo_id=None)
        PaletBazliStokDomainService._depo_erisim_dogrula(kullanici, 999, "Uzak Depo")

    def test_depo_id_none_her_yere_erisir(self):
        kullanici = _make_kullanici(rol=KullaniciRol.DEPOCU, depo_id=None)
        PaletBazliStokDomainService._depo_erisim_dogrula(kullanici, 5, "Depo-E")

    def test_atanmis_depo_eslesir(self):
        kullanici = _make_kullanici(depo_id=3)
        PaletBazliStokDomainService._depo_erisim_dogrula(kullanici, 3, "Depo-C")

    def test_atanmis_depo_eslesmez(self):
        kullanici = _make_kullanici(depo_id=3)
        with pytest.raises(DepoErisimHatasi):
            PaletBazliStokDomainService._depo_erisim_dogrula(kullanici, 7, "Depo-G")
