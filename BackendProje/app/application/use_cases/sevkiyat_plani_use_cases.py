"""
Sevkiyat Planı Use Case'leri.

İş kuralları:
- Durum geçişleri domain entity'deki SevkiyatDurum makinesi ile doğrulanır.
- Planlandi → Yukleniyor geçişi ve stok çıkışı yalnızca YuklemeOnaylaUseCase'den yapılabilir.
- Teslim edilmiş sevkiyatlar silinemez.
- Her kritik işlemde sistem logu yazılır.
"""

from __future__ import annotations
from datetime import datetime, date
from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.repositories.stok_hareketi_repository import IStokHareketiRepository
from app.core.repositories.sevkiyat_plani_repository import ISevkiyatPlaniRepository
from app.core.repositories.siparis_repository import ISiparisRepository
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.services.stok_cikis_domain_service import StokCikisDomainService
from app.core.entities.sevkiyat_plani import SevkiyatPlani, SevkiyatKalemi, SevkiyatDurum
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import (
    KayitBulunamadiError,
    GecersizDurumGecisiError,
    GecersizIslemError,
)
from app.application.dto.sevkiyat_plani_dto import (
    SevkiyatPlaniOlusturRequestDTO,
    SevkiyatPlaniGuncelleRequestDTO,
    SevkiyatPlaniResponseDTO,
)


# ─────────────────────────────────────────────────────────────────
# SEVKIYAT PLANI LİSTELE
# ─────────────────────────────────────────────────────────────────

class SevkiyatPlaniListeleUseCase:

    def __init__(self, sevkiyat_repo: ISevkiyatPlaniRepository):
        self._repo = sevkiyat_repo

    def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        durum: Optional[str] = None,
        tarih_baslang: Optional[date] = None,
        tarih_bitis: Optional[date] = None,
    ) -> List[SevkiyatPlaniResponseDTO]:
        planlar = self._repo.getir_hepsi(
            skip=skip, limit=limit, durum=durum,
            tarih_baslangic=tarih_baslang, tarih_bitis=tarih_bitis,
        )
        return [SevkiyatPlaniResponseDTO.from_entity(p) for p in planlar]


# ─────────────────────────────────────────────────────────────────
# SEVKIYAT PLANI GETİR
# ─────────────────────────────────────────────────────────────────

class SevkiyatPlaniGetirUseCase:

    def __init__(self, sevkiyat_repo: ISevkiyatPlaniRepository):
        self._repo = sevkiyat_repo

    def execute(self, plan_id: int) -> SevkiyatPlaniResponseDTO:
        plan = self._repo.getir_id_ile(plan_id)
        if not plan:
            raise KayitBulunamadiError("Sevkiyat Planı", plan_id)
        return SevkiyatPlaniResponseDTO.from_entity(plan)


# ─────────────────────────────────────────────────────────────────
# SEVKIYAT PLANI OLUŞTUR
# ─────────────────────────────────────────────────────────────────

class SevkiyatPlaniOlusturUseCase:

    def __init__(
        self,
        sevkiyat_repo: ISevkiyatPlaniRepository,
        siparis_repo: ISiparisRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = sevkiyat_repo
        self._siparis_repo = siparis_repo
        self._log_repo = log_repo

    def execute(
        self,
        dto: SevkiyatPlaniOlusturRequestDTO,
        kullanici_id: int,
    ) -> SevkiyatPlaniResponseDTO:
        siparis = self._siparis_repo.getir_id_ile(dto.siparis_id)
        if not siparis:
            raise KayitBulunamadiError("Sipariş", dto.siparis_id)

        plan = SevkiyatPlani(
            siparis_id=dto.siparis_id,
            tir_plaka=dto.tir_plaka,
            sofor_adi=dto.sofor_adi,
            sofor_telefon=dto.sofor_telefon,
            depo_kapi=dto.depo_kapi,
            yukleme_tarihi=dto.yukleme_tarihi,
            cikis_saati=dto.cikis_saati,
            varis_saati=dto.varis_saati,
            durum=dto.durum,
            notlar=dto.notlar,
        )

        kaydedilen = self._repo.olustur(plan)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.CREATE,
                modul="Sevkiyat Planlama",
                detay=f"Yeni sevkiyat planı oluşturuldu - Sipariş ID: {dto.siparis_id}",
            )
        )

        return SevkiyatPlaniResponseDTO.from_entity(kaydedilen)


