"""Palet bazli stok giris/cikis domain service.

Palet numarasi uzerinden stok girisi ve cikisi is kurallarini icerir.
IPaletVeriKaynagiService soyutlamasi sayesinde kaynak bagimsiz calisir.
Tekli ve toplu (Faz 2) islemleri destekler.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, List

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


@dataclass
class TopluPaletSonuc:
    """Toplu islemdeki tek bir paletin sonucu."""

    palet_no: str
    basarili: bool
    hata_mesaji: Optional[str] = None
    hareket: Optional[StokHareketi] = None

if TYPE_CHECKING:
    from app.core.services.palet_veri_kaynagi_service import IPaletVeriKaynagiService
    from app.core.repositories.palet_repository import IPaletRepository
    from app.core.repositories.lot_repository import ILotRepository
    from app.core.repositories.raf_repository import IRafRepository
    from app.core.repositories.stok_hareketi_repository import IStokHareketiRepository
    from app.core.repositories.sistem_log_repository import ISistemLogRepository


class PaletBazliStokDomainService:
    """Palet numarasi bazli stok giris ve cikis islemlerini yonetir."""

    def __init__(
        self,
        veri_kaynagi: IPaletVeriKaynagiService,
        palet_repo: IPaletRepository,
        lot_repo: ILotRepository,
        raf_repo: IRafRepository,
        hareket_repo: IStokHareketiRepository,
        log_repo: ISistemLogRepository,
    ):
        self._veri_kaynagi = veri_kaynagi
        self._palet_repo = palet_repo
        self._lot_repo = lot_repo
        self._raf_repo = raf_repo
        self._hareket_repo = hareket_repo
        self._log_repo = log_repo

    # ── Palet Giris ──

    def palet_giris(self, palet_no: str, kullanici: Kullanici) -> StokHareketi:
        """Palet numarasi ile stok girisi yapar.

        1. Veri kaynagindan palet bilgisini getirir
        2. Cift giris kontrolu
        3. Depo yetki kontrolu
        4. Lot bul/olustur
        5. Palet olustur
        6. StokHareketi kaydi
        7. Kaynaktaki kalemi GirisYapildi olarak isaretle
        8. SistemLog yaz
        """
        # 1. Palet bilgisini getir
        dto = self._veri_kaynagi.palet_bilgisi_getir(palet_no)

        # 2. Zaten giris yapilmis mi?
        if dto.giris_yapildi_mi:
            raise GecersizIslemError("Bu palet zaten sisteme kaydedilmis.")

        # 3. DB'de palet mevcut mu? (cift giris engeli)
        mevcut_palet = self._palet_repo.getir_palet_no_ile(palet_no)
        if mevcut_palet:
            raise CakismaHatasi("Palet numarası", palet_no)

        # 4. Depo yetki kontrolu
        if dto.depo_id:
            self._depo_erisim_dogrula(kullanici, dto.depo_id, dto.depo_adi)

        # 5. Lot bul veya olustur
        lot = self._lot_bul_veya_olustur(dto)

        # 6. Palet olustur
        palet = Palet(
            lot_id=lot.id,
            raf_id=dto.raf_id,
            palet_no=dto.palet_no,
            koli_adedi=dto.miktar,
        )
        palet = self._palet_repo.olustur(palet, auto_commit=False)

        # 7. StokHareketi kaydi
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

        # 8. Kaynagi guncelle (MalKabulKalemi.durum -> GirisYapildi)
        self._veri_kaynagi.palet_giris_onayla(palet_no)

        # 9. SistemLog
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

    # ── Palet Cikis ──

    def palet_cikis(
        self,
        palet_no: str,
        kullanici: Kullanici,
        miktar: Optional[int] = None,
        siparis_no: Optional[str] = None,
        aciklama: Optional[str] = None,
    ) -> StokHareketi:
        """Palet numarasi ile stok cikisi yapar.

        miktar=None ise tam cikis (palet.sevk_et), degilse kismi cikis (palet.stok_dus).
        """
        # 1. Paleti bul (KİLİTLİ OKUMA) - Eş zamanlı çıkışları engeller
        palet = self._palet_repo.getir_palet_no_ile(palet_no, kilitli_mi=True)
        if not palet:
            raise KayitBulunamadiError("Palet", palet_no)

        # 2. Aktif ve dolu mu?
        if not palet.aktif or palet.bos_mu():
            raise GecersizIslemError("Bu palette stok bulunmuyor.")

        # 3. Depo yetki kontrolu (raf_id=None olan paletlerde depo kontrolu atlanir)
        hedef_depo_id = self._raf_depo_id_coz(palet.raf_id)
        if hedef_depo_id:
            self._depo_erisim_dogrula(kullanici, hedef_depo_id)

        # 4. Cikis tipi
        if miktar is None:
            gercek_miktar = palet.koli_adedi
            palet.sevk_et()
        else:
            if miktar > palet.koli_adedi:
                raise GecersizIslemError(
                    f"Istenen miktar ({miktar}) paletteki stoktan ({palet.koli_adedi}) fazla."
                )
            gercek_miktar = palet.stok_dus(miktar)

        # 5. Palet guncelle
        self._palet_repo.guncelle(palet, auto_commit=False)

        # 6. StokHareketi
        aciklama_metin = aciklama or f"Palet bazli stok cikisi: {palet_no}"
        hareket = StokHareketi(
            urun_id=0,
            lot_id=palet.lot_id,
            palet_id=palet.id,
            raf_id=palet.raf_id,
            hareket_tipi=HareketTipi.CIKIS,
            miktar=gercek_miktar,
            siparis_no=siparis_no,
            kullanici_id=kullanici.id,
            aciklama=aciklama_metin,
        )

        # urun_id'yi lot uzerinden al
        lot = self._lot_repo.getir_id_ile(palet.lot_id)
        if lot:
            hareket.urun_id = lot.urun_id

        hareket = self._hareket_repo.olustur(hareket, auto_commit=False)

        # 7. SistemLog
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

    # ── Yardimci Metodlar ──

    @staticmethod
    def _depo_erisim_dogrula(
        kullanici: Kullanici, hedef_depo_id: int, depo_adi: str = "",
    ) -> None:
        """Kullanici entity'sinin depo_erisim_var() metodunu kullanarak yetki kontrol eder."""
        if not kullanici.depo_erisim_var(hedef_depo_id):
            raise DepoErisimHatasi(kullanici.depo_id, hedef_depo_id, depo_adi)

    def _raf_depo_id_coz(self, raf_id: Optional[int]) -> Optional[int]:
        """Raf ID'sinden depo ID'sini cozumler."""
        if not raf_id:
            return None
        raf = self._raf_repo.getir_id_ile(raf_id)
        return raf.depo_id if raf else None

    def _lot_bul_veya_olustur(self, dto: PaletBilgiDTO) -> Lot:
        """Lot numarasina gore mevcut lotu bulur veya yenisini olusturur."""
        if dto.lot_no:
            mevcut_lot = self._lot_repo.getir_lot_no_ile(dto.lot_no)
            if mevcut_lot:
                return mevcut_lot

        lot = Lot(
            urun_id=dto.urun_id,
            lot_no=dto.lot_no,
            son_kullanma_tarihi=dto.son_kullanma_tarihi,
        )
        return self._lot_repo.olustur(lot, auto_commit=False)

    # ── Toplu Palet Giris (Faz 2) ──

    def toplu_palet_giris(
        self, palet_no_listesi: List[str], kullanici: Kullanici,
    ) -> List[TopluPaletSonuc]:
        """Birden fazla paleti tek seferde giris yapar.

        Pre-validation: Her palet icin dogrulama yapilir, hatali olanlar raporlanir.
        Sadece tumu gecerli ise islem gerceklestirilir (all-or-nothing).
        """
        sonuclar: List[TopluPaletSonuc] = []

        # --- Faz 1: Pre-validation ---
        for palet_no in palet_no_listesi:
            hata = self._giris_on_dogrula(palet_no, kullanici)
            if hata:
                sonuclar.append(TopluPaletSonuc(palet_no=palet_no, basarili=False, hata_mesaji=hata))
            else:
                sonuclar.append(TopluPaletSonuc(palet_no=palet_no, basarili=True))

        # Herhangi bir hata varsa islem yapma
        if any(not s.basarili for s in sonuclar):
            return sonuclar

        # --- Faz 2: Atomik islem ---
        for sonuc in sonuclar:
            hareket = self.palet_giris(sonuc.palet_no, kullanici)
            sonuc.hareket = hareket

        return sonuclar

    def _giris_on_dogrula(self, palet_no: str, kullanici: Kullanici) -> Optional[str]:
        """Tek bir palet icin giris on-dogrulama. Hata varsa mesaj doner, yoksa None."""
        try:
            dto = self._veri_kaynagi.palet_bilgisi_getir(palet_no)
        except (KayitBulunamadiError, GecersizIslemError) as e:
            return str(e)

        if dto.giris_yapildi_mi:
            return "Bu palet zaten sisteme kaydedilmis."

        mevcut = self._palet_repo.getir_palet_no_ile(palet_no)
        if mevcut:
            return f"Palet numarasi '{palet_no}' zaten mevcut."

        if dto.depo_id and not kullanici.depo_erisim_var(dto.depo_id):
            return f"Bu palet {dto.depo_adi} deposuna ait, yetkiniz bulunmuyor."

        return None

    # ── Toplu Palet Cikis (Faz 2) ──

    def toplu_palet_cikis(
        self,
        kalemler: List[dict],
        kullanici: Kullanici,
        siparis_no: Optional[str] = None,
        aciklama: Optional[str] = None,
    ) -> List[TopluPaletSonuc]:
        """Birden fazla paletten tek seferde cikis yapar.

        kalemler: [{"palet_no": str, "miktar": Optional[int]}, ...]
        Pre-validation sonrasi all-or-nothing atomik islem.
        """
        sonuclar: List[TopluPaletSonuc] = []

        # --- Faz 1: Pre-validation ---
        for kalem in kalemler:
            palet_no = kalem["palet_no"]
            miktar = kalem.get("miktar")
            hata = self._cikis_on_dogrula(palet_no, miktar, kullanici)
            if hata:
                sonuclar.append(TopluPaletSonuc(palet_no=palet_no, basarili=False, hata_mesaji=hata))
            else:
                sonuclar.append(TopluPaletSonuc(palet_no=palet_no, basarili=True))

        # Herhangi bir hata varsa islem yapma
        if any(not s.basarili for s in sonuclar):
            return sonuclar

        # --- Faz 2: Atomik islem ---
        for i, kalem in enumerate(kalemler):
            hareket = self.palet_cikis(
                palet_no=kalem["palet_no"],
                kullanici=kullanici,
                miktar=kalem.get("miktar"),
                siparis_no=siparis_no,
                aciklama=aciklama,
            )
            sonuclar[i].hareket = hareket

        return sonuclar

    def _cikis_on_dogrula(
        self, palet_no: str, miktar: Optional[int], kullanici: Kullanici,
    ) -> Optional[str]:
        """Tek bir palet icin cikis on-dogrulama. Hata varsa mesaj doner, yoksa None."""
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
