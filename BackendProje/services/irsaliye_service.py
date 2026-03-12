"""İrsaliye İşlemleri — Service Layer"""
from typing import Optional
from sqlalchemy.orm import Session, joinedload

from models import Irsaliye, Siparis, SiparisKalemi
from schemas import IrsaliyeCreate, IrsaliyeUpdate
from core.exceptions import NotFoundError
import crud


class IrsaliyeService:

    @staticmethod
    def get_irsaliyeler(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        durum: Optional[str] = None,
        arama: Optional[str] = None,
    ):
        return crud.get_irsaliyeler(db, skip=skip, limit=limit, durum=durum, arama=arama)

    @staticmethod
    def get_irsaliye(db: Session, irsaliye_id: int):
        i = crud.get_irsaliye(db, irsaliye_id)
        if not i:
            raise NotFoundError("İrsaliye", irsaliye_id)
        return i

    @staticmethod
    def create_irsaliye(db: Session, data: IrsaliyeCreate, kullanici_id: int):
        siparis = crud.get_siparis(db, data.siparis_id)
        if not siparis:
            raise NotFoundError("Sipariş", data.siparis_id)
        return crud.create_irsaliye(db, data, kullanici_id=kullanici_id)

    @staticmethod
    def update_irsaliye(db: Session, irsaliye_id: int, data: IrsaliyeUpdate, kullanici_id: int):
        IrsaliyeService.get_irsaliye(db, irsaliye_id)
        return crud.update_irsaliye(db, irsaliye_id, data, kullanici_id=kullanici_id)

    @staticmethod
    def get_yazdir_verisi(db: Session, irsaliye_id: int) -> dict:
        """İrsaliye yazdırma verisi; joinedload ile sipariş + kalemler + ürünler."""
        irsaliye = (
            db.query(Irsaliye)
            .options(
                joinedload(Irsaliye.siparis)
                .joinedload(Siparis.kalemler)
                .joinedload(SiparisKalemi.urun)
            )
            .filter(Irsaliye.id == irsaliye_id)
            .first()
        )
        if not irsaliye:
            raise NotFoundError("İrsaliye", irsaliye_id)

        siparis = irsaliye.siparis
        kalemler = [
            {
                "urun_id": k.urun_id,
                "urun_isim": k.urun.adi if k.urun else "-",
                "miktar": k.miktar,
                "birim_fiyat": k.birim_fiyat,
                "kdv_orani": k.kdv_orani,
                "toplam": k.toplam,
            }
            for k in (siparis.kalemler if siparis else [])
        ]

        return {
            "irsaliye": {
                "id": irsaliye.id,
                "irsaliye_no": irsaliye.irsaliye_no,
                "irsaliye_tarihi": str(irsaliye.irsaliye_tarihi),
                "belge_turu": irsaliye.belge_turu,
                "tir_plaka": irsaliye.tir_plaka,
                "sofor_adi": irsaliye.sofor_adi,
                "durum": irsaliye.durum,
            },
            "siparis": {
                "siparis_no": siparis.siparis_no if siparis else "-",
                "musteri_adi": siparis.musteri_adi if siparis else "-",
                "teslimat_adresi": siparis.teslimat_adresi if siparis else "-",
                "teslimat_tarihi": str(siparis.teslimat_tarihi) if siparis else "-",
                "top_tutar": siparis.top_tutar if siparis else 0,
                "top_miktar": siparis.top_miktar if siparis else 0,
            },
            "kalemler": kalemler,
        }
