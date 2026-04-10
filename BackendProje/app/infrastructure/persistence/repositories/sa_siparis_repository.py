from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.core.entities.siparis import Siparis
from app.core.repositories.siparis_repository import ISiparisRepository
from app.infrastructure.persistence.mappers import (
    siparis_to_entity, siparis_kalemi_to_orm,
)
from models import Siparis as SiparisORM


class SqlAlchemySiparisRepository(ISiparisRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(
        self, skip: int = 0, limit: int = 100,
        durum: Optional[str] = None,
        arama: Optional[str] = None,
    ) -> List[Siparis]:
        query = self._db.query(SiparisORM).options(
            joinedload(SiparisORM.kalemler),
            joinedload(SiparisORM.olusturan_kullanici),
        )

        if durum:
            query = query.filter(SiparisORM.durum == durum)

        if arama:
            query = query.filter(
                or_(
                    SiparisORM.siparis_no.ilike(f"%{arama}%"),
                    SiparisORM.musteri_adi.ilike(f"%{arama}%"),
                )
            )

        orm_list = query.order_by(
            SiparisORM.olusturma_tarihi.desc()
        ).offset(skip).limit(limit).all()
        return [siparis_to_entity(o) for o in orm_list]

    def getir_id_ile(self, siparis_id: int) -> Optional[Siparis]:
        orm = self._db.query(SiparisORM).options(
            joinedload(SiparisORM.kalemler),
            joinedload(SiparisORM.olusturan_kullanici),
        ).filter(SiparisORM.id == siparis_id).first()
        return siparis_to_entity(orm) if orm else None

    def olustur(self, siparis: Siparis) -> Siparis:
        orm = SiparisORM(
            siparis_no=siparis.siparis_no,
            musteri_adi=siparis.musteri_adi,
            teslimat_adresi=siparis.teslimat_adresi,
            teslimat_tarihi=siparis.teslimat_tarihi,
            durum=siparis.durum,
            top_miktar=siparis.top_miktar,
            top_tutar=siparis.top_tutar,
            notlar=siparis.notlar,
            olusturan_kullanici_id=siparis.olusturan_kullanici_id,
            aktif=siparis.aktif,
        )

        for kalem in siparis.kalemler:
            orm.kalemler.append(siparis_kalemi_to_orm(kalem))

        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return siparis_to_entity(orm)

    def guncelle(self, siparis: Siparis) -> Siparis:
        orm = self._db.query(SiparisORM).filter(SiparisORM.id == siparis.id).first()
        if not orm:
            return None
        orm.musteri_adi = siparis.musteri_adi
        orm.teslimat_adresi = siparis.teslimat_adresi
        orm.teslimat_tarihi = siparis.teslimat_tarihi
        orm.durum = siparis.durum
        orm.top_miktar = siparis.top_miktar
        orm.top_tutar = siparis.top_tutar
        orm.notlar = siparis.notlar
        orm.aktif = siparis.aktif
        orm.guncelleme_tarihi = siparis.guncelleme_tarihi
        self._db.commit()
        self._db.refresh(orm)
        return siparis_to_entity(orm)

    def sil(self, siparis_id: int) -> bool:
        orm = self._db.query(SiparisORM).filter(SiparisORM.id == siparis_id).first()
        if not orm:
            return False
        orm.aktif = False
        self._db.commit()
        return True

    def sonraki_siparis_no(self) -> str:
        yil = datetime.utcnow().year
        prefix = f"SIP-{yil}-"
        son_siparis = self._db.query(SiparisORM).filter(
            SiparisORM.siparis_no.startswith(prefix)
        ).order_by(SiparisORM.id.desc()).first()

        if son_siparis:
            try:
                son_no = int(son_siparis.siparis_no.split("-")[-1])
                yeni_no = son_no + 1
            except (ValueError, IndexError):
                yeni_no = 1
        else:
            yeni_no = 1

        return f"{prefix}{yeni_no:04d}"
