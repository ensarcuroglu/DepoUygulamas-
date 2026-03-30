"""
Unit testler: PaletBazliStokDomainService is kurallari (mock repo ile).
"""

import pytest
from unittest.mock import MagicMock, call
from datetime import date

from app.core.services.palet_bazli_stok_domain_service import PaletBazliStokDomainService
from app.core.entities.kullanici import Kullanici
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


# ── Helpers ──

def _make_service():
    """Mock repo'lu domain service olusturur."""
    mocks = {
        "veri_kaynagi": MagicMock(),
        "palet_repo": MagicMock(),
        "lot_repo": MagicMock(),
        "raf_repo": MagicMock(),
        "hareket_repo": MagicMock(),
        "log_repo": MagicMock(),
    }
    service = PaletBazliStokDomainService(**mocks)
    return service, mocks


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
    defaults = dict(id=1, kullanici_adi="depocu1", rol="depocu", depo_id=1)
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

    def test_basarili_giris(self):
        service, m = _make_service()
        dto = _make_palet_bilgi_dto()
        kullanici = _make_kullanici()

        m["veri_kaynagi"].palet_bilgisi_getir.return_value = dto
        m["palet_repo"].getir_palet_no_ile.return_value = None  # DB'de yok
        m["lot_repo"].getir_lot_no_ile.return_value = None  # yeni lot
        m["lot_repo"].olustur.return_value = Lot(id=1, urun_id=1, lot_no="LOT-2026-0001")
        m["palet_repo"].olustur.return_value = Palet(id=10, lot_id=1, palet_no="PLT-2026-00001", koli_adedi=100)
        m["hareket_repo"].olustur.return_value = StokHareketi(id=1, hareket_tipi=HareketTipi.GIRIS, miktar=100)

        result = service.palet_giris("PLT-2026-00001", kullanici)

        assert result.hareket_tipi == HareketTipi.GIRIS
        m["veri_kaynagi"].palet_giris_onayla.assert_called_once_with("PLT-2026-00001")
        m["log_repo"].olustur.assert_called_once()

    def test_zaten_giris_yapilmis(self):
        service, m = _make_service()
        dto = _make_palet_bilgi_dto(giris_yapildi_mi=True)
        m["veri_kaynagi"].palet_bilgisi_getir.return_value = dto

        with pytest.raises(GecersizIslemError, match="zaten sisteme kaydedilmis"):
            service.palet_giris("PLT-2026-00001", _make_kullanici())

    def test_db_de_mevcut_palet_cakisma(self):
        service, m = _make_service()
        dto = _make_palet_bilgi_dto()
        m["veri_kaynagi"].palet_bilgisi_getir.return_value = dto
        m["palet_repo"].getir_palet_no_ile.return_value = _make_palet()

        with pytest.raises(CakismaHatasi):
            service.palet_giris("PLT-2026-00001", _make_kullanici())

    def test_depo_yetki_hatasi(self):
        service, m = _make_service()
        dto = _make_palet_bilgi_dto(depo_id=2, depo_adi="Depo-B")
        kullanici = _make_kullanici(depo_id=1)

        m["veri_kaynagi"].palet_bilgisi_getir.return_value = dto
        m["palet_repo"].getir_palet_no_ile.return_value = None

        with pytest.raises(DepoErisimHatasi):
            service.palet_giris("PLT-2026-00001", kullanici)

    def test_mevcut_lot_bulunur(self):
        service, m = _make_service()
        dto = _make_palet_bilgi_dto()
        kullanici = _make_kullanici()
        mevcut_lot = Lot(id=5, urun_id=1, lot_no="LOT-2026-0001")

        m["veri_kaynagi"].palet_bilgisi_getir.return_value = dto
        m["palet_repo"].getir_palet_no_ile.return_value = None
        m["lot_repo"].getir_lot_no_ile.return_value = mevcut_lot
        m["palet_repo"].olustur.return_value = Palet(id=10, lot_id=5, palet_no="PLT-2026-00001", koli_adedi=100)
        m["hareket_repo"].olustur.return_value = StokHareketi(id=1, hareket_tipi=HareketTipi.GIRIS, miktar=100)

        service.palet_giris("PLT-2026-00001", kullanici)

        # lot_repo.olustur cagirilmamali — mevcut lot kullanildi
        m["lot_repo"].olustur.assert_not_called()

    def test_lot_no_bos_yeni_lot_olusturulur(self):
        service, m = _make_service()
        dto = _make_palet_bilgi_dto(lot_no=None)
        kullanici = _make_kullanici()

        m["veri_kaynagi"].palet_bilgisi_getir.return_value = dto
        m["palet_repo"].getir_palet_no_ile.return_value = None
        m["lot_repo"].olustur.return_value = Lot(id=1, urun_id=1)
        m["palet_repo"].olustur.return_value = Palet(id=10, lot_id=1, koli_adedi=100)
        m["hareket_repo"].olustur.return_value = StokHareketi(id=1, hareket_tipi=HareketTipi.GIRIS, miktar=100)

        service.palet_giris("PLT-2026-00001", kullanici)

        m["lot_repo"].olustur.assert_called_once()

    def test_depo_id_none_yetki_kontrolu_atlanir(self):
        """depo_id=0 veya None olan DTO'da yetki kontrolu yapilmaz."""
        service, m = _make_service()
        dto = _make_palet_bilgi_dto(depo_id=0)
        kullanici = _make_kullanici(depo_id=99)

        m["veri_kaynagi"].palet_bilgisi_getir.return_value = dto
        m["palet_repo"].getir_palet_no_ile.return_value = None
        m["lot_repo"].olustur.return_value = Lot(id=1, urun_id=1)
        m["palet_repo"].olustur.return_value = Palet(id=10, lot_id=1, koli_adedi=100)
        m["hareket_repo"].olustur.return_value = StokHareketi(id=1, hareket_tipi=HareketTipi.GIRIS, miktar=100)

        # DepoErisimHatasi firlatilmamali
        service.palet_giris("PLT-2026-00001", kullanici)