# ─────────────────────────────────────────────────────────────────
# SEVKIYAT PLANI GÜNCELLE (durum geçişi + stok çıkışı)
# ─────────────────────────────────────────────────────────────────

class SevkiyatPlaniGuncelleUseCase:
    """
    Sevkiyat planını günceller (meta bilgi + belirli durum geçişleri).

    İş kuralları:
    - Durum değişimi varsa SevkiyatDurum makinesi ile doğrulanır.
    - Planlandi → Yukleniyor geçişi bu use case'den ENGELLENİR; yalnızca
      YuklemeOnaylaUseCase üzerinden yapılabilir (stok çıkışı komutu).
    - Güncelleme logu yazılır.
    """

    def __init__(
        self,
        sevkiyat_repo: ISevkiyatPlaniRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = sevkiyat_repo
        self._log_repo = log_repo

    def execute(
        self,
        plan_id: int,
        dto: SevkiyatPlaniGuncelleRequestDTO,
        kullanici_id: int,
    ) -> SevkiyatPlaniResponseDTO:
        plan = self._repo.getir_id_ile(plan_id)
        if not plan:
            raise KayitBulunamadiError("Sevkiyat Planı", plan_id)

        eski_durum = plan.durum

        if dto.tir_plaka is not None:
            plan.tir_plaka = dto.tir_plaka
        if dto.sofor_adi is not None:
            plan.sofor_adi = dto.sofor_adi
        if dto.sofor_telefon is not None:
            plan.sofor_telefon = dto.sofor_telefon
        if dto.depo_kapi is not None:
            plan.depo_kapi = dto.depo_kapi
        if dto.yukleme_tarihi is not None:
            plan.yukleme_tarihi = dto.yukleme_tarihi
        if dto.cikis_saati is not None:
            plan.cikis_saati = dto.cikis_saati
        if dto.varis_saati is not None:
            plan.varis_saati = dto.varis_saati
        if dto.notlar is not None:
            plan.notlar = dto.notlar

        durum_degisti = dto.durum is not None and dto.durum != eski_durum

        if durum_degisti:
            if (
                eski_durum == SevkiyatDurum.PLANLANDI
                and dto.durum == SevkiyatDurum.YUKLENIYOR
            ):
                raise GecersizIslemError(
                    "Planlandi → Yukleniyor geçişi yalnızca yükleme onayı "
                    "(POST /sevkiyat-planlama/{id}/yukleme-onayla) ile yapılabilir."
                )
            if not SevkiyatDurum.gecis_gecerli_mi(eski_durum, dto.durum):
                raise GecersizDurumGecisiError("Sevkiyat Planı", eski_durum, dto.durum)
            plan.durum = dto.durum

        plan.guncelleme_tarihi = datetime.utcnow()

        kaydedilen = self._repo.guncelle(plan)

        if durum_degisti:
            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici_id,
                    islem_tipi=IslemTipi.UPDATE,
                    modul="Sevkiyat Planlama",
                    detay=f"Sevkiyat planı durumu değiştirildi. Durum: {eski_durum} → {dto.durum}",
                )
            )

        return SevkiyatPlaniResponseDTO.from_entity(kaydedilen)


# ─────────────────────────────────────────────────────────────────
# YÜKLEME ONAYLA — stok çıkışının tek yetkili komutu
# ─────────────────────────────────────────────────────────────────

