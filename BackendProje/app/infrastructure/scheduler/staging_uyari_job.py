"""
Staging Uyarı Job — Infrastructure katmanı.

APScheduler ile günlük sabah 07:00'de çalışır.
Staging'de eşik saatten fazla bekleyen paletleri SistemLog'a yazar.
Eşik süresi STAGING_UYARI_ESIK_SAAT ortam değişkeniyle (varsayılan: 24) ayarlanabilir.
"""

import logging
from datetime import datetime, timedelta

from database import SessionLocal
from app.core.config import get_settings

logger = logging.getLogger(__name__)

def staging_uyari_kontrol() -> None:
    """Staging'de esik_saat'ten uzun bekleyen paletleri SistemLog'a kaydeder."""
    esik_saat = get_settings().staging_uyari_esik_saat
    esik_tarih = datetime.utcnow() - timedelta(hours=esik_saat)

    db = SessionLocal()
    try:
        from models import Palet as PaletORM, Raf as RafORM, SistemLog as SistemLogORM
        from app.core.entities.sistem_log import OlayTipi

        # Staging'de bekleyen aktif paletler
        rows = (
            db.query(
                PaletORM.id,
                PaletORM.palet_no,
                PaletORM.olusturma_tarihi,
                RafORM.depo_id,
            )
            .join(RafORM, RafORM.id == PaletORM.raf_id)
            .filter(
                RafORM.is_staging,
                PaletORM.aktif,
                PaletORM.olusturma_tarihi <= esik_tarih,
            )
            .all()
        )

        if not rows:
            logger.info("Staging uyarı: eşiği aşan palet yok.")
            return

        # Depo bazında grupla ve tek log yaz
        depo_sayac: dict[int, int] = {}
        for row in rows:
            depo_sayac[row.depo_id] = depo_sayac.get(row.depo_id, 0) + 1

        for depo_id, palet_sayisi in depo_sayac.items():
            log = SistemLogORM(
                kullanici_id=None,
                islem_tipi=OlayTipi.STAGING_UYARI,
                modul="Staging",
                detay=(
                    f"Staging uyarı: Depo {depo_id} — "
                    f"{palet_sayisi} palet {esik_saat}+ saat bekleniyor."
                ),
                tarih=datetime.utcnow(),
            )
            db.add(log)

        db.commit()
        toplam = sum(depo_sayac.values())
        logger.warning(
            "Staging uyarı yazıldı: %d depo, toplam %d palet (%d+ saat).",
            len(depo_sayac),
            toplam,
            esik_saat,
        )
    except Exception as exc:
        logger.error("Staging uyarı job hatası: %s", exc)
        db.rollback()
    finally:
        db.close()
