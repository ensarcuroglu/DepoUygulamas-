from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.core.exceptions import GecersizDurumGecisiError


class ToplamaGoreviDurum:
    BEKLEMEDE = "Beklemede"
    ATANDI = "Atandi"
    DEVAM_EDIYOR = "DevamEdiyor"
    TAMAMLANDI = "Tamamlandi"
    IPTAL_EDILDI = "IptalEdildi"

    _GECISLER: dict[str, set[str]] = {}

    @classmethod
    def gecis_gecerli_mi(cls, mevcut: str, hedef: str) -> bool:
        return hedef in cls._GECISLER.get(mevcut, set())


ToplamaGoreviDurum._GECISLER = {
    ToplamaGoreviDurum.BEKLEMEDE: {
        ToplamaGoreviDurum.ATANDI,
        ToplamaGoreviDurum.IPTAL_EDILDI,
    },
    ToplamaGoreviDurum.ATANDI: {
        ToplamaGoreviDurum.DEVAM_EDIYOR,
        ToplamaGoreviDurum.BEKLEMEDE,   # operatör iade eder
        ToplamaGoreviDurum.IPTAL_EDILDI,
    },
    ToplamaGoreviDurum.DEVAM_EDIYOR: {
        ToplamaGoreviDurum.TAMAMLANDI,
        ToplamaGoreviDurum.IPTAL_EDILDI,
    },
    ToplamaGoreviDurum.TAMAMLANDI: set(),
    ToplamaGoreviDurum.IPTAL_EDILDI: set(),
}


@dataclass
class ToplamaGorevi:
    """Toplama (Pick Task) görevi domain entity.

    Yaşam döngüsü: Beklemede → Atandi → DevamEdiyor → Tamamlandi
    İstisnai:      herhangi bir aktif durumdan → IptalEdildi
    """

    id: Optional[int] = None
    sevkiyat_id: int = 0
    palet_id: int = 0
    lot_id: int = 0
    urun_id: int = 0
    depo_id: Optional[int] = None
    atanan_kullanici_id: Optional[int] = None
    durum: str = ToplamaGoreviDurum.BEKLEMEDE
    fefo_override: bool = False
    override_neden: Optional[str] = None
    override_kullanici_id: Optional[int] = None
    sira_no: int = 0
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)
    atanma_tarihi: Optional[datetime] = None
    baslama_tarihi: Optional[datetime] = None
    tamamlanma_tarihi: Optional[datetime] = None
    iptal_nedeni: Optional[str] = None

    # Görüntüleme alanları (repository JOIN ile doldurur)
    palet_no: Optional[str] = None
    urun_adi: Optional[str] = None
    lot_no: Optional[str] = None
    koli_adedi: Optional[int] = None
    atanan_kullanici_adi: Optional[str] = None

    # ── İş Kuralları ──

    def _durum_gecisi(self, hedef: str) -> None:
        if not ToplamaGoreviDurum.gecis_gecerli_mi(self.durum, hedef):
            raise GecersizDurumGecisiError(
                f"Geçersiz durum geçişi: {self.durum} → {hedef}",
                mevcut=self.durum,
                hedef=hedef,
            )
        self.durum = hedef

    def ata(self, kullanici_id: int) -> None:
        """Operatör görevi havuzdan çeker (pull-based)."""
        self._durum_gecisi(ToplamaGoreviDurum.ATANDI)
        self.atanan_kullanici_id = kullanici_id
        self.atanma_tarihi = datetime.utcnow()

    def bırak(self) -> None:
        """Operatör görevi iade eder; Beklemede'ye döner."""
        self._durum_gecisi(ToplamaGoreviDurum.BEKLEMEDE)
        self.atanan_kullanici_id = None
        self.atanma_tarihi = None

    def baslat(self) -> None:
        """Operatör paleti fiziksel olarak almaya başladı."""
        self._durum_gecisi(ToplamaGoreviDurum.DEVAM_EDIYOR)
        self.baslama_tarihi = datetime.utcnow()

    def tamamla(self) -> None:
        """Toplama tamamlandı; tam koli zorunluluğu use case'de kontrol edilir."""
        self._durum_gecisi(ToplamaGoreviDurum.TAMAMLANDI)
        self.tamamlanma_tarihi = datetime.utcnow()

    def iptal_et(self, neden: Optional[str] = None) -> None:
        self._durum_gecisi(ToplamaGoreviDurum.IPTAL_EDILDI)
        self.iptal_nedeni = neden
