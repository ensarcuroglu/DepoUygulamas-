from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar, Optional, Set


class ZonTipi:
    MAL_KABUL = "MalKabul"
    GENEL = "Genel"
    SOGUK = "Soguk"
    KARANTINA = "Karantina"
    SEVKIYAT = "Sevkiyat"
    TEHLIKELI = "Tehlikeli"

    _DEPOLAMA_TIPI_UYUMLULUK: ClassVar[dict[str, Set[str]]] = {
        GENEL: {"Kuru"},
        SOGUK: {"Kuru", "Soguk"},
        TEHLIKELI: {"Tehlikeli"},
        MAL_KABUL: {"Kuru", "Soguk", "Tehlikeli"},
        SEVKIYAT: {"Kuru", "Soguk", "Tehlikeli"},
        KARANTINA: {"Kuru", "Soguk", "Tehlikeli"},
    }

    @classmethod
    def tipler(cls) -> Set[str]:
        return {
            cls.MAL_KABUL,
            cls.GENEL,
            cls.SOGUK,
            cls.KARANTINA,
            cls.SEVKIYAT,
            cls.TEHLIKELI,
        }

    @classmethod
    def gecerli_mi(cls, tip: str) -> bool:
        return tip in cls.tipler()

    @classmethod
    def izin_verilen_depolama_tipleri(cls, zon_tipi: str) -> Set[str]:
        return cls._DEPOLAMA_TIPI_UYUMLULUK.get(zon_tipi, set())

    @classmethod
    def kalici_depolama_zonlari(cls) -> Set[str]:
        """Algoritmanın kalıcı yerleştirme önerebileceği zon tipleri.

        MalKabul ve Sevkiyat staging alanlarıdır; Karantina izolasyon alanıdır.
        Bunların hiçbiri kalıcı depolama hedefi değildir.
        """
        return {cls.GENEL, cls.SOGUK, cls.TEHLIKELI}

    @classmethod
    def kalici_depolama_mi(cls, zon_tipi: str) -> bool:
        return zon_tipi in cls.kalici_depolama_zonlari()


@dataclass
class Zon:
    """Depolama zonu domain entity."""

    id: Optional[int] = None
    depo_id: int = 0
    isim: str = ""
    tip: str = ZonTipi.GENEL
    kod: str = ""
    aciklama: str = ""
    sira: int = 0
    aktif: bool = True
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)

    def deaktif_et(self) -> None:
        self.aktif = False

    def aktif_et(self) -> None:
        self.aktif = True

    def depolama_tipi_uygun_mu(self, depolama_tipi: str) -> bool:
        """Faz 0.3 ile gelecek depolama_tipi alani icin uyumluluk kontrolu."""
        return depolama_tipi in ZonTipi.izin_verilen_depolama_tipleri(self.tip)

    def karantinadan_cikis_onay_gerekli_mi(self) -> bool:
        return self.tip == ZonTipi.KARANTINA

