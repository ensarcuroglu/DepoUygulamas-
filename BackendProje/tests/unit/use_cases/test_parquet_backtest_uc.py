"""Unit testler — ParquetBacktestUseCase.

FastAPI / DB bagimliligi yok; dogrudan ml_models predictor + tmp parquet
ile calisir.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest

import _ml_models_path  # noqa: F401

from app.application.use_cases import ParquetBacktestUseCase
from app.core.exceptions import GecersizIslemError, KayitBulunamadiError
from ml_models.talep_tahmin.application import PredictDemandUseCase
from ml_models.talep_tahmin.infrastructure import BaselineMovingAveragePredictor


pytestmark = pytest.mark.unit


def _datagen_parquet_yaz(path: Path, urunler: tuple[int, ...] = (1, 2)) -> None:
    baslangic = date(2024, 1, 1)
    kayitlar = []
    for urun_id in urunler:
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
    pd.DataFrame(kayitlar).to_parquet(path)


@pytest.fixture
def parquet_uc(tmp_path: Path) -> ParquetBacktestUseCase:
    predict_uc = PredictDemandUseCase(BaselineMovingAveragePredictor())
    return ParquetBacktestUseCase(predict_uc=predict_uc, parquet_dir=tmp_path)


def test_veri_setlerini_listele_bos_dizinde_bos_donmeli(tmp_path: Path) -> None:
    predict_uc = PredictDemandUseCase(BaselineMovingAveragePredictor())
    uc = ParquetBacktestUseCase(predict_uc=predict_uc, parquet_dir=tmp_path)
    assert uc.veri_setlerini_listele() == []


def test_veri_setlerini_listele_metadatayi_doldurmali(
    parquet_uc: ParquetBacktestUseCase, tmp_path: Path
) -> None:
    _datagen_parquet_yaz(tmp_path / "talep_gecmis_test.parquet", urunler=(1, 2, 3))

    setler = parquet_uc.veri_setlerini_listele()

    assert len(setler) == 1
    seti = setler[0]
    assert seti.dosya == "talep_gecmis_test.parquet"
    assert seti.boyut_bytes > 0
    assert seti.satir_sayisi == 90
    assert seti.urun_sayisi == 3


def test_calistir_tum_urunler_icin_per_urun_sonuc_uretmeli(
    parquet_uc: ParquetBacktestUseCase, tmp_path: Path
) -> None:
    _datagen_parquet_yaz(tmp_path / "veri.parquet", urunler=(1, 2))

    sonuc = parquet_uc.calistir(dosya="veri.parquet", tahmin_gun=7)

    assert sonuc.veri_kaynagi == "veri.parquet"
    assert sonuc.tahmin_gun == 7
    assert sonuc.urun_sayisi == 2
    assert len(sonuc.sonuclar) == 2
    urun_idleri = {s.urun_id for s in sonuc.sonuclar}
    assert urun_idleri == {1, 2}
    for kayit in sonuc.sonuclar:
        assert kayit.gercek_talep > 0
        assert kayit.tahmini_talep >= 0
        assert kayit.mae >= 0
        assert kayit.mape >= 0
        assert 0 <= kayit.veri_guven_skoru <= 1
        assert kayit.stok_riski in {"yok", "dikkat", "kritik"}


def test_calistir_tek_urun_icin_yalniz_o_urun_donmeli(
    parquet_uc: ParquetBacktestUseCase, tmp_path: Path
) -> None:
    _datagen_parquet_yaz(tmp_path / "veri.parquet", urunler=(1, 2, 3))

    sonuc = parquet_uc.calistir(dosya="veri.parquet", tahmin_gun=7, urun_id=2)

    assert sonuc.urun_sayisi == 1
    assert sonuc.sonuclar[0].urun_id == 2


def test_calistir_gecersiz_tahmin_gun_hata_uretmeli(
    parquet_uc: ParquetBacktestUseCase, tmp_path: Path
) -> None:
    _datagen_parquet_yaz(tmp_path / "veri.parquet")

    with pytest.raises(GecersizIslemError):
        parquet_uc.calistir(dosya="veri.parquet", tahmin_gun=15)


def test_calistir_bilinmeyen_dosya_404_uretmeli(
    parquet_uc: ParquetBacktestUseCase,
) -> None:
    with pytest.raises(KayitBulunamadiError):
        parquet_uc.calistir(dosya="yok.parquet", tahmin_gun=7)


def test_calistir_bilinmeyen_urun_id_404_uretmeli(
    parquet_uc: ParquetBacktestUseCase, tmp_path: Path
) -> None:
    _datagen_parquet_yaz(tmp_path / "veri.parquet", urunler=(1, 2))

    with pytest.raises(KayitBulunamadiError):
        parquet_uc.calistir(dosya="veri.parquet", tahmin_gun=7, urun_id=999)


def test_calistir_path_traversal_engellenmeli(
    parquet_uc: ParquetBacktestUseCase,
) -> None:
    with pytest.raises(GecersizIslemError):
        parquet_uc.calistir(dosya="../../etc/passwd.parquet", tahmin_gun=7)


def test_calistir_yanlis_uzanti_engellenmeli(
    parquet_uc: ParquetBacktestUseCase, tmp_path: Path
) -> None:
    (tmp_path / "veri.csv").write_text("dummy")
    with pytest.raises(GecersizIslemError):
        parquet_uc.calistir(dosya="veri.csv", tahmin_gun=7)
