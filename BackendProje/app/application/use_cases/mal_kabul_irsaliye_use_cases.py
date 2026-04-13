"""
Mal Kabul İrsaliyesi Use Case'leri.

Mal kabul belgesi CRUD + durum geçişleri.
Kalemler (palet tanımları) irsaliye ile birlikte yönetilir.
"""

from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy.orm import Session

from app.core.repositories.mal_kabul_irsaliye_repository import IMalKabulIrsaliyeRepository
from app.core.repositories.tedarikci_repository import ITedarikciRepository
from app.core.repositories.depo_repository import IDepoRepository
from app.core.repositories.urun_repository import IUrunRepository
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.repositories.lot_repository import ILotRepository
from app.core.repositories.palet_repository import IPaletRepository
from app.core.repositories.stok_hareketi_repository import IStokHareketiRepository
from app.core.repositories.raf_repository import IRafRepository
from app.core.repositories.yerlestirme_gorevi_repository import IYerlestirmeGoreviRepository
from app.core.entities.mal_kabul_irsaliye import (
    MalKabulIrsaliye,
    MalKabulKalemi,
    MalKabulDurum,
)
from app.core.entities.lot import Lot
from app.core.entities.palet import Palet
from app.core.entities.stok_hareketi import StokHareketi, HareketTipi
from app.core.entities.yerlestirme_gorevi import YerlestirmeGorevi, GorevTipi
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import KayitBulunamadiError, GecersizDurumGecisiError, GecersizIslemError
from app.application.dto.mal_kabul_irsaliye_dto import (
    MalKabulIrsaliyeOlusturRequestDTO,
    MalKabulIrsaliyeGuncelleRequestDTO,
    MalKabulIrsaliyeResponseDTO,
    MalKabulKalemiOlusturDTO,
    MalKabulKalemiIstisnaRequestDTO,
)

if TYPE_CHECKING:
    from app.core.services.yerlestirme_algoritmasi import YerlestirmeAlgoritmasi


def _dto_to_kalem_entity(dto: MalKabulKalemiOlusturDTO) -> MalKabulKalemi:
    return MalKabulKalemi(
        palet_no=dto.palet_no,
        urun_id=dto.urun_id,
        lot_no=dto.lot_no,
        miktar=dto.miktar,
        raf_id=dto.raf_id,
        uretim_tarihi=dto.uretim_tarihi,
        son_kullanma_tarihi=dto.son_kullanma_tarihi,
    )


def _urunleri_dogrula(urun_repo: IUrunRepository, kalem_dtolar: list[MalKabulKalemiOlusturDTO]) -> None:
    urun_idler = {k.urun_id for k in kalem_dtolar}
    for urun_id in urun_idler:
        if not urun_repo.getir_id_ile(urun_id):
            raise KayitBulunamadiError("Ürün", urun_id)


# ─────────────────────────────────────────────────────────────────
# LİSTELE
# ─────────────────────────────────────────────────────────────────

class MalKabulIrsaliyeListeleUseCase:

    def __init__(self, repo: IMalKabulIrsaliyeRepository):
        self._repo = repo

    def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        durum: Optional[str] = None,
        arama: Optional[str] = None,
        depo_id: Optional[int] = None,
        tedarikci_id: Optional[int] = None,
    ) -> List[MalKabulIrsaliyeResponseDTO]:
        irsaliyeler = self._repo.getir_hepsi(
            skip=skip, limit=limit, durum=durum, arama=arama,
            depo_id=depo_id, tedarikci_id=tedarikci_id,
        )
        return [MalKabulIrsaliyeResponseDTO.from_entity(i) for i in irsaliyeler]


# ─────────────────────────────────────────────────────────────────
# GETİR
# ─────────────────────────────────────────────────────────────────

class MalKabulIrsaliyeGetirUseCase:

    def __init__(self, repo: IMalKabulIrsaliyeRepository):
        self._repo = repo

    def execute(self, irsaliye_id: int) -> MalKabulIrsaliyeResponseDTO:
        irsaliye = self._repo.getir_id_ile(irsaliye_id)
        if not irsaliye:
            raise KayitBulunamadiError("Mal Kabul İrsaliyesi", irsaliye_id)
        return MalKabulIrsaliyeResponseDTO.from_entity(irsaliye)


