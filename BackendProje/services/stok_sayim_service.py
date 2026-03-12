"""Stok Sayım (Inventar) — Service Layer"""
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import StokSayim, StokSayimKalemi, Urun, Palet, Lot
from schemas import StokSayimCreate, StokSayimKalemiCreate
from core.exceptions import NotFoundError, BadRequestError


def _ekle_urun_adi(sayim: StokSayim) -> StokSayim:
    """Sayım kalemlerindeki urun_adi geçici alanını doldurur."""
    for kalem in sayim.sayim_kalemleri:
        if kalem.urun:
            kalem.urun_adi = kalem.urun.adi
    return sayim


class StokSayimService:

    @staticmethod
    def get_sayimlar(db: Session) -> List[StokSayim]:
        sayimlar = (
            db.query(StokSayim)
            .filter(StokSayim.aktif == True)
            .order_by(StokSayim.olusturma_tarihi.desc())
            .all()
        )
        return [_ekle_urun_adi(s) for s in sayimlar]

    @staticmethod
    def get_sayim(db: Session, sayim_id: int) -> StokSayim:
        sayim = db.query(StokSayim).filter(StokSayim.id == sayim_id).first()
        if not sayim:
            raise NotFoundError("Sayım", sayim_id)
        return _ekle_urun_adi(sayim)

    @staticmethod
    def basla(db: Session, data: StokSayimCreate, kullanici_id: int) -> StokSayim:
        """
        Yeni stok sayımı başlatır.
        - Benzersiz sayim_no üretir (SAY-YYYYMM-GG-HHMM)
        - Aktif tüm ürünlerin stok snapshot'ını alır (referans_stok_json)
        """
        now = datetime.utcnow()
        sayim_no = f"SAY-{now.year}{now.month:02d}-{now.day:02d}-{now.hour:02d}{now.minute:02d}"

        # Aynı dakikada çakışmayı önle
        if db.query(StokSayim).filter(StokSayim.sayim_no == sayim_no).first():
            sayim_no = f"{sayim_no}-{now.second:02d}"

        # Stok snapshot: her aktif ürün için palet toplamı
        urunler = db.query(Urun).filter(Urun.aktif == True).all()
        referans_stok = {}
        for urun in urunler:
            toplam = (
                db.query(func.sum(Palet.koli_adedi))
                .filter(
                    Palet.lot_id.in_(
                        db.query(Lot.id).filter(Lot.urun_id == urun.id, Lot.aktif == True)
                    ),
                    Palet.aktif == True,
                )
                .scalar() or 0
            )
            referans_stok[str(urun.id)] = int(toplam)

        yeni = StokSayim(
            sayim_no=sayim_no,
            aciklama=data.aciklama or "",
            kontrol_eden_user_id=kullanici_id,
            referans_stok_json=referans_stok,
            durum="devam_ediyor",
        )
        db.add(yeni)
        db.commit()
        db.refresh(yeni)
        return yeni

    @staticmethod
    def kalem_kaydet(
        db: Session, sayim_id: int, data: StokSayimKalemiCreate, kullanici_id: int
    ) -> StokSayimKalemi:
        """
        Ürün sayısını kaydeder (upsert).
        Aynı ürün tekrar tarandığında miktar güncellenir.
        """
        sayim = db.query(StokSayim).filter(StokSayim.id == sayim_id).first()
        if not sayim:
            raise NotFoundError("Sayım", sayim_id)
        if sayim.durum != "devam_ediyor":
            raise BadRequestError("Bu sayım aktif değil")

        urun = db.query(Urun).filter(Urun.id == data.urun_id).first()
        if not urun:
            raise NotFoundError("Ürün", data.urun_id)

        kalem = (
            db.query(StokSayimKalemi)
            .filter(
                StokSayimKalemi.sayim_id == sayim_id,
                StokSayimKalemi.urun_id == data.urun_id,
            )
            .first()
        )

        if kalem:
            kalem.sayilan_miktar = data.sayilan_miktar
            kalem.notlar = data.notlar or ""
            kalem.sayim_tarihi = datetime.utcnow()
        else:
            kalem = StokSayimKalemi(
                sayim_id=sayim_id,
                urun_id=data.urun_id,
                sayilan_miktar=data.sayilan_miktar,
                notlar=data.notlar or "",
                user_id=kullanici_id,
            )
            db.add(kalem)

        db.commit()
        db.refresh(kalem)
        kalem.urun_adi = urun.adi
        return kalem

    @staticmethod
    def varyans_hesapla(db: Session, sayim_id: int) -> dict:
        """
        Referans stok ile sayılan miktarı karşılaştırır.
        Sadece sapmalı ürünleri döner.
        """
        sayim = db.query(StokSayim).filter(StokSayim.id == sayim_id).first()
        if not sayim:
            raise NotFoundError("Sayım", sayim_id)

        if not sayim.referans_stok_json:
            return {
                "sayim_no": sayim.sayim_no,
                "varyanslar": [], "toplam_sapma": 0, "sapma_orani": 0,
            }

        varyanslar = []
        toplam_fark = 0

        for urun_id_str, beklenen in sayim.referans_stok_json.items():
            urun_id = int(urun_id_str)
            kalem = (
                db.query(StokSayimKalemi)
                .filter(
                    StokSayimKalemi.sayim_id == sayim_id,
                    StokSayimKalemi.urun_id == urun_id,
                )
                .first()
            )
            sayilan = kalem.sayilan_miktar if kalem else 0
            fark = sayilan - beklenen

            if abs(fark) > 0:
                urun = db.query(Urun).filter(Urun.id == urun_id).first()
                varyanslar.append({
                    "urun_id": urun_id,
                    "urun_adi": urun.adi if urun else f"Ürün #{urun_id}",
                    "beklenen": beklenen,
                    "sayilan": sayilan,
                    "fark": fark,
                    "yuzde": round(fark / beklenen * 100, 1) if beklenen > 0 else 0,
                    "notlar": kalem.notlar if kalem else "",
                })
                toplam_fark += abs(fark)

        return {
            "sayim_no": sayim.sayim_no,
            "referans_tarih": sayim.baslangic_tarihi,
            "varyanslar": varyanslar,
            "toplam_sapma": toplam_fark,
            "sayilan_urun_sayisi": len(sayim.sayim_kalemleri),
            "sapma_orani": round(
                len(varyanslar) / len(sayim.referans_stok_json) * 100, 1
            ) if sayim.referans_stok_json else 0,
        }

    @staticmethod
    def onayla(db: Session, sayim_id: int, kullanici_id: int) -> dict:
        """Sayımı kapatır ve 'onaylandı' durumuna geçirir."""
        sayim = db.query(StokSayim).filter(StokSayim.id == sayim_id).first()
        if not sayim:
            raise NotFoundError("Sayım", sayim_id)
        if sayim.durum not in ("devam_ediyor", "oluşturuldu"):
            raise BadRequestError(f"Sayım zaten '{sayim.durum}' durumunda")

        sayim.durum = "onaylandı"
        sayim.bitis_tarihi = datetime.utcnow()
        sayim.onaylayan_user_id = kullanici_id
        db.commit()
        return {"message": "Sayım onaylandı", "sayim_no": sayim.sayim_no}
