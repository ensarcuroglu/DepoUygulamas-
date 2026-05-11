"""Belge taslagi use case'leri."""

from __future__ import annotations

import math
import re
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.application.dto.belge_taslagi_dto import (
    BelgeTaslagiKalemOnayDTO,
    BelgeTaslagiOlusturRequestDTO,
    BelgeTaslagiOnaylaRequestDTO,
    BelgeTaslagiReddetRequestDTO,
    BelgeTaslagiResponseDTO,
)
from app.core.entities.belge_taslagi import BelgeTaslagi, BelgeTaslagiDurum
from app.core.entities.mal_kabul_irsaliye import MalKabulIrsaliye, MalKabulKalemi
from app.core.entities.sistem_log import IslemTipi, SistemLog
from app.core.exceptions import GecersizIslemError, KayitBulunamadiError
from app.core.repositories.belge_taslagi_repository import IBelgeTaslagiRepository
from app.core.repositories.depo_repository import IDepoRepository
from app.core.repositories.mal_kabul_irsaliye_repository import IMalKabulIrsaliyeRepository
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.repositories.tedarikci_repository import ITedarikciRepository
from app.core.repositories.urun_repository import IUrunRepository


def _alan_value(raw: Any) -> Any:
    if isinstance(raw, dict) and "value" in raw:
        return raw.get("value")
    return raw


def _normalize(value: Any) -> str:
    text = str(value or "").casefold().strip()
    return re.sub(r"\s+", " ", text)


def _to_date(value: Any) -> Optional[date]:
    value = _alan_value(value)
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        try:
            return date.fromisoformat(raw[:10])
        except ValueError:
            return None
    return None


def _to_positive_int(value: Any, *, field_name: str) -> int:
    value = _alan_value(value)
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise GecersizIslemError(f"{field_name} sayisal olmali.") from exc
    if not math.isfinite(number) or number <= 0:
        raise GecersizIslemError(f"{field_name} sifirdan buyuk olmali.")
    return max(1, int(round(number)))


def _extract_confidence(raw: dict[str, Any]) -> float:
    taslak = raw.get("taslak") if isinstance(raw.get("taslak"), dict) else raw
    value = raw.get("confidence_skoru") or raw.get("confidence_score")
    if value is None and isinstance(taslak, dict):
        value = taslak.get("confidence_score")
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(confidence, 1.0))


def _taslak_payload(raw: dict[str, Any]) -> dict[str, Any]:
    taslak = raw.get("taslak")
    return taslak if isinstance(taslak, dict) else raw


def _kalem_from_raw(raw: dict[str, Any]) -> BelgeTaslagiKalemOnayDTO:
    return BelgeTaslagiKalemOnayDTO(
        urun_kodu=_alan_value(raw.get("urun_kodu")),
        ad=_alan_value(raw.get("ad")),
        miktar=_alan_value(raw.get("miktar")),
        birim=_alan_value(raw.get("birim")),
        lot_no=_alan_value(raw.get("lot_no")),
        palet_no=_alan_value(raw.get("palet_no")),
        uretim_tarihi=_to_date(raw.get("uretim_tarihi")),
        son_kullanma_tarihi=_to_date(raw.get("son_kullanma_tarihi")),
    )


class BelgeTaslagiListeleUseCase:
    def __init__(self, repo: IBelgeTaslagiRepository):
        self._repo = repo

    def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        durum: Optional[str] = None,
        depo_id: Optional[int] = None,
        max_confidence: Optional[float] = None,
    ) -> list[BelgeTaslagiResponseDTO]:
        taslaklar = self._repo.getir_hepsi(
            skip=skip,
            limit=limit,
            durum=durum,
            depo_id=depo_id,
            max_confidence=max_confidence,
        )
        return [BelgeTaslagiResponseDTO.from_entity(taslak) for taslak in taslaklar]


class BelgeTaslagiIncelemeKuyruguUseCase:
    def __init__(self, repo: IBelgeTaslagiRepository):
        self._repo = repo

    def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        depo_id: Optional[int] = None,
        max_confidence: float = 0.6,
    ) -> list[BelgeTaslagiResponseDTO]:
        taslaklar = self._repo.getir_hepsi(
            skip=skip,
            limit=limit,
            durum=BelgeTaslagiDurum.KABUL_BEKLIYOR,
            depo_id=depo_id,
            max_confidence=max_confidence,
        )
        return [BelgeTaslagiResponseDTO.from_entity(taslak) for taslak in taslaklar]


class BelgeTaslagiGetirUseCase:
    def __init__(self, repo: IBelgeTaslagiRepository):
        self._repo = repo

    def execute(self, taslak_id: int) -> BelgeTaslagiResponseDTO:
        taslak = self._repo.getir_id_ile(taslak_id)
        if not taslak:
            raise KayitBulunamadiError("Belge Taslagi", taslak_id)
        return BelgeTaslagiResponseDTO.from_entity(taslak)