# ─────────────────────────────────────────────────────────────────
# OLUŞTUR
# ─────────────────────────────────────────────────────────────────

class MalKabulIrsaliyeOlusturUseCase:

    def __init__(
        self,
        repo: IMalKabulIrsaliyeRepository,
        tedarikci_repo: ITedarikciRepository,
        depo_repo: IDepoRepository,
        urun_repo: IUrunRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = repo
        self._tedarikci_repo = tedarikci_repo
        self._depo_repo = depo_repo
        self._urun_repo = urun_repo
        self._log_repo = log_repo

    def execute(
        self,
        dto: MalKabulIrsaliyeOlusturRequestDTO,
        kullanici_id: int,
    ) -> MalKabulIrsaliyeResponseDTO:
        # Ön koşullar
        tedarikci = self._tedarikci_repo.getir_id_ile(dto.tedarikci_id)
        if not tedarikci:
            raise KayitBulunamadiError("Tedarikçi", dto.tedarikci_id)

        depo = self._depo_repo.getir_id_ile(dto.depo_id)
        if not depo:
            raise KayitBulunamadiError("Depo", dto.depo_id)

        # Kalem ürünlerini doğrula (deduplicated)
        _urunleri_dogrula(self._urun_repo, dto.kalemler)

        # Entity oluştur
        irsaliye_no = self._repo.sonraki_irsaliye_no()
        kalemler = [_dto_to_kalem_entity(k) for k in dto.kalemler]

        irsaliye = MalKabulIrsaliye(
            irsaliye_no=irsaliye_no,
            tedarikci_id=dto.tedarikci_id,
            depo_id=dto.depo_id,
            tarih=dto.tarih,
            tir_plaka=dto.tir_plaka,
            sofor_adi=dto.sofor_adi,
            kalemler=kalemler,
        )

        kaydedilen = self._repo.olustur(irsaliye)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.CREATE,
                modul="Mal Kabul İrsaliyesi",
                detay=f"Yeni mal kabul irsaliyesi: {irsaliye_no} | {len(kalemler)} kalem",
            )
        )

        return MalKabulIrsaliyeResponseDTO.from_entity(kaydedilen)


# ─────────────────────────────────────────────────────────────────
# GÜNCELLE
# ─────────────────────────────────────────────────────────────────

class MalKabulIrsaliyeGuncelleUseCase:

    def __init__(
        self,
        repo: IMalKabulIrsaliyeRepository,
        urun_repo: IUrunRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = repo
        self._urun_repo = urun_repo
        self._log_repo = log_repo

    def execute(
        self,
        irsaliye_id: int,
        dto: MalKabulIrsaliyeGuncelleRequestDTO,
        kullanici_id: int,
    ) -> MalKabulIrsaliyeResponseDTO:
        irsaliye = self._repo.getir_id_ile(irsaliye_id)
        if not irsaliye:
            raise KayitBulunamadiError("Mal Kabul İrsaliyesi", irsaliye_id)

        eski_durum = irsaliye.durum

        # Durum geçişi
        if dto.durum is not None and dto.durum != eski_durum:
            try:
                irsaliye.durum_degistir(dto.durum)
            except ValueError as e:
                raise GecersizDurumGecisiError(
                    "Mal Kabul İrsaliyesi", eski_durum, dto.durum
                ) from e

        # Basit alan güncellemeleri (sadece taslakta)
        if eski_durum == MalKabulDurum.TASLAK:
            if dto.tedarikci_id is not None:
                irsaliye.tedarikci_id = dto.tedarikci_id
            if dto.depo_id is not None:
                irsaliye.depo_id = dto.depo_id
            if dto.tarih is not None:
                irsaliye.tarih = dto.tarih
            if dto.tir_plaka is not None:
                irsaliye.tir_plaka = dto.tir_plaka
            if dto.sofor_adi is not None:
                irsaliye.sofor_adi = dto.sofor_adi

            # Kalem güncellemesi
            if dto.kalemler is not None:
                _urunleri_dogrula(self._urun_repo, dto.kalemler)
                irsaliye.kalemler = [_dto_to_kalem_entity(k) for k in dto.kalemler]

        kaydedilen = self._repo.guncelle(irsaliye)

        # Durum değişikliği loglama
        if dto.durum and dto.durum != eski_durum:
            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici_id,
                    islem_tipi=IslemTipi.UPDATE,
                    modul="Mal Kabul İrsaliyesi",
                    detay=f"İrsaliye durumu: {eski_durum} → {dto.durum} | {irsaliye.irsaliye_no}",
                )
            )

        return MalKabulIrsaliyeResponseDTO.from_entity(kaydedilen)


