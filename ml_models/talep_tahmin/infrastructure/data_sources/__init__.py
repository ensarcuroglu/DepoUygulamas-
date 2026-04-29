"""Data source adapters for local model development."""

from ml_models.talep_tahmin.infrastructure.data_sources.synthetic_data_source import (
    SyntheticDemandDataSource,
    SyntheticProductProfile,
)

__all__ = [
    "CsvDemandDataSource",
    "PublicDatasetAdapter",
    "PublicDatasetColumnMap",
    "SyntheticDemandDataSource",
    "SyntheticProductProfile",
]


def __getattr__(name: str):
    """Lazy-load pandas-backed adapters only when explicitly requested."""

    if name == "CsvDemandDataSource":
        from ml_models.talep_tahmin.infrastructure.data_sources.csv_data_source import (
            CsvDemandDataSource,
        )

        return CsvDemandDataSource
    if name in {"PublicDatasetAdapter", "PublicDatasetColumnMap"}:
        from ml_models.talep_tahmin.infrastructure.data_sources.public_dataset_adapter import (
            PublicDatasetAdapter,
            PublicDatasetColumnMap,
        )

        return {
            "PublicDatasetAdapter": PublicDatasetAdapter,
            "PublicDatasetColumnMap": PublicDatasetColumnMap,
        }[name]
    raise AttributeError(name)
