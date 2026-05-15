"""Pydantic v2 DTO şemaları (backend uyumlu, minimal alan kümesi).

Backend'in `app/application/dto/*` modülleriyle alan adları ve kısıtları
uyumludur ama bağımlılık değildir; DataGenService bağımsız evrim sürdürür.
Emitter katmanı bu DTO'ları JSON payload'a çevirip backend uçlarına yayar.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

DepolamaTipi = Literal["Kuru", "Soguk", "Tehlikeli"]
Birim = Literal["Adet", "Kg", "Lt", "Mt"]
SiparisDurumu = Literal[
    "TASLAK", "ONAYLANDI", "HAZIRLANIYOR", "SEVKEDILDI", "TESLIM_EDILDI"
]
GorevTipi = Literal["yerlestirme", "toplama"]
PerformansEventTipi = Literal[
    "GOREV_BASLATILDI", "GOREV_TAMAMLANDI", "GOREV_IPTAL"
]


class _DataGenBase(BaseModel):
    """Tüm DataGen DTO'ları için ortak Pydantic config."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        frozen=False,
    )


class UrunDTO(_DataGenBase):
    """`POST /api/urunler/` payload'ı (UrunOlusturRequestDTO uyumlu)."""

    isim: str = Field(..., min_length=1, max_length=200)
    marka_id: int | None = Field(None, gt=0)
    kategori_id: int | None = Field(None, gt=0)
    tedarikci_id: int | None = Field(None, gt=0)
    ean: str | None = Field(None, max_length=14)
    barkod: str | None = Field(None, max_length=100)
    ic_adet: int = Field(1, ge=1)
    gramaj: float | None = Field(None, ge=0)
    birim: Birim = "Adet"
    fiyat: float = Field(0.0, ge=0)
    min_stok: int = Field(10, ge=0)
    aciklama: str = Field("", max_length=2000)
    depolama_tipi: DepolamaTipi = "Kuru"

    @field_validator("ean")
    @classmethod
    def _ean_numerik(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not v.isdigit():
            raise ValueError("EAN yalnız rakam içermelidir")
        if len(v) not in {8, 13, 14}:
            raise ValueError("EAN uzunluğu 8, 13 ya da 14 olmalıdır")
        return v


class RafDTO(_DataGenBase):
    """`POST /api/raflar/` payload'ı (RafOlusturRequestDTO uyumlu)."""

    depo_id: int = Field(..., gt=0)
    zon_id: int | None = Field(None, gt=0)
    kod: str = Field(..., min_length=1, max_length=50)
    bolge: str = Field("", max_length=100)
    kapasite: int = Field(100, ge=1)
    max_agirlik_kg: float | None = Field(None, gt=0)
    koridor: str = Field("", max_length=10)
    kat: int = Field(0, ge=0)
    goz: int = Field(0, ge=0)


class LotDTO(_DataGenBase):
    """`POST /api/lotlar/` payload'ı (LotOlusturRequestDTO uyumlu)."""

    urun_id: int = Field(..., gt=0)
    lot_no: str | None = Field(None, max_length=100)
    parti_no: str | None = Field(None, max_length=100)
    uretim_tarihi: date | None = None
    son_kullanma_tarihi: date | None = None
    aciklama: str = Field("", max_length=2000)


class PaletDTO(_DataGenBase):
    """`POST /api/paletler/` payload'ı (PaletOlusturRequestDTO uyumlu)."""

    lot_id: int = Field(..., gt=0)
    raf_id: int = Field(..., gt=0)
    palet_no: str = Field(..., min_length=1, max_length=100)
    koli_adedi: int = Field(..., gt=0)
    palet_kg: float | None = Field(None, ge=0)
    vardiya: str | None = Field(None, max_length=50)


class SiparisKalemDTO(_DataGenBase):
    urun_id: int = Field(..., gt=0)
    miktar: int = Field(..., gt=0)
    birim_fiyat: float = Field(..., ge=0)
    kdv_orani: float = Field(18.0, ge=0, le=100)


class SiparisDTO(_DataGenBase):
    """`POST /api/siparisler/` payload'ı (SiparisOlusturRequestDTO uyumlu)."""

    musteri_adi: str = Field(..., min_length=1, max_length=200)
    teslimat_adresi: str = Field(..., min_length=1, max_length=500)
    teslimat_tarihi: date
    notlar: str = Field("", max_length=2000)
    kalemler: list[SiparisKalemDTO] = Field(..., min_length=1)


class YerlestirmeGoreviDTO(_DataGenBase):
    """`POST /api/yerlestirme-gorevleri/` payload'ı."""

    palet_id: int = Field(..., gt=0)
    mal_kabul_irsaliye_id: int | None = Field(None, gt=0)
    tip: str = Field("yerlestirme")
    kaynak_raf_id: int | None = Field(None, gt=0)
    onerilen_raf_id: int = Field(..., gt=0)
    oncelik: int = Field(5, ge=1, le=5)


class ToplamaGoreviDTO(_DataGenBase):
    """`POST /api/v1/toplama-gorevleri/uret` payload'ı (PickTaskUretRequestDTO)."""

    sevkiyat_id: int = Field(..., gt=0)


class PerformansEventDTO(_DataGenBase):
    """`GorevPerformansEvent` ile uyumlu — RabbitMQ payload.

    Routing key dışarıdan üretilir: ``lms.gorev_performans.<event_tipi>``.
    Consumer mesajdaki ``event_uuid`` üzerinden idempotent — saf yük
    testinde DB'de karşılık olmadığı için DLQ'ya düşmesi beklenir
    (envanter §2 notu).
    """

    event_uuid: str = Field(..., min_length=8, max_length=64)
    event_tipi: PerformansEventTipi = "GOREV_TAMAMLANDI"
    gorev_tipi: GorevTipi = "yerlestirme"
    gorev_id: int = Field(..., gt=0)
    kullanici_id: int = Field(..., gt=0)
    depo_id: int | None = Field(None, gt=0)
    sure_saniye: int | None = Field(None, ge=0)
    iptal_nedeni: str | None = Field(None, max_length=500)
    payload: dict[str, object] | None = None
    olusturma_tarihi: datetime


class TalepGecmisKaydiDTO(_DataGenBase):
    """ML eğitim verisi (file emitter çıktısı).

    Backend'e gitmez; doğrudan parquet/CSV'ye yazılır.
    """

    tarih: date
    urun_kodu: str = Field(..., min_length=1)
    urun_id: int = Field(..., gt=0)
    miktar: int = Field(..., ge=0)
    fiyat: float = Field(..., ge=0)
    promosyon: bool = False
    haftanin_gunu: int = Field(..., ge=0, le=6, description="0=Pazartesi, 6=Pazar")


__all__ = [
    "DepolamaTipi",
    "Birim",
    "SiparisDurumu",
    "GorevTipi",
    "PerformansEventTipi",
    "UrunDTO",
    "RafDTO",
    "LotDTO",
    "PaletDTO",
    "SiparisDTO",
    "SiparisKalemDTO",
    "YerlestirmeGoreviDTO",
    "ToplamaGoreviDTO",
    "PerformansEventDTO",
    "TalepGecmisKaydiDTO",
]
