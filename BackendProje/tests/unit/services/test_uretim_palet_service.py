"""Unit testleri — UretimPaletService domain kuralları.

Domain service saf olduğu için hiçbir mock kullanılmaz;
doğrudan entity üzerinde çalışılır.

TC-002: Aynı palet 2 kez kabul_et → 2. reddedilir
TC-003: İptal edilmiş palet kabul_et → reddedilir
TC-005: KARANTINA → KABUL_EDILDI (yetkili) → başarılı
TC-006: KARANTINA → KABUL_EDILDI (yetkisiz) → red
"""

import pytest
from datetime import date

from app.core.entities.palet import Palet, UretimPaletDurum
from app.core.entities.palet_durum_log import PaletDurumLog
from app.core.exceptions import GecersizIslemError, YetkisizIslemError
from app.core.services.uretim_palet_service import UretimPaletService


@pytest.fixture
def service() -> UretimPaletService:
    return UretimPaletService()


@pytest.fixture
def yeni_palet(service: UretimPaletService) -> Palet:
    palet, _ = service.olustur(
        palet_no="PRD-20250416-0001",
        lot_id=1,
        raf_id=99,
        koli_adedi=48,
        uretim_tarihi=date(2025, 4, 16),
        kullanici_id=1,
    )
    palet.id = 1  # persist simülasyonu
    return palet


# ── Oluşturma ────────────────────────────────────────────────────────────────

class TestUretimPaletiOlustur:
    def test_durum_olusturuldu_olarak_baslar(self, service: UretimPaletService):
        palet, log = service.olustur(
            palet_no="PRD-20250416-0001",
            lot_id=1,
            raf_id=99,
            koli_adedi=48,
            uretim_tarihi=date(2025, 4, 16),
            kullanici_id=5,
        )
        assert palet.durum == UretimPaletDurum.OLUSTURULDU
        assert palet.kaynak == "uretim"
        assert palet.palet_no == "PRD-20250416-0001"
        assert palet.koli_adedi == 48
        assert palet.raf_id == 99

    def test_log_donduruluyor(self, service: UretimPaletService):
        _, log = service.olustur(
            palet_no="PRD-X",
            lot_id=1,
            raf_id=55,
            koli_adedi=10,
            kullanici_id=1,
        )
        assert isinstance(log, PaletDurumLog)
        assert log.eski_durum is None
        assert log.yeni_durum == UretimPaletDurum.OLUSTURULDU
        assert log.degistiren_kullanici_id == 1

    def test_repo_cagrisi_yok(self, service: UretimPaletService):
        """Domain service hiçbir repo'ya erişmez — bu test yan etki olmadığını doğrular."""
        palet, log = service.olustur(
            palet_no="PRD-Y",
            lot_id=2,
            raf_id=77,
            koli_adedi=24,
        )
        assert palet is not None and log is not None


# ── Kabul Et (TC-002, TC-003) ─────────────────────────────────────────────────

class TestKabulEt:
    def test_kabul_bekliyor_dan_kabul_edildi_ye_gecer(
        self, service: UretimPaletService, yeni_palet: Palet
    ):
        service.kabul_bekle(yeni_palet, kullanici_id=1)
        log = service.kabul_et(yeni_palet, kullanici_id=2)
        assert yeni_palet.durum == UretimPaletDurum.KABUL_EDILDI
        assert yeni_palet.kabul_eden_kullanici_id == 2
        assert yeni_palet.kabul_tarihi is not None
        assert log.yeni_durum == UretimPaletDurum.KABUL_EDILDI

    def test_tc002_cift_kabul_reddedilir(
        self, service: UretimPaletService, yeni_palet: Palet
    ):
        """TC-002: Zaten kabul_edildi durumundaki paleti tekrar kabul_et → red."""
        service.kabul_bekle(yeni_palet)
        service.kabul_et(yeni_palet, kullanici_id=1)
        with pytest.raises(GecersizIslemError, match="zaten kabul edilmiş"):
            service.kabul_et(yeni_palet, kullanici_id=1)

    def test_tc003_iptal_edilmis_palet_kabul_edilemez(
        self, service: UretimPaletService, yeni_palet: Palet
    ):
        """TC-003: İptal edilmiş palet kabul_et → 'yeniden etiket' mesajı."""
        service.iptal_et(yeni_palet, kullanici_id=1, sebep="test")
        with pytest.raises(GecersizIslemError, match="yeniden etiket"):
            service.kabul_et(yeni_palet, kullanici_id=1)