# ─────────────────────────────────────────────────────────────────
# SİL
# ─────────────────────────────────────────────────────────────────

class MalKabulIrsaliyeSilUseCase:

    def __init__(
        self,
        repo: IMalKabulIrsaliyeRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = repo
        self._log_repo = log_repo

    def execute(self, irsaliye_id: int, kullanici_id: int) -> bool:
        irsaliye = self._repo.getir_id_ile(irsaliye_id)
        if not irsaliye:
            raise KayitBulunamadiError("Mal Kabul İrsaliyesi", irsaliye_id)

        if not irsaliye.duzenlenebilir_mi():
            raise GecersizIslemError(
                f"Sadece taslak durumundaki irsaliyeler silinebilir. Mevcut durum: {irsaliye.durum}"
            )

        silindi = self._repo.sil(irsaliye_id)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.DELETE,
                modul="Mal Kabul İrsaliyesi",
                detay=f"İrsaliye silindi: {irsaliye.irsaliye_no}",
            )
        )

        return silindi


# ─────────────────────────────────────────────────────────────────
# İRSALİYE ONAYLA VE GÖREV OLUŞTUR (Faz 2.1)
# ─────────────────────────────────────────────────────────────────

class IrsaliyeOnaylaVeGorevOlusturUseCase:
    """
    İrsaliye onayında her kalem için Palet + StokHareketi + YerlestirmeGorevi oluşturur.

    Akış:
      1. İrsaliye doğrula (durum TASLAK olmalı)
      2. MIGRATION_STAGING rafını bul (onerilen_raf yoksa staging'e atanır)
      3. Her kalem için:
         a. Lot bul veya oluştur
         b. Palet oluştur (raf_id = STAGING)
         c. StokHareketi (giris) oluştur
         d. YerlestirmeAlgoritmasi çalıştır → önerilen raf
         e. YerlestirmeGorevi oluştur (durum = BEKLIYOR)
         f. Kalemi GirisYapildi olarak işaretle
      4. İrsaliyeyi ONAYLANDI durumuna geçir
      5. Tek transaction ile commit
    """

    def __init__(
        self,
        repo: IMalKabulIrsaliyeRepository,
        urun_repo: IUrunRepository,
        lot_repo: ILotRepository,
        palet_repo: IPaletRepository,
        hareket_repo: IStokHareketiRepository,
        gorev_repo: IYerlestirmeGoreviRepository,
        raf_repo: IRafRepository,
        yerlestirme_algoritmasi: "YerlestirmeAlgoritmasi",
        log_repo: ISistemLogRepository,
        db: Session,
    ):
        self._repo = repo
        self._urun_repo = urun_repo
        self._lot_repo = lot_repo
        self._palet_repo = palet_repo
        self._hareket_repo = hareket_repo
        self._gorev_repo = gorev_repo
        self._raf_repo = raf_repo
        self._algoritma = yerlestirme_algoritmasi
        self._log_repo = log_repo
        self._db = db

    def execute(
        self, irsaliye_id: int, kullanici_id: int
    ) -> MalKabulIrsaliyeResponseDTO:
        irsaliye = self._repo.getir_id_ile(irsaliye_id)
        if not irsaliye:
            raise KayitBulunamadiError("Mal Kabul İrsaliyesi", irsaliye_id)

        if irsaliye.durum != MalKabulDurum.TASLAK:
            raise GecersizIslemError(
                f"Sadece Taslak durumundaki irsaliyeler onaylanabilir. Mevcut durum: {irsaliye.durum}"
            )
        if not irsaliye.kalemler:
            raise GecersizIslemError("Kalemsiz irsaliye onaylanamaz.")

        staging_raf = self._raf_repo.getir_staging_raf(irsaliye.depo_id)
        if not staging_raf:
            raise GecersizIslemError(
                f"Depo {irsaliye.depo_id} için MIGRATION_STAGING rafı bulunamadı. "
                "Lütfen migrate_putaway_system.py'yi çalıştırın."
            )

        try:
            for kalem in irsaliye.kalemler:
                if not kalem.giris_bekliyor_mu():
                    continue

                urun = self._urun_repo.getir_id_ile(kalem.urun_id)
                # Pyright'a urun.id'nin None olmadığını kanıtla
                if not urun or urun.id is None:
                    raise KayitBulunamadiError("Ürün", kalem.urun_id)

                lot = self._lot_bul_veya_olustur(kalem)
                
                # Repository'den dönen nesnelerin ID'si None olmamalı
                if lot.id is None:
                    raise GecersizIslemError("Lot oluşturuldu fakat ID alınamadı.")
                if staging_raf.id is None:
                    raise GecersizIslemError("Staging raf ID bulunamadı.")

                palet = Palet(
                    lot_id=lot.id,
                    raf_id=staging_raf.id,
                    palet_no=kalem.palet_no,
                    koli_adedi=kalem.miktar,
                )
                palet = self._palet_repo.olustur(palet, auto_commit=False)
                
                # Yeni oluşturulan paletin ID'sini doğrula
                if palet.id is None:
                    raise GecersizIslemError("Palet oluşturuldu fakat ID alınamadı. Flush eksik olabilir.")

                hareket = StokHareketi(
                    urun_id=urun.id,
                    lot_id=lot.id,
                    palet_id=palet.id,
                    raf_id=staging_raf.id,
                    hareket_tipi=HareketTipi.GIRIS,
                    miktar=kalem.miktar,
                    irsaliye_no=irsaliye.irsaliye_no,
                    kullanici_id=kullanici_id,
                    aciklama=f"Mal kabul girişi: {irsaliye.irsaliye_no} — {kalem.palet_no}",
                )
                self._hareket_repo.olustur(hareket, auto_commit=False)

                oneri = self._algoritma.raf_oner(palet, urun, irsaliye.depo_id)
                
                # Onerilen raf ID'si için güvenli atama
                if oneri and oneri.onerilen_raf.id is not None:
                    onerilen_raf_id = oneri.onerilen_raf.id
                else:
                    onerilen_raf_id = staging_raf.id

                # irsaliye.id'nin None olamayacağını da garantilemek isteyebilirsin
                assert irsaliye.id is not None, "İrsaliye ID eksik"

                gorev = YerlestirmeGorevi(
                    palet_id=palet.id,
                    mal_kabul_irsaliye_id=irsaliye.id,
                    depo_id=irsaliye.depo_id,
                    tip=GorevTipi.YERLESTIRME,
                    onerilen_raf_id=onerilen_raf_id,
                    oncelik=5,
                )
                self._gorev_repo.olustur(gorev)

                kalem.giris_yapildi()
        except Exception:
            self._db.rollback()
            raise

        olusturulan_gorev_sayisi = len(irsaliye.kalemler)
        return MalKabulIrsaliyeResponseDTO.from_entity(
            self._repo.getir_id_ile(irsaliye_id),
            olusturulan_gorev_sayisi=olusturulan_gorev_sayisi,
        )

    def _lot_bul_veya_olustur(self, kalem: MalKabulKalemi) -> Lot:
        if kalem.lot_no:
            mevcut = self._lot_repo.getir_lot_no_ile(kalem.lot_no)
            if mevcut:
                return mevcut
        lot = Lot(
            urun_id=kalem.urun_id,
            lot_no=kalem.lot_no,
            uretim_tarihi=kalem.uretim_tarihi,
            son_kullanma_tarihi=kalem.son_kullanma_tarihi,
        )
        return self._lot_repo.olustur(lot, auto_commit=False)


