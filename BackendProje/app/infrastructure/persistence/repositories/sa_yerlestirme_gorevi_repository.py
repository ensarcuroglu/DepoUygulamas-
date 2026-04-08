from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.core.entities.yerlestirme_gorevi import YerlestirmeGorevi, GorevDurum
from app.core.repositories.yerlestirme_gorevi_repository import IYerlestirmeGoreviRepository
from app.infrastructure.persistence.mappers.yerlestirme_mapper import (
    yerlestirme_gorevi_to_entity,
    yerlestirme_gorevi_to_orm,
)
from models import YerlestirmeGorevi as YerlestirmeGoreviORM, Palet, Lot, Urun, Raf, Zon
from datetime import datetime, timedelta


def _zenginlestir(orm: YerlestirmeGoreviORM, entity: YerlestirmeGorevi) -> YerlestirmeGorevi:
    """ORM ilişkilerinden görüntüleme alanlarını entity'ye yazar."""
    palet = getattr(orm, "palet", None)
    if palet:
        entity.palet_barkodu = palet.palet_no
        entity.miktar = palet.koli_adedi
        lot = getattr(palet, "lot", None)
        if lot:
            entity.lot_no = lot.lot_no
            urun = getattr(lot, "urun", None)
            if urun:
                entity.urun_adi = urun.isim

    onerilen_raf = getattr(orm, "onerilen_raf", None)
    if onerilen_raf:
        entity.onerilen_raf_kodu = onerilen_raf.kod
        zon = getattr(onerilen_raf, "zon", None)
        if zon:
            entity.zone_adi = zon.isim

    return entity


def _joinli_query(db: Session):
    return db.query(YerlestirmeGoreviORM).options(
        joinedload(YerlestirmeGoreviORM.palet)
        .joinedload(Palet.lot)
        .joinedload(Lot.urun),
        joinedload(YerlestirmeGoreviORM.onerilen_raf)
        .joinedload(Raf.zon),
    )


class SqlAlchemyYerlestirmeGoreviRepository(IYerlestirmeGoreviRepository):
    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(
        self,
        skip: int = 0,
        limit: int = 100,
        durum: Optional[str] = None,
        atanan_kullanici_id: Optional[int] = None,
        palet_id: Optional[int] = None,
    ) -> List[YerlestirmeGorevi]:
        q = _joinli_query(self._db)
        if durum:
            q = q.filter(YerlestirmeGoreviORM.durum == durum)
        if atanan_kullanici_id is not None:
            q = q.filter(YerlestirmeGoreviORM.atanan_kullanici_id == atanan_kullanici_id)
        if palet_id is not None:
            q = q.filter(YerlestirmeGoreviORM.palet_id == palet_id)
        q = q.order_by(
            YerlestirmeGoreviORM.oncelik.asc(),
            YerlestirmeGoreviORM.olusturma_tarihi.asc(),
        )
        return [_zenginlestir(o, yerlestirme_gorevi_to_entity(o)) for o in q.offset(skip).limit(limit).all()]

    def getir_id_ile(self, gorev_id: int) -> Optional[YerlestirmeGorevi]:
        orm = _joinli_query(self._db).filter(YerlestirmeGoreviORM.id == gorev_id).first()
        return _zenginlestir(orm, yerlestirme_gorevi_to_entity(orm)) if orm else None

    def olustur(self, gorev: YerlestirmeGorevi, auto_commit: bool = True) -> YerlestirmeGorevi:
        orm = yerlestirme_gorevi_to_orm(gorev)
        orm.id = None
        self._db.add(orm)
        
        if auto_commit:
            self._db.commit()
            self._db.refresh(orm)
        else:
            self._db.flush()
            
        return yerlestirme_gorevi_to_entity(orm)

    def guncelle(self, gorev: YerlestirmeGorevi, auto_commit: bool = True) -> YerlestirmeGorevi:
        orm = self._db.query(YerlestirmeGoreviORM).filter(YerlestirmeGoreviORM.id == gorev.id).first()
        if not orm:
            return None
            
        orm.tip = gorev.tip
        orm.kaynak_raf_id = gorev.kaynak_raf_id
        orm.onerilen_raf_id = gorev.onerilen_raf_id
        orm.gerceklesen_raf_id = gorev.gerceklesen_raf_id
        orm.durum = gorev.durum
        orm.oncelik = gorev.oncelik
        orm.atanan_kullanici_id = gorev.atanan_kullanici_id
        orm.override_kullanici_id = gorev.override_kullanici_id
        orm.override_neden = gorev.override_neden
        orm.atanma_tarihi = gorev.atanma_tarihi
        orm.baslama_tarihi = gorev.baslama_tarihi
        orm.tamamlanma_tarihi = gorev.tamamlanma_tarihi
        orm.iptal_nedeni = gorev.iptal_nedeni
        
        if auto_commit:
            self._db.commit()
            self._db.refresh(orm)
        else:
            self._db.flush()
            
        return yerlestirme_gorevi_to_entity(orm)

    def sonraki_gorevi_kilitle(self, kullanici_id: int, depo_id: Optional[int] = None) -> Optional[YerlestirmeGorevi]:
        """Pull-based FIFO: öncelik ASC, olusturma_tarihi ASC — SELECT FOR UPDATE."""
        q = self._db.query(YerlestirmeGoreviORM).filter(
            YerlestirmeGoreviORM.durum == GorevDurum.BEKLIYOR
        )
        if depo_id is not None:
            q = q.filter(YerlestirmeGoreviORM.depo_id == depo_id)
        orm = (
            q.order_by(
                YerlestirmeGoreviORM.oncelik.asc(),
                YerlestirmeGoreviORM.olusturma_tarihi.asc(),
            )
            .with_for_update(skip_locked=True)
            .first()
        )
        if not orm:
            return None

        orm.durum = GorevDurum.ATANDI
        orm.atanan_kullanici_id = kullanici_id
        orm.atanma_tarihi = datetime.utcnow()
        self._db.commit()
        self._db.refresh(orm)
        # Refresh sonrası ilişkileri yükle
        self._db.expire(orm)
        orm = _joinli_query(self._db).filter(YerlestirmeGoreviORM.id == orm.id).first()
        return _zenginlestir(orm, yerlestirme_gorevi_to_entity(orm))

    def getir_zaman_asimi_gecmis(self, timeout_dk: int) -> List[YerlestirmeGorevi]:
        """ATANDI durumundaki ve timeout'u geçmiş görevleri döner."""
        sinir = datetime.utcnow() - timedelta(minutes=timeout_dk)
        ormlar = (
            self._db.query(YerlestirmeGoreviORM)
            .filter(
                YerlestirmeGoreviORM.durum == GorevDurum.ATANDI,
                YerlestirmeGoreviORM.atanma_tarihi <= sinir,
            )
            .all()
        )
        return [yerlestirme_gorevi_to_entity(o) for o in ormlar]

    def getir_irsaliye_id_ile(self, mal_kabul_irsaliye_id: int) -> List[YerlestirmeGorevi]:
        """Belirli bir mal kabul irsaliyesine ait tüm görevleri döner."""
        ormlar = (
            self._db.query(YerlestirmeGoreviORM)
            .filter(YerlestirmeGoreviORM.mal_kabul_irsaliye_id == mal_kabul_irsaliye_id)
            .all()
        )
        return [yerlestirme_gorevi_to_entity(o) for o in ormlar]
