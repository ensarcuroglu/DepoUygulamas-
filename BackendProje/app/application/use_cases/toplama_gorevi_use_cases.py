"""
Toplama Görevi (Pick Task) Use Case'leri.

Akış:
  PickTaskUretUseCase      — sevkiyat kalemi + rezervasyondan görev üretir
  SiradanGorevAlUseCase    — pull-based: ilk Beklemede görevi Atandı'ya çeker
  GorevBaslatUseCase       — Atandı → DevamEdiyor
  GorevTamamlaUseCase      — DevamEdiyor → Tamamlandı (tam koli zorunlu)
  GorevIptalUseCase        — herhangi aktif durumdan → IptalEdildi
  FefoOverrideUseCase      — admin: göreve farklı palet atar + override log
"""

from __future__ import annotations
from typing import List, Optional

from app.core.repositories.toplama_gorevi_repository import IToplamaGoreviRepository
from app.core.repositories.palet_rezervasyonu_repository import IPaletRezervasyonuRepository
from app.core.repositories.palet_repository import IPaletRepository
from app.core.repositories.stok_hareketi_repository import IStokHareketiRepository
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.repositories.sevkiyat_plani_repository import ISevkiyatPlaniRepository
from app.core.entities.toplama_gorevi import ToplamaGorevi, ToplamaGoreviDurum
from app.core.entities.stok_hareketi import StokHareketi, HareketTipi
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import (
    KayitBulunamadiError,
    GecersizIslemError,
    YetkisizIslemError,
)
from app.core.services.fefo_secim_servisi import FEFOSecimServisi
from app.application.dto.toplama_gorevi_dto import (
    ToplamaGoreviResponseDTO,
    FefoOverrideRequestDTO,
)


# ─────────────────────────────────────────────────────────────────
# GÖREV LİSTELE
# ─────────────────────────────────────────────────────────────────

class ToplamaGoreviListeleUseCase:

    def __init__(self, gorev_repo: IToplamaGoreviRepository):
        self._repo = gorev_repo

    def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        durum: Optional[str] = None,
        depo_id: Optional[int] = None,
        kullanici_id: Optional[int] = None,
        sevkiyat_id: Optional[int] = None,
    ) -> List[ToplamaGoreviResponseDTO]:
        gorevler = self._repo.getir_hepsi(
            skip=skip, limit=limit, durum=durum,
            depo_id=depo_id, kullanici_id=kullanici_id, sevkiyat_id=sevkiyat_id,
        )
        return [ToplamaGoreviResponseDTO.from_entity(g) for g in gorevler]


# ─────────────────────────────────────────────────────────────────
# GÖREV GETİR
# ─────────────────────────────────────────────────────────────────

class ToplamaGoreviGetirUseCase:

    def __init__(self, gorev_repo: IToplamaGoreviRepository):
        self._repo = gorev_repo

    def execute(self, gorev_id: int) -> ToplamaGoreviResponseDTO:
        gorev = self._repo.getir_id_ile(gorev_id)
        if not gorev:
            raise KayitBulunamadiError("Toplama Görevi", gorev_id)
        return ToplamaGoreviResponseDTO.from_entity(gorev)


# ─────────────────────────────────────────────────────────────────
# PICK TASK ÜRET
# ─────────────────────────────────────────────────────────────────

