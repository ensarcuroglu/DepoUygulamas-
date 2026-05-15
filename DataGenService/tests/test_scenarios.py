"""Faz 3 — senaryo testleri (`timeseries_history` file modu)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from app.scenarios import TimeseriesHistoryParams, run_timeseries_history


@pytest.mark.unit
async def test_timeseries_history_writes_parquet(tmp_path: Path) -> None:
    params = TimeseriesHistoryParams(
        gun_sayisi=7,
        urun_count=10,
        seed=42,
        output_dir=tmp_path,
    )
    result = await run_timeseries_history(params)
    assert result.output_path is not None
    assert result.output_path.exists()
    assert result.total == 7 * 10
    assert result.success == 70
    assert result.failed == 0

    table = pq.read_table(result.output_path)
    assert table.num_rows == 70
    assert set(table.column_names) == {
        "tarih",
        "urun_kodu",
        "urun_id",
        "miktar",
        "fiyat",
        "promosyon",
        "haftanin_gunu",
    }


@pytest.mark.unit
async def test_timeseries_history_deterministic_file_content(tmp_path: Path) -> None:
    params1 = TimeseriesHistoryParams(
        gun_sayisi=5, urun_count=5, seed=99, output_dir=tmp_path / "run1"
    )
    params2 = TimeseriesHistoryParams(
        gun_sayisi=5, urun_count=5, seed=99, output_dir=tmp_path / "run2"
    )
    r1 = await run_timeseries_history(params1)
    r2 = await run_timeseries_history(params2)

    assert r1.output_path is not None
    assert r2.output_path is not None
    t1 = pq.read_table(r1.output_path)
    t2 = pq.read_table(r2.output_path)
    # Şema ve içerik eşit olmalı (sıra dahil).
    assert t1.to_pylist() == t2.to_pylist()


@pytest.mark.unit
async def test_timeseries_history_csv_target(tmp_path: Path) -> None:
    params = TimeseriesHistoryParams(
        gun_sayisi=3,
        urun_count=4,
        seed=42,
        output_dir=tmp_path,
        file_format="csv",
    )
    result = await run_timeseries_history(params)
    assert result.output_path is not None
    assert result.output_path.suffix == ".csv"
    lines = result.output_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1 + (3 * 4)  # header + 12 satır


@pytest.mark.unit
async def test_timeseries_history_default_output_dir(tmp_path: Path) -> None:
    """params.output_dir None ise default_output_dir kullanılır."""
    params = TimeseriesHistoryParams(gun_sayisi=2, urun_count=2, seed=1)
    result = await run_timeseries_history(params, default_output_dir=tmp_path)
    assert result.output_path is not None
    assert tmp_path in result.output_path.parents


@pytest.mark.unit
async def test_timeseries_history_requires_output_dir(tmp_path: Path) -> None:
    params = TimeseriesHistoryParams(gun_sayisi=1, urun_count=1, seed=1)
    with pytest.raises(ValueError, match="output_dir"):
        await run_timeseries_history(params)


@pytest.mark.unit
def test_timeseries_history_rest_target_not_implemented_yet() -> None:
    with pytest.raises(NotImplementedError, match="Faz 4"):
        TimeseriesHistoryParams(gun_sayisi=1, target="rest")


@pytest.mark.unit
def test_timeseries_history_invalid_params() -> None:
    with pytest.raises(ValueError, match="gun_sayisi"):
        TimeseriesHistoryParams(gun_sayisi=0)
    with pytest.raises(ValueError, match="urun_count"):
        TimeseriesHistoryParams(gun_sayisi=1, urun_count=0)
    with pytest.raises(ValueError, match="batch_size"):
        TimeseriesHistoryParams(gun_sayisi=1, batch_size=0)


@pytest.mark.unit
async def test_timeseries_history_file_naming(tmp_path: Path) -> None:
    """Dosya adı seed + gün + ürün sayısını kodlamalı (tekrarlanabilir)."""
    params = TimeseriesHistoryParams(
        gun_sayisi=3,
        urun_count=5,
        seed=77,
        baslangic=date(2024, 6, 1),
        output_dir=tmp_path,
    )
    result = await run_timeseries_history(params)
    assert result.output_path is not None
    name = result.output_path.name
    assert "talep_gecmis_20240601" in name
    assert "seed77" in name
    assert "u5" in name
    assert "g3" in name
