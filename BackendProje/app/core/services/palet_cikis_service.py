"""Palet stok çıkış domain service — tekli ve toplu çıkış iş kuralları."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from app.core.entities.kullanici import Kullanici
from app.core.entities.stok_hareketi import StokHareketi, HareketTipi
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import (
    KayitBulunamadiError,
    GecersizIslemError,
    DepoErisimHatasi,
)

if TYPE_CHECKING:
    from app.core.repositories.palet_repository import IPaletRepository
    from app.core.repositories.lot_repository import ILotRepository
    from app.core.repositories.raf_repository import IRafRepository
    from app.core.repositories.stok_hareketi_repository import IStokHareketiRepository
    from app.core.repositories.sistem_log_repository import ISistemLogRepository
    from app.core.services.palet_bazli_stok_domain_service import TopluPaletSonuc


class PaletCikisService:
    """Palet numarası bazlı stok çıkış iş kuralları (tekli + toplu)."""

    def __init__(
        self,
        palet_repo: IPaletRepository,
        lot_repo: ILotRepository,
        raf_repo: IRafRepository,
        hareket_repo: IStokHareketiRepository,
        log_repo: ISistemLogRepository,
    ):
        self._palet_repo = palet_repo
        self._lot_repo = lot_repo
        self._raf_repo = raf_repo
        self._hareket_repo = hareket_repo
        self._log_repo = log_repo

    def palet_cikis(
        self,
        palet_no: str,
        kullanici: Kullanici,
        miktar: Optional[int] = None,
        siparis_no: Optional[str] = None,
        aciklama: Optional[str] = None,
    ) -> StokHareketi:
        """Palet numarası ile stok çıkışı yapar.

        miktar=None ise tam çıkış (palet.sevk_et), değilse kısmi çıkış (palet.stok_dus).
        """
        palet = self._palet_repo.getir_palet_no_ile(palet_no, kilitli_mi=True)
        if not palet:
            raise KayitBulunamadiError("Palet", palet_no)

        if not palet.aktif or palet.bos_mu():
            raise GecersizIslemError("Bu palette stok bulunmuyor.")

        hedef_depo_id = self._raf_depo_id_coz(palet.raf_id)
        if hedef_depo_id:
            self._depo_erisim_dogrula(kullanici, hedef_depo_id)

        if miktar is None:
            gercek_miktar = palet.koli_adedi
            palet.sevk_et()
        else:
            if miktar > palet.koli_adedi:
                raise GecersizIslemError(
                    f"Istenen miktar ({miktar}) paletteki stoktan ({palet.koli_adedi}) fazla."
                )
            gercek_miktar = palet.stok_dus(miktar)

        self._palet_repo.guncelle(palet, auto_commit=False)

        hareket = StokHareketi(
            urun_id=0,
            lot_id=palet.lot_id,
            palet_id=palet.id,
            raf_id=palet.raf_id,
            hareket_tipi=HareketTipi.CIKIS,
            miktar=gercek_miktar,
            siparis_no=siparis_no,
            kullanici_id=kullanici.id,
            aciklama=aciklama or f"Palet bazli stok cikisi: {palet_no}",
        )

        lot = self._lot_repo.getir_id_ile(palet.lot_id)
        if lot:
            hareket.urun_id = lot.urun_id

        hareket = self._hareket_repo.olustur(hareket, auto_commit=False)

        cikis_tipi = "tam" if miktar is None else "kismi"
        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici.id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Stok Islemleri",
                detay=f"Palet cikisi ({cikis_tipi}): {palet_no} (Miktar: {gercek_miktar} koli)",
            ),
            auto_commit=False,
        )

        return hareket

    def toplu_palet_cikis(
        self,
        kalemler: list[dict],
        kullanici: Kullanici,
        siparis_no: Optional[str] = None,
        aciklama: Optional[str] = None,
    ) -> list[TopluPaletSonuc]:
        """Birden fazla paletten tek seferde çıkış yapar (pre-validation + all-or-nothing).

        kalemler: [{"palet_no": str, "miktar": Optional[int]}, ...]
        """
        from app.core.services.palet_bazli_stok_domain_service import TopluPaletSonuc

        sonuclar: list[TopluPaletSonuc] = []

        for kalem in kalemler:
            palet_no = kalem["palet_no"]
            miktar = kalem.get("miktar")
            hata = self.cikis_on_dogrula(palet_no, miktar, kullanici)
            sonuclar.append(
                TopluPaletSonuc(palet_no=palet_no, basarili=hata is None, hata_mesaji=hata)
            )

        if any(not s.basarili for s in sonuclar):
            return sonuclar

        for i, kalem in enumerate(kalemler):
            sonuclar[i].hareket = self.palet_cikis(
                palet_no=kalem["palet_no"],
                kullanici=kullanici,
                miktar=kalem.get("miktar"),
                siparis_no=siparis_no,
                aciklama=aciklama,
            )

        return sonuclar

    def cikis_on_dogrula(
        self, palet_no: str, miktar: Optional[int], kullanici: Kullanici,
    ) -> Optional[str]:
        """Tekil palet için çıkış ön-doğrulama. Hata varsa mesaj döner, yoksa None."""
        palet = self._palet_repo.getir_palet_no_ile(palet_no)
        if not palet:
            return f"Palet '{palet_no}' bulunamadi."

        if not palet.aktif or palet.bos_mu():
            return "Bu palette stok bulunmuyor."

        hedef_depo_id = self._raf_depo_id_coz(palet.raf_id)
        if hedef_depo_id and not kullanici.depo_erisim_var(hedef_depo_id):
            return "Bu palet farkli bir depoya ait, yetkiniz bulunmuyor."

        if miktar is not None and miktar > palet.koli_adedi:
            return f"Istenen miktar ({miktar}) paletteki stoktan ({palet.koli_adedi}) fazla."

        return None

    def _raf_depo_id_coz(self, raf_id: Optional[int]) -> Optional[int]:
        """Raf ID'sinden depo ID'sini çözümler."""
        if not raf_id:
            return None
        raf = self._raf_repo.getir_id_ile(raf_id)
        return raf.depo_id if raf else None

    @staticmethod
    def _depo_erisim_dogrula(
        kullanici: Kullanici, hedef_depo_id: int, depo_adi: str = "",
    ) -> None:
        """Kullanıcının hedef depoya erişim yetkisini doğrular."""
        if not kullanici.depo_erisim_var(hedef_depo_id):
            raise DepoErisimHatasi(kullanici.depo_id, hedef_depo_id, depo_adi)
