"""
Yerleştirme Görevi Use Case'leri.
"""

from __future__ import annotations
from typing import List, Optional

from app.core.repositories.yerlestirme_gorevi_repository import IYerlestirmeGoreviRepository
from app.core.repositories.palet_repository import IPaletRepository
from app.core.repositories.raf_repository import IRafRepository
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.entities.yerlestirme_gorevi import YerlestirmeGorevi, GorevTipi
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import KayitBulunamadiError, GecersizIslemError
from app.application.dto.yerlestirme_gorevi_dto import (
    YerlestirmeGoreviOlusturRequestDTO,
    YerlestirmeGoreviTamamlaRequestDTO,
    YerlestirmeGoreviOverrideRequestDTO,
    YerlestirmeGoreviIptalRequestDTO,
    YerlestirmeGoreviResponseDTO,
)


class YerlestirmeGoreviListeleUseCase:
    def __init__(self, repo: IYerlestirmeGoreviRepository):
        self._repo = repo

    def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        durum: Optional[str] = None,
        atanan_kullanici_id: Optional[int] = None,
        palet_id: Optional[int] = None,
    ) -> List[YerlestirmeGoreviResponseDTO]:
        gorevler = self._repo.getir_hepsi(
            skip=skip, limit=limit, durum=durum,
            atanan_kullanici_id=atanan_kullanici_id, palet_id=palet_id,
        )
        return [YerlestirmeGoreviResponseDTO.from_entity(g) for g in gorevler]


class YerlestirmeGoreviGetirUseCase:
    def __init__(self, repo: IYerlestirmeGoreviRepository):
        self._repo = repo

    def execute(self, gorev_id: int) -> YerlestirmeGoreviResponseDTO:
        gorev = self._repo.getir_id_ile(gorev_id)
        if not gorev:
            raise KayitBulunamadiError("YerlestirmeGorevi", gorev_id)
        return YerlestirmeGoreviResponseDTO.from_entity(gorev)


class YerlestirmeGoreviOlusturUseCase:
    """
    Manuel görev oluşturur. Otomatik oluşturma irsaliye onay akışından tetiklenir.

    İş kuralları:
    - Palet var olmalı.
    - Önerilen raf var olmalı.
    - Transfer görevinde kaynak_raf_id zorunlu.
    """

    def __init__(
        self,
        repo: IYerlestirmeGoreviRepository,
        palet_repo: IPaletRepository,
        raf_repo: IRafRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = repo
        self._palet_repo = palet_repo
        self._raf_repo = raf_repo
        self._log_repo = log_repo

    def execute(
        self, dto: YerlestirmeGoreviOlusturRequestDTO, kullanici_id: int
    ) -> YerlestirmeGoreviResponseDTO:
        palet = self._palet_repo.getir_id_ile(dto.palet_id)
        if not palet:
            raise KayitBulunamadiError("Palet", dto.palet_id)

        raf = self._raf_repo.getir_id_ile(dto.onerilen_raf_id)
        if not raf:
            raise KayitBulunamadiError("Raf", dto.onerilen_raf_id)

        if dto.tip == GorevTipi.TRANSFER and not dto.kaynak_raf_id:
            raise GecersizIslemError("Transfer görevi için kaynak_raf_id zorunludur.")

        gorev = YerlestirmeGorevi(
            palet_id=dto.palet_id,
            mal_kabul_irsaliye_id=dto.mal_kabul_irsaliye_id,
            tip=dto.tip,
            kaynak_raf_id=dto.kaynak_raf_id,
            onerilen_raf_id=dto.onerilen_raf_id,
            oncelik=dto.oncelik,
        )
        kaydedilen = self._repo.olustur(gorev)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.CREATE,
                modul="Yerleştirme",
                detay=f"Yerleştirme görevi oluşturuldu: Palet {dto.palet_id} → Raf {raf.kod}",
                yeni_veri={"palet_id": dto.palet_id, "onerilen_raf_id": dto.onerilen_raf_id},
            )
        )
        return YerlestirmeGoreviResponseDTO.from_entity(kaydedilen)


class SonrakiGorevisiniAlUseCase:
    """Pull-based FIFO: Operatör sıradaki görevi kilitleyerek çeker."""

    def __init__(self, repo: IYerlestirmeGoreviRepository):
        self._repo = repo

    def execute(self, kullanici_id: int) -> Optional[YerlestirmeGoreviResponseDTO]:
        gorev = self._repo.sonraki_gorevi_kilitle(kullanici_id)
        if not gorev:
            return None
        return YerlestirmeGoreviResponseDTO.from_entity(gorev)


