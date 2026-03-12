"""
Ürün İşlemleri — Service Layer
CRUD'un üstüne business logic ve standardize hata yönetimi ekler.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import Urun, Lot, Palet
from schemas import UrunCreate, UrunUpdate
from core.exceptions import NotFoundError, DuplicateError
import crud


class UrunService:

    @staticmethod
    def get_urun(db: Session, urun_id: int) -> Urun:
        """ID'ye göre ürün getir; bulunamazsa NotFoundError fırlatır."""
        urun = crud.get_urun(db, urun_id)
        if not urun:
            raise NotFoundError("Ürün", urun_id)
        return urun

    @staticmethod
    def get_urun_by_barkod(db: Session, barkod: str) -> Optional[Urun]:
        """Barkod'a göre ürün getir; None dönebilir."""
        return crud.get_urun_by_barkod(db, barkod=barkod)

    @staticmethod
    def get_urunler(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        kategori_id: Optional[int] = None,
        marka_id: Optional[int] = None,
    ) -> List[Urun]:
        """Ürün listesi; arama, kategori ve marka filtresi destekler."""
        return crud.get_urunler(
            db, skip=skip, limit=limit,
            search=search, kategori_id=kategori_id, marka_id=marka_id,
        )

    @staticmethod
    def get_kritik_urunler(db: Session) -> List[Urun]:
        """Min stok seviyesinin altındaki ürünleri döner."""
        return crud.get_kritik_urunler(db)

    @staticmethod
    def create_urun(db: Session, urun_data: UrunCreate, kullanici_id: int) -> Urun:
        """Yeni ürün oluştur; ad ve barkod mükerrer ise DuplicateError fırlatır."""
        existing = db.query(Urun).filter(
            Urun.adi == urun_data.adi, Urun.aktif == True
        ).first()
        if existing:
            raise DuplicateError("Ürün adı", urun_data.adi)

        if urun_data.barkod:
            existing_barkod = db.query(Urun).filter(
                Urun.barkod == urun_data.barkod
            ).first()
            if existing_barkod:
                raise DuplicateError("Barkod", urun_data.barkod)

        return crud.create_urun(db, urun_data, kullanici_id=kullanici_id)

    @staticmethod
    def update_urun(db: Session, urun_id: int, urun_data: UrunUpdate, kullanici_id: int) -> Urun:
        """Ürün güncelle; bulunamazsa NotFoundError fırlatır."""
        UrunService.get_urun(db, urun_id)  # varlık kontrolü
        db_urun = crud.update_urun(db, urun_id, urun_data, kullanici_id=kullanici_id)
        return db_urun

    @staticmethod
    def delete_urun(db: Session, urun_id: int, kullanici_id: int) -> bool:
        """Ürün soft-delete; bulunamazsa NotFoundError fırlatır."""
        UrunService.get_urun(db, urun_id)  # varlık kontrolü
        return crud.delete_urun(db, urun_id, kullanici_id=kullanici_id)

    @staticmethod
    def get_urun_stok(db: Session, urun_id: int) -> int:
        """Ürünün aktif palet üzerinden toplam stok miktarını hesaplar."""
        toplam = (
            db.query(func.sum(Palet.koli_adedi))
            .join(Lot, Lot.id == Palet.lot_id)
            .filter(
                Lot.urun_id == urun_id,
                Lot.aktif == True,
                Palet.aktif == True,
            )
            .scalar() or 0
        )
        return int(toplam)
