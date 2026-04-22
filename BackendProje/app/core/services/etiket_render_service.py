"""Etiket render service — şablonlardaki placeholder'ları palet verisiyle doldurur.

Desteklenen placeholder'lar:
    {palet_no}, {lot_no}, {urun_isim}, {skt}, {koli}, {vardiya},
    {uretim_tarihi}, {barkod}, {qr}

`{barkod}` ve `{qr}` değerleri varsayılan olarak palet_no'dur ve use case
katmanı bunları özelleştirebilir.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from app.core.entities.palet import Palet


class EtiketRenderService:

    PLACEHOLDER_ANAHTARLARI = (
        "palet_no", "lot_no", "urun_isim", "skt", "koli",
        "vardiya", "uretim_tarihi", "barkod", "qr",
    )

    def render(
        self,
        template: str,
        palet: Palet,
        barkod_deger: str,
        qr_deger: Optional[str] = None,
    ) -> str:
        degerler = self._palet_degerleri(palet, barkod_deger, qr_deger)
        sonuc = template
        for anahtar in self.PLACEHOLDER_ANAHTARLARI:
            sonuc = sonuc.replace("{" + anahtar + "}", degerler.get(anahtar, ""))
        return sonuc

    def _palet_degerleri(
        self, palet: Palet, barkod_deger: str, qr_deger: Optional[str]
    ) -> dict[str, str]:
        urun_isim = ""
        skt: Optional[date] = None
        if palet.lot:
            skt = palet.lot.son_kullanma_tarihi
            if palet.lot.urun:
                urun_isim = palet.lot.urun.isim or ""

        return {
            "palet_no": palet.palet_no or "",
            "lot_no": palet.lot_no or (palet.lot.lot_no if palet.lot else "") or "",
            "urun_isim": urun_isim,
            "skt": skt.isoformat() if skt else "",
            "koli": str(palet.koli_adedi),
            "vardiya": palet.vardiya or "",
            "uretim_tarihi": palet.uretim_tarihi.isoformat() if palet.uretim_tarihi else "",
            "barkod": barkod_deger,
            "qr": qr_deger or barkod_deger,
        }
