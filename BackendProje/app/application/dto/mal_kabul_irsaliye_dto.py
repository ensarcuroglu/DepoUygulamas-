"""
Mal Kabul İrsaliyesi veri transfer nesneleri (DTO).
"""

from __future__ import annotations
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator

from app.core.entities.mal_kabul_irsaliye import MalKabulDurum, IstisnaKalemTip

# Kullanıcı yalnızca Onaylandi geçişini tetikleyebilir.
# Kapandi sisteme özel (auto-close), API üzerinden ayarlanamaz.
_IZINLI_DURUMLAR = {MalKabulDurum.ONAYLANDI}


# ─────────────────────────────────────────
# KALEM DTO'LARI
# ─────────────────────────────────────────

class MalKabulKalemiOlusturDTO(BaseModel):
    """Yeni kalem oluşturma isteği (irsaliye oluşturma/güncelleme içinde)."""

    palet_no: str = Field(..., min_length=1, max_length=30)
    urun_id: int = Field(..., gt=0)
    lot_no: Optional[str] = Field(None, max_length=50)
    miktar: int = Field(..., gt=0)
    raf_id: Optional[int] = Field(None, gt=0)
    uretim_tarihi: Optional[date] = None
    son_kullanma_tarihi: Optional[date] = None


class MalKabulKalemiResponseDTO(BaseModel):
    """Kalem response."""

    id: int
    mal_kabul_irsaliyesi_id: int
    palet_no: str
    urun_id: int
    lot_no: Optional[str] = None
    miktar: int
    raf_id: Optional[int] = None
    durum: str
    uretim_tarihi: Optional[date] = None
    son_kullanma_tarihi: Optional[date] = None
    olusturma_tarihi: datetime
    istisna_tip: Optional[str] = None
    istisna_aciklama: Optional[str] = None
    gerceklesen_miktar: Optional[int] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity) -> "MalKabulKalemiResponseDTO":
        return cls(
            id=entity.id,
            mal_kabul_irsaliyesi_id=entity.mal_kabul_irsaliyesi_id,
            palet_no=entity.palet_no,
            urun_id=entity.urun_id,
            lot_no=entity.lot_no,
            miktar=entity.miktar,
            raf_id=entity.raf_id,
            durum=entity.durum,
            uretim_tarihi=entity.uretim_tarihi,
            son_kullanma_tarihi=entity.son_kullanma_tarihi,
            olusturma_tarihi=entity.olusturma_tarihi,
            istisna_tip=entity.istisna_tip,
            istisna_aciklama=entity.istisna_aciklama,
            gerceklesen_miktar=entity.gerceklesen_miktar,
        )


class MalKabulKalemiIstisnaRequestDTO(BaseModel):
    """Kalem istisna/fark bildirim isteği."""

    istisna_tip: str = Field(..., description=f"Geçerli tipler: {list(IstisnaKalemTip._TIPLER)}")
    istisna_aciklama: Optional[str] = Field(None, max_length=500)
    gerceklesen_miktar: Optional[int] = Field(None, ge=0)

    @field_validator("istisna_tip")
    @classmethod
    def gecerli_istisna_tip(cls, v: str) -> str:
        if not IstisnaKalemTip.gecerli_mi(v):
            raise ValueError(f"Geçersiz istisna tipi: '{v}'")
        return v


# ─────────────────────────────────────────
# İRSALİYE REQUEST DTO'LARI
# ─────────────────────────────────────────

class MalKabulIrsaliyeOlusturRequestDTO(BaseModel):
    """Yeni mal kabul irsaliyesi oluşturma isteği."""

    tedarikci_id: int = Field(..., gt=0)
    depo_id: int = Field(..., gt=0)
    tarih: date
    tir_plaka: Optional[str] = Field(None, max_length=20)
    sofor_adi: Optional[str] = Field(None, max_length=100)
    kalemler: List[MalKabulKalemiOlusturDTO] = Field(default_factory=list)


