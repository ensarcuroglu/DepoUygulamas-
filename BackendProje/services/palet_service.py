"""
Palet İşlemleri — Service Layer
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from models import Palet
from schemas import PaletCreate, PaletUpdate
from core.exceptions import NotFoundError
import crud


class PaletService:

    @staticmethod
    def get_palet(db: Session, palet_id: int) -> Palet:
        """ID'ye göre palet getir; bulunamazsa NotFoundError fırlatır."""
        palet = crud.get_palet(db, palet_id)
        if not palet:
            raise NotFoundError("Palet", palet_id)
        return palet

    @staticmethod
    def get_palet_by_no(db: Session, palet_no: str) -> Optional[Palet]:
        """Barkod numarasına göre palet getir; None dönebilir."""
        return crud.get_palet_by_no(db, palet_no=palet_no)

    @staticmethod
    def get_sonraki_palet_no(db: Session) -> str:
        """Bir sonraki palet barkod numarasını döner."""
        return crud.get_sonraki_palet_no(db)

    @staticmethod
    def get_paletler(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        lot_id: Optional[int] = None,
        raf_id: Optional[int] = None,
    ) -> List[Palet]:
        """Palet listesi; LOT veya rafa göre filtreleme destekler."""
        return crud.get_paletler(db, skip=skip, limit=limit, lot_id=lot_id, raf_id=raf_id)

    @staticmethod
    def create_palet(db: Session, palet_data: PaletCreate) -> Palet:
        """
        Yeni palet oluştur.
        - LOT bulunamazsa NotFoundError
        - Raf belirtilmişse ve bulunamazsa NotFoundError
        """
        lot = crud.get_lot(db, palet_data.lot_id)
        if not lot:
            raise NotFoundError("LOT", palet_data.lot_id)

        if palet_data.raf_id:
            raf = crud.get_raf(db, palet_data.raf_id)
            if not raf:
                raise NotFoundError("Raf", palet_data.raf_id)

        return crud.create_palet(db, palet_data)

    @staticmethod
    def update_palet(db: Session, palet_id: int, palet_data: PaletUpdate) -> Palet:
        """Palet güncelle; bulunamazsa NotFoundError fırlatır."""
        PaletService.get_palet(db, palet_id)  # varlık kontrolü
        return crud.update_palet(db, palet_id, palet_data)

    @staticmethod
    def delete_palet(db: Session, palet_id: int) -> bool:
        """Palet soft-delete; bulunamazsa NotFoundError fırlatır."""
        PaletService.get_palet(db, palet_id)  # varlık kontrolü
        return crud.delete_palet(db, palet_id)