# ── Karantina (TC-005, TC-006) ────────────────────────────────────────────────

class TestKarantina:
    def _kabul_edildi_palet(
        self, service: UretimPaletService, yeni_palet: Palet
    ) -> Palet:
        service.kabul_bekle(yeni_palet)
        service.kabul_et(yeni_palet, kullanici_id=1)
        return yeni_palet

    def test_kabul_edildi_den_karantina(
        self, service: UretimPaletService, yeni_palet: Palet
    ):
        self._kabul_edildi_palet(service, yeni_palet)
        log = service.karantinaya_al(yeni_palet, kullanici_id=3, sebep="Hasar")
        assert yeni_palet.durum == UretimPaletDurum.KARANTINA
        assert log.sebep == "Hasar"

    def test_tc005_karantinadan_yetkili_cikar(
        self, service: UretimPaletService, yeni_palet: Palet
    ):
        """TC-005: KARANTINA → KABUL_EDILDI (yetkili) başarılı."""
        self._kabul_edildi_palet(service, yeni_palet)
        service.karantinaya_al(yeni_palet)
        log = service.karantinadan_cikar(yeni_palet, kullanici_id=1, yetkili=True)
        assert yeni_palet.durum == UretimPaletDurum.KABUL_EDILDI
        assert log.yeni_durum == UretimPaletDurum.KABUL_EDILDI

    def test_tc006_karantinadan_yetkisiz_cikar_reddedilir(
        self, service: UretimPaletService, yeni_palet: Palet
    ):
        """TC-006: KARANTINA → KABUL_EDILDI (yetkisiz) → red."""
        self._kabul_edildi_palet(service, yeni_palet)
        service.karantinaya_al(yeni_palet)
        with pytest.raises(YetkisizIslemError):
            service.karantinadan_cikar(yeni_palet, kullanici_id=5, yetkili=False)


# ── İptal ─────────────────────────────────────────────────────────────────────

class TestIptal:
    def test_olusturuldu_dan_iptal(
        self, service: UretimPaletService, yeni_palet: Palet
    ):
        log = service.iptal_et(yeni_palet, kullanici_id=1, sebep="Hatalı etiket")
        assert yeni_palet.durum == UretimPaletDurum.IPTAL_EDILDI
        assert yeni_palet.aktif is False
        assert yeni_palet.iptal_sebebi == "Hatalı etiket"
        assert log.yeni_durum == UretimPaletDurum.IPTAL_EDILDI

    def test_kabul_bekliyor_dan_iptal(
        self, service: UretimPaletService, yeni_palet: Palet
    ):
        service.kabul_bekle(yeni_palet)
        service.iptal_et(yeni_palet, sebep="test")
        assert yeni_palet.durum == UretimPaletDurum.IPTAL_EDILDI


# ── Stok Sorguları ────────────────────────────────────────────────────────────

class TestStokSorgu:
    def test_kabul_edildi_stokta(
        self, service: UretimPaletService, yeni_palet: Palet
    ):
        service.kabul_bekle(yeni_palet)
        service.kabul_et(yeni_palet, kullanici_id=1)
        assert yeni_palet.stokta_mi is True
        assert yeni_palet.kullanilabilir_mi is True

    def test_karantina_stokta_ama_kullanilamaz(
        self, service: UretimPaletService, yeni_palet: Palet
    ):
        service.kabul_bekle(yeni_palet)
        service.kabul_et(yeni_palet, kullanici_id=1)
        service.karantinaya_al(yeni_palet)
        assert yeni_palet.stokta_mi is True
        assert yeni_palet.kullanilabilir_mi is False

    def test_iptal_stokta_degil(
        self, service: UretimPaletService, yeni_palet: Palet
    ):
        service.iptal_et(yeni_palet, sebep="test")
        assert yeni_palet.stokta_mi is False
