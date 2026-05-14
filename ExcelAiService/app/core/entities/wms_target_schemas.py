"""WMS hedef sema sabitleri.

Bu modul ExcelAiService'in sutun esleme onerisi uretirken kullandigi
hedef semalari tanimlar. **BackendProje'nin gercek SQLAlchemy modeli
DEGILDIR**: yalnizca esleme/onerme amacli kanonik isim + alias listesidir.

Faz 1 (2026-05-14): siparis_kalemleri, stok_sayim_kalemleri, urun.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TargetField:
    """Hedef bir sutun: kanonik ad + Turkce/Ingilizce alias kumesi."""

    name: str
    aliases: tuple[str, ...]
    required: bool = False
    description: str = ""

    @property
    def all_terms(self) -> tuple[str, ...]:
        """Eslestirmede kullanilan tum terim kumesi (name + aliases)."""
        return (self.name, *self.aliases)


@dataclass(frozen=True)
class TargetSchema:
    name: str
    label: str
    fields: tuple[TargetField, ...] = field(default_factory=tuple)

    @property
    def required_field_names(self) -> tuple[str, ...]:
        return tuple(f.name for f in self.fields if f.required)


SIPARIS_KALEMLERI = TargetSchema(
    name="siparis_kalemleri",
    label="Siparis Kalemleri",
    fields=(
        TargetField(
            name="siparis_no",
            aliases=("siparis numarasi", "siparis id", "order no", "order number", "order id"),
            required=True,
            description="Siparis basligi referansi.",
        ),
        TargetField(
            name="urun_kodu",
            aliases=("sku", "stok kodu", "urun kod", "product code", "item code", "kod"),
            required=True,
            description="Urun karti referansi.",
        ),
        TargetField(
            name="urun_adi",
            aliases=("urun ad", "urun ismi", "product name", "item name", "ad", "isim"),
            description="Aciklayici urun adi (opsiyonel).",
        ),
        TargetField(
            name="miktar",
            aliases=("adet", "quantity", "qty", "siparis miktari", "talep"),
            required=True,
            description="Siparis edilen miktar.",
        ),
        TargetField(
            name="birim",
            aliases=("olcu birimi", "unit", "uom", "olcum"),
            description="Olcu birimi (ADET, KG, LT vs.).",
        ),
        TargetField(
            name="birim_fiyat",
            aliases=("fiyat", "unit price", "price", "birim fiyati"),
        ),
        TargetField(
            name="toplam_fiyat",
            aliases=("toplam", "total", "tutar", "amount", "satir tutari"),
        ),
        TargetField(
            name="musteri",
            aliases=("musteri adi", "alici", "customer", "buyer", "client"),
        ),
        TargetField(
            name="teslim_tarihi",
            aliases=("sevk tarihi", "delivery date", "tarih", "termin"),
        ),
    ),
)


STOK_SAYIM_KALEMLERI = TargetSchema(
    name="stok_sayim_kalemleri",
    label="Stok Sayim Kalemleri",
    fields=(
        TargetField(
            name="sayim_no",
            aliases=("sayim numarasi", "sayim id", "count no", "count id"),
            required=True,
        ),
        TargetField(
            name="urun_kodu",
            aliases=("sku", "stok kodu", "urun kod", "product code", "item code"),
            required=True,
        ),
        TargetField(
            name="urun_adi",
            aliases=("urun ad", "urun ismi", "product name", "ad"),
        ),
        TargetField(
            name="lokasyon",
            aliases=("konum", "raf", "raf kodu", "hucre", "location", "bin", "lokasyon kodu"),
            description="Stok lokasyon kodu.",
        ),
        TargetField(
            name="lot_no",
            aliases=("parti no", "lot", "batch", "batch no", "parti"),
        ),
        TargetField(
            name="sistem_miktari",
            aliases=("beklenen", "sistem stok", "expected", "expected qty", "beklenen miktar"),
            description="Sistemde olmasi beklenen miktar.",
        ),
        TargetField(
            name="sayim_miktari",
            aliases=("fiili", "gerçek", "actual", "actual qty", "fiili miktar", "sayilan"),
            required=True,
            description="Sayim sirasinda olculen miktar.",
        ),
        TargetField(
            name="fark",
            aliases=("difference", "diff", "sayim farki", "sapma"),
        ),
        TargetField(
            name="sayim_tarihi",
            aliases=("count date", "tarih", "sayim zamani"),
        ),
    ),
)


URUN = TargetSchema(
    name="urun",
    label="Urun Karti",
    fields=(
        TargetField(
            name="urun_kodu",
            aliases=("sku", "stok kodu", "urun kod", "product code", "item code", "kod"),
            required=True,
        ),
        TargetField(
            name="urun_adi",
            aliases=("urun ad", "urun ismi", "product name", "ad", "isim", "name"),
            required=True,
        ),
        TargetField(
            name="barkod",
            aliases=("ean", "ean13", "gtin", "barcode", "barkod no"),
        ),
        TargetField(
            name="birim",
            aliases=("olcu birimi", "unit", "uom"),
        ),
        TargetField(
            name="agirlik",
            aliases=("weight", "kg", "brut agirlik", "net agirlik", "gross weight"),
        ),
        TargetField(
            name="hacim",
            aliases=("volume", "m3", "vol", "hacim degeri"),
        ),
        TargetField(
            name="kategori",
            aliases=("category", "grup", "urun grubu", "kategori adi"),
        ),
        TargetField(
            name="marka",
            aliases=("brand", "uretici", "manufacturer"),
        ),
        TargetField(
            name="aciklama",
            aliases=("description", "not", "tanim", "detay"),
        ),
    ),
)


TARGET_SCHEMAS: dict[str, TargetSchema] = {
    schema.name: schema
    for schema in (SIPARIS_KALEMLERI, STOK_SAYIM_KALEMLERI, URUN)
}


def list_target_schemas() -> list[TargetSchema]:
    return list(TARGET_SCHEMAS.values())


def get_target_schema(name: str) -> TargetSchema:
    try:
        return TARGET_SCHEMAS[name]
    except KeyError as exc:
        valid = sorted(TARGET_SCHEMAS.keys())
        raise ValueError(
            f"Bilinmeyen hedef sema: '{name}'. Gecerli secenekler: {valid}"
        ) from exc
