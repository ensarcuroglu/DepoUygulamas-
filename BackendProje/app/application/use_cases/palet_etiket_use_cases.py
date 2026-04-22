"""Palet Etiket use case'leri — şablon seç, render et, persist et, yazdırma say."""

from __future__ import annotations

from typing import List, TYPE_CHECKING

from sqlalchemy.orm import Session

from app.core.entities.kullanici import KullaniciRol
from app.core.entities.palet_etiket import PaletEtiket
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import (
    KayitBulunamadiError,
    YetkisizIslemError,
    GecersizIslemError,
)
from app.application.dto.etiket_dto import (
    PaletEtiketOlusturDTO,
    PaletEtiketResponseDTO,
)

if TYPE_CHECKING:
    from app.core.entities.kullanici import Kullanici
    from app.core.services.etiket_render_service import EtiketRenderService
    from app.core.repositories.palet_repository import IPaletRepository
    from app.core.repositories.etiket_sablonu_repository import IEtiketSablonuRepository
    from app.core.repositories.palet_etiket_repository import IPaletEtiketRepository
    from app.core.repositories.sistem_log_repository import ISistemLogRepository


def _yetki_dogrula(kullanici: "Kullanici") -> None:
    if kullanici.rol not in {KullaniciRol.ADMIN, KullaniciRol.DEPOCU}:
        raise YetkisizIslemError(
            "Etiket oluşturmak için admin veya depocu yetkisi gereklidir."
        )


class PaletEtiketOlusturUseCase:
    """Palete bir şablondan etiket oluşturur (render + persist)."""

    def __init__(
        self,
        palet_repo: "IPaletRepository",
        sablon_repo: "IEtiketSablonuRepository",
        etiket_repo: "IPaletEtiketRepository",
        render_service: "EtiketRenderService",
        sistem_log_repo: "ISistemLogRepository",
        db: Session,
    ):
        self._palet_repo = palet_repo
        self._sablon_repo = sablon_repo
        self._etiket_repo = etiket_repo
        self._render = render_service
        self._log_repo = sistem_log_repo
        self._db = db

    def execute(
        self,
        palet_no: str,
        dto: PaletEtiketOlusturDTO,
        kullanici: "Kullanici",
    ) -> PaletEtiketResponseDTO:
        _yetki_dogrula(kullanici)

        palet = self._palet_repo.getir_palet_no_ile(palet_no)
        if not palet or palet.id is None:
            raise KayitBulunamadiError("Palet", palet_no)

        sablon = self._sablon_repo.getir_id_ile(dto.sablon_id)
        if not sablon or not sablon.aktif:
            raise KayitBulunamadiError("Etiket şablonu", dto.sablon_id)

        barkod_deger = palet.palet_no
        qr_deger = palet.palet_no

        render_zpl = self._render.render(sablon.zpl_template, palet, barkod_deger, qr_deger)
        render_html = self._render.render(sablon.html_template, palet, barkod_deger, qr_deger)

        etiket = PaletEtiket(
            palet_id=palet.id,
            sablon_id=sablon.id or 0,
            render_edilmis_zpl=render_zpl,
            render_edilmis_html=render_html,
            barkod_deger=barkod_deger,
            qr_deger=qr_deger,
            basim_sayisi=0,
            kullanici_id=kullanici.id,
        )

        try:
            kaydedilen = self._etiket_repo.olustur(etiket)
            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici.id,
                    islem_tipi=IslemTipi.CREATE,
                    modul="Palet Etiket",
                    detay=f"Etiket oluşturuldu: {palet_no} (şablon: {sablon.ad})",
                ),
                auto_commit=True,
            )
        except Exception:
            self._db.rollback()
            raise

        kaydedilen.sablon_ad = sablon.ad
        kaydedilen.palet_no = palet.palet_no
        return PaletEtiketResponseDTO.from_entity(kaydedilen)


class PaletEtiketleriListeleUseCase:
    def __init__(
        self,
        palet_repo: "IPaletRepository",
        etiket_repo: "IPaletEtiketRepository",
    ):
        self._palet_repo = palet_repo
        self._etiket_repo = etiket_repo

    def execute(self, palet_no: str) -> List[PaletEtiketResponseDTO]:
        palet = self._palet_repo.getir_palet_no_ile(palet_no)
        if not palet or palet.id is None:
            raise KayitBulunamadiError("Palet", palet_no)
        etiketler = self._etiket_repo.getir_hepsi_palet_id_ile(palet.id)
        return [PaletEtiketResponseDTO.from_entity(e) for e in etiketler]


class PaletEtiketYazdirUseCase:
    """basim_sayisi++ ve son_basim_tarihi günceller."""

    def __init__(
        self,
        etiket_repo: "IPaletEtiketRepository",
        sistem_log_repo: "ISistemLogRepository",
        db: Session,
    ):
        self._etiket_repo = etiket_repo
        self._log_repo = sistem_log_repo
        self._db = db

    def execute(self, etiket_id: int, kullanici: "Kullanici") -> PaletEtiketResponseDTO:
        _yetki_dogrula(kullanici)
        etiket = self._etiket_repo.getir_id_ile(etiket_id)
        if not etiket:
            raise KayitBulunamadiError("Palet etiketi", etiket_id)

        etiket.basildi()
        try:
            guncellenen = self._etiket_repo.guncelle(etiket)
            if not guncellenen:
                raise GecersizIslemError("Etiket güncellenemedi.")
            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici.id,
                    islem_tipi=IslemTipi.UPDATE,
                    modul="Palet Etiket",
                    detay=f"Etiket yazdırıldı: #{etiket_id} (basım {guncellenen.basim_sayisi})",
                ),
                auto_commit=True,
            )
        except Exception:
            self._db.rollback()
            raise
        return PaletEtiketResponseDTO.from_entity(guncellenen)
