"""Palet bilgi kaynagi soyutlamasi (ERP-Ready).

Gecis donemi: IrsaliyePaletVeriKaynagiService -> MalKabulKalemi'nden okur
Hedef:        ErpPaletVeriKaynagiService -> ERP API'den okur
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.dto.palet_bilgi_dto import PaletBilgiDTO


class IPaletVeriKaynagiService(ABC):
    """Palet bilgi kaynagi arayuzu.

    Tum palet veri kaynaklari (irsaliye, ERP) bu arayuzu uygular.
    Domain service bu arayuz uzerinden calisir — kaynak degistiginde
    sadece adapter swap yapilir.
    """

    @abstractmethod
    def palet_bilgisi_getir(self, palet_no: str) -> PaletBilgiDTO:
        """Palet numarasina gore tum bilgileri getirir.

        Raises:
            KayitBulunamadiError: Palet numarasi kaynakta bulunamazsa.
        """
        ...

    @abstractmethod
    def palet_giris_onayla(self, palet_no: str) -> None:
        """Palet girisinin yapildigini kaynaga bildirir.

        Irsaliye adapter'inda MalKabulKalemi.durum -> GirisYapildi gunceller.
        ERP adapter'inda ERP API'ye bildirim gonderir.

        Raises:
            KayitBulunamadiError: Palet numarasi kaynakta bulunamazsa.
            GecersizIslemError: Giris zaten yapilmissa.
        """
        ...
