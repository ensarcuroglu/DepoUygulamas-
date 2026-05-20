from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import sys

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml_models.talep_tahmin.infrastructure.data_sources import ParquetDemandDataSource


def _datagen_parquet_yaz(tmp_path: Path) -> Path:
    baslangic = date(2024, 1, 1)
    kayitlar = []
    for urun_id in (1, 2):
        for gun in range(30):
            tarih = baslangic + timedelta(days=gun)
            kayitlar.append(
                {
                    "tarih": tarih,
                    "urun_kodu": f"URN-{urun_id:03d}",
                    "urun_id": urun_id,
                    "miktar": 10 + urun_id + (gun % 5),
                    "fiyat": 100.0,
                    "promosyon": False,
                    "haftanin_gunu": tarih.weekday(),
                }
            )
    dosya = tmp_path / "talep_gecmis_test.parquet"
    pd.DataFrame(kayitlar).to_parquet(dosya)
    return dosya


def test_parquet_data_source_available_urun_ids(tmp_path: Path) -> None:
    dosya = _datagen_parquet_yaz(tmp_path)
    kaynak = ParquetDemandDataSource(dosya)
    assert kaynak.available_urun_ids() == [1, 2]


def test_parquet_data_source_build_features_canonical_donusum(tmp_path: Path) -> None:
    dosya = _datagen_parquet_yaz(tmp_path)
    kaynak = ParquetDemandDataSource(dosya, default_mevcut_stok=120, default_min_stok=30)

    features = kaynak.build_features(urun_id=1)

    assert features.urun_id == 1
    assert features.tenant_id == "datagen-demo"
    assert features.mevcut_stok == 120
    assert features.min_stok == 30
    assert len(features.stok_cikis_gecmisi) == 30
    ilk_kayit = features.stok_cikis_gecmisi[0]
    assert ilk_kayit.tarih == date(2024, 1, 1)
    assert ilk_kayit.miktar == 11  # 10 + urun_id(1) + (0 % 5)
    # InputFeatures validator tarih siralamasi yapmalidir
    tarihler = [item.tarih for item in features.stok_cikis_gecmisi]
    assert tarihler == sorted(tarihler)


def test_parquet_data_source_max_gun_kesimi(tmp_path: Path) -> None:
    dosya = _datagen_parquet_yaz(tmp_path)
    kaynak = ParquetDemandDataSource(dosya, max_gun=7)

    features = kaynak.build_features(urun_id=1)

    assert len(features.stok_cikis_gecmisi) == 7
    # En son 7 gun dondurulmeli
    assert features.stok_cikis_gecmisi[-1].tarih == date(2024, 1, 30)


def test_parquet_data_source_runtime_overrides(tmp_path: Path) -> None:
    dosya = _datagen_parquet_yaz(tmp_path)
    kaynak = ParquetDemandDataSource(dosya)

    features = kaynak.build_features(
        urun_id=2,
        tenant_id="acme",
        mevcut_stok=200,
        min_stok=50,
    )

    assert features.urun_id == 2
    assert features.tenant_id == "acme"
    assert features.mevcut_stok == 200
    assert features.min_stok == 50


def test_parquet_data_source_bilinmeyen_urun_hata_uretmeli(tmp_path: Path) -> None:
    dosya = _datagen_parquet_yaz(tmp_path)
    kaynak = ParquetDemandDataSource(dosya)

    with pytest.raises(ValueError, match="urun_id=999"):
        kaynak.build_features(urun_id=999)


def test_parquet_data_source_eksik_kolon_hata_uretmeli(tmp_path: Path) -> None:
    dosya = tmp_path / "bozuk.parquet"
    pd.DataFrame({"urun_id": [1], "tarih": [date(2024, 1, 1)]}).to_parquet(dosya)
    kaynak = ParquetDemandDataSource(dosya)

    with pytest.raises(ValueError, match="eksik kolonlar"):
        kaynak.available_urun_ids()
