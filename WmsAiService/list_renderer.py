"""
Çok-satır LIST sonuçları için deterministik Türkçe template renderer.

Strateji:
- Kolon kombinasyonu (column signature) anahtarına göre özelleşmiş şablonlar:
    * (kategori_adi, urun_sayisi)            -> grup-sayım anlatımı
    * (marka_adi, urun_sayisi)               -> grup-sayım anlatımı
    * (stok_durumu, COUNT)                   -> durum dağılımı
    * (urun_adi, guncel_stok_miktari, ...)   -> ürün listesi
    * (urun_adi, marka_adi)                  -> isim listesi
    * default                                 -> generic "N kayıt bulundu"
- LLM tamamen by-pass; qwen2.5-coder:7b'nin Türkçe morfoloji bozukluklarına maruz kalmaz.
- İlk 5 satır cümle içine gömülür, geri kalan "ve N tanesi daha" şeklinde özetlenir.
"""

from __future__ import annotations

from typing import Any, Callable

from result_formatter import StructuredResult

MAX_INLINE_ITEMS = 5  # cümleye gömülecek maksimum satır sayısı


# ----------------------------------------------------------------------------
# Yardımcılar
# ----------------------------------------------------------------------------

def _fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        if value == int(value):
            return str(int(value))
        return f"{value:.2f}"
    return str(value).strip()


def _join_tr(items: list[str]) -> str:
    """Türkçe doğru bağlaçla birleştir: 'a, b ve c'."""
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} ve {items[1]}"
    return ", ".join(items[:-1]) + " ve " + items[-1]


def _has_columns(structured: StructuredResult, required: set[str]) -> bool:
    return required.issubset(set(structured.columns))


# ----------------------------------------------------------------------------
# Şablonlar — her biri (sonuç) -> str veya None döndürür.
# Hiçbir şablon eşleşmezse generic fallback kullanılır.
# ----------------------------------------------------------------------------

def _tpl_kategori_sayim(s: StructuredResult) -> str | None:
    if not _has_columns(s, {"kategori_adi", "urun_sayisi"}):
        return None
    inline = [
        f"{_fmt(r['kategori_adi'])} kategorisinde {_fmt(r['urun_sayisi'])}"
        for r in s.rows[:MAX_INLINE_ITEMS]
    ]
    suffix = f" ve {s.row_count - MAX_INLINE_ITEMS} kategori daha" if s.row_count > MAX_INLINE_ITEMS else ""
    return _join_tr(inline) + " ürün bulunuyor" + suffix + "."


def _tpl_marka_sayim(s: StructuredResult) -> str | None:
    if not _has_columns(s, {"marka_adi", "urun_sayisi"}):
        return None
    inline = [
        f"{_fmt(r['marka_adi'])} markasında {_fmt(r['urun_sayisi'])}"
        for r in s.rows[:MAX_INLINE_ITEMS]
    ]
    suffix = f" ve {s.row_count - MAX_INLINE_ITEMS} marka daha" if s.row_count > MAX_INLINE_ITEMS else ""
    return _join_tr(inline) + " ürün var" + suffix + "."


def _tpl_marka_toplam(s: StructuredResult) -> str | None:
    if not _has_columns(s, {"marka_adi", "toplam_miktar"}):
        return None
    parts = [
        f"{_fmt(r['marka_adi'])}: {_fmt(r['toplam_miktar'])}"
        for r in s.rows[:MAX_INLINE_ITEMS]
    ]
    suffix = f"; {s.row_count - MAX_INLINE_ITEMS} marka daha" if s.row_count > MAX_INLINE_ITEMS else ""
    return "Toplam stok miktarları — " + _join_tr(parts) + suffix + "."


def _tpl_stok_durumu_dagilim(s: StructuredResult) -> str | None:
    # SELECT stok_durumu, COUNT(*) AS adet/urun_sayisi ...
    sayim_kolonu = next((c for c in s.columns if c in {"adet", "urun_sayisi", "kayit_sayisi"}), None)
    if not (sayim_kolonu and "stok_durumu" in s.columns):
        return None
    parts = [
        f"{_fmt(r['stok_durumu'])} {_fmt(r[sayim_kolonu])}"
        for r in s.rows[:MAX_INLINE_ITEMS]
    ]
    return "Stok durumu dağılımı: " + _join_tr(parts) + " ürün."


