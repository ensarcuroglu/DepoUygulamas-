from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import or_

from app.core.entities.mal_kabul_irsaliye import MalKabulIrsaliye, MalKabulKalemi
from app.core.repositories.mal_kabul_irsaliye_repository import IMalKabulIrsaliyeRepository
from app.core.exceptions import KayitBulunamadiError
from app.infrastructure.persistence.mappers import (
    mal_kabul_irsaliye_to_entity,
    mal_kabul_irsaliye_to_orm,
    mal_kabul_kalemi_to_entity,
    mal_kabul_kalemi_to_orm,
)
from models import (
    MalKabulIrsaliye as MalKabulIrsaliyeORM,
    MalKabulKalemi as MalKabulKalemiORM,
)


class SqlAlchemyMalKabulIrsaliyeRepository(IMalKabulIrsaliyeRepository):

    def __init__(self, db: Session):
        self._db = db

    def _base_query(self, detay_getir: bool = True):
        # Temel ilişkiler her zaman yüklensin (Header bilgileri)
        query = self._db.query(MalKabulIrsaliyeORM).options(
            joinedload(MalKabulIrsaliyeORM.tedarikci),
            joinedload(MalKabulIrsaliyeORM.depo),
        )
        
        # Sadece detay istendiğinde kalemleri ve alt ilişkilerini yükle
        if detay_getir:
            query = query.options(
                # Bire-çok ilişki olduğu için joinedload yerine selectinload kullanıyoruz!
                selectinload(MalKabulIrsaliyeORM.kalemler).joinedload(MalKabulKalemiORM.urun),
                selectinload(MalKabulIrsaliyeORM.kalemler).joinedload(MalKabulKalemiORM.raf),
            )
        else:
            # Liste ekranı kalem satırlarını expand ediyor ve istisna sayaçlarını
            # gösteriyor. Bu nedenle kalemler yüklenir; alt ilişkiler yine alınmaz.
            query = query.options(selectinload(MalKabulIrsaliyeORM.kalemler))
            
        return query

    def getir_hepsi(
        self, skip: int = 0, limit: int = 100,
        durum: Optional[str] = None,
        arama: Optional[str] = None,
        depo_id: Optional[int] = None,
        tedarikci_id: Optional[int] = None,
    ) -> List[MalKabulIrsaliye]:
        # Liste ekranı olduğu için kalemleri YÜKLEME (Performans optimizasyonu)
        query = self._base_query(detay_getir=False)

        if durum:
            query = query.filter(MalKabulIrsaliyeORM.durum == durum)
        if depo_id:
            query = query.filter(MalKabulIrsaliyeORM.depo_id == depo_id)
        if tedarikci_id:
            query = query.filter(MalKabulIrsaliyeORM.tedarikci_id == tedarikci_id)
        if arama:
            query = query.filter(
                or_(
                    MalKabulIrsaliyeORM.irsaliye_no.ilike(f"%{arama}%"),
                    MalKabulIrsaliyeORM.tir_plaka.ilike(f"%{arama}%"),
                    MalKabulIrsaliyeORM.sofor_adi.ilike(f"%{arama}%"),
                )
            )

        orm_list = query.order_by(
            MalKabulIrsaliyeORM.olusturma_tarihi.desc()
        ).offset(skip).limit(limit).all()
        return [mal_kabul_irsaliye_to_entity(o) for o in orm_list]

    def getir_id_ile(self, irsaliye_id: int) -> Optional[MalKabulIrsaliye]:
        # Tekil detay sorgusu olduğu için kalemleri YÜKLE
        orm = self._base_query(detay_getir=True).filter(
            MalKabulIrsaliyeORM.id == irsaliye_id
        ).first()
        return mal_kabul_irsaliye_to_entity(orm) if orm else None

    def olustur(self, irsaliye: MalKabulIrsaliye, auto_commit: bool = False) -> MalKabulIrsaliye:
        orm = mal_kabul_irsaliye_to_orm(irsaliye)
        orm.id = None
        for kalem_orm in orm.kalemler:
            kalem_orm.id = None
        self._db.add(orm)
        
        # P0 Transaction kuralına uygun hale getirildi
        if auto_commit:
            self._db.commit()
            self._db.refresh(orm)
        else:
            self._db.flush()
            
        return mal_kabul_irsaliye_to_entity(orm)

    def guncelle(self, irsaliye: MalKabulIrsaliye, auto_commit: bool = False) -> MalKabulIrsaliye:
        # P0 kuralı gereği auto_commit varsayılan olarak False yapıldı
        orm = self._db.query(MalKabulIrsaliyeORM).filter(
            MalKabulIrsaliyeORM.id == irsaliye.id
        ).first()
        if not orm:
            raise KayitBulunamadiError("Mal Kabul İrsaliyesi", irsaliye.id)

        orm.tedarikci_id = irsaliye.tedarikci_id
        orm.depo_id = irsaliye.depo_id
        orm.tir_plaka = irsaliye.tir_plaka
        orm.sofor_adi = irsaliye.sofor_adi
        orm.durum = irsaliye.durum
        orm.tarih = irsaliye.tarih
        orm.guncelleme_tarihi = irsaliye.guncelleme_tarihi

        # Kalemler — senkronize et
        orm_kalem_map = {k.id: k for k in orm.kalemler if k.id}
        yeni_kalem_idler = {k.id for k in irsaliye.kalemler if k.id}

        # Silinen kalemleri kaldır
        for kalem_orm in list(orm.kalemler):
            if kalem_orm.id and kalem_orm.id not in yeni_kalem_idler:
                self._db.delete(kalem_orm)

        # Mevcut kalemleri güncelle veya yeni ekle
        for kalem_entity in irsaliye.kalemler:
            if kalem_entity.id and kalem_entity.id in orm_kalem_map:
                kalem_orm = orm_kalem_map[kalem_entity.id]
                kalem_orm.palet_no = kalem_entity.palet_no
                kalem_orm.urun_id = kalem_entity.urun_id
                kalem_orm.lot_no = kalem_entity.lot_no
                kalem_orm.miktar = kalem_entity.miktar
                kalem_orm.raf_id = kalem_entity.raf_id
                kalem_orm.durum = kalem_entity.durum
                kalem_orm.uretim_tarihi = kalem_entity.uretim_tarihi
                kalem_orm.son_kullanma_tarihi = kalem_entity.son_kullanma_tarihi
            else:
                yeni_orm = mal_kabul_kalemi_to_orm(kalem_entity)
                yeni_orm.id = None
                yeni_orm.mal_kabul_irsaliyesi_id = orm.id
                orm.kalemler.append(yeni_orm)

        if auto_commit:
            self._db.commit()
            self._db.refresh(orm)
        else:
            self._db.flush()
        return mal_kabul_irsaliye_to_entity(orm)

    def sil(self, irsaliye_id: int, auto_commit: bool = False) -> bool:
        orm = self._db.query(MalKabulIrsaliyeORM).filter(
            MalKabulIrsaliyeORM.id == irsaliye_id
        ).first()
        if not orm:
            return False
        self._db.delete(orm)
        
        # P0 Transaction kuralına uygun hale getirildi
        if auto_commit:
            self._db.commit()
        else:
            self._db.flush()
            
        return True

    def sonraki_irsaliye_no(self) -> str:
        yil = datetime.utcnow().year
        prefix = f"MKI-{yil}-"
        son = self._db.query(MalKabulIrsaliyeORM).filter(
            MalKabulIrsaliyeORM.irsaliye_no.startswith(prefix)
        ).order_by(MalKabulIrsaliyeORM.id.desc()).first()

        if son:
            try:
                son_no = int(son.irsaliye_no.split("-")[-1])
                yeni_no = son_no + 1
            except (ValueError, IndexError):
                yeni_no = 1
        else:
            yeni_no = 1

        return f"{prefix}{yeni_no:05d}"

    def kalem_guncelle(self, kalem_id: int, **kwargs) -> None:
        orm = self._db.query(MalKabulKalemiORM).filter(
            MalKabulKalemiORM.id == kalem_id
        ).first()
        if not orm:
            raise KayitBulunamadiError("Mal Kabul Kalemi", kalem_id)
        for alan, deger in kwargs.items():
            setattr(orm, alan, deger)
        self._db.commit()

    def getir_kalem_palet_no_ile(self, palet_no: str) -> Optional[MalKabulKalemi]:
        orm = self._db.query(MalKabulKalemiORM).options(
            joinedload(MalKabulKalemiORM.urun),
            joinedload(MalKabulKalemiORM.raf),
            joinedload(MalKabulKalemiORM.irsaliye).joinedload(MalKabulIrsaliyeORM.depo),
        ).filter(MalKabulKalemiORM.palet_no == palet_no).first()
        return mal_kabul_kalemi_to_entity(orm) if orm else None
