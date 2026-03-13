from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class DestekDurum:
    ACIK = "Açık"
    ISLEMDE = "İşlemde"
    COZULDU = "Çözüldü"


class DestekOncelik:
    DUSUK = "Düşük"
    NORMAL = "Normal"
    YUKSEK = "Yüksek"


@dataclass
class DestekTalebi:
    """Destek talebi domain entity."""

    id: Optional[int] = None
    kullanici_id: int = 0
    konu: str = ""
    kategori: str = ""
    oncelik: str = DestekOncelik.NORMAL
    durum: str = DestekDurum.ACIK
    aciklama: str = ""
    admin_cevabi: Optional[str] = None
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)
    guncelleme_tarihi: datetime = field(default_factory=datetime.utcnow)

    # ── İş Kuralları ──

    def cevapla(self, cevap: str) -> None:
        """Admin cevabı ekler ve durumu günceller."""
        self.admin_cevabi = cevap
        self.durum = DestekDurum.ISLEMDE
        self.guncelleme_tarihi = datetime.utcnow()

    def coz(self, cevap: Optional[str] = None) -> None:
        """Talebi çözüldü olarak işaretler."""
        if cevap:
            self.admin_cevabi = cevap
        self.durum = DestekDurum.COZULDU
        self.guncelleme_tarihi = datetime.utcnow()

    def cozuldu_mu(self) -> bool:
        return self.durum == DestekDurum.COZULDU