# ─────────────────────────────────────────────────────────────────
# KALEM İSTİSNA BİLDİR
# ─────────────────────────────────────────────────────────────────

class MalKabulKalemiIstisnaBildirUseCase:
    """
    Mal kabul kalemi için fark/hasar/istisna kaydeder.

    Kural: İrsaliye TASLAK veya ONAYLANDI ise bildirilebilir.
    KAPANDI durumunda hata verir.
    """

    def __init__(
        self,
        repo: IMalKabulIrsaliyeRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = repo
        self._log_repo = log_repo

    def execute(
        self,
        irsaliye_id: int,
        kalem_id: int,
        dto: MalKabulKalemiIstisnaRequestDTO,
        kullanici_id: int,
    ) -> MalKabulIrsaliyeResponseDTO:
        irsaliye = self._repo.getir_id_ile(irsaliye_id)
        if not irsaliye:
            raise KayitBulunamadiError("Mal Kabul İrsaliyesi", irsaliye_id)

        if irsaliye.durum == MalKabulDurum.KAPANDI:
            raise GecersizIslemError(
                "Kapanmış irsaliyeler için istisna bildirilemez."
            )

        kalem = next((k for k in irsaliye.kalemler if k.id == kalem_id), None)
        if not kalem:
            raise KayitBulunamadiError("Mal Kabul Kalemi", kalem_id)

        kalem.istisna_bildir(
            tip=dto.istisna_tip,
            aciklama=dto.istisna_aciklama,
            gerceklesen_miktar=dto.gerceklesen_miktar,
        )

        self._repo.kalem_guncelle(
            kalem_id=kalem_id,
            istisna_tip=kalem.istisna_tip,
            istisna_aciklama=kalem.istisna_aciklama,
            gerceklesen_miktar=kalem.gerceklesen_miktar,
        )

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Mal Kabul İrsaliyesi",
                detay=(
                    f"Kalem istisna: {dto.istisna_tip} | "
                    f"İrsaliye: {irsaliye.irsaliye_no} | Kalem: {kalem_id}"
                ),
            )
        )

        return MalKabulIrsaliyeResponseDTO.from_entity(
            self._repo.getir_id_ile(irsaliye_id)
        )


