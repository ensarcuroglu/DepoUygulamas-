from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.core.entities.palet_rezervasyonu import PaletRezervasyonu, RezervasyonDurum
from app.core.repositories.palet_rezervasyonu_repository import IPaletRezervasyonuRepository
from models import PaletRezervasyonu as PaletRezervasyonuORM, Palet, Lot


def _to_entity(orm: PaletRezervasyonuORM) -> PaletRezervasyonu:
    entity = PaletRezervasyonu(
        id=orm.id,
        palet_id=orm.palet_id,
        siparis_id=orm.siparis_id,
        sevkiyat_kalemi_id=orm.sevkiyat_kalemi_id,
        durum=orm.durum,
        rezerve_tarihi=orm.rezerve_tarihi,
        kesinlesme_tarihi=orm.kesinlesme_tarihi,
        iptal_tarihi=orm.iptal_tarihi,
        iptal_nedeni=orm.iptal_nedeni,
    )
    palet = getattr(orm, "palet", None)
    if palet:
        entity.palet_no = palet.palet_no
        lot = getattr(palet, "lot", None)
        if lot:
            entity.lot_no = getattr(lot, "lot_no", None)
            urun = getattr(lot, "urun", None)
            if urun:
                entity.urun_adi = urun.isim
    siparis = getattr(orm, "siparis", None)
    if siparis:
        entity.siparis_no = getattr(siparis, "siparis_no", None)
    return entity


def _joinli_query(db: Session):
    return db.query(PaletRezervasyonuORM).options(
        joinedload(PaletRezervasyonuORM.palet)
        .joinedload(Palet.lot)
        .joinedload(Lot.urun),
        joinedload(PaletRezervasyonuORM.siparis),
    )


class SqlAlchemyPaletRezervasyonuRepository(IPaletRezervasyonuRepository):

    def __init__(self, db: Session):
        self._db = db

    def olustur(self, rezervasyon: PaletRezervasyonu, auto_commit: bool = True) -> PaletRezervasyonu:
        orm = PaletRezervasyonuORM(
            palet_id=rezervasyon.palet_id,
            siparis_id=rezervasyon.siparis_id,
            sevkiyat_kalemi_id=rezervasyon.sevkiyat_kalemi_id,
            durum=rezervasyon.durum,
            rezerve_tarihi=rezervasyon.rezerve_tarihi,
        )
        self._db.add(orm)
        if auto_commit:
            self._db.commit()
            self._db.refresh(orm)
        else:
            self._db.flush()
        return _to_entity(orm)

    def guncelle(self, rezervasyon: PaletRezervasyonu, auto_commit: bool = True) -> Optional[PaletRezervasyonu]:
        orm = self._db.query(PaletRezervasyonuORM).filter(
            PaletRezervasyonuORM.id == rezervasyon.id
        ).first()
        if not orm:
            return None
        orm.palet_id = rezervasyon.palet_id
        orm.durum = rezervasyon.durum
        orm.kesinlesme_tarihi = rezervasyon.kesinlesme_tarihi
        orm.iptal_tarihi = rezervasyon.iptal_tarihi
        orm.iptal_nedeni = rezervasyon.iptal_nedeni
        if auto_commit:
            self._db.commit()
            self._db.refresh(orm)
        else:
            self._db.flush()
        return _to_entity(orm)

    def getir_id_ile(self, rezervasyon_id: int) -> Optional[PaletRezervasyonu]:
        orm = _joinli_query(self._db).filter(
            PaletRezervasyonuORM.id == rezervasyon_id
        ).first()
        return _to_entity(orm) if orm else None

    def getir_hepsi(
        self,
        skip: int = 0,
        limit: int = 100,
        durum: Optional[str] = None,
        siparis_id: Optional[int] = None,
    ) -> List[PaletRezervasyonu]:
        q = _joinli_query(self._db)
        if durum:
            q = q.filter(PaletRezervasyonuORM.durum == durum)
        if siparis_id is not None:
            q = q.filter(PaletRezervasyonuORM.siparis_id == siparis_id)
        q = q.order_by(PaletRezervasyonuORM.rezerve_tarihi.desc())
        return [_to_entity(o) for o in q.offset(skip).limit(limit).all()]

    def getir_siparis_rezervasyonlari(self, siparis_id: int) -> List[PaletRezervasyonu]:
        ormlar = _joinli_query(self._db).filter(
            PaletRezervasyonuORM.siparis_id == siparis_id
        ).order_by(PaletRezervasyonuORM.rezerve_tarihi.desc()).all()
        return [_to_entity(o) for o in ormlar]

    def getir_aktif_by_siparis(self, siparis_id: int) -> List[PaletRezervasyonu]:
        ormlar = self._db.query(PaletRezervasyonuORM).filter(
            PaletRezervasyonuORM.siparis_id == siparis_id,
            PaletRezervasyonuORM.durum == RezervasyonDurum.AKTIF,
        ).all()
        return [_to_entity(o) for o in ormlar]

    def getir_aktif_by_palet(
        self,
        palet_id: int,
        with_lock: bool = False,
    ) -> Optional[PaletRezervasyonu]:
        q = self._db.query(PaletRezervasyonuORM).filter(
            PaletRezervasyonuORM.palet_id == palet_id,
            PaletRezervasyonuORM.durum == RezervasyonDurum.AKTIF,
        )
        if with_lock:
            q = q.with_for_update()
        orm = q.first()
        return _to_entity(orm) if orm else None

    def getir_by_sevkiyat_kalemi(self, sevkiyat_kalemi_id: int) -> Optional[PaletRezervasyonu]:
        orm = self._db.query(PaletRezervasyonuORM).filter(
            PaletRezervasyonuORM.sevkiyat_kalemi_id == sevkiyat_kalemi_id,
        ).first()
        return _to_entity(orm) if orm else None

    def rezerve_palet_idleri(self, urun_id: int) -> List[int]:
        """Ürüne ait Aktif rezervasyonlardaki palet ID'lerini döner."""
        from models import Palet as PaletORM, Lot as LotORM
        sonuclar = (
            self._db.query(PaletRezervasyonuORM.palet_id)
            .join(PaletORM, PaletRezervasyonuORM.palet_id == PaletORM.id)
            .join(LotORM, PaletORM.lot_id == LotORM.id)
            .filter(
                PaletRezervasyonuORM.durum == RezervasyonDurum.AKTIF,
                LotORM.urun_id == urun_id,
            )
            .all()
        )
        return [r[0] for r in sonuclar]
