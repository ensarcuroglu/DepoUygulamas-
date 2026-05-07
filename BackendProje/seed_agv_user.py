"""Synthetic AGV system user seed (idempotent).

AGV servisinden gelen `/api/agv-callbacks/*` çağrıları görev tamamlama
işlemini kullanıcı id ile yapar. Bunun için sahte bir "agv-system"
kullanıcısı oluşturulur.

Kullanım:
    python seed_agv_user.py

Çoklu çalıştırma güvenli: kullanıcı zaten varsa no-op.
"""

from __future__ import annotations

import secrets
import sys

from sqlalchemy.exc import SQLAlchemyError

from app.core.auth import get_password_hash
from database import SessionLocal
from models import Kullanici


AGV_KULLANICI_ADI = "agv-system"
AGV_AD_SOYAD = "AGV Otomasyon Sistemi"
AGV_ROL = "agv"


def main() -> int:
    db = SessionLocal()
    try:
        existing = (
            db.query(Kullanici)
            .filter(Kullanici.kullanici_adi == AGV_KULLANICI_ADI)
            .first()
        )
        if existing is not None:
            print(f"[OK] {AGV_KULLANICI_ADI} zaten mevcut (id={existing.id}, rol={existing.rol})")
            # Rol kayması düzeltmesi (eski kayıt depocu/admin ise restore et).
            if existing.rol != AGV_ROL:
                existing.rol = AGV_ROL
                db.commit()
                print(f"[FIX] Rol guncellendi: {existing.rol} -> {AGV_ROL}")
            return 0

        # Hiç login olmayacağı için rastgele uzun parola — kimse bilmesin.
        rastgele_sifre = secrets.token_urlsafe(48)
        agv = Kullanici(
            kullanici_adi=AGV_KULLANICI_ADI,
            sifre_hash=get_password_hash(rastgele_sifre),
            ad_soyad=AGV_AD_SOYAD,
            rol=AGV_ROL,
            depo_id=None,
        )
        db.add(agv)
        db.commit()
        db.refresh(agv)
        print(f"[CREATED] {AGV_KULLANICI_ADI} olusturuldu (id={agv.id}, rol={AGV_ROL})")
        return 0
    except SQLAlchemyError as e:
        db.rollback()
        print(f"[ERROR] DB hata: {e}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