class YuklemeOnaylaUseCase:
    """
    Sevkiyat yüklemesini onaylayan komut.

    İş kuralları:
    - Plan Planlandi durumunda olmalıdır (mükerrer onay reddedilir).
    - Sipariş kalemlerinden 1:1 sevkiyat kalemleri oluşturulur.
    - FIFO stok çıkışı yapılır.
    - Plan durumu Yukleniyor yapılır.
    - Tüm işlemler tek transaction'da commit edilir; hatada rollback.
    """

    def __init__(
        self,
        sevkiyat_repo: ISevkiyatPlaniRepository,
        siparis_repo: ISiparisRepository,
        hareket_repo: IStokHareketiRepository,
        log_repo: ISistemLogRepository,
        stok_cikis_service: StokCikisDomainService,
        db: Session,
    ):
        self._repo = sevkiyat_repo
        self._siparis_repo = siparis_repo
        self._hareket_repo = hareket_repo
        self._log_repo = log_repo
        self._stok_cikis = stok_cikis_service
        self._db = db

    def execute(self, plan_id: int, kullanici_id: int) -> SevkiyatPlaniResponseDTO:
        plan = self._repo.getir_id_ile_kilitli(plan_id)
        if not plan:
            raise KayitBulunamadiError("Sevkiyat Planı", plan_id)

        if plan.durum != SevkiyatDurum.PLANLANDI:
            raise GecersizIslemError(
                f"Yükleme onayı yalnızca 'Planlandi' durumundaki planlar için yapılabilir. "
                f"Mevcut durum: '{plan.durum}'."
            )

        siparis = self._siparis_repo.getir_id_ile(plan.siparis_id)
        if not siparis:
            raise KayitBulunamadiError("Sipariş", plan.siparis_id)
        if not siparis.kalemler:
            raise GecersizIslemError(
                "Siparişte kalem bulunmadığından yükleme onayı yapılamaz."
            )
        if self._hareket_repo.siparis_icin_cikis_var_mi(siparis.siparis_no):
            raise GecersizIslemError(
                "Bu sipariş için daha önce stok çıkışı işlendiği tespit edildi. "
                "Çifte stok düşümünü önlemek için yükleme onayı durduruldu."
            )
        if plan.kalemler:
            raise GecersizIslemError(
                "Bu sevkiyat için yükleme kalemleri zaten oluşturulmuş. "
                "Planı yenileyip tekrar deneyin."
            )

        plan.kalemler.extend(
            SevkiyatKalemi(
                sevkiyat_id=plan.id,
                siparis_kalemi_id=k.id,
                urun_id=k.urun_id,
                miktar=k.miktar,
            )
            for k in siparis.kalemler
        )
        plan.durum = SevkiyatDurum.YUKLENIYOR
        plan.guncelleme_tarihi = datetime.utcnow()

        try:
            kaydedilen = self._repo.guncelle(plan, auto_commit=False)

            self._stok_cikis.siparis_bazli_stok_cikisi(
                kalemler=siparis.kalemler,
                siparis_no=siparis.siparis_no,
                kullanici_id=kullanici_id,
                tir_plaka=plan.tir_plaka,
                depo_kapi=plan.depo_kapi,
                aciklama_prefix="Sevkiyat yüklemesi",
                modul="Sevkiyat Planlama",
            )

            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici_id,
                    islem_tipi=IslemTipi.UPDATE,
                    modul="Sevkiyat Planlama",
                    detay=(
                        f"Yükleme onaylandı - Plan ID: {plan.id}, "
                        f"Sipariş: {siparis.siparis_no}"
                    ),
                ),
                auto_commit=False,
            )

            self._db.commit()
            return SevkiyatPlaniResponseDTO.from_entity(kaydedilen)

        except IntegrityError as exc:
            self._db.rollback()
            raise GecersizIslemError(
                "Yükleme onayı başka bir işlem tarafından aynı anda işlendi. "
                "Lütfen planı yenileyip tekrar deneyin."
            ) from exc
        except Exception:
            self._db.rollback()
            raise


# ─────────────────────────────────────────────────────────────────
# SEVKIYAT PLANI SİL
# ─────────────────────────────────────────────────────────────────

class SevkiyatPlaniSilUseCase:
    """
    Sevkiyat planını siler.

    İş kuralları:
    - Plan bulunamazsa KayitBulunamadiError.
    - Teslim edilmiş planlar silinemez.
    - Silme logu yazılır.
    """

    def __init__(
        self,
        sevkiyat_repo: ISevkiyatPlaniRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = sevkiyat_repo
        self._log_repo = log_repo

    def execute(self, plan_id: int, kullanici_id: int) -> None:
        plan = self._repo.getir_id_ile(plan_id)
        if not plan:
            raise KayitBulunamadiError("Sevkiyat Planı", plan_id)

        if plan.teslim_edildi_mi():
            raise GecersizIslemError("Teslim edilmiş sevkiyat planları silinemez.")

        self._repo.sil(plan_id)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.DELETE,
                modul="Sevkiyat Planlama",
                detay=f"Sevkiyat planı silindi - Sipariş ID: {plan.siparis_id}",
            )
        )
