from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app.core.entities.toplama_gorevi import ToplamaGorevi, ToplamaGoreviDurum
from app.core.repositories.toplama_gorevi_repository import IToplamaGoreviRepository
from models import ToplamaGorevi as ToplamaGoreviORM, Palet, Lot, Urun, Kullanici


def _to_entity(orm: ToplamaGoreviORM) -> ToplamaGorevi:
    entity = ToplamaGorevi(
        id=orm.id,
        sevkiyat_id=orm.sevkiyat_id,
        palet_id=orm.palet_id,
        lot_id=orm.lot_id,
        urun_id=orm.urun_id,
        depo_id=orm.depo_id,
        atanan_kullanici_id=orm.atanan_kullanici_id,
        durum=orm.durum,
        fefo_override=orm.fefo_override,
        override_neden=orm.override_neden,
        override_kullanici_id=orm.override_kullanici_id,
        sira_no=orm.sira_no,
        olusturma_tarihi=orm.olusturma_tarihi,
        atanma_tarihi=orm.atanma_tarihi,
        baslama_tarihi=orm.baslama_tarihi,
        tamamlanma_tarihi=orm.tamamlanma_tarihi,
        iptal_nedeni=orm.iptal_nedeni,
    )
    # Görüntüleme alanlarını doldur
    palet = getattr(orm, "palet", None)
    if palet:
        entity.palet_no = palet.palet_no
        entity.koli_adedi = palet.koli_adedi
        lot = getattr(palet, "lot", None)
        if lot:
            entity.lot_no = lot.lot_no
            urun = getattr(lot, "urun", None)
            if urun:
                entity.urun_adi = urun.isim
    kullanici = getattr(orm, "atanan_kullanici", None)
    if kullanici:
        entity.atanan_kullanici_adi = kullanici.ad_soyad
    return entity


def _joinli_query(db: Session):
    return db.query(ToplamaGoreviORM).options(
        joinedload(ToplamaGoreviORM.palet)
        .joinedload(Palet.lot)
        .joinedload(Lot.urun),
        joinedload(ToplamaGoreviORM.atanan_kullanici),
    )


class SqlAlchemyToplamaGoreviRepository(IToplamaGoreviRepository):

    def __init__(self, db: Session):
        self._db = db

    def olustur(self, gorev: ToplamaGorevi, auto_commit: bool = True) -> ToplamaGorevi:
        orm = ToplamaGoreviORM(
            sevkiyat_id=gorev.sevkiyat_id,
            palet_id=gorev.palet_id,
            lot_id=gorev.lot_id,
            urun_id=gorev.urun_id,
            depo_id=gorev.depo_id,
            atanan_kullanici_id=gorev.atanan_kullanici_id,
            durum=gorev.durum,
            fefo_override=gorev.fefo_override,
            override_neden=gorev.override_neden,
            override_kullanici_id=gorev.override_kullanici_id,
            sira_no=gorev.sira_no,
            olusturma_tarihi=gorev.olusturma_tarihi,
        )
        self._db.add(orm)
        if auto_commit:
            self._db.commit()
            self._db.refresh(orm)
        else:
            self._db.flush()
        return _to_entity(orm)

    def guncelle(self, gorev: ToplamaGorevi, auto_commit: bool = True) -> Optional[ToplamaGorevi]:
        orm = self._db.query(ToplamaGoreviORM).filter(ToplamaGoreviORM.id == gorev.id).first()
        if not orm:
            return None
        orm.palet_id = gorev.palet_id
        orm.lot_id = gorev.lot_id
        orm.urun_id = gorev.urun_id
        orm.depo_id = gorev.depo_id
        orm.atanan_kullanici_id = gorev.atanan_kullanici_id
        orm.durum = gorev.durum
        orm.fefo_override = gorev.fefo_override
        orm.override_neden = gorev.override_neden
        orm.override_kullanici_id = gorev.override_kullanici_id
        orm.sira_no = gorev.sira_no
        orm.atanma_tarihi = gorev.atanma_tarihi
        orm.baslama_tarihi = gorev.baslama_tarihi
        orm.tamamlanma_tarihi = gorev.tamamlanma_tarihi
        orm.iptal_nedeni = gorev.iptal_nedeni
        if auto_commit:
            self._db.commit()
            self._db.refresh(orm)
        else:
            self._db.flush()
        return _to_entity(orm)

    def getir_id_ile(self, gorev_id: int) -> Optional[ToplamaGorevi]:
        orm = _joinli_query(self._db).filter(ToplamaGoreviORM.id == gorev_id).first()
        return _to_entity(orm) if orm else None

    def getir_hepsi(
        self,
        skip: int = 0,
        limit: int = 100,
        durum: Optional[str] = None,
        depo_id: Optional[int] = None,
        kullanici_id: Optional[int] = None,
        sevkiyat_id: Optional[int] = None,
    ) -> List[ToplamaGorevi]:
        q = _joinli_query(self._db)
        if durum:
            q = q.filter(ToplamaGoreviORM.durum == durum)
        if depo_id is not None:
            q = q.filter(ToplamaGoreviORM.depo_id == depo_id)
        if kullanici_id is not None:
            q = q.filter(ToplamaGoreviORM.atanan_kullanici_id == kullanici_id)
        if sevkiyat_id is not None:
            q = q.filter(ToplamaGoreviORM.sevkiyat_id == sevkiyat_id)
        q = q.order_by(ToplamaGoreviORM.sira_no.asc(), ToplamaGoreviORM.olusturma_tarihi.asc())
        return [_to_entity(o) for o in q.offset(skip).limit(limit).all()]

    def getir_next_bekleyen(self, depo_id: Optional[int] = None) -> Optional[ToplamaGorevi]:
        """Pull-based: sira_no ASC ilk Beklemede görevi döner.
        # TODO Faz 2: .with_for_update(skip_locked=True) eklenecek
        """
        q = self._db.query(ToplamaGoreviORM).filter(
            ToplamaGoreviORM.durum == ToplamaGoreviDurum.BEKLEMEDE
        )
        if depo_id is not None:
            q = q.filter(ToplamaGoreviORM.depo_id == depo_id)
        orm = q.order_by(
            ToplamaGoreviORM.sira_no.asc(),
            ToplamaGoreviORM.olusturma_tarihi.asc(),
        ).first()
        if not orm:
            return None
        return _to_entity(orm)

    def getir_sevkiyat_gorevleri(self, sevkiyat_id: int) -> List[ToplamaGorevi]:
        ormlar = (
            _joinli_query(self._db)
            .filter(ToplamaGoreviORM.sevkiyat_id == sevkiyat_id)
            .order_by(ToplamaGoreviORM.sira_no.asc())
            .all()
        )
        return [_to_entity(o) for o in ormlar]

    def gorev_var_mi(self, sevkiyat_id: int, palet_id: int) -> bool:
        return self._db.query(ToplamaGoreviORM).filter(
            ToplamaGoreviORM.sevkiyat_id == sevkiyat_id,
            ToplamaGoreviORM.palet_id == palet_id,
            ToplamaGoreviORM.durum != ToplamaGoreviDurum.IPTAL_EDILDI,
        ).first() is not None
