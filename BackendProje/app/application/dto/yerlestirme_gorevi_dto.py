"""
Yerleştirme Görevi veri transfer nesneleri (DTO).
"""

from __future__ import annotations
from datetime import datetime
from typing import Dict, Optional, List
from pydantic import BaseModel, Field, field_validator

from app.core.entities.yerlestirme_gorevi import GorevTipi, YerlestirmeGorevi


# ─────────────────────────────────────────
# İSTEK (REQUEST) DTO'LARI
# ─────────────────────────────────────────

class YerlestirmeGoreviOlusturRequestDTO(BaseModel):
    palet_id: int = Field(..., gt=0)
    mal_kabul_irsaliye_id: Optional[int] = Field(None, gt=0)
    tip: str = Field(default=GorevTipi.YERLESTIRME)
    kaynak_raf_id: Optional[int] = Field(None, gt=0)
    onerilen_raf_id: int = Field(..., gt=0)
    oncelik: int = Field(default=5, ge=1, le=5, description="1=Acil, 5=Normal")

    @field_validator("tip")
    @classmethod
    def gecerli_tip(cls, v: str) -> str:
        if not GorevTipi.gecerli_mi(v):
            raise ValueError(f"Geçersiz görev tipi: '{v}'")
        return v


class YerlestirmeGoreviTamamlaRequestDTO(BaseModel):
    gerceklesen_raf_id: int = Field(..., gt=0, description="Operatörün barkod okuttuğu raf")


class YerlestirmeGoreviOverrideRequestDTO(BaseModel):
    gerceklesen_raf_id: int = Field(..., gt=0)
    neden: str = Field(..., min_length=5, max_length=500, description="Override gerekçesi")


class YerlestirmeGoreviIptalRequestDTO(BaseModel):
    neden: str = Field(..., min_length=1, max_length=500)


class YerlestirmeOnaylaRequestDTO(BaseModel):
    """Scan-to-verify: operatör raf barkodunu okuttuğunda gönderilir."""
    okutulan_raf_kodu: str = Field(..., min_length=1, max_length=50, description="Raf barkodu")


class KarantinadanCikarRequestDTO(BaseModel):
    palet_id: int = Field(..., gt=0)


class KarantinayaAlRequestDTO(BaseModel):
    palet_id: int = Field(..., gt=0)
    neden: str = Field(..., min_length=3, max_length=500, description="Karantinaya alma gerekçesi")


# ─────────────────────────────────────────
# YANIT (RESPONSE) DTO'LARI
# ─────────────────────────────────────────

class AlternatifRafDTO(BaseModel):
    raf_id: int
    raf_kod: str
    bos_slot: int
    skor: float
    gerekce: Optional[str] = None
    bilesenler: Optional[Dict[str, float]] = None


class RafOneriDetayDTO(BaseModel):
    """Akıllı yerleştirme önerisinin tek raf detayı (önerilen veya alternatif)."""
    raf_id: int
    raf_kod: str
    zon_id: Optional[int] = None
    zon_kod: Optional[str] = None
    zon_tipi: Optional[str] = None
    bos_slot: int
    skor: float
    gerekce: str = ""
    bilesenler: Dict[str, float] = Field(default_factory=dict)


class RafOneriResponseDTO(BaseModel):
    """Akıllı yerleştirme öneri sorgusu yanıtı."""
    palet_id: int
    palet_no: Optional[str] = None
    urun_id: Optional[int] = None
    urun_adi: Optional[str] = None
    depo_id: int
    onerilen: Optional[RafOneriDetayDTO] = None
    alternatifler: List[RafOneriDetayDTO] = Field(default_factory=list)
    uyari: Optional[str] = None


class YerlestirmeOnaylaSonucDTO(BaseModel):
    """Scan-to-verify sonuç DTO'su. Hem başarı hem hata için kullanılır."""
    basarili: bool
    durum: str                                  # "TAMAMLANDI" | "DOGRULAMA_HATASI"
    palet_no: Optional[str] = None
    raf_kod: Optional[str] = None
    zon: Optional[str] = None
    onerilen_raf_kod: Optional[str] = None      # Farklıysa gösterilir
    mesaj: str = ""
    hata_tipi: Optional[str] = None             # "KAPASITE_YETERSIZ" | "ZON_UYUMSUZ"
    alternatifler: List[AlternatifRafDTO] = []
    override_gerekli: bool = False
    gorev: Optional["YerlestirmeGoreviResponseDTO"] = None


class BilinmeyenKonumGorevleriOlusturSonucDTO(BaseModel):
    olusturulan_gorev_sayisi: int
    palet_sayisi: int
    uyari_mesajlari: List[str] = []

class YerlestirmeGoreviResponseDTO(BaseModel):
    id: int
    palet_id: int
    mal_kabul_irsaliye_id: Optional[int]
    depo_id: Optional[int]
    tip: str
    kaynak_raf_id: Optional[int]
    onerilen_raf_id: int
    gerceklesen_raf_id: Optional[int]
    durum: str
    oncelik: int
    atanan_kullanici_id: Optional[int]
    override_kullanici_id: Optional[int]
    override_neden: Optional[str]
    olusturma_tarihi: datetime
    baslama_tarihi: Optional[datetime]
    tamamlanma_tarihi: Optional[datetime]
    iptal_nedeni: Optional[str]
    onerilen_raf_farkli: bool
    # Görüntüleme alanları (JOIN ile zenginleştirilir)
    palet_barkodu: Optional[str] = None
    urun_adi: Optional[str] = None
    lot_no: Optional[str] = None
    miktar: Optional[int] = None
    onerilen_raf_kodu: Optional[str] = None
    zone_adi: Optional[str] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity: YerlestirmeGorevi) -> "YerlestirmeGoreviResponseDTO":

        if entity.id is None:
            raise ValueError("YerlestirmeGoreviResponseDTO   oluşturulamadı: entity.id boş olamaz.")

        return cls(
            id=entity.id,
            palet_id=entity.palet_id,
            mal_kabul_irsaliye_id=entity.mal_kabul_irsaliye_id,
            depo_id=entity.depo_id,
            tip=entity.tip,
            kaynak_raf_id=entity.kaynak_raf_id,
            onerilen_raf_id=entity.onerilen_raf_id,
            gerceklesen_raf_id=entity.gerceklesen_raf_id,
            durum=entity.durum,
            oncelik=entity.oncelik,
            atanan_kullanici_id=entity.atanan_kullanici_id,
            override_kullanici_id=entity.override_kullanici_id,
            override_neden=entity.override_neden,
            olusturma_tarihi=entity.olusturma_tarihi,
            baslama_tarihi=entity.baslama_tarihi,
            tamamlanma_tarihi=entity.tamamlanma_tarihi,
            iptal_nedeni=entity.iptal_nedeni,
            onerilen_raf_farkli=entity.onerilen_raf_farkli_mi(),
            palet_barkodu=entity.palet_barkodu,
            urun_adi=entity.urun_adi,
            lot_no=entity.lot_no,
            miktar=entity.miktar,
            onerilen_raf_kodu=entity.onerilen_raf_kodu,
            zone_adi=entity.zone_adi,
        )
