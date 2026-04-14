from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.core.entities.irsaliye import Irsaliye
from app.core.repositories.irsaliye_repository import IIrsaliyeRepository
from app.infrastructure.persistence.mappers import irsaliye_to_entity, irsaliye_to_orm
from models import Irsaliye as IrsaliyeORM


class SqlAlchemyIrsaliyeRepository(IIrsaliyeRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(
        self, skip: int = 0, limit: int = 100,
        durum: Optional[str] = None,
        arama: Optional[str] = None,
    ) -> List[Irsaliye]:
        query = self._db.query(IrsaliyeORM).options(
            joinedload(IrsaliyeORM.siparis),
        )

        if durum:
            query = query.filter(IrsaliyeORM.durum == durum)

        if arama:
            query = query.filter(
                or_(
                    IrsaliyeORM.irsaliye_no.ilike(f"%{arama}%"),
                    IrsaliyeORM.tir_plaka.ilike(f"%{arama}%"),
                )
            )

        orm_list = query.order_by(
            IrsaliyeORM.olusturma_tarihi.desc()
        ).offset(skip).limit(limit).all()
        return [irsaliye_to_entity(o) for o in orm_list]

    def getir_id_ile(self, irsaliye_id: int) -> Optional[Irsaliye]:
        orm = self._db.query(IrsaliyeORM).options(
            joinedload(IrsaliyeORM.siparis),
        ).filter(IrsaliyeORM.id == irsaliye_id).first()
        return irsaliye_to_entity(orm) if orm else None

    def olustur(self, irsaliye: Irsaliye, auto_commit: bool = True) -> Irsaliye:
        orm = irsaliye_to_orm(irsaliye)
        orm.id = None  # type: ignore[assignment]
        self._db.add(orm)
        self._db.flush()
        if auto_commit:
            self._db.commit()
        self._db.refresh(orm)
        return irsaliye_to_entity(orm)

    def guncelle(self, irsaliye: Irsaliye, auto_commit: bool = True) -> "Optional[Irsaliye]":
        orm = self._db.query(IrsaliyeORM).filter(IrsaliyeORM.id == irsaliye.id).first()
        if not orm:
            return None
        orm.siparis_id = irsaliye.siparis_id
        orm.sevkiyat_id = irsaliye.sevkiyat_id
        orm.irsaliye_tarihi = irsaliye.irsaliye_tarihi  # type: ignore[assignment]
        orm.belge_turu = irsaliye.belge_turu
        orm.tir_plaka = irsaliye.tir_plaka
        orm.sofor_adi = irsaliye.sofor_adi
        orm.durum = irsaliye.durum
        orm.guncelleme_tarihi = irsaliye.guncelleme_tarihi
        self._db.flush()
        if auto_commit:
            self._db.commit()
        self._db.refresh(orm)
        return irsaliye_to_entity(orm)

    def sonraki_irsaliye_no(self) -> str:
        yil = datetime.utcnow().year
        prefix = f"IRS-{yil}-"
        son_irsaliye = self._db.query(IrsaliyeORM).filter(
            IrsaliyeORM.irsaliye_no.startswith(prefix)
        ).order_by(IrsaliyeORM.id.desc()).first()

        if son_irsaliye:
            try:
                son_no = int(son_irsaliye.irsaliye_no.split("-")[-1])
                yeni_no = son_no + 1
            except (ValueError, IndexError):
                yeni_no = 1
        else:
            yeni_no = 1

        return f"{prefix}{yeni_no:04d}"

    def sevkiyat_icin_irsaliye_var_mi(self, sevkiyat_id: int) -> bool:
        subq = (
            self._db.query(IrsaliyeORM)
            .filter(IrsaliyeORM.sevkiyat_id == sevkiyat_id)
            .exists()
        )
        return self._db.query(subq).scalar()
