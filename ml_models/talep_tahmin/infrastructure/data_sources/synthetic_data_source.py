from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from random import Random

from ml_models.talep_tahmin.domain.entities import DailyStockExit, InputFeatures


@dataclass(frozen=True)
class SyntheticProductProfile:
    urun_id: int
    mevcut_stok: float
    min_stok: float
    base_daily_demand: float
    weekly_seasonality: float = 0.2
    trend_per_30_days: float = 0.0


class SyntheticDemandDataSource:
    """Deterministic demo data source for SaaS pre-sales and local tests."""

    def __init__(self, seed: int = 42) -> None:
        self._seed = seed

    def build_features(
        self,
        profile: SyntheticProductProfile,
        days: int = 90,
        tenant_id: str | None = "demo-tenant",
    ) -> InputFeatures:
        if days < 0 or days > 90:
            raise ValueError("days 0 ile 90 arasinda olmalidir.")

        rng = Random(self._seed + profile.urun_id)
        baslangic = date.today() - timedelta(days=max(days - 1, 0))
        seri: list[DailyStockExit] = []

        for index in range(days):
            tarih = baslangic + timedelta(days=index)
            hafta_sonu_carpani = (
                1 + profile.weekly_seasonality
                if tarih.weekday() in (5, 6)
                else 1
            )
            trend_carpani = 1 + ((index / 30) * profile.trend_per_30_days)
            noise = rng.uniform(-0.08, 0.08)
            miktar = max(
                0.0,
                profile.base_daily_demand * hafta_sonu_carpani * trend_carpani * (1 + noise),
            )
            seri.append(DailyStockExit(tarih=tarih, miktar=round(miktar, 2)))

        return InputFeatures(
            urun_id=profile.urun_id,
            tenant_id=tenant_id,
            stok_cikis_gecmisi=seri,
            mevcut_stok=profile.mevcut_stok,
            min_stok=profile.min_stok,
        )

    def demo_profiles(self) -> list[SyntheticProductProfile]:
        return [
            SyntheticProductProfile(
                urun_id=1,
                mevcut_stok=420,
                min_stok=80,
                base_daily_demand=9,
                trend_per_30_days=0.03,
            ),
            SyntheticProductProfile(
                urun_id=2,
                mevcut_stok=85,
                min_stok=50,
                base_daily_demand=7,
                trend_per_30_days=0.08,
            ),
            SyntheticProductProfile(
                urun_id=3,
                mevcut_stok=12,
                min_stok=25,
                base_daily_demand=2,
                trend_per_30_days=-0.04,
            ),
        ]
