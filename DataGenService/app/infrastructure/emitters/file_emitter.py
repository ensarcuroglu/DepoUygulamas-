"""Dosya emitter — Parquet (default) veya CSV.

Streaming yazım: `pyarrow.parquet.ParquetWriter` ilk batch'te lazy açılır,
her batch tek RowGroup olarak yazılır. CSV modunda satırlar append edilir.

Determinism: aynı (seed, factory_output, output_dir) kombinasyonu aynı
dosya içeriğini üretir. Dosya adına timestamp yerine sequence numarası
yazılmaz; çağıran tarafı isim'i yönetir.

Async signature `IEmitter` ile uyumlu olsun diye; gerçek I/O sync — küçük
dosyalar için event loop'u bloklamaz, büyük dosyalar için `asyncio.to_thread`
ile sarılabilir (gerekirse).
"""

from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import Literal, Sequence

import pyarrow as pa
import pyarrow.parquet as pq
from pydantic import BaseModel

from .base import EmitSummary

FileFormat = Literal["parquet", "csv"]


class FileEmitter:
    """`IEmitter` implementasyonu — DTO listesini dosyaya yazar."""

    def __init__(
        self,
        output_path: Path,
        *,
        file_format: FileFormat = "parquet",
        compression: str = "snappy",
    ) -> None:
        self.output_path = Path(output_path)
        self.file_format: FileFormat = file_format
        self.compression = compression
        self._summary = EmitSummary()
        self._parquet_writer: pq.ParquetWriter | None = None
        self._parquet_schema: pa.Schema | None = None
        self._csv_writer: csv.DictWriter | None = None
        self._csv_file = None
        self._closed = False

        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # IEmitter
    # ------------------------------------------------------------------

    async def emit_batch(self, items: Sequence[BaseModel]) -> None:
        if self._closed:
            raise RuntimeError("FileEmitter zaten kapalı.")
        if not items:
            return

        t0 = time.perf_counter()
        rows = [item.model_dump(mode="python") for item in items]

        try:
            if self.file_format == "parquet":
                self._write_parquet(rows)
            else:
                self._write_csv(rows)
        except Exception as exc:
            self._summary.failed += len(items)
            self._summary.errors.append(f"{type(exc).__name__}: {exc}")
            raise
        else:
            self._summary.success += len(items)
        finally:
            self._summary.total += len(items)
            self._summary.latencies_ms.append(
                (time.perf_counter() - t0) * 1000.0
            )

    async def close(self) -> None:
        if self._closed:
            return
        if self._parquet_writer is not None:
            self._parquet_writer.close()
            self._parquet_writer = None
        if self._csv_file is not None:
            self._csv_file.close()
            self._csv_file = None
            self._csv_writer = None
        self._summary.mark_finished()
        self._closed = True

    def summary(self) -> EmitSummary:
        return self._summary

    async def __aenter__(self) -> FileEmitter:
        return self

    async def __aexit__(self, *exc_info) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _write_parquet(self, rows: list[dict[str, object]]) -> None:
        table = pa.Table.from_pylist(rows)
        if self._parquet_writer is None:
            self._parquet_schema = table.schema
            self._parquet_writer = pq.ParquetWriter(
                self.output_path,
                self._parquet_schema,
                compression=self.compression,
            )
        else:
            # Sonraki batch'lerde şema sürüklemesini engelle.
            table = table.cast(self._parquet_schema)
        self._parquet_writer.write_table(table)

    def _write_csv(self, rows: list[dict[str, object]]) -> None:
        if self._csv_writer is None:
            self._csv_file = self.output_path.open(
                "w", encoding="utf-8", newline=""
            )
            self._csv_writer = csv.DictWriter(self._csv_file, fieldnames=list(rows[0].keys()))
            self._csv_writer.writeheader()
        self._csv_writer.writerows(rows)