class PickTaskUretUseCase:
    """Sevkiyatın aktif rezervasyonlarından ToplamaGorevi (Beklemede) üretir.

    İdempotent: sevkiyat+palet için görev varsa skip edilir.
    """

    def __init__(
        self,
        gorev_repo: IToplamaGoreviRepository,
        rezervasyon_repo: IPaletRezervasyonuRepository,
        sevkiyat_repo: ISevkiyatPlaniRepository,
        palet_repo: IPaletRepository,
        log_repo: ISistemLogRepository,
    ):
        self._gorev_repo = gorev_repo
        self._rezervasyon_repo = rezervasyon_repo
        self._sevkiyat_repo = sevkiyat_repo
        self._palet_repo = palet_repo
        self._log_repo = log_repo

    def execute(self, sevkiyat_id: int, kullanici_id: int) -> List[ToplamaGoreviResponseDTO]:
        sevkiyat = self._sevkiyat_repo.getir_id_ile(sevkiyat_id)
        if not sevkiyat:
            raise KayitBulunamadiError("Sevkiyat", sevkiyat_id)

        # Sevkiyata bağlı aktif rezervasyonlar (siparis_id üzerinden)
        aktif_rezervasyonlar = self._rezervasyon_repo.getir_aktif_by_siparis(sevkiyat.siparis_id)
        if not aktif_rezervasyonlar:
            raise GecersizIslemError(
                "Sevkiyat için aktif palet rezervasyonu bulunamadı. "
                "Önce sipariş Hazırlanıyor durumuna geçirilmelidir."
            )

        olusturulan: List[ToplamaGorevi] = []
        for sira, rezervasyon in enumerate(aktif_rezervasyonlar, start=1):
            # İdempotency: bu sevkiyat + palet için görev var mı?
            if self._gorev_repo.gorev_var_mi(sevkiyat_id, rezervasyon.palet_id):
                continue

            palet = self._palet_repo.getir_id_ile(rezervasyon.palet_id)
            if not palet or not palet.aktif:
                continue

            urun_id = 0
            if palet.lot:
                urun_id = palet.lot.urun_id
            elif hasattr(palet, 'urun_id'):
                urun_id = palet.urun_id

            gorev = ToplamaGorevi(
                sevkiyat_id=sevkiyat_id,
                palet_id=rezervasyon.palet_id,
                lot_id=palet.lot_id,
                urun_id=urun_id,
                depo_id=getattr(palet.raf, "depo_id", None) if palet.raf else None,
                sira_no=sira,
            )
            kaydedilen = self._gorev_repo.olustur(gorev)
            olusturulan.append(kaydedilen)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.CREATE,
                modul="Toplama Görevi",
                detay=f"Sevkiyat #{sevkiyat_id} için {len(olusturulan)} toplama görevi üretildi.",
            )
        )

        return [ToplamaGoreviResponseDTO.from_entity(g) for g in olusturulan]


# ─────────────────────────────────────────────────────────────────
# SIRADAN GÖREV AL (pull-based)
# ─────────────────────────────────────────────────────────────────

class SiradanGorevAlUseCase:
    """Operatör sıradaki Beklemede görevi havuzdan çeker.

    # TODO Faz 2: getir_next_bekleyen içinde SELECT FOR UPDATE SKIP LOCKED uygulanacak.
    MVP'de son-yazar-kazanır riski kabul edilmiştir.
    """

    def __init__(self, gorev_repo: IToplamaGoreviRepository):
        self._repo = gorev_repo

    def execute(
        self,
        kullanici_id: int,
        depo_id: Optional[int] = None,
    ) -> Optional[ToplamaGoreviResponseDTO]:
        gorev = self._repo.getir_next_bekleyen(depo_id=depo_id)
        if not gorev:
            return None

        gorev.ata(kullanici_id)
        guncellenen = self._repo.guncelle(gorev)
        if not guncellenen:
            return None
        return ToplamaGoreviResponseDTO.from_entity(guncellenen)


# ─────────────────────────────────────────────────────────────────
# GÖREV BAŞLAT
# ─────────────────────────────────────────────────────────────────

class GorevBaslatUseCase:
    """Atandı → DevamEdiyor. Yalnızca atanan operatör başlatabilir."""

    def __init__(self, gorev_repo: IToplamaGoreviRepository):
        self._repo = gorev_repo

    def execute(self, gorev_id: int, kullanici_id: int) -> ToplamaGoreviResponseDTO:
        gorev = self._repo.getir_id_ile(gorev_id)
        if not gorev:
            raise KayitBulunamadiError("Toplama Görevi", gorev_id)

        if gorev.atanan_kullanici_id != kullanici_id:
            raise YetkisizIslemError("Bu görevi yalnızca atanan operatör başlatabilir.")

        gorev.baslat()
        guncellenen = self._repo.guncelle(gorev)
        return ToplamaGoreviResponseDTO.from_entity(guncellenen)


# ─────────────────────────────────────────────────────────────────
# GÖREV TAMAMLA
# ─────────────────────────────────────────────────────────────────

