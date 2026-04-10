"""
Unit testler: ERP adapter'lari — Mock, Strict Mapping, Config-driven secim.
"""

import pytest
from datetime import date
from unittest.mock import patch

from app.infrastructure.services.mock_erp_palet_veri_kaynagi_service import (
    MockErpPaletVeriKaynagiService,
)
from app.infrastructure.services.erp_palet_veri_kaynagi_service import (
    ErpPaletVeriKaynagiService,
)
from app.infrastructure.config.erp_config import ErpConfig, PaletVeriKaynagi
from app.application.dto.palet_bilgi_dto import PaletBilgiDTO
from app.core.exceptions import (
    KayitBulunamadiError,
    GecersizIslemError,
    ErpBaglantiHatasi,
    ErpVeriDogrulamaHatasi,
)

pytestmark = pytest.mark.unit


# ═══════════════════════════════════════════════════════════
# MockErpPaletVeriKaynagiService
# ═══════════════════════════════════════════════════════════


class TestMockErpAdapter:
    """Mock ERP adapter dummy data ve state testleri."""

    def setup_method(self):
        self.service = MockErpPaletVeriKaynagiService()

    def test_gecerli_palet_bilgi_doner(self):
        dto = self.service.palet_bilgisi_getir("ERP-2026-00001")
        assert isinstance(dto, PaletBilgiDTO)
        assert dto.palet_no == "ERP-2026-00001"
        assert dto.urun_adi == "Demo Makarna 500g"
        assert dto.miktar == 120
        assert dto.kaynak == "erp"
        assert dto.giris_yapildi_mi is False

    def test_bilinmeyen_palet_kayit_bulunamadi(self):
        with pytest.raises(KayitBulunamadiError):
            self.service.palet_bilgisi_getir("BILINMEYEN-001")

    def test_giris_onayla_durumu_degistirir(self):
        self.service.palet_giris_onayla("ERP-2026-00001")
        dto = self.service.palet_bilgisi_getir("ERP-2026-00001")
        assert dto.giris_yapildi_mi is True

    def test_cift_giris_onayla_hata_firlatir(self):
        self.service.palet_giris_onayla("ERP-2026-00001")
        with pytest.raises(GecersizIslemError):
            self.service.palet_giris_onayla("ERP-2026-00001")

    def test_bilinmeyen_palet_giris_onayla_hata(self):
        with pytest.raises(KayitBulunamadiError):
            self.service.palet_giris_onayla("BILINMEYEN-001")

    def test_tum_mock_paletler_erp_kaynakli(self):
        for palet_no in ["ERP-2026-00001", "ERP-2026-00002", "ERP-2026-00003"]:
            dto = self.service.palet_bilgisi_getir(palet_no)
            assert dto.kaynak == "erp"

    def test_son_kullanma_tarihi_gelecekte(self):
        dto = self.service.palet_bilgisi_getir("ERP-2026-00001")
        assert dto.son_kullanma_tarihi > date.today()

    def test_farkli_depolardaki_paletler(self):
        dto1 = self.service.palet_bilgisi_getir("ERP-2026-00001")
        dto3 = self.service.palet_bilgisi_getir("ERP-2026-00003")
        assert dto1.depo_id == 1
        assert dto3.depo_id == 2


# ═══════════════════════════════════════════════════════════
# ErpPaletVeriKaynagiService — Strict Mapping
# ═══════════════════════════════════════════════════════════


