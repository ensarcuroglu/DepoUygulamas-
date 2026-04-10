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
    depo_id: Optional[int] = None
    depo_erisimi_yok: bool = False
    refresh_token_hash: Optional[str] = None
    refresh_token_son_kullanim: Optional[datetime] = None
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)

    # ── İş Kuralları ──

    def admin_mi(self) -> bool:
        return self.rol == KullaniciRol.ADMIN

    def depo_erisim_var(self, hedef_depo_id: int) -> bool:
        """Kullanıcının hedef depoya erişim yetkisi olup olmadığını kontrol eder.

        Admin rolü veya depo_id=None olan kullanıcılar tüm depolara erişebilir.
        Diğer kullanıcılar yalnızca atanmış oldukları depoya erişebilir.
        """
        if self.admin_mi():
            return True
        if self.depo_erisimi_yok:
            return False
        if self.depo_id is None:
            return True
        return self.depo_id == hedef_depo_id

    def rol_kontrol(self, *izinli_roller: str) -> bool:
        """Kullanıcının verilen rollerden birine sahip olup olmadığını kontrol eder."""
        return self.rol in izinli_roller

    def rol_degistir(self, yeni_rol: str) -> None:
        if yeni_rol not in KullaniciRol.TUMU:
            raise ValueError(f"Geçersiz rol: {yeni_rol}. İzin verilen roller: {KullaniciRol.TUMU}")
        self.rol = yeni_rol
