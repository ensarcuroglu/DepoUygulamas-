"""Palet stok giriş domain service — tekli ve toplu giriş iş kuralları."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from app.application.dto.palet_bilgi_dto import PaletBilgiDTO
from app.core.entities.kullanici import Kullanici
from app.core.entities.lot import Lot
from app.core.entities.palet import Palet
from app.core.entities.stok_hareketi import StokHareketi, HareketTipi
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import (
    KayitBulunamadiError,
    GecersizIslemError,
    CakismaHatasi,
    DepoErisimHatasi,
)

if TYPE_CHECKING:
    from app.core.services.palet_veri_kaynagi_service import IPaletVeriKaynagiService
    from app.core.repositories.palet_repository import IPaletRepository
    from app.core.repositories.lot_repository import ILotRepository
    from app.core.repositories.stok_hareketi_repository import IStokHareketiRepository
    from app.core.repositories.sistem_log_repository import ISistemLogRepository
    from app.core.services.palet_bazli_stok_domain_service import TopluPaletSonuc


class PaletGirisService:
    """Palet numarası bazlı stok giriş iş kuralları (tekli + toplu)."""

    def __init__(
        self,
        veri_kaynagi: IPaletVeriKaynagiService,
        palet_repo: IPaletRepository,
        lot_repo: ILotRepository,
        hareket_repo: IStokHareketiRepository,
        log_repo: ISistemLogRepository,
    ):
        self._veri_kaynagi = veri_kaynagi
        self._palet_repo = palet_repo
        self._lot_repo = lot_repo
        self._hareket_repo = hareket_repo
        self._log_repo = log_repo

    def palet_giris(
        self,
        palet_no: str,
        kullanici: Kullanici,
        kaynagi_onayla: bool = True,
    ) -> StokHareketi:
        """Palet numarası ile stok girişi yapar.

        1. Veri kaynağından palet bilgisini getirir
        2. Çift giriş kontrolü
        3. Depo yetki kontrolü
        4. Lot bul/oluştur
        5. Palet oluştur
        6. StokHareketi kaydı
        7. Kaynaktaki kalemi GirisYapildi olarak işaretle
        8. SistemLog yaz
        """
        dto = self._veri_kaynagi.palet_bilgisi_getir(palet_no)

        if dto.giris_yapildi_mi:
            raise GecersizIslemError("Bu palet zaten sisteme kaydedilmis.")

        if self._palet_repo.getir_palet_no_ile(palet_no):
            raise CakismaHatasi("Palet numarası", palet_no)

        if dto.depo_id:
            self._depo_erisim_dogrula(kullanici, dto.depo_id, dto.depo_adi)

        lot = self._lot_bul_veya_olustur(dto)

        palet = Palet(
            lot_id=lot.id,
            raf_id=dto.raf_id,
            palet_no=dto.palet_no,
            koli_adedi=dto.miktar,
        )
        palet = self._palet_repo.olustur(palet, auto_commit=False)

        hareket = StokHareketi(
            urun_id=dto.urun_id,
            lot_id=lot.id,
            palet_id=palet.id,
            raf_id=dto.raf_id,
            hareket_tipi=HareketTipi.GIRIS,
            miktar=dto.miktar,
            kullanici_id=kullanici.id,
            aciklama=f"Palet bazli stok girisi: {palet_no}",
        )
        hareket = self._hareket_repo.olustur(hareket, auto_commit=False)

        if kaynagi_onayla:
            self._veri_kaynagi.palet_giris_onayla(palet_no)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici.id,
                islem_tipi=IslemTipi.CREATE,
                modul="Stok Islemleri",
                detay=f"Palet girisi: {palet_no} (Urun: {dto.urun_adi}, Miktar: {dto.miktar} koli)",
            ),
            auto_commit=False,
        )

        return hareket

    def son_hareketi_getir_palet_ile(self, palet_no: str) -> Optional[StokHareketi]:
        """Idempotency akışında mükerrer istek için mevcut hareketi döner."""
        palet = self._palet_repo.getir_palet_no_ile(palet_no)
        if not palet:
            return None
        return self._hareket_repo.getir_son_hareket_palet_id_ile(palet.id)

    def toplu_palet_giris(
        self,
        palet_no_listesi: list[str],
        kullanici: Kullanici,
    ) -> list[TopluPaletSonuc]:
        """Birden fazla paleti tek seferde giriş yapar (pre-validation + all-or-nothing)."""
        from app.core.services.palet_bazli_stok_domain_service import TopluPaletSonuc

        sonuclar: list[TopluPaletSonuc] = []

        for palet_no in palet_no_listesi:
            hata = self.giris_on_dogrula(palet_no, kullanici)
            sonuclar.append(
                TopluPaletSonuc(palet_no=palet_no, basarili=hata is None, hata_mesaji=hata)
            )

        if any(not s.basarili for s in sonuclar):
            return sonuclar

        for sonuc in sonuclar:
            sonuc.hareket = self.palet_giris(sonuc.palet_no, kullanici, kaynagi_onayla=False)

        return sonuclar

    def toplu_palet_giris_kaynagini_onayla(self, palet_no_listesi: list[str]) -> None:
        """Toplu giriş sonrası kaynak sistem kayıtlarını onaylar (commit sonrası çağrılmalı)."""
        for palet_no in palet_no_listesi:
            self._veri_kaynagi.palet_giris_onayla(palet_no)

    def giris_on_dogrula(self, palet_no: str, kullanici: Kullanici) -> Optional[str]:
        """Tekil palet için giriş ön-doğrulama. Hata varsa mesaj döner, yoksa None."""
        try:
            dto = self._veri_kaynagi.palet_bilgisi_getir(palet_no)
        except (KayitBulunamadiError, GecersizIslemError) as e:
            return str(e)

        if dto.giris_yapildi_mi:
            return "Bu palet zaten sisteme kaydedilmis."

        if self._palet_repo.getir_palet_no_ile(palet_no):
            return f"Palet numarasi '{palet_no}' zaten mevcut."

        if dto.depo_id and not kullanici.depo_erisim_var(dto.depo_id):
            return f"Bu palet {dto.depo_adi} deposuna ait, yetkiniz bulunmuyor."

        return None

    def _lot_bul_veya_olustur(self, dto: PaletBilgiDTO) -> Lot:
        """Lot numarasına göre mevcut lotu bulur veya yenisini oluşturur."""
        if dto.lot_no:
            mevcut = self._lot_repo.getir_lot_no_ile(dto.lot_no)
            if mevcut:
                return mevcut

        lot = Lot(
            urun_id=dto.urun_id,
            lot_no=dto.lot_no,
            son_kullanma_tarihi=dto.son_kullanma_tarihi,
        )
        return self._lot_repo.olustur(lot, auto_commit=False)

    @staticmethod
    def _depo_erisim_dogrula(
        kullanici: Kullanici, hedef_depo_id: int, depo_adi: str = "",
    ) -> None:
        """Kullanıcının hedef depoya erişim yetkisini doğrular."""
        if not kullanici.depo_erisim_var(hedef_depo_id):
            raise DepoErisimHatasi(kullanici.depo_id, hedef_depo_id, depo_adi)