class MalKabulIrsaliyeGuncelleRequestDTO(BaseModel):
    """Güncelleme isteği — tüm alanlar opsiyonel."""

    tedarikci_id: Optional[int] = Field(None, gt=0)
    depo_id: Optional[int] = Field(None, gt=0)
    tarih: Optional[date] = None
    tir_plaka: Optional[str] = Field(None, max_length=20)
    sofor_adi: Optional[str] = Field(None, max_length=100)
    durum: Optional[str] = Field(None, max_length=20)
    kalemler: Optional[List[MalKabulKalemiOlusturDTO]] = None

    @field_validator("durum")
    @classmethod
    def gecerli_durum(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _IZINLI_DURUMLAR:
            raise ValueError(f"Geçersiz durum: '{v}'. İzin verilen: {_IZINLI_DURUMLAR}")
        return v


# ─────────────────────────────────────────
# İRSALİYE RESPONSE DTO'LARI
# ─────────────────────────────────────────

class MalKabulIrsaliyeResponseDTO(BaseModel):
    """Mal kabul irsaliyesi response."""

    id: int
    irsaliye_no: str
    tedarikci_id: int
    depo_id: int
    tir_plaka: Optional[str] = None
    sofor_adi: Optional[str] = None
    durum: str
    tarih: Optional[date] = None
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime
    kalemler: List[MalKabulKalemiResponseDTO] = []
    # Yalnızca onay endpointinde dolar; listelemede None gelir.
    olusturulan_gorev_sayisi: Optional[int] = None
    istisna_sayisi: int = 0
    kapanma_ozeti: Optional[Dict[str, Any]] = None

    # Operasyon ilerleme — kalem durumlarından hesaplanır
    toplam_kalem: int = 0
    yerlestirilen: int = 0
    bekleyen: int = 0

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(
        cls,
        entity,
        olusturulan_gorev_sayisi: Optional[int] = None,
    ) -> "MalKabulIrsaliyeResponseDTO":
        kalemler_dto = [MalKabulKalemiResponseDTO.from_entity(k) for k in entity.kalemler]
        toplam, yerlestirilen, bekleyen = cls._ilerleme_hesapla(entity)

        return cls(
            id=entity.id,
            irsaliye_no=entity.irsaliye_no,
            tedarikci_id=entity.tedarikci_id,
            depo_id=entity.depo_id,
            tir_plaka=entity.tir_plaka,
            sofor_adi=entity.sofor_adi,
            durum=entity.durum,
            tarih=entity.tarih,
            olusturma_tarihi=entity.olusturma_tarihi,
            guncelleme_tarihi=entity.guncelleme_tarihi,
            kalemler=kalemler_dto,
            olusturulan_gorev_sayisi=olusturulan_gorev_sayisi,
            istisna_sayisi=entity.istisna_sayisi(),
            kapanma_ozeti=entity.kapanma_ozeti,
            toplam_kalem=toplam,
            yerlestirilen=yerlestirilen,
            bekleyen=bekleyen,
        )

    @staticmethod
    def _ilerleme_hesapla(entity) -> tuple[int, int, int]:
        kapanma_ozeti = entity.kapanma_ozeti or {}
        if kapanma_ozeti:
            toplam = int(kapanma_ozeti.get("toplam_kalem") or len(entity.kalemler))
            yerlestirilen = int(kapanma_ozeti.get("yerlestirilen") or 0)
            iptal = int(kapanma_ozeti.get("iptal_edilen") or 0)
        elif entity.durum == MalKabulDurum.TASLAK:
            toplam = len(entity.kalemler)
            yerlestirilen = 0
            iptal = 0
        else:
            toplam = int(getattr(entity, "yerlestirme_gorev_toplam", 0) or len(entity.kalemler))
            yerlestirilen = int(getattr(entity, "yerlestirme_gorev_tamamlanan", 0) or 0)
            iptal = int(getattr(entity, "yerlestirme_gorev_iptal", 0) or 0)

        bekleyen = max(toplam - yerlestirilen - iptal, 0)
        return toplam, yerlestirilen, bekleyen


# ─────────────────────────────────────────
# INBOUND DASHBOARD DTO
# ─────────────────────────────────────────

class InboundIrsaliyeOzetDTO(BaseModel):
    id: int
    irsaliye_no: str
    tir_plaka: Optional[str] = None
    durum: str
    olusturma_tarihi: Optional[str] = None
    kalem_sayisi: int = 0


class InboundDashboardResponseDTO(BaseModel):
    """Inbound kontrol paneli — bugünkü operasyon özeti."""

    # İrsaliye dağılımı
    irsaliye_toplam: int = 0
    irsaliye_taslak: int = 0
    irsaliye_onaylandi: int = 0
    irsaliye_kapandi: int = 0

    # Görev dağılımı
    gorev_toplam: int = 0
    gorev_bekleyen: int = 0
    gorev_devam_eden: int = 0
    gorev_tamamlanan: int = 0
    gorev_iptal: int = 0

    # Performans
    ort_yerlestirme_sure_dk: Optional[float] = None

    # İstisnalar
    istisna_sayisi: int = 0
    override_sayisi: int = 0

    # Bugünkü irsaliye listesi
    bugunun_irsaliyeleri: List[InboundIrsaliyeOzetDTO] = []