class BelgeTaslagiOlusturUseCase:
    def __init__(
        self,
        repo: IBelgeTaslagiRepository,
        depo_repo: IDepoRepository,
        log_repo: ISistemLogRepository,
        db: Session,
    ):
        self._repo = repo
        self._depo_repo = depo_repo
        self._log_repo = log_repo
        self._db = db

    def execute(self, dto: BelgeTaslagiOlusturRequestDTO) -> BelgeTaslagiResponseDTO:
        if not self._depo_repo.getir_id_ile(dto.depo_id):
            raise KayitBulunamadiError("Depo", dto.depo_id)

        confidence = dto.confidence_skoru
        if confidence is None:
            confidence = _extract_confidence(dto.ham_json)

        taslak = BelgeTaslagi(
            kaynak_dosya_yolu=dto.kaynak_dosya_yolu,
            belge_tipi=dto.belge_tipi,
            ham_json=dto.ham_json,
            confidence_skoru=confidence,
            olusturan_kullanici_id=dto.olusturan_kullanici_id,
            depo_id=dto.depo_id,
        )
        try:
            kaydedilen = self._repo.olustur(taslak, auto_commit=False)
            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=dto.olusturan_kullanici_id,
                    islem_tipi=IslemTipi.CREATE,
                    modul="Belge Taslagi",
                    detay=f"Belge taslagi olusturuldu | depo={dto.depo_id}",
                ),
                auto_commit=False,
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise
        return BelgeTaslagiResponseDTO.from_entity(kaydedilen)


class BelgeTaslagiReddetUseCase:
    def __init__(
        self,
        repo: IBelgeTaslagiRepository,
        log_repo: ISistemLogRepository,
        db: Session,
    ):
        self._repo = repo
        self._log_repo = log_repo
        self._db = db

    def execute(
        self,
        taslak_id: int,
        dto: BelgeTaslagiReddetRequestDTO,
        kullanici_id: int,
    ) -> BelgeTaslagiResponseDTO:
        taslak = self._taslak_getir(taslak_id)
        try:
            taslak.reddet()
        except ValueError as exc:
            raise GecersizIslemError(str(exc)) from exc

        try:
            guncel = self._repo.guncelle(taslak, auto_commit=False)
            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici_id,
                    islem_tipi=IslemTipi.UPDATE,
                    modul="Belge Taslagi",
                    detay=f"Belge taslagi reddedildi | id={taslak_id} | neden={dto.neden or ''}",
                ),
                auto_commit=False,
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise
        return BelgeTaslagiResponseDTO.from_entity(guncel)

    def _taslak_getir(self, taslak_id: int) -> BelgeTaslagi:
        taslak = self._repo.getir_id_ile(taslak_id)
        if not taslak:
            raise KayitBulunamadiError("Belge Taslagi", taslak_id)
        return taslak


