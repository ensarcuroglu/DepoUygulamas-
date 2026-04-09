from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any


class IslemTipi:
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    ERROR = "ERROR"


class OlayTipi:
    """Terminal ve operasyon olayları için standart tip sabitleri."""
    PALET_OKUTMA_HATASI = "PALET_OKUTMA_HATASI"
    RAF_OKUTMA_HATASI = "RAF_OKUTMA_HATASI"
    KARANTINA_BASLAT = "KARANTINA_BASLAT"
    OVERRIDE_KULLANIM = "OVERRIDE_KULLANIM"
    STAGING_GIRIS = "STAGING_GIRIS"
    STAGING_CIKIS = "STAGING_CIKIS"
    IRSALIYE_ONAYLA = "IRSALIYE_ONAYLA"
    GOREV_TAMAMLA = "GOREV_TAMAMLA"
    STAGING_UYARI = "STAGING_UYARI"


@dataclass
class SistemLog:
    """Sistem log domain entity."""

    id: Optional[int] = None
    kullanici_id: Optional[int] = None
    islem_tipi: str = IslemTipi.CREATE
    modul: str = ""
    detay: Optional[str] = None
    eski_veri: Optional[Any] = None
    yeni_veri: Optional[Any] = None
    tarih: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def olustur(
        kullanici_id: int,
        islem_tipi: str,
        modul: str,
        detay: str,
        eski_veri: Any = None,
        yeni_veri: Any = None,
    ) -> SistemLog:
        """Kolaylaştırılmış factory metodu."""
        return SistemLog(
            kullanici_id=kullanici_id,
            islem_tipi=islem_tipi,
            modul=modul,
            detay=detay,
            eski_veri=eski_veri,
            yeni_veri=yeni_veri,
        )
