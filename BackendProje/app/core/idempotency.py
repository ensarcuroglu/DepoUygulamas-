"""
Idempotency yardımcı modülü.

Kritik POST endpoint'lerinde aynı Idempotency-Key ile gelen
tekrar isteklerinde ilk yanıtı önbellekten döndürür.

Kullanım:
    cached = idempotency_kontrol(db, key, "endpoint-adi")
    if cached is not None:
        return cached          # FastAPI response_model ile doğrular

    result = use_case.execute(...)
    idempotency_kaydet(db, key, "endpoint-adi", sonuc_dict)
    return result
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy.orm import Session

IDEMPOTENCY_TTL_SAAT: int = 24


def idempotency_kontrol(
    db: Session,
    key: str,
    endpoint: str,
) -> Optional[Any]:
    """Key + endpoint çifti için TTL içinde geçerli kayıt varsa response_body döndür,
    yoksa None döndür (işlem devam etmeli).
    """
    from models import IdempotencyKaydi  # circular import önlemi

    kayit = (
        db.query(IdempotencyKaydi)
        .filter(
            IdempotencyKaydi.idempotency_key == key,
            IdempotencyKaydi.endpoint == endpoint,
            IdempotencyKaydi.son_kullanim_tarihi > datetime.utcnow(),
        )
        .first()
    )
    return kayit.response_body if kayit else None


def idempotency_kaydet(
    db: Session,
    key: str,
    endpoint: str,
    body: Any,
    auto_commit: bool = True,
) -> None:
    """İşlem sonucunu 24 saatlik TTL ile idempotency tablosuna upsert eder."""
    from models import IdempotencyKaydi  # circular import önlemi

    son_kullanim = datetime.utcnow() + timedelta(hours=IDEMPOTENCY_TTL_SAAT)
    kayit = IdempotencyKaydi(
        idempotency_key=key,
        endpoint=endpoint,
        response_body=body,
        son_kullanim_tarihi=son_kullanim,
    )
    db.merge(kayit)  # PK çakışmasında güncelle
    if auto_commit:
        db.commit()


def idempotency_temizle(db: Session, auto_commit: bool = True) -> int:
    """Süresi dolmuş kayıtları siler. Uygulama başlangıcında çağrılır."""
    from models import IdempotencyKaydi  # circular import önlemi

    silinen = db.query(IdempotencyKaydi).filter(
        IdempotencyKaydi.son_kullanim_tarihi < datetime.utcnow()
    ).delete(synchronize_session=False)
    if auto_commit:
        db.commit()
    return silinen