class YerlestirmeGoreviBaslatUseCase:
    """Operatör paleti fiziksel olarak aldığında DEVAM_EDIYOR'a geçer."""

    def __init__(self, repo: IYerlestirmeGoreviRepository):
        self._repo = repo

    def execute(self, gorev_id: int, kullanici_id: int) -> YerlestirmeGoreviResponseDTO:
        gorev = self._repo.getir_id_ile(gorev_id)
        if not gorev:
            raise KayitBulunamadiError("YerlestirmeGorevi", gorev_id)
        if gorev.atanan_kullanici_id != kullanici_id:
            raise GecersizIslemError("Bu görev size atanmamış.")
        gorev.baslat()
        kaydedilen = self._repo.guncelle(gorev)
        return YerlestirmeGoreviResponseDTO.from_entity(kaydedilen)


class YerlestirmeGoreviTamamlaUseCase:
    """Operatör raf barkodunu okuttu — görev tamamlanır, palet rafına atanır."""

    def __init__(
        self,
        repo: IYerlestirmeGoreviRepository,
        palet_repo: IPaletRepository,
        raf_repo: IRafRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = repo
        self._palet_repo = palet_repo
        self._raf_repo = raf_repo
        self._log_repo = log_repo

    def execute(
        self, gorev_id: int, dto: YerlestirmeGoreviTamamlaRequestDTO, kullanici_id: int
    ) -> YerlestirmeGoreviResponseDTO:
        gorev = self._repo.getir_id_ile(gorev_id)
        if not gorev:
            raise KayitBulunamadiError("YerlestirmeGorevi", gorev_id)
        if gorev.atanan_kullanici_id != kullanici_id:
            raise GecersizIslemError("Bu görev size atanmamış.")

        raf = self._raf_repo.getir_id_ile(dto.gerceklesen_raf_id)
        if not raf:
            raise KayitBulunamadiError("Raf", dto.gerceklesen_raf_id)

        palet = self._palet_repo.getir_id_ile(gorev.palet_id)
        if not palet:
            raise KayitBulunamadiError("Palet", gorev.palet_id)

        palet.raf_ata(dto.gerceklesen_raf_id)
        self._palet_repo.guncelle(palet, auto_commit=False)

        gorev.tamamla(dto.gerceklesen_raf_id)
        kaydedilen = self._repo.guncelle(gorev)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Yerleştirme",
                detay=f"Görev tamamlandı: ID {gorev_id} → Raf {raf.kod}",
                yeni_veri={"gerceklesen_raf_id": dto.gerceklesen_raf_id},
            )
        )
        return YerlestirmeGoreviResponseDTO.from_entity(kaydedilen)


class YerlestirmeGoreviOverrideUseCase:
    """Süpervizör kapasite/zon kuralı ihlali ile override tamamlama."""

    def __init__(
        self,
        repo: IYerlestirmeGoreviRepository,
        palet_repo: IPaletRepository,
        raf_repo: IRafRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = repo
        self._palet_repo = palet_repo
        self._raf_repo = raf_repo
        self._log_repo = log_repo

    def execute(
        self, gorev_id: int, dto: YerlestirmeGoreviOverrideRequestDTO, supervisor_id: int
    ) -> YerlestirmeGoreviResponseDTO:
        gorev = self._repo.getir_id_ile(gorev_id)
        if not gorev:
            raise KayitBulunamadiError("YerlestirmeGorevi", gorev_id)

        raf = self._raf_repo.getir_id_ile(dto.gerceklesen_raf_id)
        if not raf:
            raise KayitBulunamadiError("Raf", dto.gerceklesen_raf_id)

        palet = self._palet_repo.getir_id_ile(gorev.palet_id)
        if not palet:
            raise KayitBulunamadiError("Palet", gorev.palet_id)

        palet.raf_ata(dto.gerceklesen_raf_id)
        self._palet_repo.guncelle(palet, auto_commit=False)

        gorev.override_ile_tamamla(dto.gerceklesen_raf_id, supervisor_id, dto.neden)
        kaydedilen = self._repo.guncelle(gorev)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=supervisor_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Yerleştirme",
                detay=f"Override tamamlama: Görev {gorev_id} → Raf {raf.kod}. Gerekçe: {dto.neden}",
                yeni_veri={"gerceklesen_raf_id": dto.gerceklesen_raf_id, "neden": dto.neden},
            )
        )
        return YerlestirmeGoreviResponseDTO.from_entity(kaydedilen)


class YerlestirmeGoreviIptalUseCase:
    def __init__(self, repo: IYerlestirmeGoreviRepository, log_repo: ISistemLogRepository):
        self._repo = repo
        self._log_repo = log_repo

    def execute(
        self, gorev_id: int, dto: YerlestirmeGoreviIptalRequestDTO, kullanici_id: int
    ) -> YerlestirmeGoreviResponseDTO:
        gorev = self._repo.getir_id_ile(gorev_id)
        if not gorev:
            raise KayitBulunamadiError("YerlestirmeGorevi", gorev_id)

        gorev.iptal_et(dto.neden)
        kaydedilen = self._repo.guncelle(gorev)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Yerleştirme",
                detay=f"Görev iptal edildi: ID {gorev_id}. Neden: {dto.neden}",
            )
        )
        return YerlestirmeGoreviResponseDTO.from_entity(kaydedilen)
