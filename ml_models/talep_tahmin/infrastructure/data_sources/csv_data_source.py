from __future__ import annotations

from pathlib import Path

import pandas as pd

from ml_models.talep_tahmin.domain.entities import DailyStockExit, InputFeatures


class CsvDemandDataSource:
    """Read canonical demand-forecast input data from a CSV file."""

    REQUIRED_COLUMNS = {
        "urun_id",
        "tarih",
        "gunluk_cikis_miktari",
        "mevcut_stok",
        "min_stok",
    }

    def __init__(self, csv_path: str | Path) -> None:
        self._csv_path = Path(csv_path)

    def build_features(self, urun_id: int, tenant_id: str | None = None) -> InputFeatures:
        df = pd.read_csv(self._csv_path)
        eksik_kolonlar = self.REQUIRED_COLUMNS - set(df.columns)
        if eksik_kolonlar:
            raise ValueError(f"CSV veri sozlesmesi eksik kolonlar: {sorted(eksik_kolonlar)}")

        urun_df = df[df["urun_id"] == urun_id].copy()
        if tenant_id and "tenant_id" in urun_df.columns:
            urun_df = urun_df[urun_df["tenant_id"] == tenant_id]
        if urun_df.empty:
            raise ValueError(f"CSV icinde urun_id={urun_id} icin veri bulunamadi.")

        urun_df["tarih"] = pd.to_datetime(urun_df["tarih"]).dt.date
        urun_df = urun_df.sort_values("tarih").tail(90)

        latest = urun_df.iloc[-1]
        return InputFeatures(
            urun_id=urun_id,
            tenant_id=tenant_id or latest.get("tenant_id"),
            stok_cikis_gecmisi=[
                DailyStockExit(
                    tarih=row.tarih,
                    miktar=float(row.gunluk_cikis_miktari),
                )
                for row in urun_df.itertuples(index=False)
            ],
            mevcut_stok=float(latest.mevcut_stok),
            min_stok=float(latest.min_stok),
        )