class TestErpAdapterStrictMapping:
    """ERP adapter strict mapping ve baglanti hata testleri."""

    def _make_config(self, url="https://erp.example.com", key="test-key", timeout=30):
        return ErpConfig(
            palet_veri_kaynagi=PaletVeriKaynagi.ERP,
            erp_api_url=url,
            erp_api_key=key,
            erp_timeout=timeout,
        )

    def _gecerli_raw_veri(self):
        return {
            "palet_no": "ERP-2026-99999",
            "urun_id": 42,
            "urun_adi": "Test Urun",
            "urun_barkod": "1234567890123",
            "lot_no": "LOT-ERP-9999",
            "lot_id": None,
            "miktar": 100,
            "raf_id": None,
            "raf_bilgi": None,
            "depo_id": 1,
            "depo_adi": "Ana Depo",
            "durum": "aktif",
            "son_kullanma_tarihi": "2027-06-15",
            "giris_yapildi_mi": False,
        }

    def test_gecerli_veri_dogru_maplenenir(self):
        config = self._make_config()
        service = ErpPaletVeriKaynagiService(config)
        raw = self._gecerli_raw_veri()

        dto = service._strict_map(raw, "ERP-2026-99999")

        assert isinstance(dto, PaletBilgiDTO)
        assert dto.palet_no == "ERP-2026-99999"
        assert dto.urun_id == 42
        assert dto.miktar == 100
        assert dto.kaynak == "erp"
        assert dto.son_kullanma_tarihi == date(2027, 6, 15)
        assert dto.giris_yapildi_mi is False

    def test_eksik_zorunlu_alan_hata_firlatir(self):
        config = self._make_config()
        service = ErpPaletVeriKaynagiService(config)
        raw = self._gecerli_raw_veri()
        raw["urun_adi"] = None  # zorunlu alan None

        with pytest.raises(ErpVeriDogrulamaHatasi) as exc_info:
            service._strict_map(raw, "ERP-2026-99999")
        assert "urun_adi" in exc_info.value.alan

    def test_yanlis_tip_int_yerine_str(self):
        config = self._make_config()
        service = ErpPaletVeriKaynagiService(config)
        raw = self._gecerli_raw_veri()
        raw["urun_id"] = "kırk iki"  # int olmasi gereken alan

        with pytest.raises(ErpVeriDogrulamaHatasi) as exc_info:
            service._strict_map(raw, "ERP-2026-99999")
        assert exc_info.value.alan == "urun_id"
        assert "int" in exc_info.value.beklenen

    def test_bool_yerine_int_hata_firlatir(self):
        config = self._make_config()
        service = ErpPaletVeriKaynagiService(config)
        raw = self._gecerli_raw_veri()
        raw["giris_yapildi_mi"] = 1  # bool olmasi gereken alan

        with pytest.raises(ErpVeriDogrulamaHatasi) as exc_info:
            service._strict_map(raw, "ERP-2026-99999")
        assert exc_info.value.alan == "giris_yapildi_mi"

    def test_gecersiz_tarih_formati(self):
        config = self._make_config()
        service = ErpPaletVeriKaynagiService(config)
        raw = self._gecerli_raw_veri()
        raw["son_kullanma_tarihi"] = "15/06/2027"  # yanlis format

        with pytest.raises(ErpVeriDogrulamaHatasi) as exc_info:
            service._strict_map(raw, "ERP-2026-99999")
        assert "son_kullanma_tarihi" in exc_info.value.alan

    def test_date_objesi_kabul_edilir(self):
        config = self._make_config()
        service = ErpPaletVeriKaynagiService(config)
        raw = self._gecerli_raw_veri()
        raw["son_kullanma_tarihi"] = date(2027, 6, 15)

        dto = service._strict_map(raw, "ERP-2026-99999")
        assert dto.son_kullanma_tarihi == date(2027, 6, 15)

    def test_opsiyonel_alanlar_none_olabilir(self):
        config = self._make_config()
        service = ErpPaletVeriKaynagiService(config)
        raw = self._gecerli_raw_veri()
        raw["urun_barkod"] = None
        raw["lot_no"] = None
        raw["lot_id"] = None
        raw["raf_id"] = None
        raw["raf_bilgi"] = None
        raw["son_kullanma_tarihi"] = None

        dto = service._strict_map(raw, "ERP-2026-99999")
        assert dto.urun_barkod is None
        assert dto.lot_no is None
        assert dto.son_kullanma_tarihi is None

    def test_bos_string_zorunlu_alan_hata(self):
        config = self._make_config()
        service = ErpPaletVeriKaynagiService(config)
        raw = self._gecerli_raw_veri()
        raw["depo_adi"] = "   "  # sadece bosluk

        with pytest.raises(ErpVeriDogrulamaHatasi) as exc_info:
            service._strict_map(raw, "ERP-2026-99999")
        assert exc_info.value.alan == "depo_adi"


# ═══════════════════════════════════════════════════════════
# ErpPaletVeriKaynagiService — Baglanti Hatalari
# ═══════════════════════════════════════════════════════════


