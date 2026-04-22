from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.entities.etiket_sablonu import EtiketSablonu
from app.core.repositories.etiket_sablonu_repository import IEtiketSablonuRepository
from models import EtiketSablonu as EtiketSablonuORM


def _to_entity(orm: EtiketSablonuORM) -> EtiketSablonu:
    return EtiketSablonu(
        id=orm.id,
        ad=orm.ad,
        boyut=orm.boyut,
        zpl_template=orm.zpl_template,
        html_template=orm.html_template,
        default_mi=bool(orm.default_mi),
        aktif=bool(orm.aktif),
        olusturan_id=orm.olusturan_id,
        olusturma_tarihi=orm.olusturma_tarihi,
    )


def _apply_to_orm(orm: EtiketSablonuORM, e: EtiketSablonu) -> None:
    orm.ad = e.ad
    orm.boyut = e.boyut
    orm.zpl_template = e.zpl_template
    orm.html_template = e.html_template
    orm.default_mi = e.default_mi
    orm.aktif = e.aktif
    if e.olusturan_id is not None:
        orm.olusturan_id = e.olusturan_id


class SqlAlchemyEtiketSablonuRepository(IEtiketSablonuRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(
        self, skip: int = 0, limit: int = 100, sadece_aktif: bool = True
    ) -> List[EtiketSablonu]:
        q = self._db.query(EtiketSablonuORM)
        if sadece_aktif:
            q = q.filter(EtiketSablonuORM.aktif)
        orm_list = q.order_by(EtiketSablonuORM.default_mi.desc(), EtiketSablonuORM.id.desc()).offset(skip).limit(limit).all()
        return [_to_entity(o) for o in orm_list]

    def getir_id_ile(self, sablon_id: int) -> Optional[EtiketSablonu]:
        orm = self._db.query(EtiketSablonuORM).filter(EtiketSablonuORM.id == sablon_id).first()
        return _to_entity(orm) if orm else None

    def getir_default(self) -> Optional[EtiketSablonu]:
        orm = (
            self._db.query(EtiketSablonuORM)
            .filter(EtiketSablonuORM.default_mi, EtiketSablonuORM.aktif)
            .first()
        )
        return _to_entity(orm) if orm else None

    def olustur(self, sablon: EtiketSablonu) -> EtiketSablonu:
        orm = EtiketSablonuORM(
            ad=sablon.ad,
            boyut=sablon.boyut,
            zpl_template=sablon.zpl_template,
            html_template=sablon.html_template,
            default_mi=sablon.default_mi,
            aktif=sablon.aktif,
            olusturan_id=sablon.olusturan_id,
        )
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return _to_entity(orm)

    def guncelle(self, sablon: EtiketSablonu) -> Optional[EtiketSablonu]:
        orm = self._db.query(EtiketSablonuORM).filter(EtiketSablonuORM.id == sablon.id).first()
        if not orm:
            return None
        _apply_to_orm(orm, sablon)
        self._db.commit()
        self._db.refresh(orm)
        return _to_entity(orm)

    def sil(self, sablon_id: int) -> bool:
        orm = self._db.query(EtiketSablonuORM).filter(EtiketSablonuORM.id == sablon_id).first()
        if not orm:
            return False
        # Soft delete
        orm.aktif = False
        orm.default_mi = False
        self._db.commit()
        return True

    def default_sifirla(self, haric_id: Optional[int] = None) -> None:
        q = self._db.query(EtiketSablonuORM).filter(EtiketSablonuORM.default_mi)
        if haric_id is not None:
            q = q.filter(EtiketSablonuORM.id != haric_id)
        for orm in q.all():
            orm.default_mi = False
        self._db.commit()
