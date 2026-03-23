"""
Destek Talebi Use Case'leri.

Durum geçişleri (Açık → İşlemde → Çözüldü) entity'deki domain metodlarıyla korunur.
"""

from __future__ import annotations
from typing import List

from app.core.repositories.destek_talebi_repository import IDestekTalebiRepository
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.entities.destek_talebi import DestekTalebi, DestekDurum
from app.core.entities.kullanici import Kullanici
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import KayitBulunamadiError, YetkisizIslemError
from app.application.dto.destek_talebi_dto import (
    DestekTalebiOlusturRequestDTO,
    DestekTalebiGuncelleRequestDTO,
    DestekTalebiResponseDTO,
)
from app.application.helpers import admin_mi


class DestekTalebiListeleUseCase:
    def __init__(self, destek_repo: IDestekTalebiRepository):
        self._destek_repo = destek_repo

    def execute(
        self,
        current_user: Kullanici,
        skip: int = 0,
        limit: int = 100,
        durum: str | None = None,
    ) -> List[DestekTalebiResponseDTO]:
        limit = min(limit, 500)
        # Admin tüm talepleri, normal kullanıcı kendi taleplerini görür
        kullanici_id = None if admin_mi(current_user) else current_user.id
        talepler = self._destek_repo.getir_hepsi(
            skip=skip, limit=limit, kullanici_id=kullanici_id, durum=durum
        )
        return [DestekTalebiResponseDTO.from_entity(t) for t in talepler]


class DestekTalebiGetirUseCase:
    def __init__(self, destek_repo: IDestekTalebiRepository):
        self._destek_repo = destek_repo

    def execute(self, talep_id: int, current_user: Kullanici) -> DestekTalebiResponseDTO:
        talep = self._destek_repo.getir_id_ile(talep_id)
        if not talep:
            raise KayitBulunamadiError("Destek talebi", talep_id)
        # Normal kullanıcı sadece kendi talebini görebilir
        if not admin_mi(current_user) and talep.kullanici_id != current_user.id:
            raise YetkisizIslemError("Bu talebe erişim yetkiniz yok")
        return DestekTalebiResponseDTO.from_entity(talep)


class DestekTalebiOlusturUseCase:
    def __init__(self, destek_repo: IDestekTalebiRepository, log_repo: ISistemLogRepository):
        self._destek_repo = destek_repo
        self._log_repo = log_repo

    def execute(
        self, dto: DestekTalebiOlusturRequestDTO, kullanici_id: int
    ) -> DestekTalebiResponseDTO:
        talep = DestekTalebi(
            kullanici_id=kullanici_id,
            konu=dto.konu,
            kategori=dto.kategori,
            oncelik=dto.oncelik,
            aciklama=dto.aciklama,
        )
        kaydedilen = self._destek_repo.olustur(talep)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.CREATE,
                modul="Destek Masası",
                detay=f"Yeni destek talebi: {kaydedilen.konu}",
                yeni_veri={"konu": kaydedilen.konu, "kategori": kaydedilen.kategori},
            )
        )

        return DestekTalebiResponseDTO.from_entity(kaydedilen)


class DestekTalebiGuncelleUseCase:
    """Sadece admin destek talebini güncelleyebilir (cevap, durum, öncelik)."""

    def __init__(self, destek_repo: IDestekTalebiRepository, log_repo: ISistemLogRepository):
        self._destek_repo = destek_repo
        self._log_repo = log_repo

    def execute(
        self, talep_id: int, dto: DestekTalebiGuncelleRequestDTO, admin_id: int
    ) -> DestekTalebiResponseDTO:
        talep = self._destek_repo.getir_id_ile(talep_id)
        if not talep:
            raise KayitBulunamadiError("Destek talebi", talep_id)

        eski_durum = talep.durum

        # Durum geçişlerini entity domain metodlarıyla uygula
        guncel = dto.model_dump(exclude_unset=True)
        yeni_durum = guncel.get("durum")
        admin_cevabi = guncel.get("admin_cevabi")

        if yeni_durum == DestekDurum.COZULDU:
            talep.coz(cevap=admin_cevabi)
        elif yeni_durum == DestekDurum.ISLEMDE or admin_cevabi:
            talep.cevapla(admin_cevabi or "")
        elif yeni_durum:
            talep.durum = yeni_durum

        if "oncelik" in guncel:
            talep.oncelik = guncel["oncelik"]

        kaydedilen = self._destek_repo.guncelle(talep)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=admin_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Destek Masası",
                detay=f"Destek talebi güncellendi: {kaydedilen.konu}",
                eski_veri={"durum": eski_durum},
                yeni_veri={"durum": kaydedilen.durum},
            )
        )

        return DestekTalebiResponseDTO.from_entity(kaydedilen)