class TestErpAdapterBaglanti:
    """ERP baglanti hatasi testleri."""

    def test_yapilandirilmamis_erp_hata_firlatir(self):
        config = ErpConfig(
            palet_veri_kaynagi=PaletVeriKaynagi.ERP,
            erp_api_url=None,
            erp_api_key=None,
            erp_timeout=30,
        )
        service = ErpPaletVeriKaynagiService(config)

        with pytest.raises(ErpBaglantiHatasi) as exc_info:
            service.palet_bilgisi_getir("ERP-2026-00001")
        assert "yapilandirilmamis" in exc_info.value.message.lower()

    def test_sadece_url_key_eksik_hata(self):
        config = ErpConfig(
            palet_veri_kaynagi=PaletVeriKaynagi.ERP,
            erp_api_url="https://erp.example.com",
            erp_api_key=None,
            erp_timeout=30,
        )
        service = ErpPaletVeriKaynagiService(config)

        with pytest.raises(ErpBaglantiHatasi):
            service.palet_bilgisi_getir("ERP-2026-00001")

    def test_yapilandirilmis_ama_implement_edilmemis(self):
        config = ErpConfig(
            palet_veri_kaynagi=PaletVeriKaynagi.ERP,
            erp_api_url="https://erp.example.com",
            erp_api_key="test-api-key-12345",
            erp_timeout=30,
        )
        service = ErpPaletVeriKaynagiService(config)

        with pytest.raises(ErpBaglantiHatasi) as exc_info:
            service.palet_bilgisi_getir("ERP-2026-00001")
        assert "implement edilmedi" in exc_info.value.message.lower()

    def test_giris_onayla_da_baglanti_hatasi_firlatir(self):
        config = ErpConfig(
            palet_veri_kaynagi=PaletVeriKaynagi.ERP,
            erp_api_url=None,
            erp_api_key=None,
            erp_timeout=30,
        )
        service = ErpPaletVeriKaynagiService(config)

        with pytest.raises(ErpBaglantiHatasi):
            service.palet_giris_onayla("ERP-2026-00001")


# ═══════════════════════════════════════════════════════════
# ErpConfig
# ═══════════════════════════════════════════════════════════


class TestErpConfig:
    """ErpConfig .env okuma ve dogrulama testleri."""

    @patch.dict("os.environ", {"PALET_VERI_KAYNAGI": "MOCK"})
    def test_mock_secimi(self):
        config = ErpConfig.from_env()
        assert config.palet_veri_kaynagi == PaletVeriKaynagi.MOCK

    @patch.dict("os.environ", {"PALET_VERI_KAYNAGI": "ERP"})
    def test_erp_secimi(self):
        config = ErpConfig.from_env()
        assert config.palet_veri_kaynagi == PaletVeriKaynagi.ERP

    @patch.dict("os.environ", {}, clear=True)
    def test_varsayilan_local(self):
        config = ErpConfig.from_env()
        assert config.palet_veri_kaynagi == PaletVeriKaynagi.LOCAL

    @patch.dict("os.environ", {"PALET_VERI_KAYNAGI": "gecersiz_deger"})
    def test_gecersiz_deger_local_a_doner(self):
        config = ErpConfig.from_env()
        assert config.palet_veri_kaynagi == PaletVeriKaynagi.LOCAL

    @patch.dict("os.environ", {
        "PALET_VERI_KAYNAGI": "ERP",
        "ERP_API_URL": "https://erp.test.com",
        "ERP_API_KEY": "secret123",
        "ERP_TIMEOUT": "60",
    })
    def test_tam_config_okunur(self):
        config = ErpConfig.from_env()
        assert config.erp_api_url == "https://erp.test.com"
        assert config.erp_api_key == "secret123"
        assert config.erp_timeout == 60
        assert config.erp_yapilandirildi_mi() is True

    @patch.dict("os.environ", {"PALET_VERI_KAYNAGI": "ERP"}, clear=True)
    def test_eksik_erp_config_yapilandirilmamis(self):
        config = ErpConfig.from_env()
        assert config.erp_yapilandirildi_mi() is False

    @patch.dict("os.environ", {"ERP_TIMEOUT": "abc"})
    def test_gecersiz_timeout_hata(self):
        with pytest.raises(ValueError):
            ErpConfig.from_env()
