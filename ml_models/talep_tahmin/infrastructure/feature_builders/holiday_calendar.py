"""TR tatil takvimi yardimci modulu.

`holidays` paketi varsa onun TR takvimi kullanilir; yoksa minimal
hardcoded set fallback olur. Production'da `holidays` paketinin
kurulu olmasi tercih edilir.
"""

from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache


# Yillik degismeyen TR resmi tatilleri (yedek fallback icin)
_SABIT_TR_TATILLER = (
    (1, 1),    # Yilbasi
    (4, 23),   # Ulusal Egemenlik ve Cocuk Bayrami
    (5, 1),    # Emek ve Dayanisma Gunu
    (5, 19),   # Atatu rk'u Anma Genclik ve Spor Bayrami
    (7, 15),   # Demokrasi ve Milli Birlik Gunu
    (8, 30),   # Zafer Bayrami
    (10, 29),  # Cumhuriyet Bayrami
)


@lru_cache(maxsize=8)
def tr_tatil_gunleri(yil_baslangic: int, yil_bitis: int) -> frozenset[date]:
    """[yil_baslangic, yil_bitis] araliginda TR tatil gunleri."""
    if yil_bitis < yil_baslangic:
        yil_baslangic, yil_bitis = yil_bitis, yil_baslangic

    try:
        import holidays  # type: ignore[import-not-found]

        tr = holidays.country_holidays("TR", years=range(yil_baslangic, yil_bitis + 1))
        return frozenset(tr.keys())
    except ImportError:
        gunler: set[date] = set()
        for yil in range(yil_baslangic, yil_bitis + 1):
            for ay, gun in _SABIT_TR_TATILLER:
                gunler.add(date(yil, ay, gun))
        return frozenset(gunler)


def tatil_aralik_listesi(baslangic: date, bitis: date) -> list[date]:
    """Belirli aralikta dusen tatil gunlerinin listesi."""
    if bitis < baslangic:
        baslangic, bitis = bitis, baslangic
    butun_tatiller = tr_tatil_gunleri(baslangic.year, bitis.year)
    aralikta = [g for g in butun_tatiller if baslangic <= g <= bitis]
    return sorted(aralikta)


def gun_tatil_mi(tarih: date) -> bool:
    """Tek tarih icin hizli kontrol."""
    return tarih in tr_tatil_gunleri(tarih.year, tarih.year)


def gelecek_tatil_aralik(tahmin_baslangic: date, gun_sayisi: int) -> list[date]:
    """Tahmin ufku icindeki tatilleri dondur (Faz 3 entegrasyon noktasi)."""
    return tatil_aralik_listesi(
        tahmin_baslangic,
        tahmin_baslangic + timedelta(days=gun_sayisi),
    )
