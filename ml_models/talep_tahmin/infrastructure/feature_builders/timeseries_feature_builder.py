"""Zaman serisi feature engineering — sklearn predictor icin.

Lag, rolling, gun-of-week, ay, hafta sonu, tatil flag uretir.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional


@dataclass(frozen=True)
class FeatureRow:
    """Tek bir gun icin training/inference satiri."""

    tarih: date
    target: float  # gercek deger (training); inference'da en son tahmin
    lag_1: float
    lag_7: float
    lag_14: float
    lag_30: float
    rolling_mean_7: float
    rolling_mean_30: float
    rolling_std_7: float
    dow: int  # 0=Pzt..6=Pzr
    is_weekend: int
    month: int
    is_holiday: int
    kategori_id: int
    marka_id: int


class TimeSeriesFeatureBuilder:
    """Gunluk talep serisinden sklearn icin feature matrisi olusturur.

    Eksik gunler (cikis olmamis gunler) sifirla doldurulmaz —
    cikis gunluk granularite ile zaten her gun bir nokta tasidigi icin
    cagrici dolduruyor olmalidir. Builder eksiklikten emin olamaz,
    bu yuzden cagrici tarafinda densify edilir.
    """

    LAG_GUNLERI = (1, 7, 14, 30)
    ROLLING_PENCERELERI = (7, 30)
    MIN_GUN = 30  # bu gunden az veri varsa baseline'a fallback

    def build_training_matrix(
        self,
        gunluk_seri: list[tuple[date, float]],
        tatil_gunleri: set[date],
        kategori_id: int,
        marka_id: int,
    ) -> list[FeatureRow]:
        """Egitim icin lag/rolling pencereleri tamamlanan tum gunlerin satirlari."""
        if len(gunluk_seri) < self.MIN_GUN:
            return []

        gunluk_seri = sorted(gunluk_seri, key=lambda item: item[0])
        rows: list[FeatureRow] = []
        baslangic_indeksi = max(self.LAG_GUNLERI[-1], self.ROLLING_PENCERELERI[-1])

        for i in range(baslangic_indeksi, len(gunluk_seri)):
            tarih_i, value_i = gunluk_seri[i]
            row = self._build_row(
                tarih=tarih_i,
                target=value_i,
                gecmis=[item[1] for item in gunluk_seri[:i]],
                tatil_gunleri=tatil_gunleri,
                kategori_id=kategori_id,
                marka_id=marka_id,
            )
            rows.append(row)
        return rows

    def build_inference_row(
        self,
        tarih: date,
        gecmis: list[float],
        tatil_gunleri: set[date],
        kategori_id: int,
        marka_id: int,
    ) -> FeatureRow:
        """Recursive multi-step forecast'in tek adimi icin satir."""
        return self._build_row(
            tarih=tarih,
            target=0.0,  # inference: target bilinmez
            gecmis=gecmis,
            tatil_gunleri=tatil_gunleri,
            kategori_id=kategori_id,
            marka_id=marka_id,
        )

    @staticmethod
    def _build_row(
        tarih: date,
        target: float,
        gecmis: list[float],
        tatil_gunleri: set[date],
        kategori_id: int,
        marka_id: int,
    ) -> FeatureRow:
        n = len(gecmis)
        lag_1 = gecmis[-1] if n >= 1 else 0.0
        lag_7 = gecmis[-7] if n >= 7 else lag_1
        lag_14 = gecmis[-14] if n >= 14 else lag_1
        lag_30 = gecmis[-30] if n >= 30 else lag_1

        son_7 = gecmis[-7:] if n >= 7 else gecmis or [0.0]
        son_30 = gecmis[-30:] if n >= 30 else (gecmis or [0.0])
        rolling_mean_7 = sum(son_7) / len(son_7)
        rolling_mean_30 = sum(son_30) / len(son_30)
        rolling_std_7 = _stdev(son_7)

        dow = tarih.weekday()
        return FeatureRow(
            tarih=tarih,
            target=target,
            lag_1=lag_1,
            lag_7=lag_7,
            lag_14=lag_14,
            lag_30=lag_30,
            rolling_mean_7=rolling_mean_7,
            rolling_mean_30=rolling_mean_30,
            rolling_std_7=rolling_std_7,
            dow=dow,
            is_weekend=1 if dow in (5, 6) else 0,
            month=tarih.month,
            is_holiday=1 if tarih in tatil_gunleri else 0,
            kategori_id=kategori_id or 0,
            marka_id=marka_id or 0,
        )


def _stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg = sum(values) / len(values)
    var = sum((v - avg) ** 2 for v in values) / (len(values) - 1)
    return var**0.5


def gunluk_seriyi_densify(
    gunluk_seri: list[tuple[date, float]],
    pencere_baslangic: Optional[date] = None,
    pencere_bitis: Optional[date] = None,
) -> list[tuple[date, float]]:
    """Bos gunleri 0.0 ile dolduran helper.

    `gunluk_seri` siralanmamis veya bos gunlere sahip olabilir.
    pencere_baslangic/bitis verilmezse var olan min/max kullanilir.
    """
    if not gunluk_seri:
        return []
    by_date = {tarih: float(value) for tarih, value in gunluk_seri}
    baslangic = pencere_baslangic or min(by_date)
    bitis = pencere_bitis or max(by_date)
    sonuc: list[tuple[date, float]] = []
    cursor = baslangic
    while cursor <= bitis:
        sonuc.append((cursor, by_date.get(cursor, 0.0)))
        cursor += timedelta(days=1)
    return sonuc
