from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, List


class SayimDurum:
    OLUSTURULDU = "oluşturuldu"
    DEVAM_EDIYOR = "devam_ediyor"
    BITTI = "bitti"
    ONAYLANDI = "onaylandı"

    _GECISLER = {
        OLUSTURULDU: {DEVAM_EDIYOR},
        DEVAM_EDIYOR: {BITTI},
        BITTI: {ONAYLANDI},
        ONAYLANDI: set(),
    }

    @classmethod
    def gecis_gecerli_mi(cls, mevcut: str, hedef: str) -> bool:
        return hedef in cls._GECISLER.get(mevcut, set())


@dataclass
class StokSayimKalemi:
    """Stok sayım kalemi domain entity."""

    id: Optional[int] = None
    sayim_id: Optional[int] = None
    urun_id: int = 0
    sayilan_miktar: int = 0
    notlar: str = ""
    user_id: Optional[int] = None
    sayim_tarihi: datetime = field(default_factory=datetime.utcnow)

    def fark_hesapla(self, beklenen_miktar: int) -> int:
        """Sayılan ile beklenen arasındaki farkı döner."""
        return self.sayilan_miktar - beklenen_miktar


@dataclass
class StokSayim:
    """Stok sayım oturumu domain entity."""

    id: Optional[int] = None
    sayim_no: str = ""
    aciklama: str = ""
    baslangic_tarihi: datetime = field(default_factory=datetime.utcnow)
    bitis_tarihi: Optional[datetime] = None
    referans_stok_json: Optional[Any] = None
    kontrol_eden_user_id: Optional[int] = None
    onaylayan_user_id: Optional[int] = None
    durum: str = SayimDurum.OLUSTURULDU
    aktif: bool = True
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)

    sayim_kalemleri: List[StokSayimKalemi] = field(default_factory=list)

    # ── İş Kuralları ──

    def baslat(self) -> None:
        """Sayımı başlatır."""
        if not SayimDurum.gecis_gecerli_mi(self.durum, SayimDurum.DEVAM_EDIYOR):
            raise ValueError(f"Sayım başlatılamaz, mevcut durum: {self.durum}")
        self.durum = SayimDurum.DEVAM_EDIYOR

    def bitir(self) -> None:
        """Sayımı bitirir."""
        if not SayimDurum.gecis_gecerli_mi(self.durum, SayimDurum.BITTI):
            raise ValueError(f"Sayım bitirilemez, mevcut durum: {self.durum}")
        self.durum = SayimDurum.BITTI
        self.bitis_tarihi = datetime.utcnow()

    def onayla(self, onaylayan_user_id: int) -> None:
        """Sayımı onaylar."""
        if not SayimDurum.gecis_gecerli_mi(self.durum, SayimDurum.ONAYLANDI):
            raise ValueError(f"Sayım onaylanamaz, mevcut durum: {self.durum}")
        self.durum = SayimDurum.ONAYLANDI
        self.onaylayan_user_id = onaylayan_user_id

    def kalem_ekle(self, kalem: StokSayimKalemi) -> None:
        if self.durum not in (SayimDurum.OLUSTURULDU, SayimDurum.DEVAM_EDIYOR):
            raise ValueError("Kalem eklemek için sayım açık olmalı.")
        self.sayim_kalemleri.append(kalem)