class GorevTamamlaUseCase:
    """DevamEdiyor → Tamamlandı.

    MVP kuralı: tam toplama zorunludur (kısmi kabul edilmez).
    İşlemler:
      1. Durum Tamamlandı
      2. Palet aktif=False (sevk edildi)
      3. Rezervasyon kesinleştirilir
      4. StokHareketi (Cikis) yazılır
    """

    def __init__(
        self,
        gorev_repo: IToplamaGoreviRepository,
        palet_repo: IPaletRepository,
        rezervasyon_repo: IPaletRezervasyonuRepository,
        hareket_repo: IStokHareketiRepository,
        log_repo: ISistemLogRepository,
    ):
        self._gorev_repo = gorev_repo
        self._palet_repo = palet_repo
        self._rezervasyon_repo = rezervasyon_repo
        self._hareket_repo = hareket_repo
        self._log_repo = log_repo

    def execute(self, gorev_id: int, kullanici_id: int) -> ToplamaGoreviResponseDTO:
        gorev = self._gorev_repo.getir_id_ile(gorev_id)
        if not gorev:
            raise KayitBulunamadiError("Toplama Görevi", gorev_id)

        if gorev.atanan_kullanici_id != kullanici_id:
            raise YetkisizIslemError("Bu görevi yalnızca atanan operatör tamamlayabilir.")

        if gorev.durum != ToplamaGoreviDurum.DEVAM_EDIYOR:
            raise GecersizIslemError(
                "Görev tamamlamak için DevamEdiyor durumunda olmalıdır."
            )

        palet = self._palet_repo.getir_id_ile(gorev.palet_id)
        if not palet or not palet.aktif:
            raise GecersizIslemError("Göreve ait palet aktif değil veya bulunamadı.")

        # 1. Görevi tamamla
        gorev.tamamla()
        self._gorev_repo.guncelle(gorev, auto_commit=False)

        # 2. Paleti devre dışı bırak
        palet.aktif = False
        self._palet_repo.guncelle(palet, auto_commit=False)

        # 3. Rezervasyonu kesinleştir
        rezervasyon = self._rezervasyon_repo.getir_aktif_by_palet(gorev.palet_id)
        if rezervasyon:
            rezervasyon.kesinlestir()
            self._rezervasyon_repo.guncelle(rezervasyon, auto_commit=False)

        # 4. StokHareketi (Cikis)
        hareket = StokHareketi(
            urun_id=gorev.urun_id,
            lot_id=gorev.lot_id,
            palet_id=gorev.palet_id,
            hareket_tipi=HareketTipi.CIKIS,
            miktar=palet.koli_adedi,
            aciklama=f"Toplama görevi #{gorev_id} tamamlandı",
            kullanici_id=kullanici_id,
            palet_no=palet.palet_no,
        )
        self._hareket_repo.olustur(hareket, auto_commit=False)

        # 5. Log (auto_commit=True → tüm flush'lar commit edilir)
        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Toplama Görevi",
                detay=(
                    f"Görev #{gorev_id} tamamlandı. "
                    f"Palet #{gorev.palet_id} sevk edildi ({palet.koli_adedi} koli)."
                ),
            )
        )

        return ToplamaGoreviResponseDTO.from_entity(gorev)


# ─────────────────────────────────────────────────────────────────
# GÖREV İPTAL
# ─────────────────────────────────────────────────────────────────

class GorevIptalUseCase:

    def __init__(
        self,
        gorev_repo: IToplamaGoreviRepository,
        rezervasyon_repo: IPaletRezervasyonuRepository,
        log_repo: ISistemLogRepository,
    ):
        self._gorev_repo = gorev_repo
        self._rezervasyon_repo = rezervasyon_repo
        self._log_repo = log_repo

    def execute(
        self,
        gorev_id: int,
        kullanici_id: int,
        neden: Optional[str] = None,
    ) -> ToplamaGoreviResponseDTO:
        gorev = self._gorev_repo.getir_id_ile(gorev_id)
        if not gorev:
            raise KayitBulunamadiError("Toplama Görevi", gorev_id)

        gorev.iptal_et(neden)
        self._gorev_repo.guncelle(gorev)

        # Rezervasyonu da iptal et (palet tekrar uygun hale gelir)
        rezervasyon = self._rezervasyon_repo.getir_aktif_by_palet(gorev.palet_id)
        if rezervasyon:
            rezervasyon.iptal_et(f"Görev #{gorev_id} iptal edildi")
            self._rezervasyon_repo.guncelle(rezervasyon)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Toplama Görevi",
                detay=f"Görev #{gorev_id} iptal edildi. Neden: {neden or '-'}",
            )
        )

        return ToplamaGoreviResponseDTO.from_entity(gorev)


# ─────────────────────────────────────────────────────────────────
# FEFO OVERRIDE (sadece admin)
# ─────────────────────────────────────────────────────────────────

