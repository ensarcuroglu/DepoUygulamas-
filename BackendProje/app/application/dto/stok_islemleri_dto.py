"""Stok islemleri request DTO'lari — palet bazli giris/cikis (tekli + toplu)."""

from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel, field_validator

TOPLU_ISLEM_MAKS_PALET = 50


def _palet_no_temizle(v: str) -> str:
    """Palet numarasi strip + bos kontrolu."""
    v = v.strip()
    if not v:
        raise ValueError("Palet numarasi bos olamaz.")
    return v


# ─────────────────────────────────────────
# TEKLİ İŞLEM DTO'LARI (Faz 1 — korunuyor)
# ─────────────────────────────────────────


class PaletGirisRequestDTO(BaseModel):
    """Palet bazli stok girisi istegi."""

    palet_no: str

    _palet_no_temizle = field_validator("palet_no", mode="before")(_palet_no_temizle)


class PaletCikisRequestDTO(BaseModel):
    """Palet bazli stok cikisi istegi."""

    palet_no: str
    miktar: Optional[int] = None  # None = tam cikis
    siparis_no: Optional[str] = None
    aciklama: Optional[str] = None

    _palet_no_temizle = field_validator("palet_no", mode="before")(_palet_no_temizle)

    @field_validator("miktar")
    @classmethod
    def miktar_pozitif(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("Miktar pozitif olmali.")
        return v


# ─────────────────────────────────────────
# TOPLU İŞLEM DTO'LARI (Faz 2)
# ─────────────────────────────────────────


class TopluPaletCikisKalemiDTO(BaseModel):
    """Toplu cikis istegindeki tek bir palet kalemi."""

    palet_no: str
    miktar: Optional[int] = None  # None = tam cikis

    _palet_no_temizle = field_validator("palet_no", mode="before")(_palet_no_temizle)

    @field_validator("miktar")
    @classmethod
    def miktar_pozitif(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("Miktar pozitif olmali.")
        return v


class TopluPaletGirisRequestDTO(BaseModel):
    """Toplu palet girisi istegi — max 50 palet."""

    palet_no_listesi: List[str]

    @field_validator("palet_no_listesi", mode="before")
    @classmethod
    def palet_listesi_dogrula(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("Palet listesi bos olamaz.")
        temiz = [p.strip() for p in v]
        if any(not p for p in temiz):
            raise ValueError("Palet numarasi bos olamaz.")
        if len(temiz) > TOPLU_ISLEM_MAKS_PALET:
            raise ValueError(
                f"Tek seferde en fazla {TOPLU_ISLEM_MAKS_PALET} palet islenebilir."
            )
        if len(set(temiz)) != len(temiz):
            raise ValueError("Listede tekrarlayan palet numarasi var.")
        return temiz


class TopluPaletCikisRequestDTO(BaseModel):
    """Toplu palet cikisi istegi — max 50 palet, per-palet opsiyonel miktar."""

    kalemler: List[TopluPaletCikisKalemiDTO]
    siparis_no: Optional[str] = None
    aciklama: Optional[str] = None

    @field_validator("kalemler")
    @classmethod
    def kalemler_dogrula(cls, v: List[TopluPaletCikisKalemiDTO]) -> List[TopluPaletCikisKalemiDTO]:
        if not v:
            raise ValueError("Kalem listesi bos olamaz.")
        if len(v) > TOPLU_ISLEM_MAKS_PALET:
            raise ValueError(
                f"Tek seferde en fazla {TOPLU_ISLEM_MAKS_PALET} palet islenebilir."
            )
        palet_nolar = [k.palet_no for k in v]
        if len(set(palet_nolar)) != len(palet_nolar):
            raise ValueError("Listede tekrarlayan palet numarasi var.")
        return v


# ─────────────────────────────────────────
# TOPLU İŞLEM RESPONSE DTO'LARI
# ─────────────────────────────────────────


class TopluIslemPaletSonucDTO(BaseModel):
    """Toplu islemdeki tek bir paletin sonucu."""

    palet_no: str
    basarili: bool
    hata_mesaji: Optional[str] = None
    hareket_id: Optional[int] = None


class TopluIslemResponseDTO(BaseModel):
    """Toplu islem sonuc ozeti."""

    toplam: int
    basarili: int
    basarisiz: int
    sonuclar: List[TopluIslemPaletSonucDTO]
