from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class KullaniciRol:
    ADMIN = "admin"
    DEPOCU = "depocu"
    GORUNTULEYEN = "goruntuleyen"
    LOJISTIK = "lojistik"

    TUMU = {ADMIN, DEPOCU, GORUNTULEYEN, LOJISTIK}


@dataclass
class Kullanici:
    """Kullanıcı domain entity.

    NOT: sifre_hash alanı burada tutulur ancak hash/verify işlemleri
    infrastructure katmanında (auth modülü) yapılır.
    """

    id: Optional[int] = None
    kullanici_adi: str = ""
    sifre_hash: str = ""
    ad_soyad: str = ""
    rol: str = KullaniciRol.DEPOCU
    telefon: Optional[str] = None
    email: Optional[str] = None
    departman: Optional[str] = None
    sicil_no: Optional[str] = None
    kart_numarasi: Optional[str] = None
    refresh_token_hash: Optional[str] = None
    refresh_token_son_kullanim: Optional[datetime] = None
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)

    # ── İş Kuralları ──

    def admin_mi(self) -> bool:
        return self.rol == KullaniciRol.ADMIN

    def rol_kontrol(self, *izinli_roller: str) -> bool:
        """Kullanıcının verilen rollerden birine sahip olup olmadığını kontrol eder."""
        return self.rol in izinli_roller

    def rol_degistir(self, yeni_rol: str) -> None:
        if yeni_rol not in KullaniciRol.TUMU:
            raise ValueError(f"Geçersiz rol: {yeni_rol}. İzin verilen roller: {KullaniciRol.TUMU}")
        self.rol = yeni_rol
