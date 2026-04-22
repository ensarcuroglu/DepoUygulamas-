"""Üretim paleti giriş sistemi — application use case'leri.

Her use case transaction sınırını yönetir ve altyapı yan etkilerini
(StokHareketi yazımı, PaletDurumLog persist, SistemLog, commit) orkestre eder.
Domain service (UretimPaletService) saf iş kurallarını içerir; bu katman
onu çağırır ve sonucu persist eder.

Transaction Yönetimi:
  Tüm repo çağrıları auto_commit=False; işlem sonunda db.commit() tek seferlik.
  Hata durumunda db.rollback() ile kısmi yazımlar geri alınır.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.core.entities.kullanici import KullaniciRol
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.entities.stok_hareketi import StokHareketi, HareketTipi
from app.core.exceptions import (
    DepoErisimHatasi,
    GecersizIslemError,
    KayitBulunamadiError,
    YetkisizIslemError,
)
from app.application.dto.uretim_paleti_dto import (
    UretimPaletiOlusturRequestDTO,
    UretimPaletiResponseDTO,
)
from typing import List

if TYPE_CHECKING:
    from app.core.entities.kullanici import Kullanici
    from app.core.services.uretim_palet_service import UretimPaletService
    from app.core.services.uretim_seri_no_uretici import IUretimSeriNoUretici
    from app.core.services.kapasite_dogrulama_servisi import KapasiteDogrulamaServisi
    from app.core.repositories.palet_repository import IPaletRepository
    from app.core.repositories.lot_repository import ILotRepository
    from app.core.repositories.raf_repository import IRafRepository
    from app.core.repositories.stok_hareketi_repository import IStokHareketiRepository
    from app.core.repositories.palet_durum_log_repository import IPaletDurumLogRepository
    from app.core.repositories.sistem_log_repository import ISistemLogRepository


# ── Oluştur ──────────────────────────────────────────────────────────────────

class UretimPaletiOlusturUseCase:
    def __init__(
        self,
        domain_service: "UretimPaletService",
        seri_no_uretici: "IUretimSeriNoUretici",
        palet_repo: "IPaletRepository",
        lot_repo: "ILotRepository",
        raf_repo: "IRafRepository",
        durum_log_repo: "IPaletDurumLogRepository",
        sistem_log_repo: "ISistemLogRepository",
        db: Session,
    ):
        self._svc = domain_service
        self._seri = seri_no_uretici
        self._palet_repo = palet_repo
        self._lot_repo = lot_repo
        self._raf_repo = raf_repo
        self._durum_log_repo = durum_log_repo
        self._log_repo = sistem_log_repo
        self._db = db

    def execute(
        self,
        dto: UretimPaletiOlusturRequestDTO,
        kullanici: "Kullanici",
    ) -> UretimPaletiResponseDTO:
        _yetki_dogrula(kullanici, {KullaniciRol.DEPOCU, KullaniciRol.ADMIN})

        lot = self._lot_repo.getir_id_ile(dto.lot_id)
        if not lot:
            raise KayitBulunamadiError("Lot", dto.lot_id)

        uretim_tarihi = dto.uretim_tarihi or date.today()
        hedef_depo_id = dto.depo_id  # DTO'da zorunlu; pydantic valide eder.
        if not kullanici.depo_erisim_var(hedef_depo_id):
            raise DepoErisimHatasi(kullanici.depo_id, hedef_depo_id)

        staging_raf = self._raf_repo.getir_staging_raf(hedef_depo_id)
        if not staging_raf or staging_raf.id is None:
            raise GecersizIslemError(
                f"Depo {hedef_depo_id} için MIGRATION_STAGING rafı bulunamadı. "
                "Lütfen sistem yöneticisi ile iletişime geçin."
            )

        palet_no = self._seri.uret(uretim_tarihi)

        palet, log = self._svc.olustur(
            palet_no=palet_no,
            lot_id=dto.lot_id,
            raf_id=staging_raf.id,
            koli_adedi=dto.koli_adedi,
            uretim_tarihi=uretim_tarihi,
            lot_no=dto.lot_no,
            palet_kg=dto.palet_kg,
            vardiya=dto.vardiya,
            kullanici_id=kullanici.id,
            uretim_hatti=dto.uretim_hatti,
            makine_kodu=dto.makine_kodu,
            operator_kullanici_id=dto.operator_kullanici_id,
            brut_kg=dto.brut_kg,
            net_kg=dto.net_kg,
        )

        try:
            palet = self._palet_repo.olustur(palet, auto_commit=False)
            log.palet_id = palet.id  # flush ID'si atandı
            self._durum_log_repo.olustur(log, auto_commit=False)
            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici.id,
                    islem_tipi=IslemTipi.CREATE,
                    modul="Üretim Paleti",
                    detay=f"Üretim paleti oluşturuldu: {palet_no}",
                    yeni_veri={"palet_no": palet_no, "lot_id": dto.lot_id, "koli": dto.koli_adedi},
                ),
                auto_commit=False,
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

        return UretimPaletiResponseDTO.from_entity(palet)


# ── Kabul Bekle ───────────────────────────────────────────────────────────────

class UretimPaletiKabulBekleUseCase:
    """OLUSTURULDU → KABUL_BEKLIYOR. Depocu veya admin çağırabilir."""

    def __init__(
        self,
        domain_service: "UretimPaletService",
        palet_repo: "IPaletRepository",
        durum_log_repo: "IPaletDurumLogRepository",
        sistem_log_repo: "ISistemLogRepository",
        db: Session,
    ):
        self._svc = domain_service
        self._palet_repo = palet_repo
        self._durum_log_repo = durum_log_repo
        self._log_repo = sistem_log_repo
        self._db = db

    def execute(self, palet_no: str, kullanici: "Kullanici") -> UretimPaletiResponseDTO:
        _yetki_dogrula(kullanici, {KullaniciRol.DEPOCU, KullaniciRol.ADMIN})

        palet = self._palet_repo.getir_palet_no_ile(palet_no, kilitli_mi=True)
        if not palet:
            raise KayitBulunamadiError("Palet", palet_no)

        log = self._svc.kabul_bekle(palet, kullanici.id)
        try:
            palet = self._palet_repo.guncelle(palet, auto_commit=False)
            log.palet_id = palet.id  # type: ignore[assignment]
            self._durum_log_repo.olustur(log, auto_commit=False)
            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici.id,
                    islem_tipi=IslemTipi.UPDATE,
                    modul="Üretim Paleti",
                    detay=f"Kabul beklemeye alındı: {palet_no}",
                ),
                auto_commit=False,
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

        return UretimPaletiResponseDTO.from_entity(palet)


# ── Kabul Et ──────────────────────────────────────────────────────────────────

class UretimPaletiKabulEtUseCase:
    """OLUSTURULDU/KABUL_BEKLIYOR → KABUL_EDILDI → YERLESTIRME_BEKLIYOR + StokHareketi.GIRIS.

    Saha akışı: Tek barkod okutma ile kabul + otomatik yerleştirme bekle.
    """

    def __init__(
        self,
        domain_service: "UretimPaletService",
        palet_repo: "IPaletRepository",
        lot_repo: "ILotRepository",
        hareket_repo: "IStokHareketiRepository",
        durum_log_repo: "IPaletDurumLogRepository",
        sistem_log_repo: "ISistemLogRepository",
        db: Session,
    ):
        self._svc = domain_service
        self._palet_repo = palet_repo
        self._lot_repo = lot_repo
        self._hareket_repo = hareket_repo
        self._durum_log_repo = durum_log_repo
        self._log_repo = sistem_log_repo
        self._db = db

    def execute(self, palet_no: str, kullanici: "Kullanici") -> UretimPaletiResponseDTO:
        _yetki_dogrula(kullanici, {KullaniciRol.DEPOCU, KullaniciRol.ADMIN})

        palet = self._palet_repo.getir_palet_no_ile(palet_no, kilitli_mi=True)
        if not palet:
            raise KayitBulunamadiError("Palet", palet_no)

        lot = self._lot_repo.getir_id_ile(palet.lot_id)
        if not lot:
            raise KayitBulunamadiError("Lot", palet.lot_id)

        log = self._svc.kabul_et(palet, kullanici.id)

        # Otomatik: KABUL_EDILDI → YERLESTIRME_BEKLIYOR (saha 2-tarama modeli)
        log_yerlestirme = self._svc.yerlestirme_bekle(palet, kullanici.id)

        hareket = StokHareketi(
            urun_id=lot.urun_id,
            lot_id=lot.id,
            palet_id=palet.id,
            raf_id=palet.raf_id or None,
            hareket_tipi=HareketTipi.GIRIS,
            miktar=palet.koli_adedi,
            kullanici_id=kullanici.id,
            aciklama=f"Üretim paleti kabulü: {palet_no}",
            palet_no=palet_no,
        )

        try:
            palet = self._palet_repo.guncelle(palet, auto_commit=False)
            log.palet_id = palet.id  # type: ignore[assignment]
            self._durum_log_repo.olustur(log, auto_commit=False)
            log_yerlestirme.palet_id = palet.id  # type: ignore[assignment]
            self._durum_log_repo.olustur(log_yerlestirme, auto_commit=False)
            self._hareket_repo.olustur(hareket, auto_commit=False)
            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici.id,
                    islem_tipi=IslemTipi.UPDATE,
                    modul="Üretim Paleti",
                    detay=f"Üretim paleti kabul edildi ve yerleştirme bekliyor: {palet_no} ({palet.koli_adedi} koli)",
                ),
                auto_commit=False,
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

        dto = UretimPaletiResponseDTO.from_entity(palet)
        dto.yerlestirme_bekliyor = True
        return dto


# ── Karantinaya Al ────────────────────────────────────────────────────────────

class UretimPaletiKarantinaAlUseCase:
    """KABUL_EDILDI → KARANTINA. Depocu, admin veya kalite."""

    def __init__(
        self,
        domain_service: "UretimPaletService",
        palet_repo: "IPaletRepository",
        durum_log_repo: "IPaletDurumLogRepository",
        sistem_log_repo: "ISistemLogRepository",
        db: Session,
    ):
        self._svc = domain_service
        self._palet_repo = palet_repo
        self._durum_log_repo = durum_log_repo
        self._log_repo = sistem_log_repo
        self._db = db

    def execute(
        self,
        palet_no: str,
        kullanici: "Kullanici",
        sebep: str | None = None,
    ) -> UretimPaletiResponseDTO:
        if (
            kullanici.rol not in {KullaniciRol.DEPOCU, KullaniciRol.ADMIN}
            and not _kalite_departmaninda_mi(kullanici)
        ):
            raise YetkisizIslemError(
                "Bu işlem için depocu, admin veya kalite departmanı yetkisi gerekli."
            )

        palet = self._palet_repo.getir_palet_no_ile(palet_no, kilitli_mi=True)
        if not palet:
            raise KayitBulunamadiError("Palet", palet_no)

        log = self._svc.karantinaya_al(palet, kullanici.id, sebep)

        try:
            palet = self._palet_repo.guncelle(palet, auto_commit=False)
            log.palet_id = palet.id  # type: ignore[assignment]
            self._durum_log_repo.olustur(log, auto_commit=False)
            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici.id,
                    islem_tipi=IslemTipi.UPDATE,
                    modul="Üretim Paleti",
                    detay=f"Karantinaya alındı: {palet_no}" + (f" — {sebep}" if sebep else ""),
                ),
                auto_commit=False,
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

        return UretimPaletiResponseDTO.from_entity(palet)


# ── Karantinadan Çıkar ────────────────────────────────────────────────────────

class UretimPaletiKarantinaCikarUseCase:
    """KARANTINA → KABUL_EDILDI. Yalnızca admin veya kalite yetkisi."""

    def __init__(
        self,
        domain_service: "UretimPaletService",
        palet_repo: "IPaletRepository",
        durum_log_repo: "IPaletDurumLogRepository",
        sistem_log_repo: "ISistemLogRepository",
        db: Session,
    ):
        self._svc = domain_service
        self._palet_repo = palet_repo
        self._durum_log_repo = durum_log_repo
        self._log_repo = sistem_log_repo
        self._db = db

    def execute(
        self,
        palet_no: str,
        kullanici: "Kullanici",
        sebep: str | None = None,
    ) -> UretimPaletiResponseDTO:
        yetkili = kullanici.rol == KullaniciRol.ADMIN or _kalite_departmaninda_mi(kullanici)

        palet = self._palet_repo.getir_palet_no_ile(palet_no, kilitli_mi=True)
        if not palet:
            raise KayitBulunamadiError("Palet", palet_no)

        log = self._svc.karantinadan_cikar(palet, kullanici.id, yetkili=yetkili, sebep=sebep)

        try:
            palet = self._palet_repo.guncelle(palet, auto_commit=False)
            log.palet_id = palet.id  # type: ignore[assignment]
            self._durum_log_repo.olustur(log, auto_commit=False)
            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici.id,
                    islem_tipi=IslemTipi.UPDATE,
                    modul="Üretim Paleti",
                    detay=f"Karantinadan çıkarıldı: {palet_no}" + (f" — {sebep}" if sebep else ""),
                ),
                auto_commit=False,
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

        return UretimPaletiResponseDTO.from_entity(palet)


# ── İptal Et ──────────────────────────────────────────────────────────────────

class UretimPaletiIptalUseCase:
    """OLUSTURULDU/KABUL_BEKLIYOR → IPTAL_EDILDI. Yalnızca admin."""

    def __init__(
        self,
        domain_service: "UretimPaletService",
        palet_repo: "IPaletRepository",
        durum_log_repo: "IPaletDurumLogRepository",
        sistem_log_repo: "ISistemLogRepository",
        db: Session,
    ):
        self._svc = domain_service
        self._palet_repo = palet_repo
        self._durum_log_repo = durum_log_repo
        self._log_repo = sistem_log_repo
        self._db = db

    def execute(
        self,
        palet_no: str,
        kullanici: "Kullanici",
        sebep: str,
    ) -> UretimPaletiResponseDTO:
        _yetki_dogrula(kullanici, {KullaniciRol.ADMIN})

        palet = self._palet_repo.getir_palet_no_ile(palet_no, kilitli_mi=True)
        if not palet:
            raise KayitBulunamadiError("Palet", palet_no)

        # State machine yalnızca OLUSTURULDU/KABUL_BEKLIYOR → IPTAL_EDILDI geçişine izin verir;
        # bu durumlarda palet henüz stokta değildir (stok KABUL_EDILDI'da girer).
        log = self._svc.iptal_et(palet, kullanici.id, sebep)

        try:
            palet = self._palet_repo.guncelle(palet, auto_commit=False)
            log.palet_id = palet.id  # type: ignore[assignment]
            self._durum_log_repo.olustur(log, auto_commit=False)
            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici.id,
                    islem_tipi=IslemTipi.DELETE,
                    modul="Üretim Paleti",
                    detay=f"Üretim paleti iptal edildi: {palet_no} — {sebep}",
                ),
                auto_commit=False,
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

        return UretimPaletiResponseDTO.from_entity(palet)


# ── Yerleştirme Bekle ─────────────────────────────────────────────────────────

class UretimPaletiYerlestirmeBekleUseCase:
    """KABUL_EDILDI → YERLESTIRME_BEKLIYOR. Depocu veya admin."""

    def __init__(
        self,
        domain_service: "UretimPaletService",
        palet_repo: "IPaletRepository",
        durum_log_repo: "IPaletDurumLogRepository",
        sistem_log_repo: "ISistemLogRepository",
        db: Session,
    ):
        self._svc = domain_service
        self._palet_repo = palet_repo
        self._durum_log_repo = durum_log_repo
        self._log_repo = sistem_log_repo
        self._db = db

    def execute(self, palet_no: str, kullanici: "Kullanici") -> UretimPaletiResponseDTO:
        _yetki_dogrula(kullanici, {KullaniciRol.DEPOCU, KullaniciRol.ADMIN})

        palet = self._palet_repo.getir_palet_no_ile(palet_no, kilitli_mi=True)
        if not palet:
            raise KayitBulunamadiError("Palet", palet_no)

        log = self._svc.yerlestirme_bekle(palet, kullanici.id)

        try:
            palet = self._palet_repo.guncelle(palet, auto_commit=False)
            log.palet_id = palet.id  # type: ignore[assignment]
            self._durum_log_repo.olustur(log, auto_commit=False)
            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici.id,
                    islem_tipi=IslemTipi.UPDATE,
                    modul="Üretim Paleti",
                    detay=f"Yerleştirme beklemeye alındı: {palet_no}",
                ),
                auto_commit=False,
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

        return UretimPaletiResponseDTO.from_entity(palet)


# ── Yerleştir ─────────────────────────────────────────────────────────────────

class UretimPaletiYerlestirUseCase:
    """YERLESTIRME_BEKLIYOR → YERLESTIRILDI + raf kapasite kontrolü. Depocu veya admin."""

    def __init__(
        self,
        domain_service: "UretimPaletService",
        palet_repo: "IPaletRepository",
        raf_repo: "IRafRepository",
        kapasite_servisi: "KapasiteDogrulamaServisi",
        durum_log_repo: "IPaletDurumLogRepository",
        sistem_log_repo: "ISistemLogRepository",
        db: Session,
    ):
        self._svc = domain_service
        self._palet_repo = palet_repo
        self._raf_repo = raf_repo
        self._kapasite = kapasite_servisi
        self._durum_log_repo = durum_log_repo
        self._log_repo = sistem_log_repo
        self._db = db

    def execute(
        self,
        palet_no: str,
        raf_id: int,
        kullanici: "Kullanici",
    ) -> UretimPaletiResponseDTO:
        _yetki_dogrula(kullanici, {KullaniciRol.DEPOCU, KullaniciRol.ADMIN})

        palet = self._palet_repo.getir_palet_no_ile(palet_no, kilitli_mi=True)
        if not palet:
            raise KayitBulunamadiError("Palet", palet_no)

        # ── Raf kapasite kontrolü ──
        raf = self._raf_repo.getir_id_ile(raf_id)
        if not raf:
            raise KayitBulunamadiError("Raf", raf_id)

        kapasite_sonuc = self._kapasite.dogrula(raf, palet.palet_kg or 0.0)
        if not kapasite_sonuc.yeterli:
            raise GecersizIslemError(
                f"Hedef raf kapasitesi yetersiz: {kapasite_sonuc.neden}"
            )

        log = self._svc.yerlestir(palet, raf_id, kullanici.id)

        try:
            palet = self._palet_repo.guncelle(palet, auto_commit=False)
            log.palet_id = palet.id  # type: ignore[assignment]
            self._durum_log_repo.olustur(log, auto_commit=False)
            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici.id,
                    islem_tipi=IslemTipi.UPDATE,
                    modul="Üretim Paleti",
                    detay=f"Yerleştirildi: {palet_no} → raf {raf.kod} (ID: {raf_id})",
                ),
                auto_commit=False,
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

        return UretimPaletiResponseDTO.from_entity(palet)


# ── Listele / Getir (salt okunur) ─────────────────────────────────────────────

class UretimPaletleriListeleUseCase:
    """Üretim kaynaklı paletleri sayfalı listeler."""

    def __init__(self, palet_repo: "IPaletRepository"):
        self._palet_repo = palet_repo

    def execute(
        self,
        skip: int = 0,
        limit: int = 50,
        lot_id: Optional[int] = None,
        durum: Optional[str] = None,
        vardiya: Optional[str] = None,
        sadece_aktif: bool = True,
    ) -> List[UretimPaletiResponseDTO]:
        paletler = self._palet_repo.getir_hepsi(
            skip=skip,
            limit=limit,
            lot_id=lot_id,
            sadece_aktif=sadece_aktif,
            kaynak="uretim",
            durum=durum,
            vardiya=vardiya,
        )
        return [UretimPaletiResponseDTO.from_entity(p) for p in paletler]


class UretimPaletiGetirUseCase:
    """Palet numarasına göre tekil üretim paleti döner."""

    def __init__(self, palet_repo: "IPaletRepository"):
        self._palet_repo = palet_repo

    def execute(self, palet_no: str) -> UretimPaletiResponseDTO:
        palet = self._palet_repo.getir_palet_no_ile(palet_no)
        if not palet or not palet.uretim_paleti_mi:
            raise KayitBulunamadiError("Üretim paleti", palet_no)
        return UretimPaletiResponseDTO.from_entity(palet)


# ── Yardımcı ──────────────────────────────────────────────────────────────────

def _yetki_dogrula(kullanici: "Kullanici", izinli_roller: set[str]) -> None:
    if kullanici.rol not in izinli_roller:
        raise YetkisizIslemError(
            f"Bu işlem için yetkiniz yok. Gerekli roller: {', '.join(izinli_roller)}"
        )


def _kalite_departmaninda_mi(kullanici: "Kullanici") -> bool:
    return (kullanici.departman or "").strip().casefold() == "kalite"
