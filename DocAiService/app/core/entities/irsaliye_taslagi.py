"""Pydantic schema for an extracted delivery-note draft."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


class ConfidenceMixin(BaseModel):
    confidence: float = Field(..., ge=0.0, le=1.0)


class MetinAlani(ConfidenceMixin):
    value: str = Field(..., min_length=1)

    @field_validator("value")
    @classmethod
    def _strip_value(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value must not be empty")
        return stripped


class TarihAlani(ConfidenceMixin):
    value: date


class SayisalAlan(ConfidenceMixin):
    value: Decimal = Field(..., ge=0)


class IrsaliyeKalemiSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    urun_kodu: MetinAlani
    ad: MetinAlani
    miktar: SayisalAlan
    birim: MetinAlani

    @computed_field
    @property
    def confidence_score(self) -> float:
        values = [
            self.urun_kodu.confidence,
            self.ad.confidence,
            self.miktar.confidence,
            self.birim.confidence,
        ]
        return round(sum(values) / len(values), 4)


class IrsaliyeTaslagiSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    belge_tipi: Literal["IRSALIYE"] = "IRSALIYE"
    tedarikci: MetinAlani
    irsaliye_no: MetinAlani
    tarih: TarihAlani
    kalemler: list[IrsaliyeKalemiSchema] = Field(..., min_length=1)
    toplam: SayisalAlan | None = None

    @computed_field
    @property
    def confidence_score(self) -> float:
        values = [
            self.tedarikci.confidence,
            self.irsaliye_no.confidence,
            self.tarih.confidence,
        ]
        for kalem in self.kalemler:
            values.extend(
                [
                    kalem.urun_kodu.confidence,
                    kalem.ad.confidence,
                    kalem.miktar.confidence,
                    kalem.birim.confidence,
                ]
            )
        if self.toplam is not None:
            values.append(self.toplam.confidence)
        return round(sum(values) / len(values), 4)
