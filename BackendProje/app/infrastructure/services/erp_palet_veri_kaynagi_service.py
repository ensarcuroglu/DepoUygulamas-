"""Gercek ERP palet veri kaynagi adapter'i.

ERP API'den palet bilgisi ceker ve strict mapping ile PaletBilgiDTO'ya donusturur.
Beklenmeyen veri tipleri loglanir ve ErpVeriDogrulamaHatasi firlatilir.

PALET_VERI_KAYNAGI=ERP ile aktif edilir.
ERP_API_URL, ERP_API_KEY, ERP_TIMEOUT env degiskenleri gereklidir.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Optional

from app.application.dto.palet_bilgi_dto import PaletBilgiDTO
from app.core.exceptions import (
    KayitBulunamadiError,
    GecersizIslemError,
    ErpBaglantiHatasi,
    ErpVeriDogrulamaHatasi,
)
from app.core.services.palet_veri_kaynagi_service import IPaletVeriKaynagiService
from app.infrastructure.config.erp_config import ErpConfig

logger = logging.getLogger(__name__)


class ErpPaletVeriKaynagiService(IPaletVeriKaynagiService):
    """ERP API'den palet bilgisi okuyan adapter.

    Strict mapping: ERP'den gelen her alan tip ve format kontrolunden gecer.
    Beklenmeyen veri → loglanir + ErpVeriDogrulamaHatasi firlatilir.
    Baglanti hatasi → ErpBaglantiHatasi firlatilir.
    """

    def __init__(self, config: ErpConfig) -> None:
        self._config = config
        if not config.erp_yapilandirildi_mi():
            logger.warning(
                "ERP adapter aktif ama ERP_API_URL/ERP_API_KEY yapilandirilmamis. "
                "Istekler ErpBaglantiHatasi donecek."
            )

    def palet_bilgisi_getir(self, palet_no: str) -> PaletBilgiDTO:
        raw = self._erp_api_cagir("GET", f"/paletler/{palet_no}")
        return self._strict_map(raw, palet_no)

    def palet_giris_onayla(self, palet_no: str) -> None:
        self._erp_api_cagir("POST", f"/paletler/{palet_no}/giris-onayla")

    # ── ERP API Cagri Iskeleti ──

    def _erp_api_cagir(self, method: str, endpoint: str, body: Any = None) -> dict:
        """ERP API'ye HTTP istegi gonderir.

        TODO: ERP entegrasyonu geldiginde bu metod implement edilecek.
        Su an icin config kontrolu yapar ve ErpBaglantiHatasi firlatir.
        """
        if not self._config.erp_yapilandirildi_mi():
            raise ErpBaglantiHatasi(
                "ERP API yapilandirilmamis. ERP_API_URL ve ERP_API_KEY degerlerini .env'de ayarlayin.",
                {"erp_api_url": self._config.erp_api_url or "(bos)"},
            )

        # ── Gercek ERP entegrasyonu buraya gelecek ──
        # Ornek implementasyon sablonu:
        #
        # import httpx
        # url = f"{self._config.erp_api_url}{endpoint}"
        # headers = {"Authorization": f"Bearer {self._config.erp_api_key}"}
        # try:
        #     response = httpx.request(
        #         method, url, json=body, headers=headers,
        #         timeout=self._config.erp_timeout,
        #     )
        #     response.raise_for_status()
        #     return response.json()
        # except httpx.ConnectError as e:
        #     logger.error("ERP baglanti hatasi: %s", e)
        #     raise ErpBaglantiHatasi(detaylar={"url": url, "hata": str(e)})
        # except httpx.TimeoutException:
        #     raise ErpBaglantiHatasi("ERP istegi zaman asimina ugradi.")

        raise ErpBaglantiHatasi(
            "ERP API entegrasyonu henuz implement edilmedi.",
            {"method": method, "endpoint": endpoint},
        )

    # ── Strict Mapping ──

    def _strict_map(self, raw: dict, palet_no: str) -> PaletBilgiDTO:
        """ERP ham verisini PaletBilgiDTO'ya strict mapping ile donusturur.

        Her alan icin tip kontrolu yapar. Hatali alan varsa loglar ve exception firlatir.
        """
        try:
            gelen_palet_no = self._str_zorunlu(raw, "palet_no")
            if gelen_palet_no != palet_no:
                logger.error(
                    "ERP strict mapping: palet_no uyusmazligi. istenen=%r, gelen=%r",
                    palet_no,
                    gelen_palet_no,
                )
                raise ErpVeriDogrulamaHatasi(
                    alan="palet_no",
                    beklenen=f"istenen palet_no ile ayni ({palet_no})",
                    gelen=repr(gelen_palet_no),
                )

            return PaletBilgiDTO(
                palet_no=gelen_palet_no,
                urun_id=self._int_zorunlu(raw, "urun_id"),
                urun_adi=self._str_zorunlu(raw, "urun_adi"),
                urun_barkod=self._str_opsiyonel(raw, "urun_barkod"),
                lot_no=self._str_opsiyonel(raw, "lot_no"),
                lot_id=self._int_opsiyonel(raw, "lot_id"),
                miktar=self._int_zorunlu(raw, "miktar"),
                raf_id=self._int_opsiyonel(raw, "raf_id"),
                raf_bilgi=self._str_opsiyonel(raw, "raf_bilgi"),
                depo_id=self._int_zorunlu(raw, "depo_id"),
                depo_adi=self._str_zorunlu(raw, "depo_adi"),
                durum=self._str_zorunlu(raw, "durum"),
                kaynak="erp",
                son_kullanma_tarihi=self._date_opsiyonel(raw, "son_kullanma_tarihi"),
                giris_yapildi_mi=self._bool_zorunlu(raw, "giris_yapildi_mi"),
            )
        except ErpVeriDogrulamaHatasi:
            raise
        except Exception as e:
            logger.error("ERP strict mapping beklenmeyen hata: %s — raw: %s", e, raw)
            raise ErpVeriDogrulamaHatasi(
                alan="(genel)",
                beklenen="gecerli ERP palet verisi",
                gelen=str(e),
            )

    # ── Tip Dogrulama Yardimcilari ──

    @staticmethod
    def _str_zorunlu(raw: dict, alan: str) -> str:
        deger = raw.get(alan)
        if not isinstance(deger, str) or not deger.strip():
            logger.error("ERP strict mapping: '%s' alani str olmali, gelen: %r", alan, deger)
            raise ErpVeriDogrulamaHatasi(alan=alan, beklenen="str (bos olmayan)", gelen=repr(deger))
        return deger.strip()

    @staticmethod
    def _str_opsiyonel(raw: dict, alan: str) -> Optional[str]:
        deger = raw.get(alan)
        if deger is None:
            return None
        if not isinstance(deger, str):
            logger.error("ERP strict mapping: '%s' alani str|None olmali, gelen: %r", alan, deger)
            raise ErpVeriDogrulamaHatasi(alan=alan, beklenen="str | None", gelen=repr(deger))
        return deger.strip() or None

    @staticmethod
    def _int_zorunlu(raw: dict, alan: str) -> int:
        deger = raw.get(alan)
        if not isinstance(deger, int) or isinstance(deger, bool):
            logger.error("ERP strict mapping: '%s' alani int olmali, gelen: %r", alan, deger)
            raise ErpVeriDogrulamaHatasi(alan=alan, beklenen="int", gelen=repr(deger))
        return deger

    @staticmethod
    def _int_opsiyonel(raw: dict, alan: str) -> Optional[int]:
        deger = raw.get(alan)
        if deger is None:
            return None
        if not isinstance(deger, int) or isinstance(deger, bool):
            logger.error("ERP strict mapping: '%s' alani int|None olmali, gelen: %r", alan, deger)
            raise ErpVeriDogrulamaHatasi(alan=alan, beklenen="int | None", gelen=repr(deger))
        return deger

    @staticmethod
    def _bool_zorunlu(raw: dict, alan: str) -> bool:
        deger = raw.get(alan)
        if not isinstance(deger, bool):
            logger.error("ERP strict mapping: '%s' alani bool olmali, gelen: %r", alan, deger)
            raise ErpVeriDogrulamaHatasi(alan=alan, beklenen="bool", gelen=repr(deger))
        return deger

    @staticmethod
    def _date_opsiyonel(raw: dict, alan: str) -> Optional[date]:
        deger = raw.get(alan)
        if deger is None:
            return None
        if isinstance(deger, date):
            return deger
        if isinstance(deger, str):
            try:
                return date.fromisoformat(deger)
            except ValueError:
                pass
        logger.error("ERP strict mapping: '%s' alani date|str(ISO)|None olmali, gelen: %r", alan, deger)
        raise ErpVeriDogrulamaHatasi(alan=alan, beklenen="date (ISO 8601) | None", gelen=repr(deger))