class InboundDashboardUseCase:
    """Inbound kontrol paneli istatistiklerini döner."""

    def __init__(self, repo: IMalKabulIrsaliyeRepository):
        self._repo = repo

    def execute(self):
        from app.application.dto.mal_kabul_irsaliye_dto import (
            InboundDashboardResponseDTO,
            InboundIrsaliyeOzetDTO,
        )
        data = self._repo.inbound_dashboard_istatistik()
        return InboundDashboardResponseDTO(
            irsaliye_toplam=data["irsaliye_toplam"],
            irsaliye_taslak=data["irsaliye_taslak"],
            irsaliye_onaylandi=data["irsaliye_onaylandi"],
            irsaliye_kapandi=data["irsaliye_kapandi"],
            gorev_toplam=data["gorev_toplam"],
            gorev_bekleyen=data["gorev_bekleyen"],
            gorev_devam_eden=data["gorev_devam_eden"],
            gorev_tamamlanan=data["gorev_tamamlanan"],
            gorev_iptal=data["gorev_iptal"],
            ort_yerlestirme_sure_dk=data["ort_yerlestirme_sure_dk"],
            istisna_sayisi=data["istisna_sayisi"],
            override_sayisi=data["override_sayisi"],
            bugunun_irsaliyeleri=[
                InboundIrsaliyeOzetDTO(**irs)
                for irs in data["bugunun_irsaliyeleri"]
            ],
        )
