"""
Auth veri transfer nesneleri (DTO).

Giriş, çıkış, token yenileme ve kullanıcı kayıt işlemlerine ait
request/response şemalarını içerir.
"""

from __future__ import annotations
import re
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────
# İSTEK (REQUEST) DTO'LARI
# ─────────────────────────────────────────

class LoginRequestDTO(BaseModel):
    kullanici_adi: str = Field(..., min_length=3, max_length=50)
    sifre: str = Field(..., min_length=1, max_length=128)


class RefreshRequestDTO(BaseModel):
    refresh_token: str


class KullaniciCreateDTO(BaseModel):
    kullanici_adi: str = Field(..., min_length=3, max_length=50)
    ad_soyad: str
    sifre: str = Field(..., min_length=8, max_length=128)
    rol: Literal["admin", "depocu", "goruntuleyen", "lojistik"] = "depocu"
    telefon: Optional[str] = None
    email: Optional[str] = None
    departman: Optional[str] = None
    sicil_no: Optional[str] = None
    kart_numarasi: Optional[str] = None
    depo_id: Optional[int] = None
    depo_erisimi_yok: bool = False

    @field_validator("sifre")
    @classmethod
    def sifre_kompleksitesi(cls, v: str) -> str:
        """Şifre en az 1 büyük harf, 1 küçük harf, 1 rakam içermeli."""
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

class TokenUserInfoDTO(BaseModel):
    id: int
    kullanici_adi: str
    ad_soyad: str
    rol: str
    depo_id: Optional[int] = None
    depo_erisimi_yok: bool = False
    telefon: Optional[str] = None
    email: Optional[str] = None
    departman: Optional[str] = None
    sicil_no: Optional[str] = None
    kart_numarasi: Optional[str] = None


class TokenResponseDTO(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: TokenUserInfoDTO
