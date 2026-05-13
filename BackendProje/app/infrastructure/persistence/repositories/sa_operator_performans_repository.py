"""SQLAlchemy implementasyonları — Operatör Performans (LMS).

İki repository:
  SqlAlchemyGorevPerformansEventRepository — outbox event log
  SqlAlchemyOperatorVardiyaMetrikleriRepository — vardiya KPI özeti
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.entities.operator_performans import (
    GorevPerformansEvent,
    OperatorVardiyaMetrikleri,
)
from app.core.repositories.operator_performans_repository import (
    IGorevPerformansEventRepository,
    IOperatorVardiyaMetrikleriRepository,
)
from app.infrastructure.persistence.mappers.operator_performans_mapper import (
    gorev_performans_event_to_entity,
    gorev_performans_event_to_orm,
    operator_vardiya_to_entity,
)
from models import (
    Depo,
    GorevPerformansEvent as GorevPerformansEventORM,
    Kullanici,
    OperatorVardiyaMetrikleri as OperatorVardiyaMetrikleriORM,
)


class SqlAlchemyGorevPerformansEventRepository(IGorevPerformansEventRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def olustur(
        self, event: GorevPerformansEvent, auto_commit: bool = False
    ) -> GorevPerformansEvent:
        orm = gorev_performans_event_to_orm(event)
        self._db.add(orm)
        if auto_commit:
            self._db.commit()
            self._db.refresh(orm)
        else:
            self._db.flush()
        return gorev_performans_event_to_entity(orm)

    def bekleyen_eventleri_getir(self, limit: int = 500) -> List[GorevPerformansEvent]:
        ormlar = (
            self._db.query(GorevPerformansEventORM)
            .filter(GorevPerformansEventORM.aggregate_edildi.is_(False))
            .order_by(GorevPerformansEventORM.olusturma_tarihi.asc())
            .limit(limit)
            .all()
        )
        return [gorev_performans_event_to_entity(o) for o in ormlar]

    def aggregate_edildi_isaretle(
        self, event_idleri: List[int], auto_commit: bool = True
    ) -> int:
        if not event_idleri:
            return 0
        guncellenen = (
            self._db.query(GorevPerformansEventORM)
            .filter(GorevPerformansEventORM.id.in_(event_idleri))
            .update({"aggregate_edildi": True}, synchronize_session=False)
        )
        if auto_commit:
            self._db.commit()
        else:
            self._db.flush()
        return guncellenen

    def yayinlanmamis_eventleri_getir(
        self, limit: int = 100
    ) -> List[GorevPerformansEvent]:
        ormlar = (
            self._db.query(GorevPerformansEventORM)
            .filter(GorevPerformansEventORM.rabbitmq_yayinlandi.is_(False))
            .order_by(GorevPerformansEventORM.olusturma_tarihi.asc())
            .limit(limit)
            .all()
        )
        return [gorev_performans_event_to_entity(o) for o in ormlar]

    def yayinlandi_isaretle(
        self,
        event_id: int,
        yayin_tarihi: Optional[datetime] = None,
        auto_commit: bool = True,
    ) -> bool:
        tarih = yayin_tarihi or datetime.utcnow()
        guncellenen = (
            self._db.query(GorevPerformansEventORM)
            .filter(GorevPerformansEventORM.id == event_id)
            .update(
                {
                    "rabbitmq_yayinlandi": True,
                    "rabbitmq_yayin_tarihi": tarih,
                    "rabbitmq_son_hata": None,
                },
                synchronize_session=False,
            )
        )
        if auto_commit:
            self._db.commit()
        else:
            self._db.flush()
        return guncellenen > 0

    def yayin_hatasi_kaydet(
        self,
        event_id: int,
        hata: str,
        auto_commit: bool = True,
    ) -> bool:
        # Hata mesajını TEXT alanına sığacak şekilde kırp.
        kisa_hata = (hata or "")[:2000]
        guncellenen = (
            self._db.query(GorevPerformansEventORM)
            .filter(GorevPerformansEventORM.id == event_id)
            .update(
                {
                    "rabbitmq_deneme_sayisi":
                        GorevPerformansEventORM.rabbitmq_deneme_sayisi + 1,
                    "rabbitmq_son_hata": kisa_hata,
                },
                synchronize_session=False,
            )
        )
        if auto_commit:
            self._db.commit()
        else:
            self._db.flush()
        return guncellenen > 0


class SqlAlchemyOperatorVardiyaMetrikleriRepository(
    IOperatorVardiyaMetrikleriRepository
):
    def __init__(self, db: Session) -> None:
        self._db = db

    def upsert_artir(
        self,
        kullanici_id: int,
        vardiya_tarihi: date,
        depo_id: Optional[int],
        yerlestirme_delta: int = 0,
        toplama_delta: int = 0,
        iptal_delta: int = 0,
        sure_saniye_delta: int = 0,
        auto_commit: bool = True,
    ) -> OperatorVardiyaMetrikleri:
        orm: Optional[OperatorVardiyaMetrikleriORM] = (
            self._db.query(OperatorVardiyaMetrikleriORM)
            .filter(
                OperatorVardiyaMetrikleriORM.kullanici_id == kullanici_id,
                OperatorVardiyaMetrikleriORM.vardiya_tarihi == vardiya_tarihi,
            )
            .with_for_update()
            .first()
        )

        if orm is None:
            orm = OperatorVardiyaMetrikleriORM(
                kullanici_id=kullanici_id,
                depo_id=depo_id,
                vardiya_tarihi=vardiya_tarihi,
                tamamlanan_yerlestirme=max(0, yerlestirme_delta),
                tamamlanan_toplama=max(0, toplama_delta),
                iptal_sayisi=max(0, iptal_delta),
                toplam_aktif_saniye=max(0, sure_saniye_delta),
                ortalama_gorev_suresi_sn=0.0,
                son_guncelleme=datetime.utcnow(),
            )
            self._db.add(orm)
        else:
            orm.tamamlanan_yerlestirme = max(
                0, orm.tamamlanan_yerlestirme + yerlestirme_delta
            )
            orm.tamamlanan_toplama = max(
                0, orm.tamamlanan_toplama + toplama_delta
            )
            orm.iptal_sayisi = max(0, orm.iptal_sayisi + iptal_delta)
            orm.toplam_aktif_saniye = max(
                0, orm.toplam_aktif_saniye + sure_saniye_delta
            )
            if depo_id is not None and orm.depo_id is None:
                orm.depo_id = depo_id
            orm.son_guncelleme = datetime.utcnow()

        toplam_tamamlanan = orm.tamamlanan_yerlestirme + orm.tamamlanan_toplama
        if toplam_tamamlanan > 0 and orm.toplam_aktif_saniye > 0:
            orm.ortalama_gorev_suresi_sn = round(
                orm.toplam_aktif_saniye / toplam_tamamlanan, 2
            )
        else:
            orm.ortalama_gorev_suresi_sn = 0.0

        if auto_commit:
            self._db.commit()
            self._db.refresh(orm)
        else:
            self._db.flush()

        return operator_vardiya_to_entity(orm)

    def getir_kullanici_tarih_ile(
        self, kullanici_id: int, vardiya_tarihi: date
    ) -> Optional[OperatorVardiyaMetrikleri]:
        orm = (
            self._db.query(OperatorVardiyaMetrikleriORM)
            .filter(
                OperatorVardiyaMetrikleriORM.kullanici_id == kullanici_id,
                OperatorVardiyaMetrikleriORM.vardiya_tarihi == vardiya_tarihi,
            )
            .first()
        )
        return operator_vardiya_to_entity(orm) if orm else None

    def leaderboard_getir(
        self,
        vardiya_tarihi: date,
        depo_id: Optional[int] = None,
        limit: int = 20,
    ) -> List[OperatorVardiyaMetrikleri]:
        q = self._db.query(
            OperatorVardiyaMetrikleriORM,
            Kullanici.ad_soyad,
            Depo.isim,
        ).join(
            Kullanici, Kullanici.id == OperatorVardiyaMetrikleriORM.kullanici_id
        ).outerjoin(
            Depo, Depo.id == OperatorVardiyaMetrikleriORM.depo_id
        ).filter(
            OperatorVardiyaMetrikleriORM.vardiya_tarihi == vardiya_tarihi,
            OperatorVardiyaMetrikleriORM.toplam_aktif_saniye > 0,
        )

        if depo_id is not None:
            q = q.filter(OperatorVardiyaMetrikleriORM.depo_id == depo_id)

        sonuclar: List[OperatorVardiyaMetrikleri] = []
        for orm, ad_soyad, depo_adi in q.limit(max(limit * 5, 100)).all():
            entity = operator_vardiya_to_entity(orm)
            entity.operator_adi = ad_soyad
            entity.depo_adi = depo_adi
            sonuclar.append(entity)
        return sonuclar

    def getir_aralik(
        self,
        kullanici_id: Optional[int] = None,
        depo_id: Optional[int] = None,
        baslangic: Optional[date] = None,
        bitis: Optional[date] = None,
        skip: int = 0,
        limit: int = 200,
    ) -> List[OperatorVardiyaMetrikleri]:
        q = self._db.query(
            OperatorVardiyaMetrikleriORM,
            Kullanici.ad_soyad,
            Depo.isim,
        ).join(
            Kullanici, Kullanici.id == OperatorVardiyaMetrikleriORM.kullanici_id
        ).outerjoin(
            Depo, Depo.id == OperatorVardiyaMetrikleriORM.depo_id
        )

        if kullanici_id is not None:
            q = q.filter(OperatorVardiyaMetrikleriORM.kullanici_id == kullanici_id)
        if depo_id is not None:
            q = q.filter(OperatorVardiyaMetrikleriORM.depo_id == depo_id)
        if baslangic is not None:
            q = q.filter(OperatorVardiyaMetrikleriORM.vardiya_tarihi >= baslangic)
        if bitis is not None:
            q = q.filter(OperatorVardiyaMetrikleriORM.vardiya_tarihi <= bitis)

        q = q.order_by(
            OperatorVardiyaMetrikleriORM.vardiya_tarihi.desc(),
            OperatorVardiyaMetrikleriORM.kullanici_id.asc(),
        )

        sonuclar: List[OperatorVardiyaMetrikleri] = []
        for orm, ad_soyad, depo_adi in q.offset(skip).limit(limit).all():
            entity = operator_vardiya_to_entity(orm)
            entity.operator_adi = ad_soyad
            entity.depo_adi = depo_adi
            sonuclar.append(entity)
        return sonuclar
