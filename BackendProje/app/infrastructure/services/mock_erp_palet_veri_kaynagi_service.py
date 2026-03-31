"""Mock ERP palet veri kaynagi adapter'i.

Demo ve gelistirme ortami icin deterministik sahte palet verisi doner.
Gercek ERP yokken sistemi uctan uca test etmek icin kullanilir.
PALET_VERI_KAYNAGI=MOCK ile aktif edilir.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Set

from app.application.dto.palet_bilgi_dto import PaletBilgiDTO
from app.core.exceptions import KayitBulunamadiError, GecersizIslemError
from app.core.services.palet_veri_kaynagi_service import IPaletVeriKaynagiService


# Deterministik demo palet katalogu
_MOCK_PALETLER: dict[str, dict] = {
    "ERP-2026-00001": {
        "urun_id": 1,
        "urun_adi": "Demo Makarna 500g",
        "urun_barkod": "8690000000001",
        "lot_no": "LOT-ERP-0001",
        "miktar": 120,
        "depo_id": 1,
        "depo_adi": "Ana Depo",
        "raf_id": 1,
        "raf_bilgi": "Ana Depo / R-01-A",
        "son_kullanma_tarihi": date.today() + timedelta(days=180),
    },
    "ERP-2026-00002": {
        "urun_id": 2,
        "urun_adi": "Demo Pirinc 1kg",
        "urun_barkod": "8690000000002",
        "lot_no": "LOT-ERP-0002",
        "miktar": 80,
        "depo_id": 1,
        "depo_adi": "Ana Depo",
        "raf_id": 2,
        "raf_bilgi": "Ana Depo / R-01-B",
        "son_kullanma_tarihi": date.today() + timedelta(days=365),
    },
    "ERP-2026-00003": {
        "urun_id": 3,
        "urun_adi": "Demo Zeytinyagi 2L",
        "urun_barkod": "8690000000003",
        "lot_no": "LOT-ERP-0003",
        "miktar": 50,
        "depo_id": 2,
        "depo_adi": "B Deposu",
        "raf_id": None,
        "raf_bilgi": None,
        "son_kullanma_tarihi": date.today() + timedelta(days=540),
    },
}


class MockErpPaletVeriKaynagiService(IPaletVeriKaynagiService):
    """Demo/dev icin sahte ERP palet verisi saglayan adapter.

    In-memory state ile palet_giris_onayla() durumunu takip eder.
    Her uygulama yeniden basladiginda state sifirlanir.
    """

    def __init__(self) -> None:
        self._giris_yapilan: Set[str] = set()

    def palet_bilgisi_getir(self, palet_no: str) -> PaletBilgiDTO:
        veri = _MOCK_PALETLER.get(palet_no)
        if not veri:
            raise KayitBulunamadiError("Palet (Mock ERP)", palet_no)

        return PaletBilgiDTO(
            palet_no=palet_no,
            urun_id=veri["urun_id"],
            urun_adi=veri["urun_adi"],
            urun_barkod=veri["urun_barkod"],
            lot_no=veri["lot_no"],
            lot_id=None,
            miktar=veri["miktar"],
            raf_id=veri["raf_id"],
            raf_bilgi=veri["raf_bilgi"],
            depo_id=veri["depo_id"],
            depo_adi=veri["depo_adi"],
            durum="aktif",
            kaynak="erp",
            son_kullanma_tarihi=veri["son_kullanma_tarihi"],
            giris_yapildi_mi=(palet_no in self._giris_yapilan),
        )

    def palet_giris_onayla(self, palet_no: str) -> None:
        if palet_no not in _MOCK_PALETLER:
            raise KayitBulunamadiError("Palet (Mock ERP)", palet_no)

        if palet_no in self._giris_yapilan:
            raise GecersizIslemError("Bu palet icin giris zaten yapilmis (Mock ERP).")

        self._giris_yapilan.add(palet_no)
