"""
Stok Hareketi İşlemleri — Service Layer
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from models import StokHareketi
from schemas import StokHareketiCreate, StokHareketiResponse
from core.exceptions import NotFoundError, BadRequestError
import crud


class StokService:

    @staticmethod
    def get_hareketler(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        urun_id: Optional[int] = None,
        lot_id: Optional[int] = None,
        hareket_tipi: Optional[str] = None,
    ) -> List[StokHareketi]:
        """Stok hareketlerini listeler; ürün, LOT, hareket tipi filtresi destekler."""
        return crud.get_stok_hareketleri(
            db, skip=skip, limit=limit,
            urun_id=urun_id, lot_id=lot_id, hareket_tipi=hareket_tipi,
        )

    @staticmethod
    def create_hareket(
        db: Session,
        hareket_data: StokHareketiCreate,
        kullanici_id: int,
    ) -> StokHareketi:
        """
        Yeni stok hareketi oluştur.
        - hareket_tipi 'giris' veya 'cikis' değilse BadRequestError
        - miktar <= 0 ise BadRequestError
        - Ürün bulunamazsa NotFoundError
        - CRUD seviyesinde ValueError → BadRequestError'a çevrilir
        """
        if hareket_data.hareket_tipi not in ("giris", "cikis"):
            raise BadRequestError("Hareket tipi 'giris' veya 'cikis' olmalıdır")

        if hareket_data.miktar <= 0:
            raise BadRequestError("Miktar 0'dan büyük olmalıdır")

        urun = crud.get_urun(db, hareket_data.urun_id)
        if not urun:
            raise NotFoundError("Ürün", hareket_data.urun_id)

        try:
            return crud.create_stok_hareketi(db, hareket_data, kullanici_id=kullanici_id)
        except ValueError as e:
            raise BadRequestError(str(e))
