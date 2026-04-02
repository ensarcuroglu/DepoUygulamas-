from datetime import datetime, timezone, timedelta

from app.application.dto.sistem_log_dto import SistemLogResponseDTO
from app.core.entities.sistem_log import SistemLog


def test_sistem_log_response_naive_tarihi_utc_kabul_eder():
    log = SistemLog(
        id=1,
        kullanici_id=10,
        islem_tipi="LOGIN",
        modul="Oturum",
        detay="Kullanici giris yapti",
        tarih=datetime(2026, 4, 2, 5, 52, 0),  # naive UTC
    )

    dto = SistemLogResponseDTO.from_entity(log)

    assert dto.tarih.tzinfo is not None
    assert dto.tarih.utcoffset() == timedelta(0)
    assert dto.tarih.isoformat().endswith("+00:00")


def test_sistem_log_response_aware_tarihi_utcye_cevirir():
    plus_three = timezone(timedelta(hours=3))
    log = SistemLog(
        id=2,
        kullanici_id=10,
        islem_tipi="LOGIN",
        modul="Oturum",
        detay="Kullanici giris yapti",
        tarih=datetime(2026, 4, 2, 8, 52, 0, tzinfo=plus_three),
    )

    dto = SistemLogResponseDTO.from_entity(log)

    assert dto.tarih.hour == 5
    assert dto.tarih.minute == 52
    assert dto.tarih.utcoffset() == timedelta(0)
