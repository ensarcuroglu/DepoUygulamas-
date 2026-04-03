"""Palet bazlı stok domain service — facade.

PaletGirisService ve PaletCikisService'i tek bir public API altında birleştirir.
Router, DI ve testler bu sınıfı import etmeye devam eder; iç yapı değişmez.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from app.core.entities.kullanici import Kullanici
from app.core.entities.stok_hareketi import StokHareketi
from app.core.exceptions import DepoErisimHatasi
from app.core.services.palet_giris_service import PaletGirisService
from app.core.services.palet_cikis_service import PaletCikisService

if TYPE_CHECKING:
    from app.core.services.palet_veri_kaynagi_service import IPaletVeriKaynagiService
    from app.core.repositories.palet_repository import IPaletRepository
    from app.core.repositories.lot_repository import ILotRepository
    from app.core.repositories.raf_repository import IRafRepository
    from app.core.repositories.stok_hareketi_repository import IStokHareketiRepository
    from app.core.repositories.sistem_log_repository import ISistemLogRepository


@dataclass
class TopluPaletSonuc:
    """Toplu işlemdeki tek bir paletin sonucu."""

    palet_no: str
    basarili: bool
    hata_mesaji: Optional[str] = None
    hareket: Optional[StokHareketi] = None


class PaletBazliStokDomainService:
    """Palet numarası bazlı stok giriş/çıkış işlemlerini yöneten facade."""

    def __init__(
        self,
        veri_kaynagi: IPaletVeriKaynagiService,
        palet_repo: IPaletRepository,
        lot_repo: ILotRepository,
        raf_repo: IRafRepository,
        hareket_repo: IStokHareketiRepository,
        log_repo: ISistemLogRepository,
    ):
        self._giris = PaletGirisService(
            veri_kaynagi=veri_kaynagi,
            palet_repo=palet_repo,
            lot_repo=lot_repo,
            hareket_repo=hareket_repo,
            log_repo=log_repo,
        )
        self._cikis = PaletCikisService(
            palet_repo=palet_repo,
            lot_repo=lot_repo,
            raf_repo=raf_repo,
            hareket_repo=hareket_repo,
            log_repo=log_repo,
        )

    # ── Tekli Giriş ──

    def palet_giris(
        self,
        palet_no: str,
        kullanici: Kullanici,
        kaynagi_onayla: bool = True,
        irsaliye_no: Optional[str] = None,
    ) -> StokHareketi:
        return self._giris.palet_giris(palet_no, kullanici, kaynagi_onayla, irsaliye_no)

    def son_hareketi_getir_palet_ile(self, palet_no: str) -> Optional[StokHareketi]:
        return self._giris.son_hareketi_getir_palet_ile(palet_no)

    # ── Tekli Çıkış ──

    def palet_cikis(
        self,
        palet_no: str,
        kullanici: Kullanici,
        miktar: Optional[int] = None,
        siparis_no: Optional[str] = None,
        aciklama: Optional[str] = None,
    ) -> StokHareketi:
        return self._cikis.palet_cikis(palet_no, kullanici, miktar, siparis_no, aciklama)

    # ── Toplu Giriş ──

    def toplu_palet_giris(
        self,
        palet_no_listesi: list[str],
        kullanici: Kullanici,
        irsaliye_no: Optional[str] = None,
    ) -> list[TopluPaletSonuc]:
        return self._giris.toplu_palet_giris(palet_no_listesi, kullanici, irsaliye_no)

    def toplu_palet_giris_kaynagini_onayla(self, palet_no_listesi: list[str]) -> None:
        self._giris.toplu_palet_giris_kaynagini_onayla(palet_no_listesi)

    # ── Toplu Çıkış ──

    def toplu_palet_cikis(
        self,
        kalemler: list[dict],
        kullanici: Kullanici,
        siparis_no: Optional[str] = None,
        aciklama: Optional[str] = None,
    ) -> list[TopluPaletSonuc]:
        return self._cikis.toplu_palet_cikis(kalemler, kullanici, siparis_no, aciklama)

    # ── Test uyumluluğu için static yardımcı ──

    @staticmethod
    def _depo_erisim_dogrula(
        kullanici: Kullanici, hedef_depo_id: int, depo_adi: str = "",
    ) -> None:
        """Kullanıcının hedef depoya erişim yetkisini doğrular."""
        if not kullanici.depo_erisim_var(hedef_depo_id):
            raise DepoErisimHatasi(kullanici.depo_id, hedef_depo_id, depo_adi)
