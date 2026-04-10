from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.entities.tedarikci import Tedarikci
from app.core.repositories.tedarikci_repository import ITedarikciRepository
from app.infrastructure.persistence.mappers import tedarikci_to_entity, tedarikci_to_orm
from models import Tedarikci as TedarikciORM


class SqlAlchemyTedarikciRepository(ITedarikciRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(self, skip: int = 0, limit: int = 100, sadece_aktif: bool = True) -> List[Tedarikci]:
        query = self._db.query(TedarikciORM)
        if sadece_aktif:
            query = query.filter(TedarikciORM.aktif)
        return [tedarikci_to_entity(o) for o in query.offset(skip).limit(limit).all()]

    def getir_id_ile(self, tedarikci_id: int) -> Optional[Tedarikci]:
        orm = self._db.query(TedarikciORM).filter(TedarikciORM.id == tedarikci_id).first()
        return tedarikci_to_entity(orm) if orm else None

    def olustur(self, tedarikci: Tedarikci) -> Tedarikci:
        orm = tedarikci_to_orm(tedarikci)
        orm.id = None  # type: ignore[assignment]
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return tedarikci_to_entity(orm)

    def guncelle(self, tedarikci: Tedarikci) -> "Optional[Tedarikci]":
        orm = self._db.query(TedarikciORM).filter(TedarikciORM.id == tedarikci.id).first()
        if not orm:
            return None
        orm.firma_adi = tedarikci.firma_adi
        orm.iletisim_kisi = tedarikci.iletisim_kisi
        orm.telefon = tedarikci.telefon
        orm.email = tedarikci.email
        orm.adres = tedarikci.adres
        orm.vergi_no = tedarikci.vergi_no
        orm.aktif = tedarikci.aktif
        self._db.commit()
        self._db.refresh(orm)
        return tedarikci_to_entity(orm)

    def sil(self, tedarikci_id: int) -> bool:
        orm = self._db.query(TedarikciORM).filter(TedarikciORM.id == tedarikci_id).first()
        if not orm:
            return False
        orm.aktif = False
        self._db.commit()
        return True
