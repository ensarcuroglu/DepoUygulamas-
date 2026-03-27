"""
Kullanıcı Yönetimi Use Case'leri.

NOT: Login/register auth.py'de kalır. Bu use case'ler sadece
kullanıcı CRUD yönetimi içindir (listeleme, güncelleme, silme).
"""

from __future__ import annotations
from typing import List

from app.core.repositories.kullanici_repository import IKullaniciRepository
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.entities.kullanici import Kullanici
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import (
    KayitBulunamadiError,
    CakismaHatasi,
    YetkisizIslemError,
    GecersizIslemError,
)
from app.application.dto.kullanici_dto import (
    KullaniciGuncelleRequestDTO,
    KullaniciResponseDTO,
)
from app.application.helpers import admin_mi


class KullaniciListeleUseCase:
    def __init__(self, kullanici_repo: IKullaniciRepository):
        self._kullanici_repo = kullanici_repo

    def execute(self, skip: int = 0, limit: int = 100) -> List[KullaniciResponseDTO]:
        limit = min(limit, 500)
        kullanicilar = self._kullanici_repo.getir_hepsi(skip=skip, limit=limit)
        return [KullaniciResponseDTO.from_entity(k) for k in kullanicilar]


class KullaniciGetirUseCase:
    def __init__(self, kullanici_repo: IKullaniciRepository):
        self._kullanici_repo = kullanici_repo

    def execute(self, kullanici_id: int) -> KullaniciResponseDTO:
        kullanici = self._kullanici_repo.getir_id_ile(kullanici_id)
        if not kullanici:
            raise KayitBulunamadiError("Kullanıcı", kullanici_id)
        return KullaniciResponseDTO.from_entity(kullanici)


class KullaniciGuncelleUseCase:
    def __init__(
        self,
        kullanici_repo: IKullaniciRepository,
        log_repo: ISistemLogRepository,
        password_hasher=None,
    ):
        self._kullanici_repo = kullanici_repo
        self._log_repo = log_repo
        self._password_hasher = password_hasher

    def execute(
        self,
        kullanici_id: int,
        dto: KullaniciGuncelleRequestDTO,
        current_user: Kullanici,
    ) -> KullaniciResponseDTO:
        # Yetki: admin değilse sadece kendi hesabını güncelleyebilir
        if not admin_mi(current_user) and current_user.id != kullanici_id:
            raise YetkisizIslemError(
                "Bu işlem için yönetici yetkisi veya hesap sahibi olmanız gereklidir"
            )

        mevcut = self._kullanici_repo.getir_id_ile(kullanici_id)
        if not mevcut:
            raise KayitBulunamadiError("Kullanıcı", kullanici_id)

        eski_veri = {"kullanici_adi": mevcut.kullanici_adi, "rol": mevcut.rol}
        guncel = dto.model_dump(exclude_unset=True)

        # Kullanıcı adı değişiyorsa çakışma kontrolü
        yeni_adi = guncel.get("kullanici_adi")
        if yeni_adi and yeni_adi != mevcut.kullanici_adi:
            sahip = self._kullanici_repo.getir_kullanici_adi_ile(yeni_adi)
            if sahip and sahip.id != kullanici_id:
                raise CakismaHatasi("Kullanıcı adı", yeni_adi)
            mevcut.kullanici_adi = yeni_adi

        # Rol değişikliği sadece admin yapabilir
        yeni_rol = guncel.get("rol")
        if yeni_rol and yeni_rol != mevcut.rol:
            if not admin_mi(current_user):
                raise YetkisizIslemError("Sadece yöneticiler rol değiştirebilir")
            mevcut.rol_degistir(yeni_rol)

        # Şifre değişikliği
        yeni_sifre = guncel.pop("sifre", None)
        if yeni_sifre and self._password_hasher:
            mevcut.sifre_hash = self._password_hasher(yeni_sifre)

        # Depo ataması sadece admin yapabilir
        if "depo_id" in guncel:
            if not admin_mi(current_user):
                raise YetkisizIslemError("Sadece yöneticiler depo ataması yapabilir")
            mevcut.depo_id = guncel["depo_id"]

        # Kalan alanlar
        for alan in ("ad_soyad", "telefon", "email", "departman", "sicil_no", "kart_numarasi"):
            if alan in guncel:
                setattr(mevcut, alan, guncel[alan])

        kaydedilen = self._kullanici_repo.guncelle(mevcut)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=current_user.id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Kullanıcı Yönetimi",
                detay=f"Kullanıcı güncellendi: {kaydedilen.kullanici_adi}",
                eski_veri=eski_veri,
                yeni_veri={"kullanici_adi": kaydedilen.kullanici_adi, "rol": kaydedilen.rol},
            )
        )

        return KullaniciResponseDTO.from_entity(kaydedilen)


class KullaniciSilUseCase:
    def __init__(self, kullanici_repo: IKullaniciRepository, log_repo: ISistemLogRepository):
        self._kullanici_repo = kullanici_repo
        self._log_repo = log_repo

    def execute(self, kullanici_id: int, current_user: Kullanici) -> None:
        if kullanici_id == current_user.id:
            raise GecersizIslemError("Kendi hesabınızı silemezsiniz")

        kullanici = self._kullanici_repo.getir_id_ile(kullanici_id)
        if not kullanici:
            raise KayitBulunamadiError("Kullanıcı", kullanici_id)

        self._kullanici_repo.sil(kullanici_id)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=current_user.id,
                islem_tipi=IslemTipi.DELETE,
                modul="Kullanıcı Yönetimi",
                detay=f"Kullanıcı silindi: {kullanici.kullanici_adi} (ID: {kullanici_id})",
            )
        )
