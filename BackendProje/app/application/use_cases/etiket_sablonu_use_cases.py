"""Etiket Şablonu CRUD use case'leri (admin-only)."""

from __future__ import annotations

from typing import List, TYPE_CHECKING

from app.core.entities.etiket_sablonu import EtiketSablonu
from app.core.entities.kullanici import KullaniciRol
from app.core.exceptions import (
    KayitBulunamadiError,
    YetkisizIslemError,
    GecersizIslemError,
)
from app.application.dto.etiket_dto import (
    EtiketSablonuOlusturDTO,
    EtiketSablonuGuncelleDTO,
    EtiketSablonuResponseDTO,
)

if TYPE_CHECKING:
    from app.core.entities.kullanici import Kullanici
    from app.core.repositories.etiket_sablonu_repository import IEtiketSablonuRepository


def _admin_zorunlu(kullanici: "Kullanici") -> None:
    if kullanici.rol != KullaniciRol.ADMIN:
        raise YetkisizIslemError("Bu işlem için admin yetkisi gereklidir.")


class EtiketSablonlariListeleUseCase:
    def __init__(self, repo: "IEtiketSablonuRepository"):
        self._repo = repo

    def execute(
        self, skip: int = 0, limit: int = 100, sadece_aktif: bool = True
    ) -> List[EtiketSablonuResponseDTO]:
        return [
            EtiketSablonuResponseDTO.from_entity(s)
            for s in self._repo.getir_hepsi(skip=skip, limit=limit, sadece_aktif=sadece_aktif)
        ]


class EtiketSablonuGetirUseCase:
    def __init__(self, repo: "IEtiketSablonuRepository"):
        self._repo = repo

    def execute(self, sablon_id: int) -> EtiketSablonuResponseDTO:
        sablon = self._repo.getir_id_ile(sablon_id)
        if not sablon:
            raise KayitBulunamadiError("Etiket şablonu", sablon_id)
        return EtiketSablonuResponseDTO.from_entity(sablon)


class EtiketSablonuOlusturUseCase:
    def __init__(self, repo: "IEtiketSablonuRepository"):
        self._repo = repo

    def execute(
        self, dto: EtiketSablonuOlusturDTO, kullanici: "Kullanici"
    ) -> EtiketSablonuResponseDTO:
        _admin_zorunlu(kullanici)
        entity = EtiketSablonu(
            ad=dto.ad.strip(),
            boyut=dto.boyut,
            zpl_template=dto.zpl_template,
            html_template=dto.html_template,
            default_mi=dto.default_mi,
            aktif=dto.aktif,
            olusturan_id=kullanici.id,
        )
        entity.dogrula()
        olusturulan = self._repo.olustur(entity)
        if olusturulan.default_mi:
            self._repo.default_sifirla(haric_id=olusturulan.id)
        return EtiketSablonuResponseDTO.from_entity(olusturulan)


class EtiketSablonuGuncelleUseCase:
    def __init__(self, repo: "IEtiketSablonuRepository"):
        self._repo = repo

    def execute(
        self,
        sablon_id: int,
        dto: EtiketSablonuGuncelleDTO,
        kullanici: "Kullanici",
    ) -> EtiketSablonuResponseDTO:
        _admin_zorunlu(kullanici)
        mevcut = self._repo.getir_id_ile(sablon_id)
        if not mevcut:
            raise KayitBulunamadiError("Etiket şablonu", sablon_id)

        if dto.ad is not None:
            mevcut.ad = dto.ad.strip()
        if dto.boyut is not None:
            mevcut.boyut = dto.boyut
        if dto.zpl_template is not None:
            mevcut.zpl_template = dto.zpl_template
        if dto.html_template is not None:
            mevcut.html_template = dto.html_template
        if dto.default_mi is not None:
            mevcut.default_mi = dto.default_mi
        if dto.aktif is not None:
            mevcut.aktif = dto.aktif

        mevcut.dogrula()
        guncellenen = self._repo.guncelle(mevcut)
        if guncellenen is None:
            raise GecersizIslemError("Şablon güncellenemedi.")
        if guncellenen.default_mi:
            self._repo.default_sifirla(haric_id=guncellenen.id)
        return EtiketSablonuResponseDTO.from_entity(guncellenen)


class EtiketSablonuSilUseCase:
    def __init__(self, repo: "IEtiketSablonuRepository"):
        self._repo = repo

    def execute(self, sablon_id: int, kullanici: "Kullanici") -> None:
        _admin_zorunlu(kullanici)
        if not self._repo.sil(sablon_id):
            raise KayitBulunamadiError("Etiket şablonu", sablon_id)
