"""Faz 3 — emitter testleri."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from app.factories import TalepGecmisKaydiDTO
from app.infrastructure.emitters import FileEmitter


def _kayit(tarih: date, urun_kodu: str, miktar: int) -> TalepGecmisKaydiDTO:
    return TalepGecmisKaydiDTO(
        tarih=tarih,
        urun_kodu=urun_kodu,
        urun_id=1,
        miktar=miktar,
        fiyat=10.0,
        promosyon=False,
        haftanin_gunu=tarih.weekday(),
    )


@pytest.mark.unit
async def test_file_emitter_parquet_roundtrip(tmp_path: Path) -> None:
    out = tmp_path / "test.parquet"
    async with FileEmitter(out) as emitter:
        await emitter.emit_batch(
            [_kayit(date(2024, 1, 1), "X-1", 10), _kayit(date(2024, 1, 2), "X-1", 12)]
        )
        await emitter.emit_batch([_kayit(date(2024, 1, 3), "X-1", 15)])

    assert out.exists()
    table = pq.read_table(out)
    assert table.num_rows == 3
    assert set(table.column_names) >= {
        "tarih",
        "urun_kodu",
        "urun_id",
        "miktar",
        "fiyat",
        "promosyon",
        "haftanin_gunu",
    }
    miktarlar = table.column("miktar").to_pylist()
    assert miktarlar == [10, 12, 15]


@pytest.mark.unit
async def test_file_emitter_csv_roundtrip(tmp_path: Path) -> None:
    out = tmp_path / "test.csv"
    async with FileEmitter(out, file_format="csv") as emitter:
        await emitter.emit_batch(
            [_kayit(date(2024, 1, 1), "X-1", 10), _kayit(date(2024, 1, 2), "X-1", 12)]
        )

    content = out.read_text(encoding="utf-8").strip().splitlines()
    assert content[0].split(",")[:3] == ["tarih", "urun_kodu", "urun_id"]
    assert len(content) == 3  # header + 2 row


@pytest.mark.unit
async def test_file_emitter_empty_batch_is_noop(tmp_path: Path) -> None:
    out = tmp_path / "empty.parquet"
    async with FileEmitter(out) as emitter:
        await emitter.emit_batch([])
    # Hiç batch yazılmadığında parquet writer açılmaz; dosya da oluşmaz.
    assert not out.exists()
    assert emitter.summary().total == 0


@pytest.mark.unit
async def test_file_emitter_summary_metrics(tmp_path: Path) -> None:
    out = tmp_path / "metrics.parquet"
    async with FileEmitter(out) as emitter:
        await emitter.emit_batch([_kayit(date(2024, 1, 1), "X-1", 5)] * 10)
        await emitter.emit_batch([_kayit(date(2024, 1, 2), "X-1", 7)] * 15)
    summary = emitter.summary()
    assert summary.total == 25
    assert summary.success == 25
    assert summary.failed == 0
    assert summary.duration_sec > 0
    assert len(summary.latencies_ms) == 2


@pytest.mark.unit
async def test_file_emitter_cannot_emit_after_close(tmp_path: Path) -> None:
    out = tmp_path / "after.parquet"
    emitter = FileEmitter(out)
    await emitter.close()
    with pytest.raises(RuntimeError, match="zaten kapalı"):
        await emitter.emit_batch([_kayit(date(2024, 1, 1), "X-1", 1)])


@pytest.mark.unit
async def test_file_emitter_schema_drift_caught(tmp_path: Path) -> None:
    """İkinci batch farklı şemada gelirse cast hatası verir (silent corruption engellenir)."""
    from pydantic import BaseModel

    class DiffSchema(BaseModel):
        farkli_alan: str
        sayi: int

    out = tmp_path / "drift.parquet"
    async with FileEmitter(out) as emitter:
        await emitter.emit_batch([_kayit(date(2024, 1, 1), "X-1", 1)])
        with pytest.raises(Exception):
            await emitter.emit_batch([DiffSchema(farkli_alan="x", sayi=1)])
