from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.dialects import mysql

from app.application.dto.mal_kabul_irsaliye_dto import MalKabulIrsaliyeResponseDTO
from app.core.entities.mal_kabul_irsaliye import (
    KalemDurum,
    MalKabulDurum,
    MalKabulIrsaliye,
    MalKabulKalemi,
)
from app.infrastructure.persistence.repositories.sa_mal_kabul_irsaliye_repository import (
    _timestampdiff_seconds,
)


def _kalem(
    *,
    kalem_id: int,
    irsaliye_id: int,
    palet_no: str,
    durum: str,
) -> MalKabulKalemi:
    return MalKabulKalemi(
        id=kalem_id,
        mal_kabul_irsaliyesi_id=irsaliye_id,
        palet_no=palet_no,
        urun_id=101,
        miktar=10,
        durum=durum,
        olusturma_tarihi=datetime(2026, 4, 9, 9, 0, 0),
    )


def test_progress_uses_putaway_task_state_instead_of_giris_yapildi():
    entity = MalKabulIrsaliye(
        id=1,
        irsaliye_no="MKI-2026-00001",
        tedarikci_id=10,
        depo_id=20,
        durum=MalKabulDurum.ONAYLANDI,
        tarih=date(2026, 4, 9),
        olusturma_tarihi=datetime(2026, 4, 9, 9, 0, 0),
        guncelleme_tarihi=datetime(2026, 4, 9, 9, 5, 0),
        kalemler=[
            _kalem(kalem_id=1, irsaliye_id=1, palet_no="PLT-1", durum=KalemDurum.GIRIS_YAPILDI),
            _kalem(kalem_id=2, irsaliye_id=1, palet_no="PLT-2", durum=KalemDurum.GIRIS_YAPILDI),
        ],
        yerlestirme_gorev_toplam=2,
        yerlestirme_gorev_tamamlanan=0,
        yerlestirme_gorev_iptal=0,
    )

    dto = MalKabulIrsaliyeResponseDTO.from_entity(entity)

    assert dto.toplam_kalem == 2
    assert dto.yerlestirilen == 0
    assert dto.bekleyen == 2


def test_progress_uses_kapanma_ozeti_when_irsaliye_closed():
    entity = MalKabulIrsaliye(
        id=2,
        irsaliye_no="MKI-2026-00002",
        tedarikci_id=10,
        depo_id=20,
        durum=MalKabulDurum.KAPANDI,
        tarih=date(2026, 4, 9),
        olusturma_tarihi=datetime(2026, 4, 9, 9, 0, 0),
        guncelleme_tarihi=datetime(2026, 4, 9, 10, 0, 0),
        kalemler=[
            _kalem(kalem_id=3, irsaliye_id=2, palet_no="PLT-3", durum=KalemDurum.GIRIS_YAPILDI),
            _kalem(kalem_id=4, irsaliye_id=2, palet_no="PLT-4", durum=KalemDurum.GIRIS_YAPILDI),
            _kalem(kalem_id=5, irsaliye_id=2, palet_no="PLT-5", durum=KalemDurum.GIRIS_YAPILDI),
        ],
        kapanma_ozeti={
            "toplam_kalem": 3,
            "yerlestirilen": 2,
            "iptal_edilen": 1,
            "istisna_sayisi": 1,
            "ort_yerlestirme_sure_dk": 7.5,
        },
    )

    dto = MalKabulIrsaliyeResponseDTO.from_entity(entity)

    assert dto.toplam_kalem == 3
    assert dto.yerlestirilen == 2
    assert dto.bekleyen == 0


def test_timestampdiff_helper_emits_second_as_sql_literal():
    sql = str(
        _timestampdiff_seconds(datetime(2026, 4, 9, 9, 0, 0), datetime(2026, 4, 9, 9, 5, 0)).compile(
            dialect=mysql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert sql.startswith("timestampdiff(SECOND,")