# ══════════════════════════════════════════
# PALET CIKIS TESTLERI
# ══════════════════════════════════════════

class TestPaletCikis:

    def _setup_cikis(self, m, palet=None, raf=None, lot=None):
        """Ortak cikis setup'i."""
        palet = palet or _make_palet()
        m["palet_repo"].getir_palet_no_ile.return_value = palet
        m["raf_repo"].getir_id_ile.return_value = raf or Raf(id=5, depo_id=1, kod="R-01-A")
        m["lot_repo"].getir_id_ile.return_value = lot or Lot(id=1, urun_id=1, lot_no="LOT-2026-0001")
        m["hareket_repo"].olustur.return_value = StokHareketi(
            id=1, hareket_tipi=HareketTipi.CIKIS, miktar=palet.koli_adedi,
        )
        return palet

    def test_tam_cikis(self):
        service, m = _make_service()
        kullanici = _make_kullanici()
        self._setup_cikis(m)

        result = service.palet_cikis("PLT-2026-00001", kullanici)

        assert result.hareket_tipi == HareketTipi.CIKIS
        m["palet_repo"].guncelle.assert_called_once()
        m["log_repo"].olustur.assert_called_once()

    def test_kismi_cikis(self):
        service, m = _make_service()
        kullanici = _make_kullanici()
        palet = self._setup_cikis(m)
        m["hareket_repo"].olustur.return_value = StokHareketi(
            id=1, hareket_tipi=HareketTipi.CIKIS, miktar=30,
        )

        result = service.palet_cikis("PLT-2026-00001", kullanici, miktar=30)

        assert result.miktar == 30
        assert palet.koli_adedi == 70  # 100 - 30
        assert palet.aktif is True

    def test_palet_bulunamadi(self):
        service, m = _make_service()
        m["palet_repo"].getir_palet_no_ile.return_value = None

        with pytest.raises(KayitBulunamadiError):
            service.palet_cikis("PLT-YOOOOK", _make_kullanici())

    def test_pasif_palet(self):
        service, m = _make_service()
        palet = _make_palet(aktif=False, koli_adedi=0)
        m["palet_repo"].getir_palet_no_ile.return_value = palet

        with pytest.raises(GecersizIslemError, match="stok bulunmuyor"):
            service.palet_cikis("PLT-2026-00001", _make_kullanici())

    def test_bos_palet(self):
        service, m = _make_service()
        palet = _make_palet(koli_adedi=0)
        m["palet_repo"].getir_palet_no_ile.return_value = palet

        with pytest.raises(GecersizIslemError, match="stok bulunmuyor"):
            service.palet_cikis("PLT-2026-00001", _make_kullanici())

    def test_miktar_asimi(self):
        service, m = _make_service()
        kullanici = _make_kullanici()
        self._setup_cikis(m, palet=_make_palet(koli_adedi=50))

        with pytest.raises(GecersizIslemError, match="fazla"):
            service.palet_cikis("PLT-2026-00001", kullanici, miktar=100)

    def test_depo_yetki_hatasi(self):
        service, m = _make_service()
        kullanici = _make_kullanici(depo_id=99)
        m["palet_repo"].getir_palet_no_ile.return_value = _make_palet()
        m["raf_repo"].getir_id_ile.return_value = Raf(id=5, depo_id=1, kod="R-01-A")

        with pytest.raises(DepoErisimHatasi):
            service.palet_cikis("PLT-2026-00001", kullanici)

    def test_raf_id_none_yetki_kontrolu_atlanir(self):
        """raf_id olmayan palette depo yetki kontrolu yapilmaz."""
        service, m = _make_service()
        kullanici = _make_kullanici(depo_id=99)
        palet = _make_palet(raf_id=None)
        m["palet_repo"].getir_palet_no_ile.return_value = palet
        m["lot_repo"].getir_id_ile.return_value = Lot(id=1, urun_id=1)
        m["hareket_repo"].olustur.return_value = StokHareketi(
            id=1, hareket_tipi=HareketTipi.CIKIS, miktar=100,
        )

        # DepoErisimHatasi firlatilmamali
        service.palet_cikis("PLT-2026-00001", kullanici)


# ══════════════════════════════════════════
# DEPO ERISIM DOGRULAMA TESTLERI
# ══════════════════════════════════════════

class TestDepoErisimDogrula:

    def test_admin_her_depoya_erisir(self):
        kullanici = _make_kullanici(rol="admin", depo_id=None)
        # Hata firlatmamali
        PaletBazliStokDomainService._depo_erisim_dogrula(kullanici, 999, "Uzak Depo")

    def test_depo_id_none_her_yere_erisir(self):
        kullanici = _make_kullanici(rol="depocu", depo_id=None)
        PaletBazliStokDomainService._depo_erisim_dogrula(kullanici, 5, "Depo-E")

    def test_atanmis_depo_eslesir(self):
        kullanici = _make_kullanici(depo_id=3)
        PaletBazliStokDomainService._depo_erisim_dogrula(kullanici, 3, "Depo-C")

    def test_atanmis_depo_eslesmez(self):
        kullanici = _make_kullanici(depo_id=3)
        with pytest.raises(DepoErisimHatasi):
            PaletBazliStokDomainService._depo_erisim_dogrula(kullanici, 7, "Depo-G")
