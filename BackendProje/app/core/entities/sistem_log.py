from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any


class IslemTipi:
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


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
