from __future__ import annotations

from pathlib import Path

import pandas as pd

from ml_models.talep_tahmin.domain.entities import DailyStockExit, InputFeatures


class ParquetDemandDataSource:
    """DataGenService `timeseries_history` parquet ciktisindan InputFeatures uretir.

    Beklenen sema (`TalepGecmisKaydiDTO`):
        tarih, urun_kodu, urun_id, miktar, fiyat, promosyon, haftanin_gunu

    `miktar` -> `gunluk_cikis_miktari` esleftirilir. `mevcut_stok` ve `min_stok`
    parquet'te bulunmadigi icin constructor uzerinden default deger alinir
    (DataGenService stok seviyesi uretmez; gercek stok BackendProje'den gelir).
    """

    REQUIRED_COLUMNS = {"urun_id", "tarih", "miktar"}

    def __init__(
        self,
        parquet_path: str | Path,
        default_mevcut_stok: float = 0.0,
        default_min_stok: float = 0.0,
        max_gun: int = 90,
    ) -> None:
        self._parquet_path = Path(parquet_path)
        self._default_mevcut_stok = float(default_mevcut_stok)
        self._default_min_stok = float(default_min_stok)
        self._max_gun = max_gun
        self._frame_cache: pd.DataFrame | None = None

    def _load_frame(self) -> pd.DataFrame:
        if self._frame_cache is not None:
            return self._frame_cache

        df = pd.read_parquet(self._parquet_path)
        eksik_kolonlar = self.REQUIRED_COLUMNS - set(df.columns)
        if eksik_kolonlar:
            raise ValueError(
                f"Parquet veri sozlesmesi eksik kolonlar: {sorted(eksik_kolonlar)}"
            )

        df = df.copy()
        df["tarih"] = pd.to_datetime(df["tarih"]).dt.date
        self._frame_cache = df
        return df

    def available_urun_ids(self) -> list[int]:
        df = self._load_frame()
        return sorted(int(value) for value in df["urun_id"].unique())

    def build_features(
        self,
        urun_id: int,
        tenant_id: str | None = "datagen-demo",
        mevcut_stok: float | None = None,
        min_stok: float | None = None,
    ) -> InputFeatures:
        df = self._load_frame()
        urun_df = df[df["urun_id"] == urun_id]
        if urun_df.empty:
            raise ValueError(f"Parquet icinde urun_id={urun_id} icin veri bulunamadi.")

        urun_df = urun_df.sort_values("tarih").tail(self._max_gun)
        stok_cikis_gecmisi = [
            DailyStockExit(tarih=row.tarih, miktar=float(row.miktar))
            for row in urun_df.itertuples(index=False)
        ]

        return InputFeatures(
            urun_id=int(urun_id),
            tenant_id=tenant_id,
            stok_cikis_gecmisi=stok_cikis_gecmisi,
            mevcut_stok=(
                float(mevcut_stok) if mevcut_stok is not None else self._default_mevcut_stok
            ),
            min_stok=(
                float(min_stok) if min_stok is not None else self._default_min_stok
            ),
        )
