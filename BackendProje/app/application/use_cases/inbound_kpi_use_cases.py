"""
Inbound KPI Use Case — Faz 5.

Tarih aralığı ve staging eşiğine göre operasyon performans metriklerini hesaplar.
"""

from __future__ import annotations
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func, case, literal_column, or_

from app.application.dto.mal_kabul_irsaliye_dto import (
    InboundKpiResponseDTO,
    OperatorVerimDTO,
)
from app.core.entities.sistem_log import OlayTipi


def _timestampdiff_seconds(start_col, end_col):
    return func.timestampdiff(literal_column("SECOND"), start_col, end_col)


class InboundKpiUseCase:
    """
    Inbound operasyon KPI metriklerini hesaplar:
      1. Araç kabulden ilk palet girişine geçen ortalama süre
      2. İlk palet girişinden son yerleştirmeye geçen ortalama süre
      3. Operatör başına saatlik yerleştirme adedi
      4. Yanlış palet okutma sayısı (terminal log tabanlı)
      5. Override kullanım oranı
      6. Karantina oranı
      7. Stagingde eşik saatten fazla bekleyen palet sayısı
    """

    def __init__(self, db: Session):
        self._db = db

    def execute(
        self,
        tarih_baslangic: datetime,
        tarih_bitis: datetime,
        staging_esik_saat: int = 24,
    ) -> InboundKpiResponseDTO:
        from models import (
            MalKabulIrsaliye as MalKabulIrsaliyeORM,
            YerlestirmeGorevi as YerlestirmeGoreviORM,
            Palet as PaletORM,
            Raf as RafORM,
            Kullanici as KullaniciORM,
            SistemLog as SistemLogORM,
        )

        # ── 1. Araç kabul → ilk palet girişi süresi ─────────────────────────
        #   Her irsaliye için: min(palet.olusturma_tarihi) - irsaliye.tarih
        arac_palet_sub = (
            self._db.query(
                YerlestirmeGoreviORM.mal_kabul_irsaliye_id.label("irsaliye_id"),
                func.min(PaletORM.olusturma_tarihi).label("ilk_palet"),
            )
            .join(PaletORM, PaletORM.id == YerlestirmeGoreviORM.palet_id)
            .filter(
                YerlestirmeGoreviORM.mal_kabul_irsaliye_id.isnot(None),
                YerlestirmeGoreviORM.olusturma_tarihi >= tarih_baslangic,
                YerlestirmeGoreviORM.olusturma_tarihi <= tarih_bitis,
            )
            .group_by(YerlestirmeGoreviORM.mal_kabul_irsaliye_id)
            .subquery()
        )
        arac_palet_row = (
            self._db.query(
                func.avg(
                    _timestampdiff_seconds(
                        MalKabulIrsaliyeORM.tarih,
                        arac_palet_sub.c.ilk_palet,
                    )
                )
            )
            .join(arac_palet_sub, arac_palet_sub.c.irsaliye_id == MalKabulIrsaliyeORM.id)
            .filter(
                MalKabulIrsaliyeORM.olusturma_tarihi >= tarih_baslangic,
                MalKabulIrsaliyeORM.olusturma_tarihi <= tarih_bitis,
            )
            .scalar()
        )
        arac_palet_sure_dk = (
            round(float(arac_palet_row) / 60.0, 1)
            if arac_palet_row and float(arac_palet_row) > 0
            else None
        )

        # ── 2. İlk palet → son yerleştirme süresi ───────────────────────────
        #   Her kapanmış irsaliye için: max(gorev.tamamlanma_tarihi) - irsaliye.tarih
        son_yerlestirme_sub = (
            self._db.query(
                YerlestirmeGoreviORM.mal_kabul_irsaliye_id.label("irsaliye_id"),
                func.max(YerlestirmeGoreviORM.tamamlanma_tarihi).label("son_yerlestirme"),
            )
            .filter(
                YerlestirmeGoreviORM.durum == "Tamamlandi",
                YerlestirmeGoreviORM.tamamlanma_tarihi >= tarih_baslangic,
                YerlestirmeGoreviORM.tamamlanma_tarihi <= tarih_bitis,
                YerlestirmeGoreviORM.mal_kabul_irsaliye_id.isnot(None),
            )
            .group_by(YerlestirmeGoreviORM.mal_kabul_irsaliye_id)
            .subquery()
        )
        son_yerlestirme_row = (
            self._db.query(
                func.avg(
                    _timestampdiff_seconds(
                        arac_palet_sub.c.ilk_palet,
                        son_yerlestirme_sub.c.son_yerlestirme,
                    )
                )
            )
            .join(arac_palet_sub, arac_palet_sub.c.irsaliye_id == MalKabulIrsaliyeORM.id)
            .join(son_yerlestirme_sub, son_yerlestirme_sub.c.irsaliye_id == MalKabulIrsaliyeORM.id)
            .filter(
                MalKabulIrsaliyeORM.durum == "Kapandi",
                MalKabulIrsaliyeORM.olusturma_tarihi >= tarih_baslangic,
                MalKabulIrsaliyeORM.olusturma_tarihi <= tarih_bitis,
            )
            .scalar()
        )
        son_yerlestirme_sure_dk = (
            round(float(son_yerlestirme_row) / 60.0, 1)
            if son_yerlestirme_row and float(son_yerlestirme_row) > 0
            else None
        )

        # ── 3. Operatör verimliliği ──────────────────────────────────────────
        aralik_saat = max(
            (tarih_bitis - tarih_baslangic).total_seconds() / 3600.0,
            1.0,
        )
        operator_rows = (
            self._db.query(
                YerlestirmeGoreviORM.atanan_kullanici_id,
                KullaniciORM.ad_soyad,
                func.count(YerlestirmeGoreviORM.id).label("toplam"),
            )
            .join(KullaniciORM, KullaniciORM.id == YerlestirmeGoreviORM.atanan_kullanici_id)
            .filter(
                YerlestirmeGoreviORM.durum == "Tamamlandi",
                YerlestirmeGoreviORM.tamamlanma_tarihi >= tarih_baslangic,
                YerlestirmeGoreviORM.tamamlanma_tarihi <= tarih_bitis,
                YerlestirmeGoreviORM.atanan_kullanici_id.isnot(None),
            )
            .group_by(YerlestirmeGoreviORM.atanan_kullanici_id, KullaniciORM.ad_soyad)
            .all()
        )
        operator_verimliligi = [
            OperatorVerimDTO(
                kullanici_id=row.atanan_kullanici_id,
                kullanici_adi=row.ad_soyad,
                toplam_yerlestirme=int(row.toplam),
                saatlik_yerlestirme=round(int(row.toplam) / aralik_saat, 2),
            )
            for row in operator_rows
        ]

        # ── 4. Yanlış palet okutma sayısı ────────────────────────────────────
        yanlis_palet_sayisi = (
            self._db.query(func.count(SistemLogORM.id))
            .filter(
                SistemLogORM.islem_tipi == OlayTipi.PALET_OKUTMA_HATASI,
                SistemLogORM.tarih >= tarih_baslangic,
                SistemLogORM.tarih <= tarih_bitis,
            )
            .scalar()
            or 0
        )

        # ── 5. Override oranı ────────────────────────────────────────────────
        override_toplam_row = (
            self._db.query(
                func.count(YerlestirmeGoreviORM.id).label("toplam"),
                func.count(
                    case((YerlestirmeGoreviORM.override_kullanici_id.isnot(None), 1))
                ).label("override"),
            )
            .filter(
                YerlestirmeGoreviORM.durum == "Tamamlandi",
                YerlestirmeGoreviORM.tamamlanma_tarihi >= tarih_baslangic,
                YerlestirmeGoreviORM.tamamlanma_tarihi <= tarih_bitis,
            )
            .one()
        )
        override_sayisi = int(override_toplam_row.override or 0)
        toplam_tamamlanan = int(override_toplam_row.toplam or 0)
        override_orani = (
            round(override_sayisi / toplam_tamamlanan * 100.0, 1)
            if toplam_tamamlanan > 0
            else None
        )

        # ── 6. Karantina sayısı / oranı ──────────────────────────────────────
        karantina_sayisi = (
            self._db.query(func.count(SistemLogORM.id))
            .filter(
                or_(
                    SistemLogORM.islem_tipi == OlayTipi.KARANTINA_BASLAT,
                    (
                        (SistemLogORM.modul == "Yerleştirme")
                        & (SistemLogORM.detay.like("Karantinaya alma:%"))
                    ),
                ),
                SistemLogORM.tarih >= tarih_baslangic,
                SistemLogORM.tarih <= tarih_bitis,
            )
            .scalar()
            or 0
        )
        # Karantina oranı = karantina kayıt / toplam kabul edilen kalem
        toplam_kalem = (
            self._db.query(func.count(YerlestirmeGoreviORM.id))
            .filter(
                YerlestirmeGoreviORM.olusturma_tarihi >= tarih_baslangic,
                YerlestirmeGoreviORM.olusturma_tarihi <= tarih_bitis,
            )
            .scalar()
            or 0
        )
        karantina_orani = (
            round(karantina_sayisi / toplam_kalem * 100.0, 1)
            if toplam_kalem > 0
            else None
        )

        # ── 7. Staging eşik palet sayısı ─────────────────────────────────────
        staging_esik_tarih = datetime.utcnow() - timedelta(hours=staging_esik_saat)
        staging_palet_sayisi = (
            self._db.query(func.count(PaletORM.id))
            .join(RafORM, RafORM.id == PaletORM.raf_id)
            .filter(
                RafORM.is_staging,
                PaletORM.aktif,
                PaletORM.olusturma_tarihi <= staging_esik_tarih,
            )
            .scalar()
            or 0
        )

        return InboundKpiResponseDTO(
            tarih_baslangic=tarih_baslangic.isoformat(),
            tarih_bitis=tarih_bitis.isoformat(),
            staging_esik_saat=staging_esik_saat,
            arac_kabul_ilk_palet_sure_dk=arac_palet_sure_dk,
            ilk_palet_son_yerlestirme_sure_dk=son_yerlestirme_sure_dk,
            operator_verimliligi=operator_verimliligi,
            yanlis_palet_okutma_sayisi=int(yanlis_palet_sayisi),
            override_sayisi=override_sayisi,
            override_orani=override_orani,
            karantina_sayisi=int(karantina_sayisi),
            karantina_orani=karantina_orani,
            staging_esik_palet_sayisi=int(staging_palet_sayisi),
        )
