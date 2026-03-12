"""
LOT İşlemleri — Service Layer
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from models import Lot
from schemas import LotCreate, LotUpdate
from core.exceptions import NotFoundError, DuplicateError
import crud


class LotService:

    @staticmethod
    def get_lot(db: Session, lot_id: int) -> Lot:
        """ID'ye göre LOT getir; bulunamazsa NotFoundError fırlatır."""
        lot = crud.get_lot(db, lot_id)
        if not lot:
            raise NotFoundError("LOT", lot_id)
        return lot

    @staticmethod
    def get_lotlar(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        urun_id: Optional[int] = None,
    ) -> List[Lot]:
        """LOT listesi; ürüne göre filtreleme destekler."""
        return crud.get_lotlar(db, skip=skip, limit=limit, urun_id=urun_id)

    @staticmethod
    def get_skt_yaklasan(db: Session, gun: int = 30) -> List[Lot]:
        """Son kullanma tarihi belirtilen gün içinde olan LOT'ları döner."""
        return crud.get_skt_yaklasan_lotlar(db, gun=gun)

    @staticmethod
    def create_lot(db: Session, lot_data: LotCreate) -> Lot:
        """
        Yeni LOT oluştur.
        - Ürün bulunamazsa NotFoundError
        - Aynı ürüne ait lot_no mükerrerse DuplicateError
        """
        urun = crud.get_urun(db, lot_data.urun_id)
        if not urun:
            raise NotFoundError("Ürün", lot_data.urun_id)

        existing_lot = (
            db.query(Lot)
            .filter(
                Lot.urun_id == lot_data.urun_id,
                Lot.lot_no == lot_data.lot_no,
                Lot.aktif == True,
            )
            .first()
        )
        if existing_lot:
            raise DuplicateError("LOT numarası", lot_data.lot_no)

        return crud.create_lot(db, lot_data)

    @staticmethod
    def update_lot(db: Session, lot_id: int, lot_data: LotUpdate) -> Lot:
        """LOT güncelle; bulunamazsa NotFoundError fırlatır."""
        LotService.get_lot(db, lot_id)  # varlık kontrolü
        return crud.update_lot(db, lot_id, lot_data)

    @staticmethod
    def delete_lot(db: Session, lot_id: int) -> bool:
        """LOT soft-delete; bulunamazsa NotFoundError fırlatır."""
        LotService.get_lot(db, lot_id)  # varlık kontrolü
        return crud.delete_lot(db, lot_id)
