"""
Sipariş Use Case'leri.

İş kuralları:
- Sipariş oluşturulurken otomatik SIP-YYYY-NNNN numarası atanır.
- Kalem toplamları (KDV dahil) Use Case'de hesaplanır.
- Durum geçişleri domain entity'deki SiparisDurum makinesi ile doğrulanır.
- Her kritik işlemde sistem logu yazılır.
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional

from app.core.repositories.siparis_repository import ISiparisRepository
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.entities.siparis import Siparis, SiparisKalemi, SiparisDurum
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import (
    KayitBulunamadiError,
    GecersizDurumGecisiError,
    GecersizIslemError,
)
from app.application.dto.siparis_dto import (
    SiparisKalemiOlusturRequestDTO,
    SiparisOlusturRequestDTO,
    SiparisGuncelleRequestDTO,
    SiparisResponseDTO,
    SiparisDetayResponseDTO,
)


# ─────────────────────────────────────────────────────────────────
# SİPARİŞ LİSTELE
# ─────────────────────────────────────────────────────────────────

class SiparisListeleUseCase:

    def __init__(self, siparis_repo: ISiparisRepository):
        self._repo = siparis_repo

    def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        durum: Optional[str] = None,
        arama: Optional[str] = None,
    ) -> List[SiparisResponseDTO]:
        siparisler = self._repo.getir_hepsi(
            skip=skip, limit=limit, durum=durum, arama=arama
        )
        return [SiparisResponseDTO.from_entity(s) for s in siparisler]


# ─────────────────────────────────────────────────────────────────
# SİPARİŞ GETİR
# ─────────────────────────────────────────────────────────────────

class SiparisGetirUseCase:

    def __init__(self, siparis_repo: ISiparisRepository):
        self._repo = siparis_repo

    def execute(self, siparis_id: int) -> SiparisDetayResponseDTO:
        siparis = self._repo.getir_id_ile(siparis_id)
        if not siparis:
            raise KayitBulunamadiError("Sipariş", siparis_id)
        return SiparisDetayResponseDTO.from_entity(siparis)


# ─────────────────────────────────────────────────────────────────
# SİPARİŞ OLUŞTUR
# ─────────────────────────────────────────────────────────────────

class SiparisOlusturUseCase:
    """
    Yeni sipariş oluşturur.

    İş kuralları:
    - Otomatik sipariş numarası (SIP-YYYY-NNNN) atanır.
    - Her kalemin KDV dahil toplamı hesaplanır.
    - Sipariş toplam miktar ve tutar domain entity üzerinde hesaplanır.
    - Oluşturma logu yazılır.
    """

    def __init__(
        self,
        siparis_repo: ISiparisRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = siparis_repo
        self._log_repo = log_repo

    def execute(
        self,
        dto: SiparisOlusturRequestDTO,
        kullanici_id: int,
    ) -> SiparisDetayResponseDTO:
        # 1. Otomatik sipariş numarası
        siparis_no = self._repo.sonraki_siparis_no()

        # 2. Sipariş entity oluştur
        siparis = Siparis(
            siparis_no=siparis_no,
            musteri_adi=dto.musteri_adi,
            teslimat_adresi=dto.teslimat_adresi,
            teslimat_tarihi=dto.teslimat_tarihi,
            oncelik=dto.oncelik,
            notlar=dto.notlar,
            olusturan_kullanici_id=kullanici_id,
        )

        # 3. Kalemleri domain entity üzerinden ekle (toplam hesabıyla)
        for kalem_dto in dto.kalemler:
            kalem = self._dto_to_kalem_entity(kalem_dto)
            siparis.kalem_ekle(kalem)  # entity hesaplar + toplam günceller

        # 4. Kaydet
        kaydedilen = self._repo.olustur(siparis)

        # 5. Sistem logu
        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.CREATE,
                modul="Sipariş Yönetimi",
                detay=(
                    f"Yeni sipariş oluşturuldu: {siparis_no} "
                    f"- {dto.musteri_adi} ({len(dto.kalemler)} kalem)"
                ),
            )
        )

        return SiparisDetayResponseDTO.from_entity(kaydedilen)

    @staticmethod
    def _dto_to_kalem_entity(dto: SiparisKalemiOlusturRequestDTO) -> SiparisKalemi:
        kalem = SiparisKalemi(
            urun_id=dto.urun_id,
            miktar=dto.miktar,
            birim_fiyat=dto.birim_fiyat,
            kdv_orani=dto.kdv_orani,
        )
        kalem.toplam_hesapla()
        return kalem


# ─────────────────────────────────────────────────────────────────
# SİPARİŞ GÜNCELLE
# ─────────────────────────────────────────────────────────────────

class SiparisGuncelleUseCase:
    """
    Sipariş bilgilerini ve durumunu günceller.

    İş kuralları:
    - Sipariş bulunamazsa KayitBulunamadiError.
    - Durum değişimi varsa domain entity'deki SiparisDurum makinesi ile doğrulanır.
    - Güncelleme logu yazılır.
    """

    def __init__(
        self,
        siparis_repo: ISiparisRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = siparis_repo
        self._log_repo = log_repo

    def execute(
        self,
        siparis_id: int,
        dto: SiparisGuncelleRequestDTO,
        kullanici_id: int,
    ) -> SiparisDetayResponseDTO:
        # 1. Varlık kontrolü
        siparis = self._repo.getir_id_ile(siparis_id)
        if not siparis:
            raise KayitBulunamadiError("Sipariş", siparis_id)

        eski_durum = siparis.durum

        # 2. Durum geçiş doğrulaması (sadece durum güncelleniyorsa)
        if dto.durum and dto.durum != eski_durum:
            # Faz 3: Hazirlaniyor ve sonrası sistem güdümlüdür; manuel olarak
            # yalnızca Iptal'e geçiş verilebilir. İleri durumlar (YolaCikti,
            # TeslimEdildi) sevkiyat lifecycle olaylarıyla yazılır.
            sistem_gudumlu_durumlar = {
                SiparisDurum.HAZIRLANIYOR,
                SiparisDurum.YOLA_CIKTI,
                SiparisDurum.TESLIM_EDILDI,
            }
            if (
                eski_durum in sistem_gudumlu_durumlar
                and dto.durum != SiparisDurum.IPTAL
            ):
                raise GecersizIslemError(
                    "Sipariş bu durumdayken manuel durum değişikliği yapılamaz; "
                    "ilerletme sevkiyat lifecycle olayları ile yürür."
                )
            if not SiparisDurum.gecis_gecerli_mi(eski_durum, dto.durum):
                raise GecersizDurumGecisiError("Sipariş", eski_durum, dto.durum)
            siparis.durum = dto.durum

        # 3. Teslimat meta alanları — ileri durumlarda kilitli.
        teslimat_meta_denemesi = any(
            v is not None for v in (dto.musteri_adi, dto.teslimat_adresi, dto.teslimat_tarihi)
        )
        if teslimat_meta_denemesi and not siparis.teslimat_meta_duzenlenebilir_mi():
            raise GecersizIslemError(
                f"Sipariş '{siparis.durum}' durumundayken müşteri, adres veya "
                "teslimat tarihi değiştirilemez."
            )

        if dto.musteri_adi is not None:
            siparis.musteri_adi = dto.musteri_adi
        if dto.teslimat_adresi is not None:
            siparis.teslimat_adresi = dto.teslimat_adresi
        if dto.teslimat_tarihi is not None:
            siparis.teslimat_tarihi = dto.teslimat_tarihi
        if dto.oncelik is not None:
            siparis.oncelik = dto.oncelik
        if dto.notlar is not None:
            siparis.notlar = dto.notlar

        siparis.guncelleme_tarihi = datetime.utcnow()

        # 4. Kaydet
        kaydedilen = self._repo.guncelle(siparis)

        # 5. Sistem logu
        log_detay = f"Sipariş güncellendi: {siparis.siparis_no}"
        if dto.durum and dto.durum != eski_durum:
            log_detay += f". Durum: {eski_durum} → {dto.durum}"
        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Sipariş Yönetimi",
                detay=log_detay,
            )
        )

        return SiparisDetayResponseDTO.from_entity(kaydedilen)


# ─────────────────────────────────────────────────────────────────
# SİPARİŞ SİL (soft delete)
# ─────────────────────────────────────────────────────────────────

class SiparisSilUseCase:
    """
    Siparişi pasife alır (aktif=False).

    İş kuralları:
    - Sipariş bulunamazsa KayitBulunamadiError.
    - Teslim edilmiş siparişler silinemez.
    - Silme logu yazılır.
    """

    def __init__(
        self,
        siparis_repo: ISiparisRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = siparis_repo
        self._log_repo = log_repo

    def execute(self, siparis_id: int, kullanici_id: int) -> None:
        siparis = self._repo.getir_id_ile(siparis_id)
        if not siparis:
            raise KayitBulunamadiError("Sipariş", siparis_id)

        if siparis.durum == SiparisDurum.TESLIM_EDILDI:
            raise GecersizIslemError(
                "Teslim edilmiş siparişler silinemez."
            )

        self._repo.sil(siparis_id)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.DELETE,
                modul="Sipariş Yönetimi",
                detay=f"Sipariş pasife alındı: {siparis.siparis_no}",
            )
        )