class BelgeTaslagiOnaylaUseCase:
    def __init__(
        self,
        taslak_repo: IBelgeTaslagiRepository,
        mal_kabul_repo: IMalKabulIrsaliyeRepository,
        tedarikci_repo: ITedarikciRepository,
        depo_repo: IDepoRepository,
        urun_repo: IUrunRepository,
        log_repo: ISistemLogRepository,
        db: Session,
    ):
        self._taslak_repo = taslak_repo
        self._mal_kabul_repo = mal_kabul_repo
        self._tedarikci_repo = tedarikci_repo
        self._depo_repo = depo_repo
        self._urun_repo = urun_repo
        self._log_repo = log_repo
        self._db = db

    def execute(
        self,
        taslak_id: int,
        dto: BelgeTaslagiOnaylaRequestDTO,
        kullanici_id: int,
    ) -> BelgeTaslagiResponseDTO:
        taslak = self._taslak_getir(taslak_id)
        if taslak.durum != BelgeTaslagiDurum.KABUL_BEKLIYOR:
            raise GecersizIslemError(
                f"Sadece kabul bekleyen taslaklar onaylanabilir. Mevcut durum: {taslak.durum}"
            )

        payload = _taslak_payload(taslak.ham_json)
        depo_id = dto.depo_id or taslak.depo_id
        if not self._depo_repo.getir_id_ile(depo_id):
            raise KayitBulunamadiError("Depo", depo_id)

        tedarikci_id = self._tedarikci_id_coz(dto, payload)
        kalemler = self._kalemleri_coz(dto, payload, taslak.id)
        if not kalemler:
            raise GecersizIslemError("Belge taslaginda mal kabul kalemi bulunamadi.")

        irsaliye = MalKabulIrsaliye(
            irsaliye_no=self._mal_kabul_repo.sonraki_irsaliye_no(),
            tedarikci_id=tedarikci_id,
            depo_id=depo_id,
            tarih=dto.tarih or _to_date(payload.get("tarih")) or date.today(),
            tir_plaka=dto.tir_plaka,
            sofor_adi=dto.sofor_adi,
            kalemler=kalemler,
        )

        try:
            kaydedilen_irsaliye = self._mal_kabul_repo.olustur(irsaliye)
            if not kaydedilen_irsaliye.id:
                raise GecersizIslemError("Mal kabul irsaliyesi olustu fakat ID alinamadi.")
            taslak.kabul_edildi(kaydedilen_irsaliye.id)
            guncel_taslak = self._taslak_repo.guncelle(taslak, auto_commit=False)
            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici_id,
                    islem_tipi=IslemTipi.UPDATE,
                    modul="Belge Taslagi",
                    detay=(
                        f"Belge taslagi onaylandi | taslak={taslak_id} | "
                        f"mal_kabul={kaydedilen_irsaliye.id}"
                    ),
                ),
                auto_commit=False,
            )
            self._db.commit()
        except Exception:
            self._db.rollback()
            raise

        return BelgeTaslagiResponseDTO.from_entity(guncel_taslak)

    def _taslak_getir(self, taslak_id: int) -> BelgeTaslagi:
        taslak = self._taslak_repo.getir_id_ile(taslak_id)
        if not taslak:
            raise KayitBulunamadiError("Belge Taslagi", taslak_id)
        return taslak

    def _tedarikci_id_coz(
        self,
        dto: BelgeTaslagiOnaylaRequestDTO,
        payload: dict[str, Any],
    ) -> int:
        if dto.tedarikci_id:
            tedarikci = self._tedarikci_repo.getir_id_ile(dto.tedarikci_id)
            if not tedarikci:
                raise KayitBulunamadiError("Tedarikci", dto.tedarikci_id)
            return dto.tedarikci_id

        tedarikci_adi = dto.tedarikci_adi or _alan_value(payload.get("tedarikci"))
        aranan = _normalize(tedarikci_adi)
        if not aranan:
            raise GecersizIslemError("Tedarikci eslestirmek icin ad veya ID gerekli.")

        adaylar = self._tedarikci_repo.getir_hepsi(limit=500)
        for aday in adaylar:
            if _normalize(aday.firma_adi) == aranan and aday.id:
                return aday.id
        for aday in adaylar:
            aday_ad = _normalize(aday.firma_adi)
            if aday.id and (aranan in aday_ad or aday_ad in aranan):
                return aday.id
        raise GecersizIslemError(
            f"Tedarikci eslestirilemedi: {tedarikci_adi}. Lutfen tedarikci_id ile onaylayin."
        )

    def _kalemleri_coz(
        self,
        dto: BelgeTaslagiOnaylaRequestDTO,
        payload: dict[str, Any],
        taslak_id: Optional[int],
    ) -> list[MalKabulKalemi]:
        if dto.kalemler is not None:
            kalem_dtolar = dto.kalemler
        else:
            raw_kalemler = payload.get("kalemler") or []
            kalem_dtolar = [
                _kalem_from_raw(raw)
                for raw in raw_kalemler
                if isinstance(raw, dict)
            ]

        kalemler: list[MalKabulKalemi] = []
        for index, kalem_dto in enumerate(kalem_dtolar, start=1):
            urun_id = self._urun_id_coz(kalem_dto)
            miktar = _to_positive_int(kalem_dto.miktar, field_name="miktar")
            palet_no = kalem_dto.palet_no or f"DOC-{taslak_id or 'X'}-{index:03}"
            kalemler.append(
                MalKabulKalemi(
                    palet_no=palet_no,
                    urun_id=urun_id,
                    lot_no=kalem_dto.lot_no,
                    miktar=miktar,
                    uretim_tarihi=kalem_dto.uretim_tarihi,
                    son_kullanma_tarihi=kalem_dto.son_kullanma_tarihi,
                )
            )
        return kalemler

    def _urun_id_coz(self, kalem: BelgeTaslagiKalemOnayDTO) -> int:
        if kalem.urun_id:
            urun = self._urun_repo.getir_id_ile(kalem.urun_id)
            if not urun:
                raise KayitBulunamadiError("Urun", kalem.urun_id)
            return kalem.urun_id

        kod = (kalem.urun_kodu or "").strip()
        if kod:
            for getter in (self._urun_repo.getir_barkod_ile, self._urun_repo.getir_ean_ile):
                urun = getter(kod)
                if urun and urun.id:
                    return urun.id

            for urun in self._urun_repo.getir_hepsi(search=kod, limit=10):
                if urun.id and (
                    _normalize(urun.barkod) == _normalize(kod)
                    or _normalize(urun.ean) == _normalize(kod)
                    or _normalize(urun.isim) == _normalize(kalem.ad)
                ):
                    return urun.id

        ad = (kalem.ad or "").strip()
        if ad:
            for urun in self._urun_repo.getir_hepsi(search=ad, limit=10):
                if urun.id and _normalize(urun.isim) == _normalize(ad):
                    return urun.id

        label = kod or ad or "bilinmeyen kalem"
        raise GecersizIslemError(
            f"Urun eslestirilemedi: {label}. Lutfen urun_id ile onaylayin."
        )
