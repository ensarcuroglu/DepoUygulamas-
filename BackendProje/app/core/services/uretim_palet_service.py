"""Üretim Paleti domain service — saf iş kuralları, repo/yan etki yok."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from app.core.entities.palet import Palet, UretimPaletDurum
from app.core.entities.palet_durum_log import PaletDurumLog
from app.core.exceptions import YetkisizIslemError


class UretimPaletService:
    """Üretim paleti yaşam döngüsü iş kuralları.

    Bu servis repo çağrısı yapmaz; hiçbir altyapı yan etkisi içermez.
    Her metot durum geçişini entity üzerinde gerçekleştirir ve persist
    edilmek üzere bir PaletDurumLog entity'si döner.
    """

    # ── Oluşturma ──

    def olustur(
        self,
        palet_no: str,
        lot_id: int,
        raf_id: int,
        koli_adedi: int,
        uretim_tarihi: Optional[date] = None,
        lot_no: Optional[str] = None,
        palet_kg: Optional[float] = None,
        vardiya: Optional[str] = None,
        kullanici_id: Optional[int] = None,
        uretim_hatti: Optional[str] = None,
        makine_kodu: Optional[str] = None,
        operator_kullanici_id: Optional[int] = None,
        brut_kg: Optional[float] = None,
        net_kg: Optional[float] = None,
    ) -> tuple[Palet, PaletDurumLog]:
        palet = Palet(
            palet_no=palet_no,
            lot_id=lot_id,
            raf_id=raf_id,
            koli_adedi=koli_adedi,
            palet_kg=palet_kg,
            vardiya=vardiya,
            kaynak="uretim",
            durum=UretimPaletDurum.OLUSTURULDU,
            uretim_tarihi=uretim_tarihi,
            lot_no=lot_no,
            uretim_hatti=uretim_hatti,
            makine_kodu=makine_kodu,
            operator_kullanici_id=operator_kullanici_id,
            brut_kg=brut_kg,
            net_kg=net_kg,
        )
        log = self._log_olustur(
            palet=palet,
            eski_durum=None,
            yeni_durum=UretimPaletDurum.OLUSTURULDU,
            kullanici_id=kullanici_id,
        )
        return palet, log

    # ── Durum Geçişleri ──

    def kabul_bekle(
        self, palet: Palet, kullanici_id: Optional[int] = None
    ) -> PaletDurumLog:
        eski = palet.durum
        palet.kabul_bekle()
        return self._log_olustur(palet, eski, palet.durum, kullanici_id)

    def kabul_et(
        self, palet: Palet, kullanici_id: int
    ) -> PaletDurumLog:
        eski = palet.durum
        palet.kabul_et(kullanici_id)
        return self._log_olustur(palet, eski, palet.durum, kullanici_id)

    def yerlestirme_bekle(
        self, palet: Palet, kullanici_id: Optional[int] = None
    ) -> PaletDurumLog:
        eski = palet.durum
        palet.yerlestirme_bekle()
        return self._log_olustur(palet, eski, palet.durum, kullanici_id)

    def yerlestir(
        self, palet: Palet, raf_id: int, kullanici_id: Optional[int] = None
    ) -> PaletDurumLog:
        eski = palet.durum
        palet.yerlestir(raf_id)
        return self._log_olustur(palet, eski, palet.durum, kullanici_id)

    def karantinaya_al(
        self,
        palet: Palet,
        kullanici_id: Optional[int] = None,
        sebep: Optional[str] = None,
    ) -> PaletDurumLog:
        eski = palet.durum
        palet.karantinaya_al()
        return self._log_olustur(palet, eski, palet.durum, kullanici_id, sebep)

    def karantinadan_cikar(
        self,
        palet: Palet,
        kullanici_id: Optional[int],
        yetkili: bool,
        sebep: Optional[str] = None,
    ) -> PaletDurumLog:
        if not yetkili:
            raise YetkisizIslemError(
                "Karantinadan çıkarma işlemi için kalite/admin yetkisi gereklidir."
            )
        eski = palet.durum
        palet.karantinadan_cikar()
        return self._log_olustur(palet, eski, palet.durum, kullanici_id, sebep)

    def iptal_et(
        self,
        palet: Palet,
        kullanici_id: Optional[int] = None,
        sebep: str = "",
    ) -> PaletDurumLog:
        eski = palet.durum
        palet.iptal_et(sebep)
        return self._log_olustur(palet, eski, palet.durum, kullanici_id, sebep)

    # ── Yardımcı ──

    @staticmethod
    def _log_olustur(
        palet: Palet,
        eski_durum: Optional[str],
        yeni_durum: str,
        kullanici_id: Optional[int] = None,
        sebep: Optional[str] = None,
    ) -> PaletDurumLog:
        return PaletDurumLog(
            palet_id=palet.id or 0,  # persist öncesi 0; use case flush sonrası günceller
            eski_durum=eski_durum,
            yeni_durum=yeni_durum,
            degistiren_kullanici_id=kullanici_id,
            sebep=sebep or None,
            degisim_tarihi=datetime.utcnow(),
        )
