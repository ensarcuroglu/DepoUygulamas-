from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.core.entities.palet_etiket import PaletEtiket
from app.core.repositories.palet_etiket_repository import IPaletEtiketRepository
from models import PaletEtiket as PaletEtiketORM


def _to_entity(orm: PaletEtiketORM) -> PaletEtiket:
    sablon_ad = None
    palet_no = None
    if getattr(orm, "sablon", None):
        sablon_ad = orm.sablon.ad
    if getattr(orm, "palet", None):
        palet_no = orm.palet.palet_no
    return PaletEtiket(
        id=orm.id,
        palet_id=orm.palet_id,
        sablon_id=orm.sablon_id,
        render_edilmis_zpl=orm.render_edilmis_zpl,
        render_edilmis_html=orm.render_edilmis_html,
        barkod_deger=orm.barkod_deger,
        qr_deger=orm.qr_deger,
        basim_sayisi=orm.basim_sayisi,
        son_basim_tarihi=orm.son_basim_tarihi,
        kullanici_id=orm.kullanici_id,
        olusturma_tarihi=orm.olusturma_tarihi,
        sablon_ad=sablon_ad,
        palet_no=palet_no,
    )


class SqlAlchemyPaletEtiketRepository(IPaletEtiketRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi_palet_id_ile(self, palet_id: int) -> List[PaletEtiket]:
        orm_list = (
            self._db.query(PaletEtiketORM)
            .options(joinedload(PaletEtiketORM.sablon), joinedload(PaletEtiketORM.palet))
            .filter(PaletEtiketORM.palet_id == palet_id)
            .order_by(PaletEtiketORM.olusturma_tarihi.desc())
            .all()
        )
        return [_to_entity(o) for o in orm_list]

    def getir_id_ile(self, etiket_id: int) -> Optional[PaletEtiket]:
        orm = (
            self._db.query(PaletEtiketORM)
            .options(joinedload(PaletEtiketORM.sablon), joinedload(PaletEtiketORM.palet))
            .filter(PaletEtiketORM.id == etiket_id)
            .first()
        )
        return _to_entity(orm) if orm else None

    def olustur(self, etiket: PaletEtiket) -> PaletEtiket:
        orm = PaletEtiketORM(
            palet_id=etiket.palet_id,
            sablon_id=etiket.sablon_id,
            render_edilmis_zpl=etiket.render_edilmis_zpl,
            render_edilmis_html=etiket.render_edilmis_html,
            barkod_deger=etiket.barkod_deger,
            qr_deger=etiket.qr_deger,
            basim_sayisi=etiket.basim_sayisi,
            son_basim_tarihi=etiket.son_basim_tarihi,
            kullanici_id=etiket.kullanici_id,
        )
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return _to_entity(orm)

    def guncelle(self, etiket: PaletEtiket) -> Optional[PaletEtiket]:
        orm = self._db.query(PaletEtiketORM).filter(PaletEtiketORM.id == etiket.id).first()
        if not orm:
            return None
        orm.basim_sayisi = etiket.basim_sayisi
        orm.son_basim_tarihi = etiket.son_basim_tarihi
        self._db.commit()
        self._db.refresh(orm)
        return _to_entity(orm)
