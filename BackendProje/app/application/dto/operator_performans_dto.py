"""Operatör Performans (LMS) — okuma DTO'ları."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.core.entities.operator_performans import OperatorVardiyaMetrikleri


class OperatorMetrikItemDTO(BaseModel):
    """Tek bir vardiya satırı — özet listesi ve kullanıcı detayında kullanılır."""

    id: Optional[int] = None
    kullanici_id: int
    operator_adi: Optional[str] = None
    depo_id: Optional[int] = None
    depo_adi: Optional[str] = None
    vardiya_tarihi: date
    tamamlanan_yerlestirme: int = 0
    tamamlanan_toplama: int = 0
    toplam_gorev: int = 0
    iptal_sayisi: int = 0
    toplam_aktif_saniye: int = 0
    ortalama_gorev_suresi_sn: float = 0.0
    uph: float = 0.0
    hata_orani: float = 0.0
    son_guncelleme: Optional[datetime] = None

    @classmethod
    def from_entity(cls, m: OperatorVardiyaMetrikleri) -> "OperatorMetrikItemDTO":
        return cls(
            id=m.id,
            kullanici_id=m.kullanici_id,
            operator_adi=m.operator_adi,
            depo_id=m.depo_id,
            depo_adi=m.depo_adi,
            vardiya_tarihi=m.vardiya_tarihi,
            tamamlanan_yerlestirme=m.tamamlanan_yerlestirme,
            tamamlanan_toplama=m.tamamlanan_toplama,
            toplam_gorev=m.toplam_gorev,
            iptal_sayisi=m.iptal_sayisi,
            toplam_aktif_saniye=m.toplam_aktif_saniye,
            ortalama_gorev_suresi_sn=m.ortalama_gorev_suresi_sn,
            uph=m.uph,
            hata_orani=m.hata_orani,
            son_guncelleme=m.son_guncelleme,
        )


class OperatorOzetListResponseDTO(BaseModel):
    """Aralık özeti (admin/lojistik liste cevabı)."""

    items: List[OperatorMetrikItemDTO] = Field(default_factory=list)
    toplam: int = 0


class LeaderboardItemDTO(BaseModel):
    """Tek günlük UPH sıralaması satırı (gamification)."""

    sira: int
    kullanici_id: int
    operator_adi: Optional[str] = None
    depo_id: Optional[int] = None
    depo_adi: Optional[str] = None
    toplam_gorev: int
    toplam_aktif_saniye: int
    uph: float
    hata_orani: float


class LeaderboardResponseDTO(BaseModel):
    vardiya_tarihi: date
    items: List[LeaderboardItemDTO] = Field(default_factory=list)


class KendiPerformansOzetDTO(BaseModel):
    """`/me` çağrısının cevabı — son N gün + bugün."""

    bugun: Optional[OperatorMetrikItemDTO] = None
    son_gunler: List[OperatorMetrikItemDTO] = Field(default_factory=list)
