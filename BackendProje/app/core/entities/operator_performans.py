"""Operatör Performans (LMS) domain entity'leri.

İki ana yapı:
  GorevPerformansEvent     — immutable görev olay log'u (transactional outbox)
  OperatorVardiyaMetrikleri — vardiya bazlı aggregate KPI özeti
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


class PerformansEventTipi:
    GOREV_BASLATILDI = "GOREV_BASLATILDI"
    GOREV_TAMAMLANDI = "GOREV_TAMAMLANDI"
    GOREV_IPTAL = "GOREV_IPTAL"

    _TIPLER = {GOREV_BASLATILDI, GOREV_TAMAMLANDI, GOREV_IPTAL}

    @classmethod
    def gecerli_mi(cls, tip: str) -> bool:
        return tip in cls._TIPLER


class PerformansGorevTipi:
    YERLESTIRME = "yerlestirme"
    TOPLAMA = "toplama"

    _TIPLER = {YERLESTIRME, TOPLAMA}

    @classmethod
    def gecerli_mi(cls, tip: str) -> bool:
        return tip in cls._TIPLER


@dataclass
class GorevPerformansEvent:
    """Görev yaşam döngüsü olayı — immutable, append-only.

    `sure_saniye` yalnızca GOREV_TAMAMLANDI olayında doludur ve
    `tamamlanma_tarihi - baslama_tarihi` farkını taşır. İptal olaylarında
    `iptal_nedeni` doludur.

    RabbitMQ alanları outbox relay (Faz 3) tarafından doldurulur; consumer
    idempotency için `event_uuid` kullanır.
    """

    id: Optional[int] = None
    event_uuid: Optional[str] = None
    event_tipi: str = PerformansEventTipi.GOREV_TAMAMLANDI
    gorev_tipi: str = PerformansGorevTipi.YERLESTIRME
    gorev_id: int = 0
    kullanici_id: int = 0
    depo_id: Optional[int] = None
    sure_saniye: Optional[int] = None
    iptal_nedeni: Optional[str] = None
    payload: Optional[dict] = None
    aggregate_edildi: bool = False
    rabbitmq_yayinlandi: bool = False
    rabbitmq_yayin_tarihi: Optional[datetime] = None
    rabbitmq_deneme_sayisi: int = 0
    rabbitmq_son_hata: Optional[str] = None
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OperatorVardiyaMetrikleri:
    """Bir operatörün bir takvim günü (vardiya) için KPI özeti.

    UPH (Units Per Hour) saklanmaz; okuma sırasında hesaplanır:
        UPH = (tamamlanan_yerlestirme + tamamlanan_toplama)
              / (toplam_aktif_saniye / 3600)
    """

    id: Optional[int] = None
    kullanici_id: int = 0
    depo_id: Optional[int] = None
    vardiya_tarihi: date = field(default_factory=date.today)
    tamamlanan_yerlestirme: int = 0
    tamamlanan_toplama: int = 0
    iptal_sayisi: int = 0
    toplam_aktif_saniye: int = 0
    ortalama_gorev_suresi_sn: float = 0.0
    son_guncelleme: datetime = field(default_factory=datetime.utcnow)

    # Görüntüleme alanları (repository JOIN ile doldurur)
    operator_adi: Optional[str] = None
    depo_adi: Optional[str] = None

    @property
    def toplam_gorev(self) -> int:
        return self.tamamlanan_yerlestirme + self.tamamlanan_toplama

    @property
    def uph(self) -> float:
        """Saatlik tamamlanan görev sayısı. Aktif çalışma süresi 0 ise 0 döner."""
        if self.toplam_aktif_saniye <= 0:
            return 0.0
        return round(self.toplam_gorev / (self.toplam_aktif_saniye / 3600.0), 2)

    @property
    def hata_orani(self) -> float:
        """İptal / (Tamamlanan + İptal) — 0..1 aralığında. Veri yoksa 0."""
        payda = self.toplam_gorev + self.iptal_sayisi
        if payda <= 0:
            return 0.0
        return round(self.iptal_sayisi / payda, 4)
