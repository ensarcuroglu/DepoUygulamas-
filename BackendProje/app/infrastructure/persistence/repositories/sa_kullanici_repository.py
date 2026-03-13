from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.entities.kullanici import Kullanici
from app.core.repositories.kullanici_repository import IKullaniciRepository
from app.infrastructure.persistence.mappers import kullanici_to_entity, kullanici_to_orm
from models import Kullanici as KullaniciORM


class SqlAlchemyKullaniciRepository(IKullaniciRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(self, skip: int = 0, limit: int = 100) -> List[Kullanici]:
        orm_list = self._db.query(KullaniciORM).offset(skip).limit(limit).all()
        return [kullanici_to_entity(o) for o in orm_list]

    def getir_id_ile(self, kullanici_id: int) -> Optional[Kullanici]:
        orm = self._db.query(KullaniciORM).filter(KullaniciORM.id == kullanici_id).first()
        return kullanici_to_entity(orm) if orm else None

    def getir_kullanici_adi_ile(self, kullanici_adi: str) -> Optional[Kullanici]:
        orm = self._db.query(KullaniciORM).filter(
            KullaniciORM.kullanici_adi == kullanici_adi
        ).first()
        return kullanici_to_entity(orm) if orm else None

    def olustur(self, kullanici: Kullanici) -> Kullanici:
        orm = kullanici_to_orm(kullanici)
        orm.id = None
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return kullanici_to_entity(orm)

    def guncelle(self, kullanici: Kullanici) -> Kullanici:
        orm = self._db.query(KullaniciORM).filter(KullaniciORM.id == kullanici.id).first()
        if not orm:
            return None
        orm.kullanici_adi = kullanici.kullanici_adi
        orm.sifre_hash = kullanici.sifre_hash
        orm.ad_soyad = kullanici.ad_soyad
        orm.rol = kullanici.rol
        orm.telefon = kullanici.telefon
        orm.email = kullanici.email
        orm.departman = kullanici.departman
        orm.sicil_no = kullanici.sicil_no
        orm.kart_numarasi = kullanici.kart_numarasi
        orm.refresh_token_hash = kullanici.refresh_token_hash
        orm.refresh_token_son_kullanim = kullanici.refresh_token_son_kullanim
        self._db.commit()
        self._db.refresh(orm)
        return kullanici_to_entity(orm)

    def sil(self, kullanici_id: int) -> bool:
        orm = self._db.query(KullaniciORM).filter(KullaniciORM.id == kullanici_id).first()
        if not orm:
            return False
        self._db.delete(orm)
        self._db.commit()
        return True
