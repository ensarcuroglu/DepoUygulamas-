from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


class HareketTipi:
    GIRIS = "giris"
    CIKIS = "cikis"


@dataclass
class StokHareketi:
    """Stok hareketi domain entity."""

    id: Optional[int] = None
    urun_id: int = 0
    lot_id: Optional[int] = None
    palet_id: Optional[int] = None
    raf_id: Optional[int] = None
    hareket_tipi: str = HareketTipi.GIRIS
    miktar: int = 0
    siparis_no: Optional[str] = None
    tir_plaka: Optional[str] = None
    depo_kapi: Optional[str] = None
    barkodlar: Optional[List[str]] = None
    aciklama: str = ""
    kullanici_id: Optional[int] = None
    tarih: datetime = field(default_factory=datetime.utcnow)

    # ── İş Kuralları ──

    def giris_mi(self) -> bool:
        return self.hareket_tipi == HareketTipi.GIRIS

    def cikis_mi(self) -> bool:
        return self.hareket_tipi == HareketTipi.CIKIS

    def dogrula(self) -> None:
        """Hareketin temel iş kurallarını doğrular."""
        if self.miktar <= 0:
            raise ValueError("Stok hareket miktarı pozitif olmalı.")
        if self.hareket_tipi not in (HareketTipi.GIRIS, HareketTipi.CIKIS):
            raise ValueError(f"Geçersiz hareket tipi: {self.hareket_tipi}")
        if self.urun_id <= 0:
            raise ValueError("Geçerli bir ürün ID gerekli.")
