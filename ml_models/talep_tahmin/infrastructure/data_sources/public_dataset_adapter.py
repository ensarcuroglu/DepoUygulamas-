from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class PublicDatasetColumnMap:
    """Map an external public dataset into the canonical demand CSV schema."""

    urun_id: str
    tarih: str
    gunluk_cikis_miktari: str
    mevcut_stok: str | None = None
    min_stok: str | None = None
    tenant_id: str | None = None


class PublicDatasetAdapter:
    """Convert public/open datasets to the project's canonical model input schema."""

    def __init__(self, column_map: PublicDatasetColumnMap) -> None:
        self._column_map = column_map

    def to_canonical_frame(
        self,
        frame: pd.DataFrame,
        default_mevcut_stok: float = 0,
        default_min_stok: float = 0,
        default_tenant_id: str | None = "public-demo",
    ) -> pd.DataFrame:
        mapped = pd.DataFrame(
            {
                "urun_id": frame[self._column_map.urun_id],
                "tarih": pd.to_datetime(frame[self._column_map.tarih]).dt.date,
                "gunluk_cikis_miktari": frame[self._column_map.gunluk_cikis_miktari],
                "mevcut_stok": (
                    frame[self._column_map.mevcut_stok]
                    if self._column_map.mevcut_stok
                    else default_mevcut_stok
                ),
                "min_stok": (
                    frame[self._column_map.min_stok]
                    if self._column_map.min_stok
                    else default_min_stok
                ),
                "tenant_id": (
                    frame[self._column_map.tenant_id]
                    if self._column_map.tenant_id
                    else default_tenant_id
                ),
            }
        )

        return (
            mapped.groupby(["tenant_id", "urun_id", "tarih"], as_index=False)
            .agg(
                gunluk_cikis_miktari=("gunluk_cikis_miktari", "sum"),
                mevcut_stok=("mevcut_stok", "last"),
                min_stok=("min_stok", "last"),
            )
            .sort_values(["tenant_id", "urun_id", "tarih"])
        )
