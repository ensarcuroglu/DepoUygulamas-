from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.repositories.talep_tahmini_repository import (
    CacheKaydi,
    ITalepTahminCacheRepository,
)
from models import TalepTahminCache


class SqlAlchemyTalepTahminCacheRepository(ITalepTahminCacheRepository):
    def __init__(self, db: Session):
        self._db = db

    def yaz(self, kayit: CacheKaydi) -> None:
        # Upsert: ayni (urun_id, tahmin_gun) varsa override
        mevcut = (
            self._db.query(TalepTahminCache)
            .filter(
                TalepTahminCache.urun_id == kayit.urun_id,
                TalepTahminCache.tahmin_gun == kayit.tahmin_gun,
            )
            .one_or_none()
        )
        if mevcut is None:
            mevcut = TalepTahminCache(
                urun_id=kayit.urun_id,
                tahmin_gun=kayit.tahmin_gun,
            )
            self._db.add(mevcut)

        mevcut.payload = kayit.payload
        mevcut.stok_riski = kayit.stok_riski
        mevcut.tahmini_talep = kayit.tahmini_talep
        mevcut.onerilen_ikmal = kayit.onerilen_ikmal
        mevcut.veri_guven_skoru = kayit.veri_guven_skoru
        mevcut.model_versiyonu = kayit.model_versiyonu
        mevcut.hesaplanma_tarihi = datetime.utcnow()
        self._db.flush()

    def getir(self, urun_id: int, tahmin_gun: int) -> Optional[CacheKaydi]:
        row = (
            self._db.query(TalepTahminCache)
            .filter(
                TalepTahminCache.urun_id == urun_id,
                TalepTahminCache.tahmin_gun == tahmin_gun,
            )
            .one_or_none()
        )
        return _to_kayit(row) if row else None

    def riskli_urunler(
        self,
        tahmin_gun: int,
        risk_seviyeleri: tuple[str, ...] = ("kritik", "dikkat"),
        limit: int = 50,
    ) -> list[CacheKaydi]:
        rows = (
            self._db.query(TalepTahminCache)
            .filter(
                TalepTahminCache.tahmin_gun == tahmin_gun,
                TalepTahminCache.stok_riski.in_(risk_seviyeleri),
            )
            .order_by(
                # kritik ustte
                TalepTahminCache.stok_riski.asc(),
                TalepTahminCache.onerilen_ikmal.desc(),
            )
            .limit(limit)
            .all()
        )
        return [_to_kayit(row) for row in rows]

    def temizle(self, gun_oncesi: int = 7) -> int:
        sinir = datetime.utcnow() - timedelta(days=gun_oncesi)
        silinen = (
            self._db.query(TalepTahminCache)
            .filter(TalepTahminCache.hesaplanma_tarihi < sinir)
            .delete(synchronize_session=False)
        )
        self._db.flush()
        return int(silinen)


def _to_kayit(row: TalepTahminCache) -> CacheKaydi:
    return CacheKaydi(
        urun_id=row.urun_id,
        tahmin_gun=row.tahmin_gun,
        payload=row.payload,
        stok_riski=row.stok_riski,
        tahmini_talep=float(row.tahmini_talep or 0),
        onerilen_ikmal=float(row.onerilen_ikmal or 0),
        veri_guven_skoru=float(row.veri_guven_skoru or 0),
        model_versiyonu=row.model_versiyonu,
        hesaplanma_tarihi=row.hesaplanma_tarihi.date()
        if isinstance(row.hesaplanma_tarihi, datetime)
        else row.hesaplanma_tarihi,
    )
