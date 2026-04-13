"""
Lot Use Case'leri.
"""

from __future__ import annotations
from typing import List
from sqlalchemy.orm import Session

from app.core.repositories.lot_repository import ILotRepository
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.entities.lot import Lot
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import KayitBulunamadiError, CakismaHatasi
from app.application.dto.lot_dto import (
    LotOlusturRequestDTO,
    LotGuncelleRequestDTO,
    LotResponseDTO,
)


class LotListeleUseCase:
    def __init__(self, lot_repo: ILotRepository):
        self._lot_repo = lot_repo

    def execute(
        self, skip: int = 0, limit: int = 50, urun_id: int | None = None
    ) -> tuple[List[LotResponseDTO], int]:
        lotlar = self._lot_repo.getir_hepsi(skip=skip, limit=limit, urun_id=urun_id)
        toplam = self._lot_repo.say(urun_id=urun_id)
        return [LotResponseDTO.from_entity(lot) for lot in lotlar], toplam


class LotGetirUseCase:
    def __init__(self, lot_repo: ILotRepository):
        self._lot_repo = lot_repo

    def execute(self, lot_id: int) -> LotResponseDTO:
        lot = self._lot_repo.getir_id_ile(lot_id)
        if not lot:
            raise KayitBulunamadiError("Lot", lot_id)
        return LotResponseDTO.from_entity(lot)


class LotSktYaklasanUseCase:
    def __init__(self, lot_repo: ILotRepository):
        self._lot_repo = lot_repo

    def execute(self, gun: int = 30) -> List[LotResponseDTO]:
        gun = min(gun, 365)
        lotlar = self._lot_repo.getir_skt_yaklasan(gun=gun)
        return [LotResponseDTO.from_entity(lot) for lot in lotlar]


class LotOlusturUseCase:
    def __init__(self, lot_repo: ILotRepository, log_repo: ISistemLogRepository, db: Session):
        self._lot_repo = lot_repo
        self._log_repo = log_repo
        self._db = db

    def execute(self, dto: LotOlusturRequestDTO, kullanici_id: int) -> LotResponseDTO:
        if (
            dto.uretim_tarihi
            and dto.son_kullanma_tarihi
            and dto.uretim_tarihi > dto.son_kullanma_tarihi
        ):
            raise CakismaHatasi("Tarih aralığı", "Üretim tarihi son kullanma tarihinden büyük olamaz")

        # Lot no çakışma kontrolü
        if dto.lot_no:
            mevcut = self._lot_repo.getir_lot_no_ile(dto.lot_no)
            if mevcut:
                raise CakismaHatasi("Lot numarası", dto.lot_no)

        lot = Lot(
            urun_id=dto.urun_id,
            lot_no=dto.lot_no,
            parti_no=dto.parti_no,
            uretim_tarihi=dto.uretim_tarihi,
            son_kullanma_tarihi=dto.son_kullanma_tarihi,
            aciklama=dto.aciklama,
        )
        try:
            kaydedilen = self._lot_repo.olustur(lot, auto_commit=False)
            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici_id,
                    islem_tipi=IslemTipi.CREATE,
                    modul="Lot Yönetimi",
                    detay=f"Yeni lot eklendi: {kaydedilen.lot_no or kaydedilen.id}",
                    yeni_veri={"lot_no": kaydedilen.lot_no, "urun_id": kaydedilen.urun_id},
                ),
                auto_commit=False,
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

        return LotResponseDTO.from_entity(kaydedilen)


class LotGuncelleUseCase:
    def __init__(self, lot_repo: ILotRepository, log_repo: ISistemLogRepository, db: Session):
        self._lot_repo = lot_repo
        self._log_repo = log_repo
        self._db = db

    def execute(
        self, lot_id: int, dto: LotGuncelleRequestDTO, kullanici_id: int
    ) -> LotResponseDTO:
        mevcut = self._lot_repo.getir_id_ile(lot_id)
        if not mevcut:
            raise KayitBulunamadiError("Lot", lot_id)

        eski_veri = {"lot_no": mevcut.lot_no, "aktif": mevcut.aktif}

        guncel = dto.model_dump(exclude_unset=True)

        # Lot no değişiyorsa çakışma kontrolü
        yeni_lot_no = guncel.get("lot_no")
        if yeni_lot_no and yeni_lot_no != mevcut.lot_no:
            sahip = self._lot_repo.getir_lot_no_ile(yeni_lot_no)
            if sahip and sahip.id != lot_id:
                raise CakismaHatasi("Lot numarası", yeni_lot_no)

        yeni_uretim = guncel.get("uretim_tarihi", mevcut.uretim_tarihi)
        yeni_skt = guncel.get("son_kullanma_tarihi", mevcut.son_kullanma_tarihi)
        if yeni_uretim and yeni_skt and yeni_uretim > yeni_skt:
            raise CakismaHatasi("Tarih aralığı", "Üretim tarihi son kullanma tarihinden büyük olamaz")

        for alan, deger in guncel.items():
            setattr(mevcut, alan, deger)

        try:
            kaydedilen = self._lot_repo.guncelle(mevcut, auto_commit=False)
            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici_id,
                    islem_tipi=IslemTipi.UPDATE,
                    modul="Lot Yönetimi",
                    detay=f"Lot güncellendi: {kaydedilen.lot_no or kaydedilen.id}",
                    eski_veri=eski_veri,
                    yeni_veri={"lot_no": kaydedilen.lot_no, "aktif": kaydedilen.aktif},
                ),
                auto_commit=False,
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

        return LotResponseDTO.from_entity(kaydedilen)


class LotSilUseCase:
    def __init__(self, lot_repo: ILotRepository, log_repo: ISistemLogRepository, db: Session):
        self._lot_repo = lot_repo
        self._log_repo = log_repo
        self._db = db

    def execute(self, lot_id: int, kullanici_id: int) -> None:
        lot = self._lot_repo.getir_id_ile(lot_id)
        if not lot:
            raise KayitBulunamadiError("Lot", lot_id)

        try:
            self._lot_repo.sil(lot_id, auto_commit=False)
            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici_id,
                    islem_tipi=IslemTipi.DELETE,
                    modul="Lot Yönetimi",
                    detay=f"Lot pasife alındı: {lot.lot_no or lot.id} (ID: {lot_id})",
                ),
                auto_commit=False,
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise
