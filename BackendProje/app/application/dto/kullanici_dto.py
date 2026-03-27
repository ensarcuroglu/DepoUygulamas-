"""
Kullanıcı veri transfer nesneleri (DTO).

NOT: Kullanıcı oluşturma (kayıt) auth.py'de kalıyor.
Bu DTO'lar sadece kullanıcı yönetimi (listeleme, güncelleme, silme) içindir.
"""

from __future__ import annotations
import re
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator

from app.core.entities.kullanici import Kullanici


# ─────────────────────────────────────────
# İSTEK (REQUEST) DTO'LARI
# ─────────────────────────────────────────

class KullaniciGuncelleRequestDTO(BaseModel):
    kullanici_adi: Optional[str] = Field(None, min_length=3, max_length=50)
    ad_soyad: Optional[str] = Field(None, max_length=200)
    rol: Optional[Literal["admin", "depocu", "goruntuleyen", "lojistik"]] = None
    sifre: Optional[str] = Field(None, min_length=8, max_length=128)
    telefon: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    departman: Optional[str] = Field(None, max_length=100)
    sicil_no: Optional[str] = Field(None, max_length=50)
    kart_numarasi: Optional[str] = Field(None, max_length=50)
    depo_id: Optional[int] = None

    @field_validator("sifre")
    @classmethod
    def sifre_kompleksitesi(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.search(r"[A-Z]", v):
                raise ValueError("Şifre en az bir büyük harf içermeli.")
            if not re.search(r"[a-z]", v):
                raise ValueError("Şifre en az bir küçük harf içermeli.")
            if not re.search(r"\d", v):
                raise ValueError("Şifre en az bir rakam içermeli.")
        return v


# ─────────────────────────────────────────
# YANIT (RESPONSE) DTO'LARI
# ─────────────────────────────────────────

class KullaniciResponseDTO(BaseModel):
    id: int
    kullanici_adi: str
    ad_soyad: str
    rol: str
    telefon: Optional[str] = None
    email: Optional[str] = None
    departman: Optional[str] = None
    sicil_no: Optional[str] = None
    kart_numarasi: Optional[str] = None
    depo_id: Optional[int] = None
    olusturma_tarihi: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity: Kullanici) -> "KullaniciResponseDTO":
        return cls(
            id=entity.id,
            kullanici_adi=entity.kullanici_adi,
            ad_soyad=entity.ad_soyad,
            rol=entity.rol,
            telefon=entity.telefon,
            email=entity.email,
            departman=entity.departman,
            sicil_no=entity.sicil_no,
            kart_numarasi=entity.kart_numarasi,
            depo_id=entity.depo_id,
            olusturma_tarihi=entity.olusturma_tarihi,
        )