class FefoOverrideUseCase:
    """Admin, mevcut göreve farklı palet atar ve override kaydeder.

    Kurallar:
    - Sadece admin rolü çağırabilir (router'da require_role + burada tekrar kontrol).
    - Görev Beklemede veya Atandı durumunda olmalıdır.
    - override_neden min 10 karakter (DTO validator'da).
    - SistemLog kategorisi: FEFO_OVERRIDE.
    """

    def __init__(
        self,
        gorev_repo: IToplamaGoreviRepository,
        rezervasyon_repo: IPaletRezervasyonuRepository,
        palet_repo: IPaletRepository,
        log_repo: ISistemLogRepository,
        fefo_servisi: Optional[FEFOSecimServisi] = None,
    ):
        self._gorev_repo = gorev_repo
        self._rezervasyon_repo = rezervasyon_repo
        self._palet_repo = palet_repo
        self._log_repo = log_repo
        self._fefo = fefo_servisi or FEFOSecimServisi()

    def execute(
        self,
        gorev_id: int,
        dto: FefoOverrideRequestDTO,
        kullanici_id: int,
        kullanici_rol: str,
    ) -> ToplamaGoreviResponseDTO:
        if kullanici_rol != "admin":
            raise YetkisizIslemError("FEFO override yalnızca admin tarafından yapılabilir.")

        gorev = self._gorev_repo.getir_id_ile(gorev_id)
        if not gorev:
            raise KayitBulunamadiError("Toplama Görevi", gorev_id)

        izin_verilen_durumlar = {ToplamaGoreviDurum.BEKLEMEDE, ToplamaGoreviDurum.ATANDI}
        if gorev.durum not in izin_verilen_durumlar:
            raise GecersizIslemError(
                f"FEFO override yalnızca {izin_verilen_durumlar} durumlarında yapılabilir."
            )

        yeni_palet = self._palet_repo.getir_id_ile(dto.yeni_palet_id)
        if not yeni_palet or not yeni_palet.aktif:
            raise KayitBulunamadiError("Palet", dto.yeni_palet_id)

        eski_palet_id = gorev.palet_id
        if dto.yeni_palet_id == eski_palet_id:
            raise GecersizIslemError(
                "FEFO override için mevcut görevden farklı bir palet seçilmelidir."
            )

        yeni_palet_urun_id = (
            yeni_palet.lot.urun_id
            if yeni_palet.lot
            else getattr(yeni_palet, "urun_id", None)
        )
        if yeni_palet_urun_id is None or yeni_palet_urun_id != gorev.urun_id:
            raise GecersizIslemError(
                "FEFO override yalnızca aynı ürüne ait aktif paletler için yapılabilir."
            )

        cakisan_rezervasyon = self._rezervasyon_repo.getir_aktif_by_palet(dto.yeni_palet_id)
        if cakisan_rezervasyon:
            raise GecersizIslemError(
                f"Palet #{dto.yeni_palet_id} zaten başka bir siparişe rezerve edilmiş."
            )

        # Eski rezervasyonu iptal et
        eski_rezervasyon = self._rezervasyon_repo.getir_aktif_by_palet(eski_palet_id)
        if eski_rezervasyon:
            eski_rezervasyon.iptal_et("FEFO override: palet değiştirildi")
            self._rezervasyon_repo.guncelle(eski_rezervasyon)

        # Yeni palet için rezervasyon oluştur
        from app.core.entities.palet_rezervasyonu import PaletRezervasyonu
        yeni_rez = PaletRezervasyonu(
            palet_id=dto.yeni_palet_id,
            siparis_id=eski_rezervasyon.siparis_id if eski_rezervasyon else 0,
            sevkiyat_kalemi_id=eski_rezervasyon.sevkiyat_kalemi_id if eski_rezervasyon else None,
        )
        self._rezervasyon_repo.olustur(yeni_rez)

        # Görevi güncelle
        gorev.palet_id = dto.yeni_palet_id
        gorev.lot_id = yeni_palet.lot_id
        gorev.urun_id = yeni_palet_urun_id
        gorev.fefo_override = True
        gorev.override_neden = dto.override_neden
        gorev.override_kullanici_id = kullanici_id
        self._gorev_repo.guncelle(gorev)

        # Audit log (FEFO_OVERRIDE kategorisi)
        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="FEFO_OVERRIDE",
                detay=(
                    f"Görev #{gorev_id}: palet #{eski_palet_id} → #{dto.yeni_palet_id}. "
                    f"Neden: {dto.override_neden}"
                ),
            )
        )

        return ToplamaGoreviResponseDTO.from_entity(gorev)