def _tpl_urun_stok(s: StructuredResult) -> str | None:
    """Ürün + stok miktarı içeren listeler (en çok/en az/eşik altı)."""
    if "urun_adi" not in s.columns or "guncel_stok_miktari" not in s.columns:
        return None
    inline = []
    for r in s.rows[:MAX_INLINE_ITEMS]:
        ad = _fmt(r["urun_adi"])
        miktar = _fmt(r["guncel_stok_miktari"])
        birim = _fmt(r.get("birim", "")).lower() if "birim" in s.columns and r.get("birim") else ""
        if birim:
            inline.append(f"{ad} ({miktar} {birim})")
        else:
            inline.append(f"{ad} ({miktar})")
    suffix = f" ve {s.row_count - MAX_INLINE_ITEMS} ürün daha" if s.row_count > MAX_INLINE_ITEMS else ""
    return f"Toplam {s.row_count} ürün bulundu: " + _join_tr(inline) + suffix + "."


def _tpl_urun_listesi(s: StructuredResult) -> str | None:
    """Sadece ürün isimleri (+ opsiyonel marka/kategori)."""
    if "urun_adi" not in s.columns:
        return None
    secondary = next((c for c in ("marka_adi", "kategori_adi") if c in s.columns), None)
    inline = []
    for r in s.rows[:MAX_INLINE_ITEMS]:
        ad = _fmt(r["urun_adi"])
        if secondary and r.get(secondary):
            inline.append(f"{ad} ({_fmt(r[secondary])})")
        else:
            inline.append(ad)
    suffix = f" ve {s.row_count - MAX_INLINE_ITEMS} ürün daha" if s.row_count > MAX_INLINE_ITEMS else ""
    return f"Toplam {s.row_count} ürün bulundu: " + _join_tr(inline) + suffix + "."


def _tpl_generic(s: StructuredResult) -> str:
    """Hiçbir özel şablon eşleşmediğinde — yine de düzgün Türkçe."""
    inline_parts = []
    for r in s.rows[:3]:
        kv = ", ".join(f"{_humanize(k)} {_fmt(v)}" for k, v in r.items())
        inline_parts.append(f"({kv})")
    suffix = f" ve {s.row_count - 3} kayıt daha" if s.row_count > 3 else ""
    return f"Toplam {s.row_count} kayıt bulundu: " + "; ".join(inline_parts) + suffix + "."


_HUMAN_LABEL_QUICK: dict[str, str] = {
    "urun_adi": "ürün",
    "kategori_adi": "kategori",
    "marka_adi": "marka",
    "guncel_stok_miktari": "stok",
    "kritik_stok_siniri": "kritik sınır",
    "birim": "birim",
    "stok_durumu": "durum",
    "barkod": "barkod",
    "urun_sayisi": "sayı",
    "toplam_miktar": "toplam",
    "adet": "adet",
}


def _humanize(col: str) -> str:
    return _HUMAN_LABEL_QUICK.get(col, col.replace("_", " "))


# ----------------------------------------------------------------------------
# Dispatcher
# ----------------------------------------------------------------------------

# Sıralı: önce daha spesifik şablonlar denenir
_TEMPLATES: list[Callable[[StructuredResult], str | None]] = [
    _tpl_stok_durumu_dagilim,
    _tpl_kategori_sayim,
    _tpl_marka_sayim,
    _tpl_marka_toplam,
    _tpl_urun_stok,
    _tpl_urun_listesi,
]


def render_list(structured: StructuredResult) -> str:
    """Bir LIST sonucu için Türkçe cümle üret. LLM çağrısı yoktur."""
    for tpl in _TEMPLATES:
        rendered = tpl(structured)
        if rendered:
            return rendered
    return _tpl_generic(structured)
