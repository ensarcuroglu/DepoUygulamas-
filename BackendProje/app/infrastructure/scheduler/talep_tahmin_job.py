"""
Talep Tahmini Nightly Precompute Job — Infrastructure katmani.

APScheduler ile her gece (varsayilan 02:00 TR) tum aktif urunler icin
7 / 30 / 90 gunluk talep tahmini hesaplar ve `talep_tahmin_cache`
tablosuna upsert eder. Sabah satin almaci frontend'i actiginda
`/riskli-urunler` ve urun bazli grafik bu cache'ten okunur.
"""

from __future__ import annotations

import logging
from datetime import date

from database import SessionLocal
from app.application.dto.talep_tahmini_dto import TalepTahminResponseDTO
from app.application.use_cases import TalepTahminiGetirUseCase
from app.core.repositories.talep_tahmini_repository import CacheKaydi
from app.infrastructure.persistence.repositories import (
    SqlAlchemyTalepTahminCacheRepository,
    SqlAlchemyTalepTahminiRepository,
)

logger = logging.getLogger(__name__)


TAHMIN_UFKLARI: tuple[int, ...] = (7, 30, 90)
ESKI_KAYIT_GUN = 14


def talep_tahmin_precompute() -> None:
    """Tum aktif urunler icin tahminleri hesaplayip cache'e yazar."""
    # DI lifecycle'ini scheduler context'i bagimsiz tutmak icin elle olustur
    from app.infrastructure.di.modules.talep_tahmini_di import (
        get_talep_tahmin_predictor,
    )
    from ml_models.talep_tahmin.application import PredictDemandUseCase

    predictor = get_talep_tahmin_predictor()
    predict_uc = PredictDemandUseCase(predictor)

    db = SessionLocal()
    try:
        repo = SqlAlchemyTalepTahminiRepository(db)
        cache_repo = SqlAlchemyTalepTahminCacheRepository(db)
        getir_uc = TalepTahminiGetirUseCase(repo, predict_uc)

        urun_idleri = repo.aktif_urun_idleri()
        toplam = len(urun_idleri)
        logger.info("Talep tahmini precompute basladi: %d urun.", toplam)

        basarili = 0
        hatali = 0
        for urun_id in urun_idleri:
            for ufuk in TAHMIN_UFKLARI:
                try:
                    sonuc = getir_uc.execute(urun_id=urun_id, tahmin_gun=ufuk)
                    cache_repo.yaz(_response_to_kayit(urun_id, ufuk, sonuc))
                    basarili += 1
                except Exception as exc:
                    hatali += 1
                    logger.warning(
                        "Talep tahmini hesaplanamadi urun_id=%s ufuk=%s: %s",
                        urun_id,
                        ufuk,
                        exc,
                    )
                    db.rollback()
            # Urun bazinda commit — bir urunun hatasi digerlerini etkilemesin
            db.commit()

        # Eski cache temizligi
        silinen = cache_repo.temizle(gun_oncesi=ESKI_KAYIT_GUN)
        db.commit()

        logger.info(
            "Talep tahmini precompute bitti: basarili=%d, hatali=%d, eski_temizlendi=%d.",
            basarili,
            hatali,
            silinen,
        )
    except Exception as exc:
        logger.error("Talep tahmini precompute job hatasi: %s", exc)
        db.rollback()
    finally:
        db.close()


def _response_to_kayit(
    urun_id: int,
    tahmin_gun: int,
    sonuc: TalepTahminResponseDTO,
) -> CacheKaydi:
    return CacheKaydi(
        urun_id=urun_id,
        tahmin_gun=tahmin_gun,
        payload=sonuc.model_dump(mode="json"),
        stok_riski=sonuc.stok_riski,
        tahmini_talep=float(sonuc.tahmini_talep),
        onerilen_ikmal=float(sonuc.onerilen_ikmal_miktari),
        veri_guven_skoru=float(sonuc.veri_guven_skoru),
        model_versiyonu=sonuc.model_versiyonu or "unknown",
        hesaplanma_tarihi=date.today(),
    )
