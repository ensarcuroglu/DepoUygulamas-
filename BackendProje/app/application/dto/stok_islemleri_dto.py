"""Stok islemleri request DTO'lari — palet bazli giris/cikis."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, field_validator


def _palet_no_temizle(v: str) -> str:
    """Palet numarasi strip + bos kontrolu."""
    v = v.strip()
    if not v:
        raise ValueError("Palet numarasi bos olamaz.")
    return v


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
